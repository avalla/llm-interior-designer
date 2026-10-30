# Writes a plan DXF "as a studio draws it" from an exported neutral model, plus the ground truth to score recognition.
#   uv run --with ezdxf --with shapely python app/tests/make_sample_dxf.py [app/build/models/apartment-100sqm.json]
# Conventions of the sample (one plausible studio, not a standard): millimetres; walls as closed polylines and a hatch on
# MURI, cut at 1.70 m so every window is a gap; doors as blocks PORTA_<w> (closed leaf, open leaf, 90 degree arc) on PORTE;
# sliding doors as blocks SCORREVOLE_<l> on PORTE; windows as blocks FINESTRA scaled to the width, with attributes
# H and DAVANZALE, on FINESTRE; furniture as one block per piece on ARREDI; room names and areas as texts on TESTI;
# a title block and dimensions as noise. Output: app/build/samples/<name>.dxf and <name>.truth.json.
# --style lines: a second, rougher studio: English layer names (A-WALL, A-DOOR...), walls as loose LINE segments without
# hatch, no declared units; output <name>-lines.dxf.
# --style codes: a third studio that names nothing: layers 0-M30, 0-INF-P, 0-INF-F, 0-A, 0-T; centimetres, undeclared;
# furniture blocks named by catalogue codes (AR01 wardrobe, SE01 chair... see CODES), each drawn with its front towards
# local -Y and inserted with a rotation. The true front comes from the model's declared uses (access zone, seat,
# destination of a sofa or armchair), else the side away from the nearest wall (cut at 0.5 m, doors closed).
# Output <name>-codes.dxf; the truth lists block, type and front of every piece.
import json
import math
import os
import sys

import ezdxf
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from app.semantics import library  # noqa: E402

STYLE = sys.argv[sys.argv.index("--style") + 1] if "--style" in sys.argv else "blocks"
args = [a for a in sys.argv[1:] if a not in ("--style", STYLE)]
src = args[0] if args else os.path.join(HERE, "..", "build", "models", "apartment-100sqm.json")
L = dict(blocks=dict(walls="MURI", doors="PORTE", windows="FINESTRE", furniture="ARREDI", texts="TESTI"),
         lines=dict(walls="A-WALL", doors="A-DOOR", windows="A-GLAZ", furniture="A-FURN", texts="A-AREA-IDEN"),
         codes=dict(walls="0-M30", doors="0-INF-P", windows="0-INF-F", furniture="0-A", texts="0-T"))[STYLE]
CODES = {"wardrobe": "AR", "chair": "SE", "table": "TA", "island": "IS", "sofa": "DI", "armchair": "PO", "bed": "LE",
         "nightstand": "CO", "bookcase": "LI", "cabinet": "MO", "tv unit": "MT", "base unit": "BA", "appliance": "EL",
         "wall unit": "PE", "mirror": "SP", "hung": "SO", "built-in": "IN", "lamp": "LA", "table lamp": "LU",
         "coffee table": "TB", "shower screen": "VE", "shower": "DO", "bath": "VA", "sanitary": "SA", "wc": "VS", "heater": "TE",
         "tv": "TV", "decor": "DE", "rug": "TP"}
m = json.load(open(src))
OUT = os.path.join(HERE, "..", "build", "samples")
os.makedirs(OUT, exist_ok=True)
MM = 100.0 if STYLE == "codes" else 1000.0
CUT = 1.70


def section(solids, z):
    polys = []
    for sol in solids or []:
        for b in sol:
            if b["z"][0] <= z < b["z"][1]:
                p = Polygon()
                for r in b["rings"]:
                    p = p.symmetric_difference(Polygon(r).buffer(0))
                polys.append(p)
    return unary_union(polys) if polys else Polygon()


def plan(solids):
    return unary_union([section(solids, (b["z"][0] + b["z"][1]) / 2) for sol in solids for b in sol])


doc = ezdxf.new("R2018", setup=True)
doc.units = ezdxf.units.MM if STYLE == "blocks" else 0
for name, color in ((L["walls"], 7), (L["doors"], 3), (L["windows"], 5), (L["furniture"], 8), (L["texts"], 2),
                    ("QUOTE", 1), ("CARTIGLIO", 7)):
    doc.layers.add(name, color=color)
msp = doc.modelspace()
truth = dict(name=m["name"], walls=None, doors=[], slides=[], windows=[], rooms=[], furniture=[])

# walls
walls = unary_union([section(w["solids"], CUT) for w in m["walls"]])
for poly in getattr(walls, "geoms", [walls]):
    if STYLE == "lines":
        for ring in [poly.exterior] + list(poly.interiors):
            c = list(ring.coords)
            for a, b in zip(c, c[1:]):
                msp.add_line((a[0] * MM, a[1] * MM), (b[0] * MM, b[1] * MM), dxfattribs={"layer": L["walls"]})
        continue
    for ring in [poly.exterior] + list(poly.interiors):
        msp.add_lwpolyline([(x * MM, y * MM) for x, y in ring.coords[:-1]], close=True, dxfattribs={"layer": L["walls"]})
    hatch = msp.add_hatch(color=8, dxfattribs={"layer": L["walls"]})
    hatch.set_pattern_fill("ANSI31", scale=10)
    for ring in [poly.exterior] + list(poly.interiors):
        hatch.paths.add_polyline_path([(x * MM, y * MM) for x, y in ring.coords[:-1]], is_closed=True)
truth["walls"] = mapping(walls)

# hinged doors (kind Door only: window, wardrobe and appliance leaves belong to their own symbols)
for d in m["doors"]:
    if d["kind"] != "Door":
        continue
    g = d["geo"]
    w = round(g["w"] * MM)
    bname = "PORTA_%d" % w
    if bname not in doc.blocks:
        blk = doc.blocks.new(bname)
        blk.add_lwpolyline([(0, 0), (w, 0), (w, -0.04 * MM), (0, -0.04 * MM)], close=True)    # closed leaf (thin)
        blk.add_line((0, 0), (0, w))                                              # open leaf
        blk.add_arc((0, 0), w, 0, 90)
    (dx, dy), (nx, ny) = g["d"], g["n"]
    mirror = dx * ny - dy * nx < 0
    msp.add_blockref(bname, (g["hinge"][0] * MM, g["hinge"][1] * MM), dxfattribs={
        "layer": L["doors"], "rotation": math.degrees(math.atan2(dy, dx)), "yscale": -1 if mirror else 1})
    truth["doors"].append(dict(name=d["name"], hinge=g["hinge"], d=g["d"], n=g["n"], w=g["w"]))

# sliding doors: the closed leaf as a block; the open position is not drawn (as on most plans)
for s in m["slides"]:
    x0, y0, _, x1, y1, _ = s["c"]
    length, along_x = max(x1 - x0, y1 - y0), (x1 - x0) >= (y1 - y0)
    bname = "SCORREVOLE_%d" % round(length * MM)
    if bname not in doc.blocks:
        blk = doc.blocks.new(bname)
        blk.add_lwpolyline([(0, 0), (length * MM, 0), (length * MM, 0.04 * MM), (0, 0.04 * MM)], close=True)
    ins = (x0 * MM, y0 * MM) if along_x else (x1 * MM, y0 * MM)
    msp.add_blockref(bname, ins, dxfattribs={"layer": L["doors"], "rotation": 0 if along_x else 90})
    truth["slides"].append(dict(name=s["name"], closed=[x0, y0, x1, y1], open=[s["o"][0], s["o"][1], s["o"][3], s["o"][4]]))

# windows: unit block scaled to the net width, attributes for height and sill
blk = doc.blocks.new("FINESTRA")
for y in (-0.06 * MM, 0, 0.06 * MM):
    blk.add_line((0, y), (MM, y))
blk.add_line((0, -0.06 * MM), (0, 0.06 * MM))
blk.add_line((MM, -0.06 * MM), (MM, 0.06 * MM))
blk.add_attdef("H", (0, 0.1 * MM), dxfattribs={"height": 0.08 * MM})
blk.add_attdef("DAVANZALE", (0, 0.2 * MM), dxfattribs={"height": 0.08 * MM})
for w in m["windows"]:
    ref = msp.add_blockref("FINESTRA", (w["x0"] * MM, w["yc"] * MM),
                           dxfattribs={"layer": L["windows"], "xscale": w["x1"] - w["x0"]})
    ref.add_auto_attribs({"H": "%d" % round((w["z1"] - w["z0"]) * MM), "DAVANZALE": "%d" % round(w["z0"] * MM)})
    truth["windows"].append(dict(name=w["name"], x0=w["x0"], x1=w["x1"], yc=w["yc"], z0=w["z0"], z1=w["z1"]))

# furniture: one block per piece, drawn as its plan outline in local coordinates
items = {}
for o in m["objects"]:
    items.setdefault(o["item"], []).append(plan(o["solids"]))
targets = [Point(p) for p in m["targets"].values()]
# walls below the sills with the doors closed, for the true fronts
low = unary_union([section(w["solids"], 0.5) for w in m["walls"]]
                  + [LineString([d["geo"]["hinge"], (d["geo"]["hinge"][0] + d["geo"]["d"][0] * d["geo"]["w"],
                                                     d["geo"]["hinge"][1] + d["geo"]["d"][1] * d["geo"]["w"])]).buffer(0.10)
                     for d in m["doors"] if d["kind"] == "Door"])


def axis(dx, dy):
    return (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dy) else (0, 1 if dy > 0 else -1)


def true_front(item, p, kind):
    """The front the designer declared through the uses, else the side away from the wall nearest to the piece."""
    c = p.centroid
    zone = next((plan(a["zone"]) for a in m["access"] if a["own"] and a["own"][0] == item), None)
    if zone is not None and not zone.is_empty:
        # the face the zone lies beyond (a narrow appliance zone at one end of a long run has its centroid off-axis)
        zx0, zy0, zx1, zy1 = zone.bounds
        bx0, by0, bx1, by1 = p.bounds
        for face, cond in (((0, 1), zy0 >= by1 - 0.10), ((0, -1), zy1 <= by0 + 0.10),      # 10 cm: a worktop
                           ((1, 0), zx0 >= bx1 - 0.10), ((-1, 0), zx1 <= bx0 + 0.10)):      # overhangs its units
            if cond:
                return face
        return axis(zone.centroid.x - c.x, zone.centroid.y - c.y)
    seat = next((s for s in m["seats"] if s["name"] == item), None)
    if seat:
        return axis(-seat["dir"][0], -seat["dir"][1])
    if kind in ("sofa", "armchair") and targets:
        t = min(targets, key=p.distance)
        return axis(t.x - c.x, t.y - c.y)
    x0, y0, x1, y1 = p.bounds
    x0, y0, x1, y1 = x0 + 0.03, y0 + 0.03, x1 - 0.03, y1 - 0.03        # side ends inset: corners touch both walls
    e = 0.03
    side = {(1, 0): LineString([(x1 + e, y0), (x1 + e, y1)]), (-1, 0): LineString([(x0 - e, y0), (x0 - e, y1)]),
            (0, 1): LineString([(x0, y1 + e), (x1, y1 + e)]), (0, -1): LineString([(x0, y0 - e), (x1, y0 - e)])}
    gap = {d: seg.distance(low) for d, seg in side.items()}

    def depth(d):                                                # free floor in front of the middle of the side
        mid = side[d].interpolate(0.5, normalized=True)
        hit = LineString([(mid.x, mid.y), (mid.x + 9 * d[0], mid.y + 9 * d[1])]).intersection(low)
        return 9 if hit.is_empty else mid.distance(hit)
    back = min(gap, key=lambda d: (round(gap[d], 2), -depth((-d[0], -d[1]))))   # equal: the deeper front wins
    return (-back[0], -back[1])


count = {}
for item, polys in sorted(items.items()):
    p = unary_union(polys)
    if p.is_empty:
        continue
    entry = dict(item=item, footprint=mapping(p))
    if STYLE == "codes":
        kind = (library.furniture_type(item) or ("unknown", None))[0]
        code = CODES.get(kind, "XX")
        count[code] = count.get(code, 0) + 1
        bname = "%s%02d" % (code, count[code])
        f = true_front(item, p, kind)
        rot = math.degrees(math.atan2(f[1], f[0])) + 90           # local -Y turned onto the front
        c = p.centroid
        local = affinity.rotate(affinity.translate(p, -c.x, -c.y), -rot, origin=(0, 0))
        ins = (c.x * MM, c.y * MM)
        entry.update(block=bname, type=kind, front=list(f))
    else:
        bname, rot, local, ins = "ARR_" + item, 0, affinity.translate(p, -p.bounds[0], -p.bounds[1]), \
            (p.bounds[0] * MM, p.bounds[1] * MM)
    blk = doc.blocks.new(bname)
    for part in getattr(local, "geoms", [local]):
        if part.geom_type == "Polygon":
            blk.add_lwpolyline([(x * MM, y * MM) for x, y in part.exterior.coords[:-1]], close=True)
    msp.add_blockref(bname, ins, dxfattribs={"layer": L["furniture"], "rotation": rot})
    truth["furniture"].append(entry)

# room names and areas
for r in m["rooms"]:
    x, y = r["xy"]
    msp.add_text(r["name"].upper(), height=0.15 * MM, dxfattribs={"layer": L["texts"]}).set_placement((x * MM, y * MM))
    msp.add_text("%.1f m²" % r["area"], height=0.1 * MM, dxfattribs={"layer": L["texts"]}).set_placement(
        (x * MM, y * MM - 0.25 * MM))
    truth["rooms"].append(dict(name=r["name"], footprint=mapping(unary_union([box(*rc) for rc in r["rects"]]))))

# noise: title block and one dimension chain
xs, ys = walls.bounds[0::2], walls.bounds[1::2]
k = MM / 1000                                                    # noise sizes in millimetres
msp.add_lwpolyline([(xs[0] * MM - 1500 * k, ys[0] * MM - 2500 * k), (xs[1] * MM + 1500 * k, ys[0] * MM - 2500 * k),
                    (xs[1] * MM + 1500 * k, ys[1] * MM + 1500 * k), (xs[0] * MM - 1500 * k, ys[1] * MM + 1500 * k)],
                   close=True, dxfattribs={"layer": "CARTIGLIO"})
msp.add_text("PIANTA ARREDO - SCALA 1:50", height=250 * k, dxfattribs={"layer": "CARTIGLIO"}).set_placement(
    (xs[0] * MM, ys[0] * MM - 2000 * k))
msp.add_linear_dim(base=(xs[0] * MM, ys[0] * MM - 800 * k), p1=(xs[0] * MM, ys[0] * MM), p2=(xs[1] * MM, ys[0] * MM),
                   dxfattribs={"layer": "QUOTE"}).render()

name = os.path.basename(src)[:-5] + ("" if STYLE == "blocks" else "-" + STYLE)
truth["units"] = "cm" if STYLE == "codes" else "mm"
doc.saveas(os.path.join(OUT, name + ".dxf"))
json.dump(truth, open(os.path.join(OUT, name + ".truth.json"), "w"))
print("sample:", os.path.join(OUT, name + ".dxf"), "| doors %d, slides %d, windows %d, rooms %d, furniture %d" % (
    len(truth["doors"]), len(truth["slides"]), len(truth["windows"]), len(truth["rooms"]), len(truth["furniture"])))
