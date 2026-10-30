"""Engine for interior design projects in FreeCAD, run through MCP (execute_code).

A project (projects/<name>/project.py) calls new_project(), draws with wall/hinged/sliding/window/box/...,
registers uses and constraints (seat, access_zone, clearance, destination, room, tv, ...), then calls verify()
and optionally export(). Coordinates in metres, y points north. Thresholds: docs/design-rules.md.
"""
import FreeCAD as App
import Part
import collections
import datetime
import fnmatch
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
    placement=0.02,                           # placement tolerance per element (survey + installation)
    occupancy_min=0.10,                       # below this a habitable room is under-furnished (L26)
    eye_standing=1.60, eye_seated=1.15,       # sightline eye heights: entrance and arrivals / seats (L25)
    clearances=dict(corridor=[1.00, 1.10], passage=[0.80, 0.90], aisle=[0.90, 1.10], bed_side=[0.60, 0.70]),
    appliance_door=dict(dishwasher=0.60, oven=0.50, drawer=0.50),   # projection of a drop-down / pull-out door (L29)
    min_area=dict(bedroom=14.0, single_bedroom=9.0, living=14.0),  # DM 5/7/1975, indicative
    service_area=dict(laundry=6.0), service_factor=2.0,            # reference area; above x factor it is oversized (L24)
)

# Room kinds (room(kind=)): the Programme and Privacy checks read them. Habitable kinds need daylight.
KINDS = ("bedroom", "single_bedroom", "living", "dining", "kitchen", "bathroom", "corridor", "laundry", "store",
         "service")
HABITABLE = ("bedroom", "single_bedroom", "living", "dining", "kitchen")
THROUGH = ("living", "dining", "kitchen")      # rooms that must not be the way into a bedroom or bathroom (L23)

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
ACCEPTED = "ACCEPTED"       # a NON-COMPLIANT result the client accepted, with name, date and reason (L28)


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
    ST.REQS, ST.PRIVATE, ST.VIEWS, ST.ELEC, ST.WET = [], [], [], [], []
    ST.VIEWPOINTS, ST.INTIMATE, ST.ACCEPTED = [], [], []
    ST.ANN = dict(dims=[], labels=[], note="")
    ST.results = []
    return ST.doc


def group(n):
    if n not in ST.groups:
        ST.groups[n] = ST.doc.addObject("App::DocumentObjectGroup", n)
    return ST.groups[n]


def _paint(o, color, tr=None):
    """Colour an object; headless FreeCAD (freecadcmd, CI) has no ViewObject: keep the values on the side."""
    if not hasattr(o, "IntColor"):
        o.addProperty("App::PropertyColor", "IntColor", "Interiors")
        o.addProperty("App::PropertyInteger", "IntTransparency", "Interiors")
    o.IntColor = color
    if tr is not None:
        o.IntTransparency = tr
    if getattr(o, "ViewObject", None) is not None:
        o.ViewObject.ShapeColor = color
        if tr is not None:
            o.ViewObject.Transparency = tr


def add(name, shape, color, g, check=True, tr=0, item=None):
    """Add a solid. check=True makes it an obstacle for every verification;
    parts of the same piece of furniture share item= so they are not reported against each other."""
    o = ST.doc.addObject("Part::Feature", name)
    o.Shape = shape
    _paint(o, color, tr)
    group(g).addObject(o)
    if check:
        ST.CHECK.append((item or name, o.Label, shape, g))
    return o


def B(x0, y0, z0, x1, y1, z1):
    return Part.makeBox((x1 - x0) * S, (y1 - y0) * S, (z1 - z0) * S, V(x0 * S, y0 * S, z0 * S))


_B = B


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
           frame=None, handle=True, own=None):
    """Hinged leaf. own = item the leaf belongs to (wardrobe body), ignored by the robustness margin.
    Hinge (hx, hy) on the wall face of the opening side; d = closed-leaf direction,
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
    ST.DOORS.append(dict(name=name, sweep=sweep, mark=m, kind=kind, handle=hnd, probe=probe, own=own,
                         leaf=leaf_shape if (leaf and z0 < 0.5) else None,
                         geo=dict(hinge=[hx, hy], d=list(d), n=list(n), w=w, z0=z0, hgt=hgt)))


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


def window(name, yc, x0, x1, z0, z1, room, mullion=False, axis="x"):
    """Window on a wall running along x (wall centre y = yc, span x0-x1), with subframe; the wall opening is enlarged.
    axis="y": wall running along y (yc = wall centre x, x0-x1 = span along y). room = the room it serves (daylight)."""
    def B(a0, b0, c0, a1, b1, c1):                      # (along the wall, across it, z), swapped for axis y
        return _B(a0, b0, c0, a1, b1, c1) if axis == "x" else _B(b0, a0, c0, b1, a1, c1)
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
    ST.WINDOWS.append(dict(name=name, yc=yc, x0=x0, x1=x1, z0=z0, z1=z1, room=room, glass=glass, axis=axis))


# ============================== registering uses and constraints ==============================
def seat(name, own, edge_xy, direction, hw):
    """Seat served by a surface: space measured from the surface edge outwards.
    own = items to ignore (the seat itself and the surface). The seated person is also a viewpoint (L25):
    seats of the same surface form one group, so a table gives one sightline row per intimate object."""
    ST.SEATS.append((name, tuple(own), edge_xy, direction, hw))
    surface = own[1] if len(own) > 1 else name
    viewpoint("%s seats" % surface, edge_xy[0] + direction[0] * 0.35, edge_xy[1] + direction[1] * 0.35,
              seated=True, who=name)


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


def access_zone(label, x0, y0, x1, y1, own, depth=None):
    """Volume that must stay clear in front of wardrobes/cabinets/appliances (depth >= RULES['access']).
    depth defaults to the shorter side; give it explicitly when the zone is narrower than deep (e.g. a 60 cm fridge,
    lesson L20). Appliances with a drop-down or pull-out door: appliance_zone()."""
    ST.ACCESS.append((label, B(x0, y0, 0.05, x1, y1, 1.80), tuple(own), depth or min(x1 - x0, y1 - y0)))


def appliance_zone(label, x0, y0, x1, y1, front, own, kind):
    """Access zone of an appliance with a drop-down or pull-out door (dishwasher, oven, drawer): the open door plus
    the person, RULES['appliance_door'][kind] + RULES['access'] deep from the unit's face (L29).
    (x0, y0, x1, y1) = the appliance footprint, front = side of the door ('+x', '-x', '+y', '-y').
    A hinged door (fridge, cabinet) is a hinged() leaf with a plain access_zone()."""
    if kind not in RULES["appliance_door"]:
        raise ValueError("appliance_zone kind %r: one of %s (hinged doors: hinged() + access_zone())"
                         % (kind, sorted(RULES["appliance_door"])))
    depth = RULES["appliance_door"][kind] + RULES["access"]
    z = {"+x": (x1 + 0.01, y0, x1 + 0.01 + depth, y1), "-x": (x0 - 0.01 - depth, y0, x0 - 0.01, y1),
         "+y": (x0, y1 + 0.01, x1, y1 + 0.01 + depth), "-y": (x0, y0 - 0.01 - depth, x1, y0 - 0.01)}[front]
    access_zone("%s (%s door open + person)" % (label, kind), *z, tuple(own), depth=depth)


def clearance(label, a, b, minimum=None, comfort=None, kind=None):
    """Plan distance between two objects (by name) with a minimum and a comfort target.
    kind = a named pair from RULES['clearances'] ('corridor', 'passage', 'aisle', 'bed_side'), the single source of
    the thresholds; explicit numbers only for a distance that has no named rule."""
    if kind is not None:
        if kind not in RULES["clearances"]:
            raise ValueError("clearance kind %r: one of %s" % (kind, sorted(RULES["clearances"])))
        minimum, comfort = RULES["clearances"][kind]
    if minimum is None:
        raise ValueError("clearance %r: give kind= or minimum=" % label)
    ST.CLEAR.append((label, a, b, minimum, comfort))


def entrance(x, y):
    """Start of every route; also the first viewpoint (standing) towards the intimate objects (L25)."""
    ST.START = (x, y)
    viewpoint("entrance", x, y)


def viewpoint(label, x, y, seated=False, who=None):
    """Place from which the intimate objects (WC, beds) must not be seen: main seats (sofa), stair arrivals, the
    entrance (added by entrance()); seats registered with seat()/chair() add themselves. Same label = same group."""
    z = RULES["eye_seated"] if seated else RULES["eye_standing"]
    for vp in ST.VIEWPOINTS:
        if vp["label"] == label:
            vp["eyes"].append([x, y, z, who or label])
            return
    ST.VIEWPOINTS.append(dict(label=label, eyes=[[x, y, z, who or label]]))


def intimate(*objects):
    """Objects that must be screened by walls from every viewpoint with the doors open: WC and beds (L25)."""
    ST.INTIMATE.extend(objects)


def accepted(pattern, by, date, reason):
    """NON-COMPLIANT results ("Category/Element", fnmatch) the client accepted: who, when (YYYY-MM-DD) and why.
    The designer proposes, only the client accepts (L28); a pattern that matches no failing check is a defect."""
    ST.ACCEPTED.append(dict(pattern=pattern, by=by, date=date, reason=reason))


def destination(label, x, y):
    """Point a person must be able to reach from the entrance (in front of furniture or a fixture)."""
    ST.TARGETS[label] = (x, y)


def route(label, src, dst):
    """Route between two destinations: verified and measured (e.g. night route bed -> toilet)."""
    ST.ROUTES.append((label, src, dst))


def room(name, rects, label_xy, kind=None, habitable=None, lines=None):
    """Room: net floor rectangles, label position on the plan, kind from KINDS (the Programme and Privacy checks
    read it: minimum area, under-furnished, oversized service room, entered from a living room).
    habitable defaults from the kind."""
    if kind not in KINDS:
        raise ValueError("room %r: kind=%r must be one of %s" % (name, kind, KINDS))
    if habitable is None:
        habitable = kind in HABITABLE
    area = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in rects)
    ST.ROOMS.append(dict(name=name, rects=rects, xy=label_xy, habitable=habitable, kind=kind,
                         area=area, lines=lines or [name.upper()]))
    return area


def tv(name):
    ST.TV.append(name)


def height_match(label, z_surface, z_seat):
    ST.HEIGHTS.append((label, z_surface, z_seat))


def requirement(rid, text, verified_by=(), satisfied_by=(), manual=False):
    """Brief requirement (id as in brief.md). verified_by = patterns "Category/Element" matched against the results
    (fnmatch, e.g. "Openings/Door_Bath*"); satisfied_by = objects that implement it; manual = judged in review only:
    True while the review is pending, or the review file (relative to the project folder) that judged it, which must
    exist and cite the id (a missing file is a broken link, as in lesson L13)."""
    ST.REQS.append(dict(id=rid, text=text, verified_by=tuple(verified_by), satisfied_by=tuple(satisfied_by),
                        manual=manual))


def private_room(name):
    """Room that must not be crossed to reach shared destinations (e.g. a bedroom)."""
    ST.PRIVATE.append(name)


def no_view(lbl, eye_xy, target, eye_z=1.60):
    """Sightline that must be blocked by walls (e.g. WC not visible from the entrance with doors open)."""
    ST.VIEWS.append((lbl, eye_xy, eye_z, target))


def electrical(*items):
    """Items with power or water supply that must stay out of wet zones (washing machine, dryer, sockets, heaters)."""
    ST.ELEC.extend(items)


def wet_zone(label, x0, y0, x1, y1, z1=1.20):
    """Splash zone next to an open side of a shower or bath (typically 60 cm): no electrical item may enter it."""
    ST.WET.append((label, B(x0, y0, 0.0, x1, y1, z1)))


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


def _common(a, b):
    """Intersections solid by solid: common() between a shape and a compound of touching or overlapping solids
    (bookcase, chair) returns an empty result in FreeCAD 1.1 (lesson L21)."""
    return [x.common(y) for x in (a.Solids or [a]) for y in (b.Solids or [b]) if x.BoundBox.intersect(y.BoundBox)]


def _vol(a, b):
    return sum(c.Volume for c in _common(a, b))


def hits_of(shape, skip_items=(), walls=True):
    out = []
    for item, lbl, sh, _g in ST.CHECK:
        if item in skip_items or not shape.BoundBox.intersect(sh.BoundBox):
            continue
        v = _vol(shape, sh)
        if v > RULES["tol"]:
            out.append("%s (%.0f cm3)" % (lbl, v / 1000))
    if walls:
        for wname, ws in ST.WALLS:
            if shape.BoundBox.intersect(ws.BoundBox) and _vol(shape, ws) > RULES["tol"]:
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


def _entered_from(nx, ny, dist, k, room):
    """Room the route from the entrance comes from when it enters `room`: walk the BFS distances back from cell k,
    skip the cells of the room and the door gaps (no room), return the first other room (L23)."""
    X0, Y0 = ST.interior[0], ST.interior[1]
    while dist[k] > 0:
        i, j = k % nx, k // nx
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny and dist[b * nx + a] == dist[k] - 1:
                k = b * nx + a
                break
        rn = _room_of(X0 + (k % nx + 0.5) * CELL, Y0 + (k // nx + 0.5) * CELL)
        if rn not in (room, "-"):
            return rn
    return "the entrance"


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


def verify(write_report=True, quiet=False):
    """Run every check, print the summary and write output/verification_report.md.
    Returns the number of NON-COMPLIANT blocking + significant results."""
    ST.results = []
    R = RULES
    NC = NON_COMPLIANT

    # 1) leaves, windows, sliding doors: full trajectory clear (FMEA F01, F04)
    for dd in ST.DOORS:
        hits = hits_of(dd["sweep"])
        for o in ST.DOORS:
            if o["name"] != dd["name"] and dd["sweep"].BoundBox.intersect(o["sweep"].BoundBox) \
                    and _vol(dd["sweep"], o["sweep"]) > R["tol"]:
                hits.append("%s %s" % (o["kind"], o["name"]))
        for sl in ST.SLIDES:
            if _vol(dd["sweep"], sl["shape"]) > R["tol"] or _vol(dd["sweep"], sl["closed"]) > R["tol"]:
                hits.append("sliding " + sl["name"])
        _paint(dd["mark"], (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3))
        _r("Openings", dd["name"], "collisions: " + (", ".join(hits) if hits else "none"), "clear trajectory",
           NC if hits else VERIFIED, "blocking", "3D intersection of the volume swept by the leaf 0-90 degrees")
    for sl in ST.SLIDES:
        hits = hits_of(sl["shape"])
        hits += ["%s %s" % (d["kind"], d["name"]) for d in ST.DOORS if _vol(sl["shape"], d["sweep"]) > R["tol"]]
        _paint(sl["mark"], (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3))
        _r("Openings", sl["name"] + " (open)", "collisions: " + (", ".join(hits) if hits else "none"),
           "clear travel", NC if hits else VERIFIED, "blocking", "3D intersection of the leaf in open position")

    # 2) handles and 3) reveals (L02, FMEA F02)
    for dd in ST.DOORS:
        if dd["handle"] is None:
            continue
        h = hits_of(dd["handle"])
        _r("Handles", dd["name"], ", ".join(h) if h else "clear", "%.0f cm clear at 90 degrees" % (R["handle"] * 100),
           NC if h else VERIFIED, "significant", "3D intersection of the handle with the leaf open")
        p = [w for w in hits_of(dd["probe"]) if w.startswith("WALL")]
        _r("Reveals", dd["name"], ", ".join(p) if p else ">= threshold", ">= %.0f cm" % (R["reveal"] * 100),
           NC if p else VERIFIED, "significant", "probe between opening edge and perpendicular wall")

    # 4) seats: from the surface edge to the first obstacle (L03, FMEA F06)
    for name, own, (ox, oy), (dx, dy), hw in ST.SEATS:
        zone = rel_box(ox, oy, (dx, dy), (-dy, dx), (0.002, 1.5), (-hw, hw), 0.05, 1.00)
        free = 1.5
        for it, _l, sh, _g in ST.CHECK + [(w, w, s, "") for w, s in ST.WALLS]:
            if it in own or not zone.BoundBox.intersect(sh.BoundBox):
                continue
            cs = _common(zone, sh)
            if sum(c.Volume for c in cs) > R["tol"]:
                free = min([free] + [(v.Point.x / S - ox) * dx + (v.Point.y / S - oy) * dy for c in cs for v in c.Vertexes])
        ok = free >= R["seat_min"]
        _r("Seats", name, "%.0f cm" % (free * 100),
           "min %.0f (stand up) / comfort %.0f (walk behind)" % (R["seat_min"] * 100, R["seat_comfort"] * 100),
           VERIFIED if ok else NC, "blocking" if not ok else ("improvement" if free < R["seat_comfort"] else ""),
           "surface edge -> first obstacle (max 150)",
           "below comfort target: nobody can walk behind a seated person" if ok and free < R["seat_comfort"] else "")

    # 5) clearances and access zones (L01, FMEA F07)
    for lbl, a, b, mn, cf in ST.CLEAR:
        d = ST.doc.getObject(a).Shape.distToShape(ST.doc.getObject(b).Shape)[0] / S
        ok = d >= mn - 1e-6
        low = cf and d < cf - 1e-6           # same tolerance as the minimum: a measure equal to comfort meets it
        _r("Clearances", lbl, "%.0f cm" % (d * 100), "min %.0f" % (mn * 100) + (" / comfort %.0f" % (cf * 100) if cf else ""),
           VERIFIED if ok else NC, "blocking" if not ok else ("improvement" if low else ""),
           "minimum plan distance %s - %s" % (a, b), "below comfort target" if ok and low else "")
    for lbl, zone, own, depth in ST.ACCESS:
        h = hits_of(zone, skip_items=own)
        ok = not h and depth >= R["access"] - 1e-6
        _r("Access zones", lbl, ("obstacles: " + ", ".join(h)) if h else "clear, %.0f cm" % (depth * 100),
           ">= %.0f cm clear" % (R["access"] * 100), VERIFIED if ok else NC, "blocking",
           "3D intersection of the zone in front of the unit")

    # 6) routes from the entrance (5 cm grid, person 60 cm wide); open leaves are obstacles (L06, L15, FMEA F03, F08)
    rects = _obstacle_rects()
    g, nx, ny = _grid(rects, R["person_radius"])
    method = "5 cm grid, obstacles inflated by 30 cm"
    dist_start = _bfs(g, nx, ny, ST.START) if ST.START else None
    if ST.START:
        dist = dist_start
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
            low = ratio < R["occupancy_min"] - 1e-6
            _r("Light and air", r["name"] + " - occupancy", "%.0f%% of the floor" % (ratio * 100),
               "%.0f-%.0f%%" % (R["occupancy_min"] * 100, R["occupancy"] * 100), NC if low else VERIFIED,
               "significant" if low else ("improvement" if ratio > R["occupancy"] else ""),
               "floor-standing footprint on a 5 cm grid",
               "under-furnished: only what a check needs? (L26)" if low else ("crowded room" if ratio > R["occupancy"] else ""))
        elif r["kind"] == "bathroom":
            _r("Light and air", r["name"], "window %.2f m2" % glazed if win else "no window", "window or mechanical ventilation",
               VERIFIED if win else NOT_VERIF, "" if win else "significant",
               "presence of an opening window", "" if win else "design mechanical ventilation")
        else:
            _r("Light and air", r["name"], "-", "non-habitable room", NOT_APPL, "", "-")

    # 7b) programme by room kind: minimum areas, oversized service rooms, empty rooms (L24, L26)
    centres = [((x0 + x1) / 2, (y0 + y1) / 2) for x0, y0, _z0, x1, y1, _z1, _g in _items().values()]
    for r in ST.ROOMS:
        k = r["kind"]
        if k in R["min_area"]:
            need = R["min_area"][k]
            ok = r["area"] >= need - 1e-6
            _r("Programme", r["name"] + " - area", "%.1f m2" % r["area"],
               ">= %.1f m2 (%s, indicative)" % (need, k.replace("_", " ")), VERIFIED if ok else NC,
               "" if ok else "significant", "net floor area by room kind")
        if k in R["service_area"]:
            lim = R["service_area"][k] * R["service_factor"]
            ok = r["area"] <= lim + 1e-6
            _r("Programme", r["name"] + " - area", "%.1f m2" % r["area"],
               "<= %.1f m2 (%.0f x %.1f reference)" % (lim, R["service_factor"], R["service_area"][k]),
               VERIFIED if ok else NC, "" if ok else "significant", "net floor area against the reference of its contents",
               "" if ok else "sized on the leftover, not on its contents (L24)")
        if k not in HABITABLE and k != "corridor":
            n = sum(1 for cx, cy in centres if _room_of(cx, cy) == r["name"])
            _r("Programme", r["name"] + " - contents", "%d objects" % n, ">= 1 object", VERIFIED if n else NC,
               "" if n else "significant", "furniture whose centre lies in the room",
               "" if n else "empty room: give it its programme or declare it (L26)")

    # 8) TV / window constraint
    for name in ST.TV:
        tvs = ST.doc.getObject(name).Shape
        cx, cy = (tvs.BoundBox.XMin + tvs.BoundBox.XMax) / 2 / S, (tvs.BoundBox.YMin + tvs.BoundBox.YMax) / 2 / S
        worst = None
        for w in ST.WINDOWS:
            d = tvs.distToShape(w["glass"])[0] / S
            same = abs((cy if w.get("axis", "x") == "x" else cx) - w["yc"]) < 0.5   # yc: the wall's centre line
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

    # 10) assembly of tall units (tilting up on site), FMEA F15
    for item, (x0, y0, z0, x1, y1, z1, _g) in _items().items():
        h = z1 - z0
        if h <= 2.0:
            continue
        diag = math.hypot(h, min(x1 - x0, y1 - y0))
        ok = diag <= ST.H - R["assembly_margin"]
        _r("Assembly", item, "diagonal %.2f m" % diag, "<= %.2f (room height - margin)" % (ST.H - R["assembly_margin"]),
           VERIFIED if ok else NC, "" if ok else "significant", "hypotenuse of height x depth",
           "" if ok else "assemble in place or in modules")

    # 10a) wet zones: no electrical item next to an open shower side (L18, FMEA F19)
    for lbl, zone in ST.WET:
        h = [lb for it, lb, sh, _g in ST.CHECK if it in ST.ELEC and zone.BoundBox.intersect(sh.BoundBox)
             and _vol(zone, sh) > R["tol"]]
        _r("Safety", lbl, ("electrical items inside: " + ", ".join(h)) if h else "no electrical item",
           "no electrical item in the splash zone", NC if h else VERIFIED, "blocking" if h else "",
           "3D intersection of the splash zone with items declared electrical()")

    # 10b) privacy: shared destinations reachable without crossing private rooms (FMEA F09)
    if ST.START and ST.PRIVATE:
        priv = [rc for r in ST.ROOMS if r["name"] in ST.PRIVATE for rc in r["rects"]]
        gp, _, _ = _grid(rects + priv, R["person_radius"])
        dist_p = _bfs(gp, nx, ny, ST.START)
        for lbl, (x, y) in ST.TARGETS.items():
            if _room_of(x, y) in ST.PRIVATE:
                continue
            c = _cell(x, y, nx, ny)
            k = c[1] * nx + c[0]
            if dist_start[k] < 0:
                continue          # unreachable at all: already a Routes failure
            ok = dist_p[k] >= 0
            _r("Privacy", lbl, "reachable without crossing %s" % ", ".join(ST.PRIVATE) if ok else
               "reachable only through " + ", ".join(ST.PRIVATE), "shared zones never through a private room",
               VERIFIED if ok else NC, "" if ok else "significant", "route search with private rooms blocked")

    # 10b2) bedrooms and bathrooms entered from circulation, never through a living room (L23)
    if ST.START:
        for r in ST.ROOMS:
            if r["kind"] not in ("bedroom", "single_bedroom", "bathroom"):
                continue
            inside = [(lbl, xy) for lbl, xy in ST.TARGETS.items() if _room_of(*xy) == r["name"]]
            if not inside:
                continue
            lbl, (x, y) = inside[0]
            c = _cell(x, y, nx, ny)
            k = c[1] * nx + c[0] if c else None
            if k is None or dist_start[k] < 0:
                continue          # unreachable or inside a footprint: already a Routes failure
            via = _entered_from(nx, ny, dist_start, k, r["name"])
            bad = next((q["kind"] for q in ST.ROOMS if q["name"] == via), "") in THROUGH
            _r("Privacy", r["name"] + ": entered from", via, "a hall, corridor or stair hall, never a living room",
               NC if bad else VERIFIED, "significant" if bad else "",
               "room before the door on the route from the entrance (to %s)" % lbl,
               "the living room is a corridor (L23)" if bad else "")

    # 10c) sightlines that walls must block (doors assumed open)
    def _seen(ex, ey, ez, bb):
        seg = Part.LineSegment(V(ex * S, ey * S, ez * S), bb.Center).toShape()
        return [w for w, ws in ST.WALLS if ws.BoundBox.intersect(seg.BoundBox) and ws.distToShape(seg)[0] < 1.0]

    for lbl, (ex, ey), ez, target in ST.VIEWS:
        blocked = _seen(ex, ey, ez, ST.doc.getObject(target).Shape.BoundBox)
        _r("Privacy", lbl, ("blocked by " + blocked[0]) if blocked else "visible", "not visible with doors open",
           VERIFIED if blocked else NC, "" if blocked else "significant", "3D sightline eye -> object centre vs walls")
    # 10c2) intimate objects (WC, beds) screened from every viewpoint: entrance, seats, declared arrivals (L25);
    # eyes in the object's own room do not count (whoever is in the bedroom sees the bed)
    for target in ST.INTIMATE:
        obj = ST.doc.getObject(target)
        if obj is None:
            _r("Privacy", target + " from viewpoints", "object missing", "intimate object exists", NC, "blocking",
               "object lookup")
            continue
        bb = obj.Shape.BoundBox
        home = _room_of(bb.Center.x / S, bb.Center.y / S)
        for vp in ST.VIEWPOINTS:
            eyes = [e for e in vp["eyes"] if _room_of(e[0], e[1]) != home]
            if not eyes:
                continue
            seen = [who for ex, ey, ez, who in eyes if not _seen(ex, ey, ez, bb)]
            _r("Privacy", "%s from %s" % (target, vp["label"]),
               ("visible from " + ", ".join(seen)) if seen else "screened by walls", "not visible with doors open",
               NC if seen else VERIFIED, "significant" if seen else "",
               "3D sightline eye -> object centre vs walls (%d eyes)" % len(eyes))

    # 10d) robustness (FMEA F14): margins smaller than the placement tolerance of two elements make the solution fragile;
    # a leaf is measured against other items, not against its own body (lesson L14)
    tol2 = 2 * R["placement"]
    fragile = []
    for x in ST.results:
        if x["cat"] in ("Seats", "Clearances") and x["status"] == VERIFIED:
            meas = float(x["measure"].split()[0]) / 100
            mn = float(x["threshold"].split()[1]) / 100
            if meas - mn < tol2 - 1e-6:
                fragile.append((x["cat"] + "/" + x["elem"], meas - mn))
    for dd in ST.DOORS:
        zone = App.BoundBox(dd["sweep"].BoundBox)
        zone.enlarge(tol2 * S)
        near = min([dd["sweep"].distToShape(sh)[0] / S for it, _l, sh, _g in ST.CHECK
                    if it != dd["own"] and zone.intersect(sh.BoundBox)] or [9])
        if near < tol2 and not hits_of(dd["sweep"], walls=False):
            fragile.append(("Openings/" + dd["name"], near))
    for elem, m in fragile:
        _r("Robustness", elem, "margin %.0f cm" % (m * 100), ">= %.0f cm (2 x placement tolerance)" % (tol2 * 100),
           NC, "significant", "measure - minimum, or swept leaf - nearest object",
           "works only with near-zero tolerance: widen it")
    if not fragile:
        _r("Robustness", "Seats, clearances, door swings", "all margins >= %.0f cm" % (tol2 * 100),
           "no fragile measure", VERIFIED, "", "measure - minimum")

    # 11) interpenetrations
    pairs = []
    C_ = ST.CHECK
    for i in range(len(C_)):
        for j in range(i + 1, len(C_)):
            a, b = C_[i], C_[j]
            if a[0] != b[0] and a[2].BoundBox.intersect(b[2].BoundBox) and _vol(a[2], b[2]) > R["tol"]:
                pairs.append("%s <-> %s" % (a[1], b[1]))
    for _item, lbl, sh, _g in C_:
        for wname, ws in ST.WALLS:
            if sh.BoundBox.intersect(ws.BoundBox) and _vol(sh, ws) > R["tol"]:
                pairs.append("%s inside %s" % (lbl, wname))
    _r("Geometry", "Furniture/wall interpenetrations", ", ".join(pairs) if pairs else "none", "none",
       NC if pairs else VERIFIED, "blocking" if pairs else "", "pairwise 3D intersection")

    # 11b) client acceptances (L28): an accepted NON-COMPLIANT result becomes ACCEPTED (who, when, why) and is no
    # longer a problem; an acceptance that matches no failing result is stale and reported
    for ac in ST.ACCEPTED:
        hit = [x for x in ST.results if x["status"] == NC
               and fnmatch.fnmatch("%s/%s" % (x["cat"], x["elem"]), ac["pattern"])]
        for x in hit:
            x["status"] = ACCEPTED
            x["note"] = (x["note"] + "; " if x["note"] else "") + "accepted by %s on %s: %s" % (
                ac["by"], ac["date"], ac["reason"])
        _r("Acceptance", ac["pattern"],
           "%d result(s) accepted by %s on %s" % (len(hit), ac["by"], ac["date"]) if hit else "no failing check matched",
           ">= 1 NON-COMPLIANT result", VERIFIED if hit else NC, "" if hit else "significant", "pattern against the results",
           ac["reason"] if hit else "stale acceptance: the defect is gone or the pattern is wrong (L28)")

    # 12) requirements traceability (brief -> design -> checks); every link is resolved here (lesson L13)
    for rq in ST.REQS:
        missing = [o for o in rq["satisfied_by"] if ST.doc.getObject(o) is None]
        linked = [x for x in ST.results if any(fnmatch.fnmatch("%s/%s" % (x["cat"], x["elem"]), p)
                                               for p in rq["verified_by"])]
        failed = [x for x in linked if x["status"] == NC]
        elem = "%s %s" % (rq["id"], rq["text"])
        if missing:
            _r("Requirements", elem, "missing objects: " + ", ".join(missing), "implemented", NC, "blocking", "object lookup")
        elif failed:
            _r("Requirements", elem, "%d/%d linked checks failed" % (len(failed), len(linked)), "all linked checks pass",
               NC, min((x["sev"] for x in failed), key=SEVERITY.index), "traceability",
               ", ".join("%s/%s" % (x["cat"], x["elem"]) for x in failed))
        elif rq["manual"] is True:
            _r("Requirements", elem, "judged in review", "-", NOT_VERIF, "", "manual: review-layout / pre-mortem")
        elif rq["manual"]:
            path = os.path.join(ST.dir, rq["manual"])
            ok = rq["manual_ok"] = os.path.exists(path) and rq["id"] in open(path).read()
            _r("Requirements", elem, "judged in %s" % rq["manual"] if ok else
               "review %s missing or without %s" % (rq["manual"], rq["id"]), "review file citing the id",
               VERIFIED if ok else NC, "" if ok else "significant", "manual: review file")
        elif not linked:
            _r("Requirements", elem, "no linked check", ">= 1 automatic check", NC, "significant", "traceability",
               "add a check or mark the requirement manual")
        else:
            _r("Requirements", elem, "%d linked checks passed" % len(linked), "all linked checks pass", VERIFIED, "",
               "traceability")

    for cat, reason in ST.NOTVERIF:
        _r("Not verifiable", cat, "-", "-", NOT_VERIF, "significant", "-", reason)

    ST.doc.recompute()
    problems = [x for x in ST.results if x["status"] == NC and x["sev"] in ("blocking", "significant")]
    improve = [x for x in ST.results if x["sev"] == "improvement"]
    cnt = collections.Counter(x["status"] for x in ST.results)
    path = _report() if write_report else None
    if quiet:
        return len(problems)
    print("=== VERIFICATION %s: %s ===" % (ST.name, ", ".join("%s %d" % kv for kv in sorted(cnt.items()))))
    for x in ST.results:
        if x["status"] == ACCEPTED:
            print("ACCEPTED      %s / %s: %s (%s)" % (x["cat"], x["elem"], x["measure"], x["note"]))
    for x in problems:
        print("NON-COMPLIANT [%s] %s / %s: %s (threshold %s)" % (x["sev"], x["cat"], x["elem"], x["measure"], x["threshold"]))
    for x in improve:
        print("improvement   %s / %s: %s (%s)" % (x["cat"], x["elem"], x["measure"], x["note"] or x["threshold"]))
    if path:
        print("report:", path)
    print("TOTAL PROBLEMS:", len(problems))
    return len(problems)


def _report():
    out = os.path.join(ST.dir, "output")
    os.makedirs(out, exist_ok=True)
    rs = ST.results
    blocking = [x for x in rs if x["status"] == NON_COMPLIANT and x["sev"] == "blocking"]
    acc = [x for x in rs if x["status"] == ACCEPTED]
    outcome = ("PRELIMINARY PROPOSAL: geometric and functional checks passed; NOT VERIFIABLE items remain open"
               if not blocking else "NOT DELIVERABLE: %d blocking checks failed" % len(blocking))
    if acc:
        outcome += "; %d non-compliant result(s) accepted by the client (see Accepted)" % len(acc)
    L = ["# Verification - %s" % ST.name, "",
         "Generated by `lib/interiors.py` on %s. Brief: [`brief.md`](../brief.md). Thresholds: `docs/design-rules.md`."
         % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "", "**Outcome:** " + outcome, "",
         "## Summary", "", "| Status | Blocking | Significant | Improvement | Total |", "|---|---|---|---|---|"]
    for st in (VERIFIED, NON_COMPLIANT, ACCEPTED, NOT_VERIF, NOT_APPL):
        sub = [x for x in rs if x["status"] == st]
        L.append("| %s | %d | %d | %d | %d |" % (st, *[sum(1 for x in sub if x["sev"] == s) for s in SEVERITY], len(sub)))
    if acc:
        L += ["", "## Accepted by the client", "", "| Category | Element | Measure | Threshold | Severity | Acceptance |",
              "|---|---|---|---|---|---|"]
        for x in acc:
            L.append("| %(cat)s | %(elem)s | %(measure)s | %(threshold)s | %(sev)s | %(note)s |" % x)
    L += ["", "## I. Checks performed", "", "| Category | Element | Measure | Threshold | Status | Severity | Method | Note |",
          "|---|---|---|---|---|---|---|---|"]
    for x in rs:
        L.append("| %(cat)s | %(elem)s | %(measure)s | %(threshold)s | %(status)s | %(sev)s | %(method)s | %(note)s |" % x)
    L += ["", "## Requirements traceability", "", "| Requirement | Result | Status | Severity | Note |", "|---|---|---|---|---|"]
    for x in rs:
        if x["cat"] == "Requirements":
            L.append("| %(elem)s | %(measure)s | %(status)s | %(sev)s | %(note)s |" % x)
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
        # plan section solid by solid, each cut at half its own height (lesson L10)
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
        data.append({"name": o.Label, "group": g, "color": list(o.IntColor[:3]) if hasattr(o, "IntColor") else [0.8, 0.8, 0.8],
                     "tr": getattr(o, "IntTransparency", 0),
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
