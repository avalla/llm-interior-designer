# Aggiunge layer, quote e nomi locali alla pianta esportata da FreeCAD (mm).
# Uso: uv run --with ezdxf python annota_pianta.py pianta_raw.dxf layers.json Appartamento_Pianta.dxf
import json, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment

src, layers_json, dst = sys.argv[1:4]
doc = ezdxf.readfile(src)
msp = doc.modelspace()

COLORS = {"MURI": 7, "SERRAMENTI": 4, "PORTE": 30, "APERTURE": 3, "ARREDI": 8, "QUOTE": 1, "TESTI": 7}
for name, aci in COLORS.items():
    if name not in doc.layers:
        doc.layers.add(name, color=aci)

mapping = json.load(open(layers_json))
for e in msp:
    e.dxf.layer = mapping.get(e.dxf.layer, "ARREDI")
for lay in [l.dxf.name for l in doc.layers]:
    if lay not in COLORS and lay not in ("0", "Defpoints"):
        doc.layers.remove(lay)

doc.header["$INSUNITS"] = 4  # mm
DIM = {"dimtxt": 110, "dimtsz": 50, "dimexe": 60, "dimexo": 80, "dimgap": 30,
       "dimdec": 0, "dimclrd": 1, "dimclre": 1, "dimclrt": 7, "dimtad": 1}


def chain(points, horizontal, base):
    for a, b in zip(points, points[1:]):
        # i punti di estensione partono dal filo del muro piu' vicino alla linea di quota
        if horizontal:
            y0 = 8000 if base > 4000 else 0
            p1, p2, loc, ang = (a, y0), (b, y0), (0, base), 0
        else:
            x0 = 12500 if base > 6000 else 0
            p1, p2, loc, ang = (x0, a), (x0, b), (base, 0), 90
        msp.add_linear_dim(base=loc, p1=p1, p2=p2, angle=ang, override=DIM,
                           dxfattribs={"layer": "QUOTE"}).render()


chain([0, 1000, 5500, 8200, 10600, 12500], True, -500)            # sud: vetrate
chain([0, 300, 6450, 6550, 12200, 12500], True, -900)             # sud: locali
chain([0, 12500], True, -1300)                                     # sud: totale
chain([0, 300, 1400, 3200, 7000, 7900, 8050, 10250, 10350, 12200, 12500], True, 8600)  # nord
chain([0, 300, 7700, 8000], False, -600)                           # ovest
chain([0, 8000], False, -1000)                                     # ovest: totale
chain([0, 300, 3550, 3650, 4750, 4850, 7700, 8000], False, 13100)  # est


def text(s, x, y, h, layer="TESTI"):
    msp.add_text(s, height=h, dxfattribs={"layer": layer}).set_placement(
        (x, y), align=TextEntityAlignment.MIDDLE_CENTER)


for lines, x, y in [
    (["SOGGIORNO - CUCINA", "45,5 m²"], 2900, 4450),
    (["CAMERA", "18,4 m²"], 8700, 2600),
    (["BAGNO", "6,3 m²"], 9300, 6250),
    (["CABINA", "ARMADIO", "5,3 m²"], 10770, 6250),
    (["DISIMPEGNO", "10,3 m²"], 9600, 4250),
]:
    for i, s in enumerate(lines):
        text(s, x, y - i * 190, 150 if i == 0 and len(lines) == 2 else 100)

for s, x, y in [
    ("P 90x215 blindata", 7450, 8250), ("P 90x210", 6000, 5100), ("P 80x210", 7000, 2550),
    ("P 80x210", 8500, 4560), ("P 70x210", 10750, 4560),
    ("F 180x100 davanzale h120 - 2 ante", 2300, 8250), ("F 60x60 h160", 9850, 8250),
    ("PF 450x240 scorrevole", 3250, -250), ("PF 240x240 scorrevole", 9400, -250),
]:
    text(s, x, y, 70)

text("APPARTAMENTO - PIANTA   Sup. lorda 100,0 m²  -  Sup. netta 85,8 m²   "
     "Quote in mm - stampa consigliata 1:50", 6250, -1900, 160)

doc.saveas(dst)
print("ok", dst, len(msp), "entita'")
