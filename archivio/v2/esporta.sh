#!/usr/bin/env bash
# Seconda meta' dell'export (la prima e' esporta_freecad.py dentro FreeCAD):
# annota la pianta, crea il DXF 3D, converte entrambi in DWG 2018 e verifica il round-trip.
set -euo pipefail
cd "$(dirname "$0")"
ODA=/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter
B=build
for f in "$B/pianta_raw.dxf" "$B/layers.json" "$B/mesh3d.json"; do
  [[ -f "$f" ]] || { echo "manca $f: esegui prima esporta_freecad.py in FreeCAD" >&2; exit 1; }
done

uv run --quiet --with ezdxf python annota_pianta.py "$B/pianta_raw.dxf" "$B/layers.json" Appartamento_Pianta.dxf
uv run --quiet --with ezdxf python esporta_3d_dwg.py "$B/mesh3d.json" Appartamento_3D.dxf

rm -rf "$B/oda" && mkdir -p "$B/oda/in" "$B/oda/out" "$B/oda/back"
cp Appartamento_Pianta.dxf Appartamento_3D.dxf "$B/oda/in/"
"$ODA" "$B/oda/in" "$B/oda/out" ACAD2018 DWG 0 1 "*.dxf" >/dev/null 2>&1
cp "$B/oda/out/"*.dwg .
"$ODA" "$B/oda/out" "$B/oda/back" ACAD2018 DXF 0 1 "*.dwg" >/dev/null 2>&1

# round-trip: il DWG riletto deve contenere entita', quote e layer attesi
uv run --quiet --with ezdxf python - "$B/oda/back" <<'EOF'
import sys, collections, ezdxf
back = sys.argv[1]
p = ezdxf.readfile(f"{back}/Appartamento_Pianta.dxf").modelspace()
t = collections.Counter(e.dxftype() for e in p)
d3 = collections.Counter(e.dxftype() for e in ezdxf.readfile(f"{back}/Appartamento_3D.dxf").modelspace())
print("DWG pianta:", dict(t), "layer:", sorted({e.dxf.layer for e in p}))
print("DWG 3D:", dict(d3))
assert t["DIMENSION"] > 0 and t["TEXT"] > 0 and t["LINE"] > 0, "pianta DWG incompleta"
assert d3["POLYLINE"] > 0, "3D DWG vuoto"
print("round-trip OK")
EOF
rm -f Appartamento_Pianta.png
uv run --quiet --with ezdxf --with matplotlib python -m ezdxf draw -o Appartamento_Pianta.png Appartamento_Pianta.dxf >/dev/null 2>&1
echo "anteprima: Appartamento_Pianta.png"
