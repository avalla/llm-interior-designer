# Da eseguire DENTRO FreeCAD (via MCP execute_code: exec(open(".../esporta_freecad.py").read()))
# dopo appartamento.py. Scrive lo STEP e i dati intermedi in build/ per esporta.sh.
import FreeCAD as App, Part, Import, importDXF, json, os

PROJECT = "/Users/andrea/dev/tmp/freecad"
BUILD = os.path.join(PROJECT, "build")
os.makedirs(BUILD, exist_ok=True)
doc = App.getDocument("Appartamento")
doc.saveAs(os.path.join(PROJECT, "Appartamento.FCStd"))

# solidi reali (escluse le aree di verifica aperture)
solids = [o for o in doc.Objects if o.TypeId == "Part::Feature" and "Area" not in o.Name]
Import.export(solids, os.path.join(PROJECT, "Appartamento_3D.step"))

# --- pianta: muri/serramenti sezionati a 1 m, arredi tagliati a meta' di ogni solido ---
LAYER = {"Strutture": "MURI", "Serramenti": "SERRAMENTI", "Porte": "PORTE", "Verifica_Porte": "APERTURE"}


def plan_section(o, g):
    parts = [o.Shape] if g in ("Strutture", "Serramenti") or "Area" in o.Name else (o.Shape.Solids or [o.Shape])
    edges = []
    for s in parts:
        bb = s.BoundBox
        zc = 1000.0 if (g in ("Strutture", "Serramenti") and bb.ZMin < 1000.0 < bb.ZMax) else (bb.ZMin + bb.ZMax) / 2
        for w in s.slice(App.Vector(0, 0, 1), zc):
            w = w.copy(); w.translate(App.Vector(0, 0, -zc)); edges.append(w)
    return Part.makeCompound(edges)


plan = App.newDocument("Pianta_DXF")
mapping = {}
for o in doc.Objects:
    if o.TypeId != "Part::Feature" or o.Name.startswith(("Solaio", "Pavimento")) or "Binario" in o.Name:
        continue
    g = o.getParentGroup().Label if o.getParentGroup() else "Altro"
    sec = plan_section(o, g)
    if not sec.Edges:
        continue
    f = plan.addObject("Part::Feature", o.Name)
    f.Shape = sec
    mapping[f.Label] = LAYER.get(g, "ARREDI")
plan.recompute()
importDXF.export(plan.Objects, os.path.join(BUILD, "pianta_raw.dxf"))
App.closeDocument("Pianta_DXF")
App.setActiveDocument("Appartamento")
json.dump(mapping, open(os.path.join(BUILD, "layers.json"), "w"))

# --- 3D: mesh colorate per il DWG 3D ---
data = []
for o in solids:
    pts, tris = o.Shape.tessellate(5.0)
    g = o.getParentGroup().Label if o.getParentGroup() else "Altro"
    data.append({"name": o.Label, "group": g, "color": list(o.ViewObject.ShapeColor[:3]),
                 "tr": o.ViewObject.Transparency,
                 "v": [[round(p.x, 1), round(p.y, 1), round(p.z, 1)] for p in pts], "f": tris})
json.dump(data, open(os.path.join(BUILD, "mesh3d.json"), "w"))
print("export FreeCAD ok:", len(mapping), "oggetti pianta,", len(data), "oggetti 3D -> ora lancia ./esporta.sh")
