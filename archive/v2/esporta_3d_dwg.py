# Crea un DXF 3D (mesh polyface colorate, un layer per gruppo) leggibile da qualsiasi AutoCAD,
# anche Mac e LT, che non importano STEP.
# Uso: uv run --with ezdxf python esporta_3d_dwg.py mesh3d.json Appartamento_3D.dxf
import json, sys
import ezdxf
from ezdxf import colors
from ezdxf.render import MeshBuilder

src, dst = sys.argv[1:3]
doc = ezdxf.new("R2018", units=4)  # mm
msp = doc.modelspace()

for obj in json.load(open(src)):
    layer = obj["group"].upper()
    if layer not in doc.layers:
        doc.layers.add(layer)
    mb = MeshBuilder()
    mb.add_mesh(vertices=[tuple(v) for v in obj["v"]], faces=[tuple(f) for f in obj["f"]])
    rgb = tuple(int(round(c * 255)) for c in obj["color"])
    attribs = {"layer": layer, "true_color": colors.rgb2int(rgb)}
    pf = mb.render_polyface(msp, dxfattribs=attribs)
    if obj["tr"]:
        pf.transparency = obj["tr"] / 100.0

doc.saveas(dst)
print("ok", dst, len(msp), "mesh,", len(doc.layers), "layer")
