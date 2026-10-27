"""Engine for interior design projects in FreeCAD, run through MCP (execute_code).

A project (projects/<name>/project.py) calls new_project(), draws with wall/hinged/sliding/window/box/...,
registers uses and constraints (seat, access_zone, clearance, destination, room, tv, ...), then calls verify()
and optionally export(). Coordinates in metres, y points north. Thresholds: docs/design-rules.md.
"""
import FreeCAD as App
import Part
import collections
import datetime
import json
import math
import os

V = App.Vector
S = 1000.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Single source of the numeric thresholds: docs/design-rules.md. Keep the two aligned.
RULES = dict(
    frame=0.05, armored_frame=0.075,          # jamb/subframe per side
    reveal=0.10,                              # wall-opening edge -> perpendicular wall on the hinge side
    handle=0.07,                              # handle projection with the leaf open at 90 degrees
    seat_min=0.75, seat_comfort=0.90,         # surface edge -> obstacle: stand up / walk behind a seated person
    access=0.70,                              # clear depth in front of wardrobes and cabinets
    person_radius=0.30,                       # routes: 60 cm minimum width
    daylight=1 / 8,                           # glazed area / floor area, habitable rooms
    occupancy=0.40,                           # furniture footprint / floor above which a room feels crowded
    tv_window=1.0,                            # minimum TV - window distance on the same wall
    seat_height=(0.25, 0.32),                 # surface - seat height difference
    assembly_margin=0.02,                     # tilt-up diagonal < room height - margin
    tol=1000.0,                               # 1 cm3: below this it is contact, not overlap
)

COL = dict(
    WALL=(0.97, 0.97, 0.96), WHITE=(0.95, 0.95, 0.94), OAK=(0.78, 0.64, 0.46), FLOOR=(0.85, 0.74, 0.58),
    TILE=(0.80, 0.80, 0.79), BLACK=(0.13, 0.13, 0.14), GREY=(0.58, 0.59, 0.61), GLASS=(0.72, 0.86, 0.95),
    FRAME=(0.62, 0.52, 0.40), STEEL=(0.76, 0.77, 0.79), SAGE=(0.60, 0.68, 0.58), GREEN=(0.33, 0.52, 0.30),
    TERRA=(0.74, 0.47, 0.36), DARK=(0.30, 0.30, 0.32), RUG=(0.88, 0.86, 0.82),
)

NOT_VERIFIABLE = [
    ("Building services", "drains, supplies, sockets, panels, HVAC are not modelled"),
    ("Structure", "lintels, load capacity, removability of partitions: survey and structural engineer required"),
    ("Local regulations", "local building code and accessibility requirements to be checked with a licensed professional"),
    ("Products", "indicative footprints: replace with manufacturers' data sheets"),
    ("Lighting, acoustics, thermal comfort", "no quantitative data or method applied"),
    ("Furniture delivery", "lift, stairs and building access routes unknown"),
]

SEVERITY = ("blocking", "significant", "improvement")
VERIFIED, NON_COMPLIANT, NOT_VERIF, NOT_APPL = "VERIFIED", "NON-COMPLIANT", "NOT VERIFIABLE", "NOT APPLICABLE"


class _State:
    pass


ST = _State()


# ============================== document and primitives ==============================
def new_project(name, folder, interior, height=2.70):
    """Create the document. interior = (x0, y0, x1, y1) of the inner face of the perimeter walls."""
    if App.listDocuments().get(name):
        App.closeDocument(name)
    ST.doc = App.newDocument(name)
    ST.name, ST.dir, ST.H, ST.interior = name, folder, height, interior
    ST.groups, ST.CHECK, ST.WALLS, ST.OPEN = {}, [], [], []
    ST.DOORS, ST.SLIDES, ST.SEATS, ST.OPENINGS = [], [], [], []
    ST.ACCESS, ST.CLEAR, ST.TARGETS, ST.ROUTES = [], [], {}, []
    ST.START, ST.ROOMS, ST.WINDOWS, ST.TV, ST.HEIGHTS = None, [], [], [], []
    ST.NOTVERIF = list(NOT_VERIFIABLE)
    ST.ANN = dict(dims=[], labels=[], note="")
    ST.results = []
    return ST.doc


def group(n):
    if n not in ST.groups:
        ST.groups[n] = ST.doc.addObject("App::DocumentObjectGroup", n)
    return ST.groups[n]


def add(name, shape, color, g, check=True, tr=0, item=None):
    """Add a solid. check=True makes it an obstacle for every verification;
    parts of the same piece of furniture share item= so they are not reported against each other."""
    o = ST.doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = color
    o.ViewObject.Transparency = tr
    group(g).addObject(o)
    if check:
        ST.CHECK.append((item or name, o.Label, shape, g))
    return o


def B(x0, y0, z0, x1, y1, z1):
    return Part.makeBox((x1 - x0) * S, (y1 - y0) * S, (z1 - z0) * S, V(x0 * S, y0 * S, z0 * S))


def C(cx, cy, z0, r, h):
    return Part.makeCylinder(r * S, h * S, V(cx * S, cy * S, z0 * S))


def box(name, x0, y0, z0, x1, y1, z1, color, g, **kw):
    return add(name, B(x0, y0, z0, x1, y1, z1), color, g, **kw)


def cyl(name, cx, cy, z0, r, h, color, g, **kw):
    return add(name, C(cx, cy, z0, r, h), color, g, **kw)


def rel_box(hx, hy, d, n, da, db, z0, z1):
    """Box in local coordinates: da along d, db along n, starting from (hx, hy)."""
    xs = [hx + d[0] * a + n[0] * b for a in da for b in db]
    ys = [hy + d[1] * a + n[1] * b for a in da for b in db]
    return B(min(xs), min(ys), z0, max(xs), max(ys), z1)


# ============================== walls and openings ==============================
def opening(label, x0, y0, x1, y1, z1, net_w, net_h, note=""):
    """Rough wall opening for a door. Declare it before the walls it crosses."""
    ST.OPEN.append(B(x0, y0, 0, x1, y1, z1))
    ST.OPENINGS.append((label, net_w, net_h, max(x1 - x0, y1 - y0), z1, note))


def wall(name, x0, y0, x1, y1):
    s = B(x0, y0, 0, x1, y1, ST.H)
    for o in ST.OPEN:
        if s.BoundBox.intersect(o.BoundBox):
            s = s.cut(o)
    ST.WALLS.append((name, s))
    return add(name, s, COL["WALL"], "Structure", check=False)


def jambs(name, x0, y0, x1, y1, z1, fr):
    """Jambs + head inside the rough opening."""
    if (x1 - x0) > (y1 - y0):
        parts = [B(x0, y0, 0, x0 + fr, y1, z1), B(x1 - fr, y0, 0, x1, y1, z1), B(x0, y0, z1 - fr, x1, y1, z1)]
    else:
        parts = [B(x0, y0, 0, x1, y0 + fr, z1), B(x0, y1 - fr, 0, x1, y1, z1), B(x0, y0, z1 - fr, x1, y1, z1)]
    add(name + "_Jambs", Part.makeCompound(parts), COL["WHITE"], "Doors", check=False)


def hinged(name, hx, hy, d, n, w, kind="Door", color=None, hgt=2.10, z0=0.0, leaf=True,
           frame=None, handle=True):
    """Hinged leaf. Hinge (hx, hy) on the wall face of the opening side; d = closed-leaf direction,
    n = opening direction. Generates the leaf open at 90 degrees, the swept volume, handle and reveal checks."""
    frame = RULES["frame"] if frame is None else frame
    leaf_shape = rel_box(hx, hy, d, n, (-0.04, 0), (0, w), z0 + 0.01, hgt)
    if leaf:
        add(name + "_Leaf", leaf_shape, color or COL["OAK"], "Doors", check=False)
    h = V(hx * S, hy * S, z0 * S)
    p1 = h + V(d[0], d[1], 0) * (w * S)
    p2 = h + V(n[0], n[1], 0) * (w * S)
    pm = h + V(d[0] + n[0], d[1] + n[1], 0) * (w * S / math.sqrt(2))
    face = Part.Face(Part.Wire([Part.LineSegment(h, p1).toShape(), Part.Arc(p1, pm, p2).toShape(),
                                Part.LineSegment(p2, h).toShape()]))
    sweep = face.extrude(V(0, 0, (hgt - z0 - 0.02) * S))
    sweep.translate(V(0, 0, 0.01 * S))
    mark = face.extrude(V(0, 0, 0.004 * S))
    mark.translate(V(0, 0, 0.005 * S))
    m = add(name + "_SwingArea", mark, (0.3, 0.8, 0.3), "Swing_Check", check=False, tr=40)
    hnd = probe = None
    if handle:
        m_ = RULES["handle"]
        hnd = rel_box(hx, hy, d, n, (-0.04 - m_, -0.04), (w - 0.12, w - 0.04), 0.95, 1.10)
        probe = rel_box(hx, hy, d, n, (-frame - RULES["reveal"] + 0.005, -frame), (0.005, 0.10), 0.10, 2.0)
    ST.DOORS.append(dict(name=name, sweep=sweep, mark=m, kind=kind, handle=hnd, probe=probe,
                         leaf=leaf_shape if (leaf and z0 < 0.5) else None))


def sliding(name, closed, opened, color=None):
    """Surface-mounted sliding door: closed leaf + track over the full travel; the open position is verified."""
    add(name + "_Leaf", B(*closed), color or COL["OAK"], "Doors", check=False)
    x0, y0, _, x1, y1, _ = opened
    cx0, cy0, _, cx1, cy1, _ = closed
    add(name + "_Track", B(min(x0, cx0), min(y0, cy0), 2.15, max(x1, cx1), max(y1, cy1), 2.22),
        COL["BLACK"], "Doors", check=False)
    m = add(name + "_SlideArea", B(x0, y0, 0.005, x1, y1, 0.009), (0.3, 0.8, 0.3), "Swing_Check",
            check=False, tr=40)
    ST.SLIDES.append(dict(name=name, shape=B(*opened), mark=m, closed=B(*closed), c=closed, o=opened))


def window(name, yc, x0, x1, z0, z1, room, mullion=False):
    """Window on a wall running along x (wall centre y = yc), with subframe; the wall opening is enlarged.
    room = the room it serves, for the daylight ratio."""
    fr = RULES["frame"]
    rx0, rx1 = x0 - fr, x1 + fr
    rz0, rz1 = (z0 - fr if z0 > 0 else 0.0), z1 + fr
    ST.OPEN.append(B(rx0, yc - 0.20, rz0, rx1, yc + 0.20, rz1))
    ST.OPENINGS.append((name, x1 - x0, z1 - z0, rx1 - rx0, rz1 - rz0,
                        "sill %.2f" % z0 if z0 > 0 else "floor level"))
    sf = [B(rx0, yc - 0.06, rz0, x0, yc + 0.06, rz1), B(x1, yc - 0.06, rz0, rx1, yc + 0.06, rz1),
          B(x0, yc - 0.06, z1, x1, yc + 0.06, rz1)]
    if z0 > 0:
        sf.append(B(x0, yc - 0.06, rz0, x1, yc + 0.06, z0))
    add(name + "_Subframe", Part.makeCompound(sf), COL["FRAME"], "Windows", check=False)
    t = 0.05
    frs = [B(x0, yc - 0.05, z0, x0 + t, yc + 0.05, z1), B(x1 - t, yc - 0.05, z0, x1, yc + 0.05, z1),
           B(x0, yc - 0.05, z1 - t, x1, yc + 0.05, z1), B(x0, yc - 0.05, z0, x1, yc + 0.05, z0 + 0.03)]
    if mullion:
        xm = (x0 + x1) / 2
        frs.append(B(xm - t / 2, yc - 0.05, z0, xm + t / 2, yc + 0.05, z1))
    add(name + "_Frame", Part.makeCompound(frs), COL["BLACK"], "Windows", check=False)
    glass = B(x0 + t, yc - 0.01, z0 + 0.03, x1 - t, yc + 0.01, z1 - t)
    add(name + "_Glass", glass, COL["GLASS"], "Windows", check=False, tr=65)
    ST.WINDOWS.append(dict(name=name, yc=yc, x0=x0, x1=x1, z0=z0, z1=z1, room=room, glass=glass))


# ============================== registering uses and constraints ==============================
def seat(name, own, edge_xy, direction, hw):
    """Seat served by a surface: space measured from the surface edge outwards.
    own = items to ignore (the seat itself and the surface)."""
    ST.SEATS.append((name, tuple(own), edge_xy, direction, hw))


def chair(name, cx, cy, bx, by, g, surface_item, edge):
    """Chair around a surface: (bx, by) = direction of the backrest; edge = surface centre -> edge distance."""
    sh = [B(cx - 0.21, cy - 0.21, 0.43, cx + 0.21, cy + 0.21, 0.47), B(cx - 0.04, cy - 0.04, 0, cx + 0.04, cy + 0.04, 0.43)]
    if bx:
        xb = cx + bx * 0.19
        sh.append(B(min(xb, xb + bx * 0.03), cy - 0.21, 0.47, max(xb, xb + bx * 0.03), cy + 0.21, 0.85))
    else:
        yb = cy + by * 0.19
        sh.append(B(cx - 0.21, min(yb, yb + by * 0.03), 0.47, cx + 0.21, max(yb, yb + by * 0.03), 0.85))
    add(name, Part.makeCompound(sh), COL["BLACK"], g)
    tx, ty = cx - bx * 0.75, cy - by * 0.75
    seat(name, (name, surface_item), (tx + bx * edge, ty + by * edge), (bx, by), 0.21)


def access_zone(label, x0, y0, x1, y1, own):
    """Volume that must stay clear in front of wardrobes/cabinets (depth >= RULES['access'])."""
    ST.ACCESS.append((label, B(x0, y0, 0.05, x1, y1, 1.80), tuple(own), min(x1 - x0, y1 - y0)))


def clearance(label, a, b, minimum, comfort=None):
    """Plan distance between two objects (by name) with a minimum and a comfort target."""
    ST.CLEAR.append((label, a, b, minimum, comfort))


def entrance(x, y):
    ST.START = (x, y)


def destination(label, x, y):
    """Point a person must be able to reach from the entrance (in front of furniture or a fixture)."""
    ST.TARGETS[label] = (x, y)


def route(label, src, dst):
    """Route between two destinations: verified and measured (e.g. night route bed -> toilet)."""
    ST.ROUTES.append((label, src, dst))


def room(name, rects, label_xy, habitable=True, kind="", lines=None):
    """Room: net floor rectangles, label position on the plan."""
    area = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in rects)
    ST.ROOMS.append(dict(name=name, rects=rects, xy=label_xy, habitable=habitable, kind=kind,
                         area=area, lines=lines or [name.upper()]))
    return area


def tv(name):
    ST.TV.append(name)


def height_match(label, z_surface, z_seat):
    ST.HEIGHTS.append((label, z_surface, z_seat))


def not_verifiable(category, reason):
    ST.NOTVERIF.append((category, reason))


def dimensions(points, horizontal, base):
    """Dimension chain on the plan (mm in the DWG): points in metres along x (horizontal) or y."""
    ST.ANN["dims"].append(([p * S for p in points], horizontal, base * S))


def label(text, x, y, h=0.07):
    ST.ANN["labels"].append((text, x * S, y * S, h * S))


def note(text):
    ST.ANN["note"] = text


# ============================== verification ==============================
def _r(cat, elem, measure, threshold, status, sev, method, note_=""):
    # severity describes a problem: a passed check keeps it only as an improvement note
    if status == VERIFIED and sev != "improvement":
        sev = ""
    ST.results.append(dict(cat=cat, elem=elem, measure=measure, threshold=threshold, status=status,
                           sev=sev, method=method, note=note_))


def hits_of(shape, skip_items=(), walls=True):
    out = []
    for item, lbl, sh, _g in ST.CHECK:
        if item in skip_items or not shape.BoundBox.intersect(sh.BoundBox):
            continue
        v = shape.common(sh).Volume
        if v > RULES["tol"]:
            out.append("%s (%.0f cm3)" % (lbl, v / 1000))
    if walls:
        for wname, ws in ST.WALLS:
            if shape.BoundBox.intersect(ws.BoundBox) and shape.common(ws).Volume > RULES["tol"]:
                out.append("WALL " + wname)
    return out


def _items():
    """Aggregated bounding box per piece of furniture (item), in metres."""
    agg = {}
    for item, _lbl, sh, g in ST.CHECK:
        bb = sh.BoundBox
        a = agg.setdefault(item, [bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax, g])
        a[:6] = [min(a[0], bb.XMin), min(a[1], bb.YMin), min(a[2], bb.ZMin),
                 max(a[3], bb.XMax), max(a[4], bb.YMax), max(a[5], bb.ZMax)]
    return {k: [v / S for v in a[:6]] + [a[6]] for k, a in agg.items()}


def _room_of(x, y):
    for r in ST.ROOMS:
        for x0, y0, x1, y1 in r["rects"]:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return r["name"]
    return "-"


# --- plan grid for routes and occupancy ---
CELL = 0.05


def _obstacle_rects(zmax=1.0):
    rects = []
    for _n, ws in ST.WALLS:
        for w in ws.slice(V(0, 0, 1), 1.0 * S):
            bb = w.BoundBox
            rects.append((bb.XMin / S, bb.YMin / S, bb.XMax / S, bb.YMax / S))
    for _item, _l, sh, _g in ST.CHECK:
        for sol in (sh.Solids or [sh]):
            bb = sol.BoundBox
            if bb.ZMin < zmax * S and bb.ZMax > 0.05 * S:
                rects.append((bb.XMin / S, bb.YMin / S, bb.XMax / S, bb.YMax / S))
    for dd in ST.DOORS:
        if dd["leaf"] is not None:
            bb = dd["leaf"].BoundBox
            rects.append((bb.XMin / S, bb.YMin / S, bb.XMax / S, bb.YMax / S))
    for sl in ST.SLIDES:
        bb = sl["shape"].BoundBox
        rects.append((bb.XMin / S, bb.YMin / S, bb.XMax / S, bb.YMax / S))
    return rects


def _grid(rects, inflate):
    X0, Y0, X1, Y1 = ST.interior
    nx, ny = int(round((X1 - X0) / CELL)), int(round((Y1 - Y0) / CELL))
    g = bytearray(nx * ny)
    for x0, y0, x1, y1 in rects:
        x0, y0, x1, y1 = x0 - inflate, y0 - inflate, x1 + inflate, y1 + inflate
        i0 = max(0, int(math.ceil((x0 - X0) / CELL - 0.5)))
        i1 = min(nx - 1, int(math.floor((x1 - X0) / CELL - 0.5)))
        j0 = max(0, int(math.ceil((y0 - Y0) / CELL - 0.5)))
        j1 = min(ny - 1, int(math.floor((y1 - Y0) / CELL - 0.5)))
        for j in range(j0, j1 + 1):
            row = j * nx
            for i in range(i0, i1 + 1):
                g[row + i] = 1
    return g, nx, ny


def _cell(x, y, nx, ny):
    X0, Y0 = ST.interior[0], ST.interior[1]
    i, j = int((x - X0) / CELL), int((y - Y0) / CELL)
    return (i, j) if 0 <= i < nx and 0 <= j < ny else None


def _bfs(g, nx, ny, start):
    dist = [-1] * (nx * ny)
    c = _cell(start[0], start[1], nx, ny)
    if c is None or g[c[1] * nx + c[0]]:
        return dist
    q = collections.deque([c])
    dist[c[1] * nx + c[0]] = 0
    while q:
        i, j = q.popleft()
        d = dist[j * nx + i]
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny:
                k = b * nx + a
                if not g[k] and dist[k] < 0:
                    dist[k] = d + 1
                    q.append((a, b))
    return dist


def verify(write_report=True):
    """Run every check, print the summary and write output/verification_report.md.
    Returns the number of NON-COMPLIANT blocking + significant results."""
    ST.results = []
    R = RULES
    NC = NON_COMPLIANT

    # 1) leaves, windows, sliding doors: full trajectory clear
    for dd in ST.DOORS:
        hits = hits_of(dd["sweep"])
        for o in ST.DOORS:
            if o["name"] != dd["name"] and dd["sweep"].BoundBox.intersect(o["sweep"].BoundBox) \
                    and dd["sweep"].common(o["sweep"]).Volume > R["tol"]:
                hits.append("%s %s" % (o["kind"], o["name"]))
        for sl in ST.SLIDES:
            if dd["sweep"].common(sl["shape"]).Volume > R["tol"] or dd["sweep"].common(sl["closed"]).Volume > R["tol"]:
                hits.append("sliding " + sl["name"])
        dd["mark"].ViewObject.ShapeColor = (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3)
        _r("Openings", dd["name"], "collisions: " + (", ".join(hits) if hits else "none"), "clear trajectory",
           NC if hits else VERIFIED, "blocking", "3D intersection of the volume swept by the leaf 0-90 degrees")
    for sl in ST.SLIDES:
        hits = hits_of(sl["shape"])
        hits += ["%s %s" % (d["kind"], d["name"]) for d in ST.DOORS if sl["shape"].common(d["sweep"]).Volume > R["tol"]]
        sl["mark"].ViewObject.ShapeColor = (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3)
        _r("Openings", sl["name"] + " (open)", "collisions: " + (", ".join(hits) if hits else "none"),
           "clear travel", NC if hits else VERIFIED, "blocking", "3D intersection of the leaf in open position")

    # 2) handles and 3) reveals
    for dd in ST.DOORS:
        if dd["handle"] is None:
            continue
        h = hits_of(dd["handle"])
        _r("Handles", dd["name"], ", ".join(h) if h else "clear", "%.0f cm clear at 90 degrees" % (R["handle"] * 100),
           NC if h else VERIFIED, "significant", "3D intersection of the handle with the leaf open")
        p = [w for w in hits_of(dd["probe"]) if w.startswith("WALL")]
        _r("Reveals", dd["name"], ", ".join(p) if p else ">= threshold", ">= %.0f cm" % (R["reveal"] * 100),
           NC if p else VERIFIED, "significant", "probe between opening edge and perpendicular wall")

    # 4) seats: from the surface edge to the first obstacle
    for name, own, (ox, oy), (dx, dy), hw in ST.SEATS:
        zone = rel_box(ox, oy, (dx, dy), (-dy, dx), (0.002, 1.5), (-hw, hw), 0.05, 1.00)
        free = 1.5
        for it, _l, sh, _g in ST.CHECK + [(w, w, s, "") for w, s in ST.WALLS]:
            if it in own or not zone.BoundBox.intersect(sh.BoundBox):
                continue
            c = zone.common(sh)
            if c.Volume > R["tol"]:
                free = min(free, min((v.Point.x / S - ox) * dx + (v.Point.y / S - oy) * dy for v in c.Vertexes))
        ok = free >= R["seat_min"]
        _r("Seats", name, "%.0f cm" % (free * 100),
           "min %.0f (stand up) / comfort %.0f (walk behind)" % (R["seat_min"] * 100, R["seat_comfort"] * 100),
           VERIFIED if ok else NC, "blocking" if not ok else ("improvement" if free < R["seat_comfort"] else ""),
           "surface edge -> first obstacle (max 150)",
           "below comfort target: nobody can walk behind a seated person" if ok and free < R["seat_comfort"] else "")

    # 5) clearances and access zones
    for lbl, a, b, mn, cf in ST.CLEAR:
        d = ST.doc.getObject(a).Shape.distToShape(ST.doc.getObject(b).Shape)[0] / S
        ok = d >= mn - 1e-6
        low = cf and d < cf
        _r("Clearances", lbl, "%.0f cm" % (d * 100), "min %.0f" % (mn * 100) + (" / comfort %.0f" % (cf * 100) if cf else ""),
           VERIFIED if ok else NC, "blocking" if not ok else ("improvement" if low else ""),
           "minimum plan distance %s - %s" % (a, b), "below comfort target" if ok and low else "")
    for lbl, zone, own, depth in ST.ACCESS:
        h = hits_of(zone, skip_items=own)
        ok = not h and depth >= R["access"] - 1e-6
        _r("Access zones", lbl, ("obstacles: " + ", ".join(h)) if h else "clear, %.0f cm" % (depth * 100),
           ">= %.0f cm clear" % (R["access"] * 100), VERIFIED if ok else NC, "blocking",
           "3D intersection of the zone in front of the unit")

    # 6) routes from the entrance (5 cm grid, person 60 cm wide)
    rects = _obstacle_rects()
    g, nx, ny = _grid(rects, R["person_radius"])
    method = "5 cm grid, obstacles inflated by 30 cm"
    if ST.START:
        dist = _bfs(g, nx, ny, ST.START)
        for lbl, (x, y) in ST.TARGETS.items():
            c = _cell(x, y, nx, ny)
            k = c[1] * nx + c[0] if c else None
            if k is None or g[k]:
                _r("Routes", lbl, "point inside a footprint", "reachable from the entrance at 60 cm", NC,
                   "blocking", method, "move the point or the furniture")
            elif dist[k] < 0:
                _r("Routes", lbl, "unreachable", "reachable from the entrance at 60 cm", NC, "blocking", method)
            else:
                _r("Routes", lbl, "%.1f m from the entrance" % (dist[k] * CELL), "reachable at 60 cm", VERIFIED, "", method)
    for lbl, src, dst in ST.ROUTES:
        dist = _bfs(g, nx, ny, ST.TARGETS[src])
        c = _cell(*ST.TARGETS[dst], nx, ny)
        k = c[1] * nx + c[0]
        ok = dist[k] >= 0
        _r("Routes", lbl, ("%.1f m" % (dist[k] * CELL)) if ok else "interrupted", "continuous at 60 cm",
           VERIFIED if ok else NC, "" if ok else "blocking", method)

    # 7) rooms: daylight ratio and occupancy
    occ, onx, ony = _grid(_obstacle_rects(zmax=0.30), 0.0)
    X0, Y0 = ST.interior[0], ST.interior[1]
    for r in ST.ROOMS:
        win = [w for w in ST.WINDOWS if w["room"] == r["name"]]
        glazed = sum((w["x1"] - w["x0"]) * (w["z1"] - w["z0"]) for w in win)
        if r["habitable"]:
            need = r["area"] * R["daylight"]
            _r("Light and air", r["name"], "%.1f m2 glazed" % glazed, ">= %.1f m2 (1/8 of %.1f)" % (need, r["area"]),
               VERIFIED if glazed >= need else NC, "blocking" if glazed < need else "",
               "sum of net window areas serving the room")
            cells = tot = 0
            for x0, y0, x1, y1 in r["rects"]:
                for j in range(int((y0 - Y0) / CELL), int((y1 - Y0) / CELL)):
                    for i in range(int((x0 - X0) / CELL), int((x1 - X0) / CELL)):
                        if 0 <= i < onx and 0 <= j < ony:
                            tot += 1
                            cells += occ[j * onx + i]
            ratio = cells / tot if tot else 0
            _r("Light and air", r["name"] + " - occupancy", "%.0f%% of the floor" % (ratio * 100),
               "<= %.0f%%" % (R["occupancy"] * 100), VERIFIED,
               "improvement" if ratio > R["occupancy"] else "", "floor-standing footprint on a 5 cm grid",
               "crowded room" if ratio > R["occupancy"] else "")
        elif r["kind"] == "bathroom":
            _r("Light and air", r["name"], "window %.2f m2" % glazed if win else "no window", "window or mechanical ventilation",
               VERIFIED if win else NOT_VERIF, "" if win else "significant",
               "presence of an opening window", "" if win else "design mechanical ventilation")
        else:
            _r("Light and air", r["name"], "-", "non-habitable room", NOT_APPL, "", "-")

    # 8) TV / window constraint
    for name in ST.TV:
        tvs = ST.doc.getObject(name).Shape
        cy = (tvs.BoundBox.YMin + tvs.BoundBox.YMax) / 2 / S
        worst = None
        for w in ST.WINDOWS:
            d = tvs.distToShape(w["glass"])[0] / S
            same = abs(cy - w["yc"]) < 0.5
            if worst is None or (same, -d) > (worst[0], -worst[1]):
                worst = (same, d, w["name"])
        if worst is None:
            _r("Brief constraints", "TV " + name, "no windows", "TV away from windows", VERIFIED, "", "-")
        else:
            same, d, wn = worst
            bad = same and d < R["tv_window"]
            _r("Brief constraints", "TV " + name, "%.2f m from %s (%s)" % (d, wn, "same wall" if same else "other wall"),
               "not above/in front of/next to a window on the same wall (>= %.1f m)" % R["tv_window"],
               NC if bad else VERIFIED, "blocking" if bad else ("improvement" if d < 1.5 else ""),
               "3D distance TV - glass", "check reflections" if not bad and d < 1.5 else "")

    # 9) ergonomics: surface / seat height
    lo, hi = R["seat_height"]
    for lbl, zp, zs in ST.HEIGHTS:
        dz = zp - zs
        ok = lo <= dz <= hi
        _r("Ergonomics", lbl, "surface %.2f / seat %.2f (diff %.2f)" % (zp, zs, dz), "diff %.2f-%.2f" % (lo, hi),
           VERIFIED if ok else NC, "" if ok else "significant", "design heights")

    # 10) assembly of tall units (tilting up on site)
    for item, (x0, y0, z0, x1, y1, z1, _g) in _items().items():
        h = z1 - z0
        if h <= 2.0:
            continue
        diag = math.hypot(h, min(x1 - x0, y1 - y0))
        ok = diag <= ST.H - R["assembly_margin"]
        _r("Assembly", item, "diagonal %.2f m" % diag, "<= %.2f (room height - margin)" % (ST.H - R["assembly_margin"]),
           VERIFIED if ok else NC, "" if ok else "significant", "hypotenuse of height x depth",
           "" if ok else "assemble in place or in modules")

    # 11) interpenetrations
    pairs = []
    C_ = ST.CHECK
    for i in range(len(C_)):
        for j in range(i + 1, len(C_)):
            a, b = C_[i], C_[j]
            if a[0] != b[0] and a[2].BoundBox.intersect(b[2].BoundBox) and a[2].common(b[2]).Volume > R["tol"]:
                pairs.append("%s <-> %s" % (a[1], b[1]))
    for _item, lbl, sh, _g in C_:
        for wname, ws in ST.WALLS:
            if sh.BoundBox.intersect(ws.BoundBox) and sh.common(ws).Volume > R["tol"]:
                pairs.append("%s inside %s" % (lbl, wname))
    _r("Geometry", "Furniture/wall interpenetrations", ", ".join(pairs) if pairs else "none", "none",
       NC if pairs else VERIFIED, "blocking" if pairs else "", "pairwise 3D intersection")

    for cat, reason in ST.NOTVERIF:
        _r("Not verifiable", cat, "-", "-", NOT_VERIF, "significant", "-", reason)

    ST.doc.recompute()
    problems = [x for x in ST.results if x["status"] == NC and x["sev"] in ("blocking", "significant")]
    improve = [x for x in ST.results if x["sev"] == "improvement"]
    cnt = collections.Counter(x["status"] for x in ST.results)
    print("=== VERIFICATION %s: %s ===" % (ST.name, ", ".join("%s %d" % kv for kv in sorted(cnt.items()))))
    for x in problems:
        print("NON-COMPLIANT [%s] %s / %s: %s (threshold %s)" % (x["sev"], x["cat"], x["elem"], x["measure"], x["threshold"]))
    for x in improve:
        print("improvement   %s / %s: %s (%s)" % (x["cat"], x["elem"], x["measure"], x["note"] or x["threshold"]))
    if write_report:
        print("report:", _report())
    print("TOTAL PROBLEMS:", len(problems))
    return len(problems)


def _report():
    out = os.path.join(ST.dir, "output")
    os.makedirs(out, exist_ok=True)
    rs = ST.results
    blocking = [x for x in rs if x["status"] == NON_COMPLIANT and x["sev"] == "blocking"]
    outcome = ("PRELIMINARY PROPOSAL: geometric and functional checks passed; NOT VERIFIABLE items remain open"
               if not blocking else "NOT DELIVERABLE: %d blocking checks failed" % len(blocking))
    L = ["# Verification - %s" % ST.name, "",
         "Generated by `lib/interiors.py` on %s. Brief: [`brief.md`](../brief.md). Thresholds: `docs/design-rules.md`."
         % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "", "**Outcome:** " + outcome, "",
         "## Summary", "", "| Status | Blocking | Significant | Improvement | Total |", "|---|---|---|---|---|"]
    for st in (VERIFIED, NON_COMPLIANT, NOT_VERIF, NOT_APPL):
        sub = [x for x in rs if x["status"] == st]
        L.append("| %s | %d | %d | %d | %d |" % (st, *[sum(1 for x in sub if x["sev"] == s) for s in SEVERITY], len(sub)))
    L += ["", "## I. Checks performed", "", "| Category | Element | Measure | Threshold | Status | Severity | Method | Note |",
          "|---|---|---|---|---|---|---|---|"]
    for x in rs:
        L.append("| %(cat)s | %(elem)s | %(measure)s | %(threshold)s | %(status)s | %(sev)s | %(method)s | %(note)s |" % x)
    L += ["", "## Rooms", "", "| Room | Net area | Habitable |", "|---|---|---|"]
    for r in ST.ROOMS:
        L.append("| %s | %.1f m2 | %s |" % (r["name"], r["area"], "yes" if r["habitable"] else "no"))
    L += ["", "## Net openings / rough openings", "", "| Opening | Net | Rough | Notes |", "|---|---|---|---|"]
    for lbl, nw, nh, rw, rh, nt in ST.OPENINGS:
        L.append("| %s | %.0f x %.0f | %.0f x %.0f | %s |" % (lbl, nw * 100, nh * 100, rw * 100, rh * 100, nt))
    L += ["", "## F. Furniture (indicative footprints)", "", "| ID | Room | W x D x H (cm) | Position x, y (m) | Source |",
          "|---|---|---|---|---|"]
    for item, (x0, y0, z0, x1, y1, z1, g) in sorted(_items().items(), key=lambda kv: kv[1][6]):
        L.append("| %s | %s | %.0f x %.0f x %.0f | %.2f, %.2f | indicative footprint |" % (
            item, _room_of((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0) * 100, (y1 - y0) * 100, (z1 - z0) * 100, x0, y0))
    path = os.path.join(out, "verification_report.md")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return path


# ============================== export ==============================
LAYER = {"Structure": "WALLS", "Windows": "WINDOWS", "Doors": "DOORS", "Swing_Check": "SWINGS"}


def export():
    """Save FCStd and STEP in output/, and in build/ the data for tools/export.sh (plan, layers, mesh, annotations)."""
    import Import
    import importDXF
    out, build = os.path.join(ST.dir, "output"), os.path.join(ST.dir, "build")
    os.makedirs(out, exist_ok=True)
    os.makedirs(build, exist_ok=True)
    doc = ST.doc
    doc.saveAs(os.path.join(out, ST.name + ".FCStd"))
    solids = [o for o in doc.Objects if o.TypeId == "Part::Feature" and "Area" not in o.Name]
    Import.export(solids, os.path.join(out, ST.name + "_3D.step"))

    def section(o, g):
        parts = [o.Shape] if g in ("Structure", "Windows") or "Area" in o.Name else (o.Shape.Solids or [o.Shape])
        edges = []
        for s in parts:
            bb = s.BoundBox
            zc = 1000.0 if (g in ("Structure", "Windows") and bb.ZMin < 1000.0 < bb.ZMax) else (bb.ZMin + bb.ZMax) / 2
            for w in s.slice(V(0, 0, 1), zc):
                w = w.copy()
                w.translate(V(0, 0, -zc))
                edges.append(w)
        return Part.makeCompound(edges)

    plan = App.newDocument("Plan_DXF")
    mapping = {}
    for o in doc.Objects:
        if o.TypeId != "Part::Feature" or o.Name.startswith(("Slab", "Tiles_")) or "Track" in o.Name:
            continue
        g = o.getParentGroup().Label if o.getParentGroup() else "Other"
        sec = section(o, g)
        if not sec.Edges:
            continue
        f = plan.addObject("Part::Feature", o.Name)
        f.Shape = sec
        mapping[f.Label] = LAYER.get(g, "FURNITURE")
    plan.recompute()
    importDXF.export(plan.Objects, os.path.join(build, "plan_raw.dxf"))
    App.closeDocument("Plan_DXF")
    App.setActiveDocument(doc.Name)
    json.dump(mapping, open(os.path.join(build, "layers.json"), "w"))

    data = []
    for o in solids:
        pts, tris = o.Shape.tessellate(5.0)
        g = o.getParentGroup().Label if o.getParentGroup() else "Other"
        data.append({"name": o.Label, "group": g, "color": list(o.ViewObject.ShapeColor[:3]),
                     "tr": o.ViewObject.Transparency,
                     "v": [[round(p.x, 1), round(p.y, 1), round(p.z, 1)] for p in pts], "f": tris})
    json.dump(data, open(os.path.join(build, "mesh3d.json"), "w"))

    # annotations: dimensions, labels, rooms with computed areas, sliding-door symbols, title block
    wb = [ws.BoundBox for _n, ws in ST.WALLS]
    gx0, gy0 = min(b.XMin for b in wb) / S, min(b.YMin for b in wb) / S
    gx1, gy1 = max(b.XMax for b in wb) / S, max(b.YMax for b in wb) / S
    net = sum(r["area"] for r in ST.ROOMS)
    slides = []
    for sl in ST.SLIDES:
        cx0, cy0, _, cx1, cy1, _ = sl["c"]
        ox0, oy0, _, ox1, oy1, _ = sl["o"]
        if (cx1 - cx0) < (cy1 - cy0):          # leaf along y, thickness along x
            xm = (cx0 + cx1) / 2
            wall_hi = any(cx1 - 1e-6 <= b.XMin / S <= cx1 + 0.05 for b in wb)
            off = cx0 - 0.12 if wall_hi else cx1 + 0.12
            a = (off, (cy0 + cy1) / 2 + 0.25 * ((cy0 + cy1) - (oy0 + oy1)) / 2)
            b_ = (off, (oy0 + oy1) / 2 - 0.25 * ((cy0 + cy1) - (oy0 + oy1)) / 2)
            leaf = ((xm, cy0), (xm, cy1))
        else:
            ym = (cy0 + cy1) / 2
            wall_hi = any(cy1 - 1e-6 <= b.YMin / S <= cy1 + 0.05 for b in wb)
            off = cy0 - 0.12 if wall_hi else cy1 + 0.12
            a = ((cx0 + cx1) / 2 + 0.25 * ((cx0 + cx1) - (ox0 + ox1)) / 2, off)
            b_ = ((ox0 + ox1) / 2 - 0.25 * ((cx0 + cx1) - (ox0 + ox1)) / 2, off)
            leaf = ((cx0, ym), (cx1, ym))
        slides.append([[p * S for p in leaf[0]], [p * S for p in leaf[1]], [p * S for p in a], [p * S for p in b_]])
    ann = dict(
        dims=ST.ANN["dims"], labels=ST.ANN["labels"], slides=slides,
        rooms=[(r["lines"] + ["%.1f m²" % r["area"]], r["xy"][0] * S, r["xy"][1] * S) for r in ST.ROOMS],
        title="%s - FLOOR PLAN   Gross area %.1f m²  -  Net area %.1f m²   Dimensions in mm - print at 1:50"
              % (ST.name.upper(), (gx1 - gx0) * (gy1 - gy0), net),
        note=ST.ANN["note"], centre=(gx0 + gx1) / 2 * S, base=gy0 * S,
    )
    json.dump(ann, open(os.path.join(build, "annotations.json"), "w"), ensure_ascii=False)
    print("FreeCAD export ok ->", out, "| next: tools/export.sh", ST.dir)
