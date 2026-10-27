#!/usr/bin/env bash
# Seconda meta' dell'export (la prima e' arredo.esporta() dentro FreeCAD).
# Uso: tools/esporta.sh <cartella progetto>   es. tools/esporta.sh progetti/appartamento-100mq
# Annota la pianta, crea il DXF 3D, converte in DWG 2018 e verifica il round-trip.
set -euo pipefail
TOOLS="$(cd "$(dirname "$0")" && pwd)"
P="$(cd "${1:?cartella progetto}" && pwd)"
ODA=/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter
B="$P/build"; O="$P/output"
for f in pianta_raw.dxf layers.json mesh3d.json annotazioni.json; do
  [[ -f "$B/$f" ]] || { echo "manca $B/$f: esegui prima arredo.esporta() in FreeCAD" >&2; exit 1; }
done
NAME="$(python3 -c "import glob,os;print(os.path.basename(glob.glob('$O/*.FCStd')[0])[:-6])")"

uv run --quiet --with ezdxf python "$TOOLS/annota_pianta.py" "$B" "$O/${NAME}_Pianta.dxf"
uv run --quiet --with ezdxf python "$TOOLS/esporta_3d_dwg.py" "$B/mesh3d.json" "$O/${NAME}_3D.dxf"

rm -rf "$B/oda" && mkdir -p "$B/oda/in" "$B/oda/out" "$B/oda/back"
cp "$O/${NAME}_Pianta.dxf" "$O/${NAME}_3D.dxf" "$B/oda/in/"
"$ODA" "$B/oda/in" "$B/oda/out" ACAD2018 DWG 0 1 "*.dxf" >/dev/null 2>&1
cp "$B/oda/out/"*.dwg "$O/"
"$ODA" "$B/oda/out" "$B/oda/back" ACAD2018 DXF 0 1 "*.dwg" >/dev/null 2>&1

uv run --quiet --with ezdxf python - "$B/oda/back" "$NAME" <<'EOF'
import sys, collections, ezdxf
back, name = sys.argv[1:3]
p = ezdxf.readfile(f"{back}/{name}_Pianta.dxf").modelspace()
t = collections.Counter(e.dxftype() for e in p)
d3 = collections.Counter(e.dxftype() for e in ezdxf.readfile(f"{back}/{name}_3D.dxf").modelspace())
print("DWG pianta:", dict(t), "layer:", sorted({e.dxf.layer for e in p}))
print("DWG 3D:", dict(d3))
assert t["DIMENSION"] > 0 and t["TEXT"] > 0 and t["LINE"] > 0, "pianta DWG incompleta"
assert d3["POLYLINE"] > 0, "3D DWG vuoto"
print("round-trip OK")
EOF
rm -f "$O/${NAME}_Pianta.png"
uv run --quiet --with ezdxf --with matplotlib python -m ezdxf draw -o "$O/${NAME}_Pianta.png" "$O/${NAME}_Pianta.dxf" >/dev/null 2>&1
echo "file in $O"
