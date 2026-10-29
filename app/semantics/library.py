"""Furniture semantics: what a plan block is (FURNITURE) and the uses its type implies (USES), the same uses that
lib/interiors.py registers by hand (seat, access_zone, clearance, destination, wet_zone, electrical, no_view).

A 2D plan says neither which side of a piece is its front nor what the piece is for. The type comes from the block
name; the front from the plan: seating faces its coffee table or the TV of its room, chairs face their table, every
other piece turns its back to the wall it stands against; failing that, the side with the deepest free floor, logged
as a guess. Block rotation is not used: real studio blocks may carry a front convention (a profile setting, later).
Everything is plan geometry (Shapely, metres); app/importer/to_model.py adds the heights.
Thresholds without a RULES key come from docs/design-rules.md: BED_SIDE, AISLE, PASSAGE, SPLASH.
"""
import math
import re

import numpy
from shapely import oriented_envelope
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

# block-name keywords -> (type, (z0, z1) in m; None = not modelled). Italian and English, first match wins, so the order
# matters: "Desk_Chair" is a chair, "Bedside_Lamp" a table lamp, "Pendant_Island" a hung lamp, "TV_Unit" not a TV.
# Hung items (z0 > 0) are objects for collisions with walls and leaves, never floor obstacles.
FURNITURE = [
    (r"PENSIL|WALL_UNIT|HOOD|CAPPA", "wall unit", (1.40, 2.20)),
    (r"MIRROR|SPECCHI", "mirror", (1.10, 1.90)),
    (r"PENDANT|SOSPENSION|APPLIQUE|DRYING|STENDI|AIRER|SHOWER_HEAD|SOFFIONE", "hung", (1.90, 2.20)),
    (r"TAPPET|RUG", "rug", None),
    (r"HOB|COTTURA|FORNELL|COOKTOP|TAP|RUBINET|MISCELAT", "built-in", (0.0, 0.95)),   # set into a unit
    (r"BEDSIDE|TABLE_LAMP|ABAT|LUME", "table lamp", (0.60, 1.00)),            # on a nightstand or a table
    (r"LAMP|LAMPAD|PIANTANA", "lamp", (0.0, 1.60)),
    (r"COMODIN|NIGHTSTAND", "nightstand", (0.0, 0.50)),
    (r"POLTRON|ARMCHAIR", "armchair", (0.0, 0.85)),
    (r"SEDI|CHAIR|SGABELL|STOOL", "chair", (0.0, 0.85)),
    (r"ARMADI|WARDROBE|CLOSET_UNIT|COLONN|TALL_UNIT|UTILITY", "wardrobe", (0.0, 2.40)),
    (r"LIBRER|BOOKCASE|SHELF", "bookcase", (0.0, 2.00)),
    (r"SCARPIER|SHOE|CONSOLE|MADIA|CREDENZ|SIDEBOARD|CASSETTIER|DRESSER|CABINET", "cabinet", (0.0, 0.90)),
    (r"TV_UNIT|PORTA_?TV|MOBILE_TV", "tv unit", (0.0, 0.50)),
    (r"LETTO|BED(?!ROOM)", "bed", (0.0, 0.60)),
    (r"DIVANO|SOFA", "sofa", (0.0, 0.85)),
    (r"TAVOLIN|COFFEE", "coffee table", (0.0, 0.40)),
    (r"ISOLA|ISLAND|PENISOL|PENINSULA", "island", (0.0, 0.90)),
    (r"TAVOL|TABLE|SCRIVAN|DESK", "table", (0.0, 0.75)),
    (r"LAVATRIC|WASHING|ASCIUGATR|DRYER|LAVASTOV|DISHWASH", "appliance", (0.0, 0.90)),
    (r"BASI|BASE|WORKTOP|PIANO|CUCINA|KITCHEN", "base unit", (0.0, 0.90)),
    (r"GLASS|VETR|SCREEN|CRISTAL", "shower screen", (0.0, 2.00)),
    (r"VASCA|BATH(?!ROOM)", "bath", (0.0, 0.55)),
    (r"DOCCIA|SHOWER|PIATTO", "shower", (0.0, 0.03)),            # a tray is walked on
    (r"WC|VATER|TAZZA", "wc", (0.0, 0.85)),
    (r"BIDET|LAVAB|WASHBASIN|VANITY|SINK|LAVELLO", "sanitary", (0.0, 0.85)),
    (r"TOWEL|SCALDASALV|TERMOARRED|RADIAT|TERMOSIF", "heater", (0.20, 1.50)),       # on the wall
    (r"TV", "tv", (0.0, 1.70)),
    (r"PLANT|PIANTA", "decor", (0.0, 0.45)),
]
# type pairs a plan draws one over the other without a collision: a chair under its table, a TV on its unit, a hob in
# the worktop, a lamp on the nightstand, a screen on the shower tray
STACKS = {frozenset(p) for p in [
    ("chair", "table"), ("chair", "island"), ("tv", "tv unit"), ("tv", "cabinet"), ("tv", "base unit"), ("lamp", "nightstand"),
    ("lamp", "table"), ("lamp", "cabinet"), ("built-in", "base unit"), ("built-in", "island"), ("built-in", "sanitary"),
    ("built-in", "cabinet"), ("sanitary", "base unit"), ("sanitary", "cabinet"), ("sanitary", "island"),
    ("built-in", "wc"),
    ("appliance", "base unit"), ("shower screen", "shower"), ("shower screen", "bath"), ("decor", "table"),
    ("decor", "cabinet"), ("wall unit", "wall unit")]}
# type -> uses
USES = {
    "chair": ("seat",),
    "wardrobe": ("access", "destination"),
    "cabinet": ("access",),
    "base unit": ("access",),
    "appliance": ("access",),
    "island": ("aisle",),
    "bed": ("bed sides", "no view"),
    "sofa": ("in front",),          # in front of the middle half of the seat
    "armchair": ("in front",),      # or any other free side: an armchair is small and its front a guess
    "sanitary": ("destination",),
    "wc": ("destination", "no view"),
    "shower": ("splash zone",),
    "bath": ("splash zone",),
}
ELECTRICAL = re.compile(r"LAVATRIC|WASHING|ASCIUG|DRYER|LAVASTOV|DISHWASH|TOWEL|SCALDASALV|TERMOARRED|BOILER|STUFA|"
                        r"HEATER|PRESA|SOCKET", re.I)
ELECTRIC_TYPES = ("appliance", "heater")                             # a towel warmer may be hydronic: assumed electric
RUN = ("wardrobe", "cabinet", "base unit", "appliance", "sanitary", "wc")  # pieces that form one run when they touch
NOT_IN_THE_WAY = ("bed", "nightstand", "lamp", "table lamp")        # around a bed side
MOVABLE = ("nightstand", "lamp", "table lamp", "chair", "decor")     # light pieces moved aside to open a unit
BED_SIDE, AISLE, PASSAGE, SPLASH = (0.60, 0.70), (0.90, 1.10), (0.80, 0.90), 0.60


TYPE_Z = {}
for _rx, _t, _z in FURNITURE:
    TYPE_Z.setdefault(_t, _z)


def furniture_type(block):
    """(type, (z0, z1)) from the block name; None when no keyword matches."""
    return next(((t, z) for rx, t, z in FURNITURE if re.search(rx, block, re.I)), None)


def type_candidates(block):
    """Every type whose keywords match the block name, the first match (the one applied) first."""
    out = []
    for rx, t, _z in FURNITURE:
        m = re.search(rx, block, re.I)
        if m and t not in [c["type"] for c in out]:
            out.append(dict(type=t, confidence=0.8 if not out else 0.4, why="block name: %s" % m.group(0)))
    return out


def _sides(fp):
    """The four sides of the minimum rotated rectangle, counter-clockwise: ends a, b, direction d, outward normal n."""
    with numpy.errstate(divide="ignore", invalid="ignore"):     # GEOS divides by zero on axis-aligned rectangles
        c = list(orient(oriented_envelope(fp)).exterior.coords)[:4]
    out = []
    for a, b in zip(c, c[1:] + c[:1]):
        L = math.dist(a, b)
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        out.append(dict(a=a, b=b, d=d, n=(d[1], -d[0]), L=L))
    return out


def _at(s, u, v):
    """Point u along side s from its end a, v outwards."""
    return (s["a"][0] + s["d"][0] * u + s["n"][0] * v, s["a"][1] + s["d"][1] * u + s["n"][1] * v)


def _strip(s, u0, u1, v0, v1):
    return Polygon([_at(s, u0, v0), _at(s, u1, v0), _at(s, u1, v1), _at(s, u0, v1)])


def _contact(s, struct):
    """Length of the side that stands against a wall (within 5 cm)."""
    return LineString([_at(s, 0.02, 0.05), _at(s, s["L"] - 0.02, 0.05)]).intersection(struct).length


def _depth(s, struct, far=5.0):
    """Free floor in front of the middle of the side, up to the first wall."""
    hit = LineString([_at(s, s["L"] / 2, 0.01), _at(s, s["L"] / 2, far)]).intersection(struct)
    return far if hit.is_empty else Point(_at(s, s["L"] / 2, 0)).distance(hit)


def _compass(n):
    return ("east" if n[0] > 0 else "west") if abs(n[0]) >= abs(n[1]) else ("north" if n[1] > 0 else "south")


def _front(f, S, items, struct):
    """(index of the front side of f among its sides S, source, confidence). Order: the block's own front (studio
    profile convention + insert rotation); seating facing its coffee table or the room's TV (a sofa with a long side,
    an armchair with any); the side opposite the wall behind; the deepest free floor (a guess)."""
    if f.get("front"):
        fx, fy = f["front"]
        return max(range(4), key=lambda i: S[i]["n"][0] * fx + S[i]["n"][1] * fy), "block rotation", 0.9
    if f["type"] in ("sofa", "armchair"):
        near = [g for g in items if g["type"] == "coffee table" and g["footprint"].distance(f["footprint"]) < 1.0]
        tv = next((g for g in items if g["type"] == "tv" and g["room"] == f["room"]), None)
        if near or tv:
            c, t = f["footprint"].centroid, (near[0] if near else tv)["footprint"].centroid
            long = [i for i in range(4) if f["type"] == "armchair" or S[i]["L"] >= max(x["L"] for x in S) / 1.3]
            i = max(long, key=lambda i: S[i]["n"][0] * (t.x - c.x) + S[i]["n"][1] * (t.y - c.y))
            return i, "faces the coffee table" if near else "faces the TV", 0.6
    con = [_contact(s, struct) for s in S]
    dep = [_depth(s, struct) for s in S]
    back = max(range(4), key=lambda i: (round(con[i], 1), dep[(i + 2) % 4]))   # equal walls: the deeper front wins
    if con[back] >= 0.30:
        return (back + 2) % 4, "back against the wall", 0.8
    return max(range(4), key=lambda i: (round(dep[i], 1), S[i]["L"])), "deepest free floor (guess)", 0.3


def _cell(area, room, obst, grid, cost):
    """The free cell of the route grid (origin and size in grid) inside area and room with the lowest cost(x, y);
    obst is already inflated as the grid inflates it. None when no cell is free."""
    gx, gy, c = grid
    x0, y0, x1, y1 = area.bounds
    best = None
    for i in range(int((x0 - gx) / c), int((x1 - gx) / c) + 1):
        for j in range(int((y0 - gy) / c), int((y1 - gy) / c) + 1):
            p = Point(gx + (i + 0.5) * c, gy + (j + 0.5) * c)
            if area.contains(p) and room.contains(p) and not obst.contains(p):
                k = cost(p.x, p.y)
                if best is None or k < best[0]:
                    best = (k, p)
    return best[1] if best else None


def _stand(s, room, obst, grid, u0=0.0, u1=None):
    """Destination in front of side s, 20-80 cm out, as near as possible to the middle of [u0, u1]. When no cell is
    free the middle point at 35 cm is returned, and the route check reports it."""
    u1 = s["L"] if u1 is None else u1
    mid = (u0 + u1) / 2

    def cost(x, y):
        dx, dy = x - s["a"][0], y - s["a"][1]
        return abs(dx * s["d"][0] + dy * s["d"][1] - mid) + dx * s["n"][0] + dy * s["n"][1]
    p = _cell(_strip(s, u0, u1, 0.20, 0.80), room, obst, grid, cost)
    return p or Point(_at(s, mid, 0.35))


def _seat(f, items, out, A):
    """The chair's table is the nearest table or island within 60 cm; the seat looks from the table edge outwards."""
    c = f["footprint"].centroid
    tables = [g for g in items if g["type"] in ("table", "island") and g["footprint"].distance(f["footprint"]) < 0.60]
    if not tables:
        A.append("%s: no table within 60 cm, no seat check" % f["item"])
        return
    t = min(tables, key=lambda g: g["footprint"].distance(c))
    ring = t["footprint"].exterior
    e = ring.interpolate(ring.project(c))
    v = (e.x - c.x, e.y - c.y) if t["footprint"].contains(c) else (c.x - e.x, c.y - e.y)
    k = math.hypot(*v)
    if k < 1e-6:
        A.append("%s: centred on the edge of %s, no seat check" % (f["item"], t["item"]))
        return
    d = (v[0] / k, v[1] / k)
    across = [(x - c.x) * -d[1] + (y - c.y) * d[0] for x, y in f["footprint"].exterior.coords]
    out["seats"].append(dict(name=f["item"], edge=[e.x, e.y], dir=list(d), hw=(max(across) - min(across)) / 2,
                             own=[f["item"], t["item"]]))


def _bed(f, S, items, struct, room, obst, grid, out, A):
    """Head against a wall (a short side); each long side not against a wall gets a destination and a clearance,
    measured beyond the 50 cm next to the head where nightstands stand."""
    short = sorted(range(4), key=lambda i: S[i]["L"])[:2]
    con = {i: _contact(S[i], struct) for i in short}
    h = max(short, key=lambda i: (round(con[i], 1), -_depth(S[i], struct)))
    if f.get("front"):                            # the block's front is the foot of the bed
        h = min(short, key=lambda i: S[i]["n"][0] * f["front"][0] + S[i]["n"][1] * f["front"][1])
        why, conf = "block rotation", 0.9
    elif con[h] >= 0.30:
        why, conf = "head against the wall", 0.8
    else:
        why, conf = "head nearest a wall (guess)", 0.3
        A.append("%s: head not against a wall, guessed %s" % (f["item"], _compass(S[h]["n"])))
    out["fronts"].append(dict(item=f["item"], side=_compass(S[(h + 2) % 4]["n"]), why=why, confidence=conf))
    hm = Point(_at(S[h], S[h]["L"] / 2, 0))
    others = [struct] + [g["footprint"] for g in items if g["type"] not in NOT_IN_THE_WAY]
    for i in range(4):
        s = S[i]
        if i in short or _contact(s, struct) >= 0.5 * s["L"]:
            continue
        u0, u1 = (0.0, s["L"] - 0.50) if hm.distance(Point(s["b"])) < hm.distance(Point(s["a"])) else (0.50, s["L"])
        label = "%s: %s %s side" % (f["room"], f["item"], _compass(s["n"]))
        p = _stand(s, room, obst, grid, u0, u1)
        out["targets"][label] = (p.x, p.y)
        strip = _strip(s, u0, u1, 0.0, 1.50)
        near = unary_union([c for c in (o.intersection(strip) for o in others) if c.area > 1e-4])   # touching: no
        if not near.is_empty:
            body = f["footprint"].intersection(_strip(s, u0, u1, -10.0, 0.01))
            out["clearances"].append(dict(label=label, a=(label + " | bed", body), b=(label + " | obstacles", near),
                                          min=BED_SIDE[0], comfort=BED_SIDE[1]))


def _splash(f, S, items, struct, room, obst, grid, out):
    """Sides of a shower tray or bath not closed by a wall or a screen: 60 cm splash zone. Destination: on the tray of
    a shower, in front of the widest open side of a bath."""
    closed = unary_union([struct] + [g["footprint"] for g in items if g["type"] == "shower screen"]).buffer(0.03)
    best = None
    for s in S:
        side = LineString([s["a"], s["b"]])
        rest = side.difference(closed)
        for piece in getattr(rest, "geoms", [rest]):
            if piece.is_empty or piece.length < 0.20:
                continue
            u0, u1 = sorted(side.project(Point(q)) for q in (piece.coords[0], piece.coords[-1]))
            out["wet"].append(dict(label="%s: %s open side (%s)" % (f["room"], f["item"], _compass(s["n"])),
                                   zone=_strip(s, u0, u1, 0.0, SPLASH)))
            if best is None or u1 - u0 > best[2] - best[1]:
                best = (s, u0, u1)
    if f["type"] == "shower":                     # one walks into a shower: a free spot on the tray
        c = f["footprint"].centroid
        p = _cell(f["footprint"], room, obst, grid, lambda x, y: c.distance(Point(x, y))) or c
    elif best:
        p = _stand(best[0], room, obst, grid, best[1], best[2])
    else:
        return
    out["targets"]["%s: %s" % (f["room"], f["item"])] = (p.x, p.y)


def uses(items, rooms, struct, obst, grid, rules, A):
    """items: modelled furniture as dict(item, type, footprint, z=(z0, z1), room); rooms: name -> footprint;
    struct: everything that is not room floor (walls, closed openings, outside); obst: everything a person walks
    around; grid: route grid origin and cell (x0, y0, cell). Returns the uses as plan geometry; guesses go to A."""
    out = dict(seats=[], access=[], clearances=[], targets={}, wet=[], elec=[], views=[], fronts=[])
    obst = obst.buffer(rules["person_radius"] + 0.005, join_style="mitre")
    fronts = {}
    every, items = items, [g for g in items if g["z"][0] == 0]          # hung pieces have no use and are no obstacle
    out["elec"] = [g["item"] for g in every if g["type"] in ELECTRIC_TYPES or ELECTRICAL.search(g["item"])]
    for f in items:
        todo = USES.get(f["type"], ())
        if not todo or f["footprint"].area < 0.01:
            continue
        room = rooms.get(f["room"]) or unary_union(list(rooms.values()))
        if "seat" in todo:
            _seat(f, items, out, A)
            continue
        S = _sides(f["footprint"])
        if "bed sides" in todo:
            _bed(f, S, items, struct, room, obst, grid, out, A)
        if "no view" in todo:
            out["views"].append(dict(label="Entrance: %s not visible" % f["item"], target=f["item"]))
        if "splash zone" in todo and f["footprint"].area >= 0.30:      # a tray or a bath, not a drain or a mixer
            _splash(f, S, items, struct, room, obst, grid, out)
        if not {"access", "destination", "in front"} & set(todo):
            continue
        i, why, conf = _front(f, S, items, struct)
        s = fronts[f["item"]] = S[i]
        out["fronts"].append(dict(item=f["item"], side=_compass(s["n"]), why=why, confidence=conf))
        if conf < 0.5:
            A.append("%s: front guessed %s (%s)" % (f["item"], _compass(s["n"]), why))
        if "access" in todo:
            # a run of touching units shares one front: the zone stops where the next unit starts (an L corner)
            run = [g for g in items if g is not f and g["type"] in RUN and g["footprint"].distance(f["footprint"]) < 0.02]
            zone = _strip(s, 0.05, s["L"] - 0.05, 0.005, 0.005 + rules["access"])
            zone = zone.difference(unary_union([g["footprint"] for g in run]).buffer(0.01))
            zone = max(getattr(zone, "geoms", [zone]), key=lambda p: p.area)
            own = [f["item"]] + [g["item"] for g in run] + [g["item"] for g in every if g["type"] in MOVABLE]
            out["access"].append(dict(label="%s: in front of %s" % (f["room"], f["item"]), own=own, zone=zone))
        if "destination" in todo or "in front" in todo:
            p = _stand(s, room, obst, grid, *((s["L"] / 4, 3 * s["L"] / 4) if "in front" in todo else ()))
            if f["type"] == "armchair" and obst.contains(p):
                p = next((q for q in (_stand(x, room, obst, grid) for x in S) if not obst.contains(q)), p)
            out["targets"]["%s: %s%s" % (f["room"], f["item"], " (in front)" if "in front" in todo else "")] = (p.x, p.y)
    # kitchen aisles: an island in front of a run of base units (or of tall units: main passage)
    for isl in [g for g in items if "aisle" in USES.get(g["type"], ())]:
        for u in [g for g in items if g["item"] in fronts and g["type"] in ("base unit", "appliance", "wardrobe")]:
            s = fronts[u["item"]]
            gap = isl["footprint"].distance(u["footprint"])
            if gap > 0.02 and _strip(s, 0.0, s["L"], 0.0, 1.50).intersects(isl["footprint"]):   # touching: peninsula
                mn, cf = AISLE if u["type"] != "wardrobe" else PASSAGE
                out["clearances"].append(dict(label="%s: %s / %s" % (u["room"], isl["item"], u["item"]),
                                              a=(isl["item"], isl["footprint"]), b=(u["item"], u["footprint"]),
                                              min=mn, comfort=cf))
    return out


def stacked(items):
    """Pairs of items whose plan outlines overlap as the plan draws them (STACKS): not a collision."""
    return [[a["item"], b["item"]] for i, a in enumerate(items) for b in items[i + 1:]
            if frozenset((a["type"], b["type"])) in STACKS and a["footprint"].intersection(b["footprint"]).area > 1e-6]
