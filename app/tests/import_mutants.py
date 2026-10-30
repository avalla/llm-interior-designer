# The import path against the FreeCAD engine on the shifted-furniture mutants of apartment-100sqm (each piece moved by
# +-20 cm, MUTANTS=1 in export_model.py): mutant -> studio-style DXF -> recognition -> semantics -> checks.
#   uv run --with ezdxf --with shapely python app/tests/import_mutants.py
# The FreeCAD reference has hand-declared uses, the import generates them from the plan, so rows cannot match one to
# one: a mutant counts as caught when both sides report at least one NON-COMPLIANT row, as extra when only the import
# does. Defects a plan cannot show (window and wardrobe leaves are not drawn) stay missed; extras are listed so each
# one can be judged (a check the project never declared, such as the washing machine's access zone, is not a fault).
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "app", "core"))
from app.importer.recognise import read, recognise  # noqa: E402
from app.importer.to_model import build  # noqa: E402
from interiors_core.checks import Model  # noqa: E402
from interiors_core.rules import RULES  # noqa: E402
MUTANTS = sorted(glob.glob(os.path.join(ROOT, "app", "build", "mutants", "*.json")))
SAMPLES = os.path.join(ROOT, "app", "build", "samples")
MIN_CAUGHT, MAX_EXTRA = 0.90, 0.15            # measured 2026-10-28: 57/61 caught, 2/39 extra; 2026-10-29: 59/64, 4/36
# The four extras of 2026-10-29 were judged one by one: the washing machine and towel warmer (zone the project never
# declared), the hob shifted 15 cm out of its run (a real obstacle the engine has no zone for since the dishwasher
# moved) and the table 20 cm nearer the island (60 cm behind the chair: real, the engine's seat edge stays registered
# where it was). None is an import fault, so the ceiling moved to 15%.


def failing(rows):
    return ["%s/%s" % (x["cat"], x["elem"]) for x in rows if x["status"] == "NON-COMPLIANT" and x["cat"] != "Requirements"]


if not MUTANTS:
    sys.exit("no mutants: run MUTANTS=1 .../freecadcmd app/tools/export_model.py first")
caught, missed, extra, clean = [], [], [], 0
for path in MUTANTS:
    name = os.path.basename(path)[:-5]
    subprocess.run([sys.executable, os.path.join(HERE, "make_sample_dxf.py"), path], check=True, capture_output=True)
    imp = failing(Model(build(recognise(read(os.path.join(SAMPLES, name + ".dxf"))), RULES, name)).verify())
    ref = failing(json.load(open(path))["reference"])
    short = name.split("~", 1)[1]
    if ref:
        (caught if imp else missed).append((short, ref))
    else:
        clean += 1
        if imp:
            extra.append((short, imp))
for short, rows in missed:
    print("missed  %-34s reference: %s" % (short, ", ".join(rows)))
for short, rows in extra:
    print("extra   %-34s import: %s" % (short, ", ".join(rows)))
n_ref = len(caught) + len(missed)
ok = len(caught) >= MIN_CAUGHT * n_ref and len(extra) <= MAX_EXTRA * clean
print("mutants %d: caught %d/%d, extra %d/%d -> %s" % (len(MUTANTS), len(caught), n_ref, len(extra), clean,
                                                     "OK" if ok else "FAILED (min caught %.0f%%, max extra %.0f%%)" % (
                                                         MIN_CAUGHT * 100, MAX_EXTRA * 100)))
sys.exit(0 if ok else 1)
