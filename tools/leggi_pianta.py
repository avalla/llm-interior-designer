# Legge una pianta di partenza (DWG o DXF) e ne stampa un riepilogo per il rilievo nel modello:
# unita', estensione, layer, quote (valori misurati), testi, segmenti lunghi (candidati muri).
# Uso: uv run --with ezdxf python tools/leggi_pianta.py <file.dwg|file.dxf> [--min-muro 0.8]
import collections
import os
import shutil
import subprocess
import sys
import tempfile

import ezdxf

ODA = "/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter"
src = sys.argv[1]
min_len = float(sys.argv[sys.argv.index("--min-muro") + 1]) if "--min-muro" in sys.argv else 0.8

if src.lower().endswith(".dwg"):
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, "in"))
    shutil.copy(src, os.path.join(tmp, "in"))
    subprocess.run([ODA, os.path.join(tmp, "in"), os.path.join(tmp, "out"), "ACAD2018", "DXF", "0", "1", "*.dwg"],
                   check=True, capture_output=True)
    src = os.path.join(tmp, "out", os.path.basename(src)[:-4] + ".dxf")

doc = ezdxf.readfile(src)
msp = doc.modelspace()
UNITS = {0: "non specificata", 1: "pollici", 2: "piedi", 4: "mm", 5: "cm", 6: "m"}
u = doc.header.get("$INSUNITS", 0)
to_m = {4: 0.001, 5: 0.01, 6: 1.0}.get(u)
print("Unita' dichiarata:", UNITS.get(u, u), "" if to_m else "-> VERIFICARE la scala con una quota nota prima di usare le misure")
to_m = to_m or 1.0

types = collections.Counter(e.dxftype() for e in msp)
print("Entita':", dict(types))
print("Layer:", ", ".join(sorted({e.dxf.layer for e in msp})))
pts = [(e.dxf.start.x, e.dxf.start.y) for e in msp.query("LINE")] + [(e.dxf.end.x, e.dxf.end.y) for e in msp.query("LINE")]
for pl in msp.query("LWPOLYLINE"):
    pts += [(p[0], p[1]) for p in pl.get_points("xy")]
if pts:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    print("Estensione: %.2f x %.2f m (origine %.2f, %.2f)" % ((max(xs) - min(xs)) * to_m, (max(ys) - min(ys)) * to_m,
                                                          min(xs) * to_m, min(ys) * to_m))

print("\nQuote presenti (valore misurato dal disegno):")
for d in msp.query("DIMENSION"):
    try:
        print("  %-12s %.3f m  testo='%s'  layer=%s" % (d.dimtype, d.get_measurement() * to_m, d.dxf.text, d.dxf.layer))
    except Exception as exc:  # noqa: BLE001 - quote anomale: segnalarle e proseguire
        print("  quota non leggibile:", exc)

print("\nTesti:")
for t in list(msp.query("TEXT")) + list(msp.query("MTEXT")):
    s = t.dxf.text if t.dxftype() == "TEXT" else t.text
    p = t.dxf.insert
    print("  (%.2f, %.2f) %s" % (p.x * to_m, p.y * to_m, s.replace("\n", " ")[:80]))

print("\nSegmenti >= %.1f m (candidati muri; ortogonali marcati):" % min_len)
segs = []
for e in msp.query("LINE"):
    a, b = e.dxf.start, e.dxf.end
    L = ((b.x - a.x) ** 2 + (b.y - a.y) ** 2) ** 0.5 * to_m
    if L >= min_len:
        orto = abs(a.x - b.x) < 1e-6 or abs(a.y - b.y) < 1e-6
        segs.append((L, a, b, orto, e.dxf.layer))
for L, a, b, orto, lay in sorted(segs, key=lambda s: -s[0])[:60]:
    print("  %6.2f m  (%.2f,%.2f)->(%.2f,%.2f) %s layer=%s" % (L, a.x * to_m, a.y * to_m, b.x * to_m, b.y * to_m,
                                                             "" if orto else "FUORI SQUADRA", lay))
