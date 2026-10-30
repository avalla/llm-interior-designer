# Parity between app/core and lib/interiors.py on the exported models (app/tools/export_model.py).
#   uv run --with shapely python app/tests/parity.py [model.json ...]     (default: app/build/models and mutants)
# Same rows in the same order, same status and severity, same measure text; numbers may differ by one unit of the
# last printed digit (float rounding), collision volumes "(N cm3)" by up to 5 cm3 or 0.1% (arcs are discretised).
import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "core"))
from interiors_core.checks import Model  # noqa: E402
from interiors_core.rules import RULES  # noqa: E402

NUM = re.compile(r"-?\d+(?:\.\d+)?")
VOL = re.compile(r" \((\d+) cm3\)")


def same_measure(a, b):
    if a == b:
        return True
    va, vb = [int(v) for v in VOL.findall(a)], [int(v) for v in VOL.findall(b)]
    if len(va) != len(vb) or any(abs(x - y) > max(5, x / 1000) for x, y in zip(va, vb)):
        return False
    a, b = VOL.sub("", a), VOL.sub("", b)
    if NUM.sub("#", a) != NUM.sub("#", b):
        return False
    for x, y in zip(NUM.findall(a), NUM.findall(b)):
        unit = 10 ** -len(x.split(".")[1]) if "." in x else 1
        if abs(float(x) - float(y)) > unit + 1e-9:
            return False
    return True


paths = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "..", "build", "models", "*.json"))) + \
    sorted(glob.glob(os.path.join(HERE, "..", "build", "mutants", "*.json")))
if not paths:
    sys.exit("no models: run app/tools/export_model.py in FreeCAD first")
ERR = os.path.join(HERE, "..", "build", "export_errors.txt")
if os.path.exists(ERR):
    sys.exit("export failed:\n" + open(ERR).read())

failed_models, rows, nc_rows, total_ms = [], 0, 0, 0.0
for p in paths:
    m = Model.load(p)
    if json.loads(json.dumps(RULES)) != m.R:        # tuples become lists on the JSON round trip, as in the model
        sys.exit("interiors_core/rules.py differs from lib/interiors.py RULES (model %s): align them" % m.name)
    t = time.perf_counter()
    new = m.verify()
    total_ms += (time.perf_counter() - t) * 1000
    ref = m.data["reference"]
    diffs = []
    ka, kb = [(x["cat"], x["elem"]) for x in ref], [(x["cat"], x["elem"]) for x in new]
    if ka != kb:
        diffs += ["row only in reference: %s/%s" % k for k in ka if k not in kb]
        diffs += ["row only in core: %s/%s" % k for k in kb if k not in ka]
        if not diffs:
            diffs.append("same rows, different order")
    else:
        for a, b in zip(ref, new):
            if (a["status"], a["sev"]) != (b["status"], b["sev"]) or not same_measure(a["measure"], b["measure"]):
                diffs.append("%s/%s: %s %s '%s' -> %s %s '%s'" % (a["cat"], a["elem"], a["status"], a["sev"], a["measure"],
                                                                 b["status"], b["sev"], b["measure"]))
    rows += len(ref)
    nc_rows += sum(1 for x in ref if x["status"] == "NON-COMPLIANT")
    if diffs:
        failed_models.append(os.path.basename(p))
        print("%s: %d differences" % (os.path.basename(p), len(diffs)))
        for d in diffs[:8]:
            print("   ", d)
print("models %d, rows %d (NON-COMPLIANT in the reference %d), core %.0f ms in total: %s" % (
    len(paths), rows, nc_rows, total_ms, "PARITY" if not failed_models else "%d models differ" % len(failed_models)))
sys.exit(1 if failed_models else 0)
