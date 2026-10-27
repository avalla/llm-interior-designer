#!/usr/bin/env bash
# Second half of the export (the first is interiors.export() inside FreeCAD).
# Usage: tools/export.sh <project folder>   e.g. tools/export.sh projects/apartment-100sqm
# Annotates the plan, builds the 3D DXF, converts both to DWG 2018 and checks the round trip.
set -euo pipefail
TOOLS="$(cd "$(dirname "$0")" && pwd)"
P="$(cd "${1:?project folder}" && pwd)"
ODA=/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter
B="$P/build"; O="$P/output"
for f in plan_raw.dxf layers.json mesh3d.json annotations.json; do
  [[ -f "$B/$f" ]] || { echo "missing $B/$f: run interiors.export() in FreeCAD first" >&2; exit 1; }
done
NAME="$(python3 -c "import glob,os;print(os.path.basename(glob.glob('$O/*.FCStd')[0])[:-6])")"

uv run --quiet --with ezdxf python "$TOOLS/annotate_plan.py" "$B" "$O/${NAME}_Plan.dxf"
uv run --quiet --with ezdxf python "$TOOLS/export_3d_dwg.py" "$B/mesh3d.json" "$O/${NAME}_3D.dxf"

rm -rf "$B/oda" && mkdir -p "$B/oda/in" "$B/oda/out" "$B/oda/back"
cp "$O/${NAME}_Plan.dxf" "$O/${NAME}_3D.dxf" "$B/oda/in/"
"$ODA" "$B/oda/in" "$B/oda/out" ACAD2018 DWG 0 1 "*.dxf" >/dev/null 2>&1
cp "$B/oda/out/"*.dwg "$O/"
"$ODA" "$B/oda/out" "$B/oda/back" ACAD2018 DXF 0 1 "*.dwg" >/dev/null 2>&1

uv run --quiet --with ezdxf python - "$B/oda/back" "$NAME" <<'EOF'
import sys, collections, ezdxf
back, name = sys.argv[1:3]
p = ezdxf.readfile(f"{back}/{name}_Plan.dxf").modelspace()
t = collections.Counter(e.dxftype() for e in p)
d3 = collections.Counter(e.dxftype() for e in ezdxf.readfile(f"{back}/{name}_3D.dxf").modelspace())
print("Plan DWG:", dict(t), "layers:", sorted({e.dxf.layer for e in p}))
print("3D DWG:", dict(d3))
assert t["DIMENSION"] > 0 and t["TEXT"] > 0 and t["LINE"] > 0, "incomplete plan DWG"
assert d3["POLYLINE"] > 0, "empty 3D DWG"
print("round-trip OK")
EOF
rm -f "$O/${NAME}_Plan.png"
uv run --quiet --with ezdxf --with matplotlib python -m ezdxf draw -o "$O/${NAME}_Plan.png" "$O/${NAME}_Plan.dxf" >/dev/null 2>&1
echo "files in $O"
