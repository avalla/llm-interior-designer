# Adds layers, dimensions, room names, labels and sliding-door symbols to the plan exported from FreeCAD.
# All project data comes from build/annotations.json (written by interiors.export()).
# Usage: uv run --with ezdxf python annotate_plan.py <build_dir> <out.dxf>
import json
import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment

build, dst = sys.argv[1:3]
doc = ezdxf.readfile(os.path.join(build, "plan_raw.dxf"))
msp = doc.modelspace()
ann = json.load(open(os.path.join(build, "annotations.json")))
mapping = json.load(open(os.path.join(build, "layers.json")))

COLORS = {"WALLS": 7, "WINDOWS": 4, "DOORS": 30, "SWINGS": 3, "FURNITURE": 8, "DIMENSIONS": 1, "TEXT": 7}
for name, aci in COLORS.items():
    if name not in doc.layers:
        doc.layers.add(name, color=aci)
for e in msp:
    e.dxf.layer = mapping.get(e.dxf.layer, "FURNITURE")
for lay in [layer.dxf.name for layer in doc.layers]:
    if lay not in COLORS and lay not in ("0", "Defpoints"):
        doc.layers.remove(lay)
doc.header["$INSUNITS"] = 4  # mm

DIM = {"dimtxt": 110, "dimtsz": 50, "dimexe": 60, "dimexo": 80, "dimgap": 30,
       "dimdec": 0, "dimclrd": 1, "dimclre": 1, "dimclrt": 7, "dimtad": 1}
xs = [e.dxf.start.x for e in msp.query("LINE")] + [e.dxf.end.x for e in msp.query("LINE")]
ys = [e.dxf.start.y for e in msp.query("LINE")] + [e.dxf.end.y for e in msp.query("LINE")]
XMIN, XMAX, YMIN, YMAX = min(xs), max(xs), min(ys), max(ys)

# dimension chains: extension lines start from the outer face closest to the dimension line
for points, horizontal, base in ann["dims"]:
    for a, b in zip(points, points[1:]):
        if horizontal:
            y0 = YMAX if base > (YMIN + YMAX) / 2 else YMIN
            p1, p2, loc, ang = (a, y0), (b, y0), (0, base), 0
        else:
            x0 = XMAX if base > (XMIN + XMAX) / 2 else XMIN
            p1, p2, loc, ang = (x0, a), (x0, b), (base, 0), 90
        msp.add_linear_dim(base=loc, p1=p1, p2=p2, angle=ang, override=DIM, dxfattribs={"layer": "DIMENSIONS"}).render()


def text(s, x, y, h):
    msp.add_text(s, height=h, dxfattribs={"layer": "TEXT"}).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)


for lines, x, y in ann["rooms"]:
    for i, s in enumerate(lines):
        text(s, x, y - i * 190, 150 if (len(lines) == 2 and i == 0) else 100)
for s, x, y, h in ann["labels"]:
    text(s, x, y, h)

# sliding doors: thick leaf + travel arrow
for leaf0, leaf1, a, b in ann["slides"]:
    msp.add_lwpolyline([leaf0, leaf1], dxfattribs={"layer": "DOORS", "const_width": 40})
    msp.add_line(a, b, dxfattribs={"layer": "DOORS"})
    ux, uy = b[0] - a[0], b[1] - a[1]
    L = (ux ** 2 + uy ** 2) ** 0.5 or 1
    ux, uy = ux / L * 120, uy / L * 120
    for sx in (1, -1):
        msp.add_line(b, (b[0] - ux - sx * uy * 0.5, b[1] - uy + sx * ux * 0.5), dxfattribs={"layer": "DOORS"})

text(ann["title"], ann["centre"], ann["base"] - 1900, 160)
if ann["note"]:
    text(ann["note"], ann["centre"], ann["base"] - 2200, 90)

doc.saveas(dst)
print("ok", dst, len(msp), "entities")
