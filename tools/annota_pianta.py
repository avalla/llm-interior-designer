# Aggiunge layer, quote, nomi locali, etichette e simboli scorrevoli alla pianta esportata da FreeCAD.
# Tutti i dati di progetto arrivano da build/annotazioni.json (scritto da arredo.esporta()).
# Uso: uv run --with ezdxf python annota_pianta.py <build_dir> <out.dxf>
import json
import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment

build, dst = sys.argv[1:3]
doc = ezdxf.readfile(os.path.join(build, "pianta_raw.dxf"))
msp = doc.modelspace()
ann = json.load(open(os.path.join(build, "annotazioni.json")))
mapping = json.load(open(os.path.join(build, "layers.json")))

COLORS = {"MURI": 7, "SERRAMENTI": 4, "PORTE": 30, "APERTURE": 3, "ARREDI": 8, "QUOTE": 1, "TESTI": 7}
for name, aci in COLORS.items():
    if name not in doc.layers:
        doc.layers.add(name, color=aci)
for e in msp:
    e.dxf.layer = mapping.get(e.dxf.layer, "ARREDI")
for lay in [l.dxf.name for l in doc.layers]:
    if lay not in COLORS and lay not in ("0", "Defpoints"):
        doc.layers.remove(lay)
doc.header["$INSUNITS"] = 4  # mm

DIM = {"dimtxt": 110, "dimtsz": 50, "dimexe": 60, "dimexo": 80, "dimgap": 30,
       "dimdec": 0, "dimclrd": 1, "dimclre": 1, "dimclrt": 7, "dimtad": 1}
xs = [e.dxf.start.x for e in msp.query("LINE")] + [e.dxf.end.x for e in msp.query("LINE")]
ys = [e.dxf.start.y for e in msp.query("LINE")] + [e.dxf.end.y for e in msp.query("LINE")]
XMIN, XMAX, YMIN, YMAX = min(xs), max(xs), min(ys), max(ys)

# catene di quote: i punti di estensione partono dal filo esterno piu' vicino alla linea di quota
for points, horizontal, base in ann["quote"]:
    for a, b in zip(points, points[1:]):
        if horizontal:
            y0 = YMAX if base > (YMIN + YMAX) / 2 else YMIN
            p1, p2, loc, ang = (a, y0), (b, y0), (0, base), 0
        else:
            x0 = XMAX if base > (XMIN + XMAX) / 2 else XMIN
            p1, p2, loc, ang = (x0, a), (x0, b), (base, 0), 90
        msp.add_linear_dim(base=loc, p1=p1, p2=p2, angle=ang, override=DIM, dxfattribs={"layer": "QUOTE"}).render()


def text(s, x, y, h):
    msp.add_text(s, height=h, dxfattribs={"layer": "TESTI"}).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)


for lines, x, y in ann["stanze"]:
    for i, s in enumerate(lines):
        last = i == len(lines) - 1
        text(s, x, y - i * 190, 150 if (len(lines) == 2 and i == 0) else 100)
for s, x, y, h in ann["testi"]:
    text(s, x, y, h)

# porte scorrevoli: anta in spessore + freccia di scorrimento
for leaf0, leaf1, a, b in ann["scorrevoli"]:
    msp.add_lwpolyline([leaf0, leaf1], dxfattribs={"layer": "PORTE", "const_width": 40})
    msp.add_line(a, b, dxfattribs={"layer": "PORTE"})
    ux, uy = b[0] - a[0], b[1] - a[1]
    L = (ux ** 2 + uy ** 2) ** 0.5 or 1
    ux, uy = ux / L * 120, uy / L * 120
    for sx in (1, -1):
        msp.add_line(b, (b[0] - ux - sx * uy * 0.5, b[1] - uy + sx * ux * 0.5), dxfattribs={"layer": "PORTE"})

text(ann["titolo"], ann["centro"], ann["base"] - 1900, 160)
if ann["note"]:
    text(ann["note"], ann["centro"], ann["base"] - 2200, 90)

doc.saveas(dst)
print("ok", dst, len(msp), "entita'")
