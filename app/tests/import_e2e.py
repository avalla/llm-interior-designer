# End to end from a plan drawing: model -> studio-style DXF (two drawing styles) -> recognition -> neutral model -> checks.
#   uv run --with ezdxf --with shapely python app/tests/import_e2e.py     (needs app/build/models from export_model.py)
# Asserts: every element recognised; each expected NON-COMPLIANT row (cat/elem pattern) is found and every
# NON-COMPLIANT row is expected. The clean apartment must stay at zero (counter-test, lesson L04).
# Planted fixture: A1-A4 and A6-A9 are found from the plan with the furniture semantics library; A5 (window leaf vs
# tap) needs window leaves on the plan. Judgement fixture: B5 (bed visible from the entrance) is found because the
# library declares no_view for beds and WCs, which the FreeCAD project does not; the bed's west side is unreachable
# with the bedroom door open at 90 degrees (the engine's route rule: the open leaf is an obstacle).
import fnmatch
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "app", "core"))
from app.importer.recognise import read, recognise  # noqa: E402
from app.importer.to_model import build  # noqa: E402
from app.semantics.library import _compass  # noqa: E402
from interiors_core.checks import Model  # noqa: E402
from interiors_core.rules import RULES  # noqa: E402
MODELS = os.path.join(ROOT, "app", "build", "models")
SAMPLES = os.path.join(ROOT, "app", "build", "samples")
EXPECTED = {
    "apartment-100sqm": [],
    "apartment-100sqm-lines": [],
    "a-planted-checks": [
        "Openings/Door_*",                                   # A1 entrance door vs shoe cabinet
        "Seats/Chair_1",                                     # A2 53 cm behind the chair
        "Brief constraints/TV *",                            # A3 TV next to the window
        "Routes/LIVING: Sofa (in front)",                    # A4 sofa front unreachable
        "Robustness/Clearances/LIVING: Island / Worktop",    # A6 aisle at exactly 90 cm
        "Privacy/BATHROOM: *",                               # A7 bathroom only through the bedroom
        "Access zones/BEDROOM: in front of Wardrobe",        # A8 bed in front of the wardrobe
        "Routes/BEDROOM: Wardrobe",                          # A8 seen as a destination
        "Handles/Door_*", "Reveals/Door_*",                  # A9 bedroom door against the wall
    ],
    "b-judgement": [
        "Privacy/Entrance: Bed not visible",                 # B5
        "Routes/BEDROOM: Bed west side",                     # open bedroom door across the bed side
    ],
}
# Third studio (--style codes): layers and blocks named by codes, cm undeclared, fronts only in the block rotation. Its
# profile is what the architect sets once on the first drawing; the other drawings of the studio must need <= 5 more
# fixes (phase 2 exit criterion) and give the same verdicts as the readable styles (codes mapped back to item names).
PROFILE = os.path.join(HERE, "profiles", "studio-codes.json")
for base in ("apartment-100sqm", "a-planted-checks", "b-judgement"):
    EXPECTED[base + "-codes"] = EXPECTED[base]
FIRST = "apartment-100sqm-codes"


def sample(name):
    base, style = next(((name[:-len(s) - 1], s) for s in ("lines", "codes") if name.endswith("-" + s)), (name, "blocks"))
    subprocess.run([sys.executable, os.path.join(HERE, "make_sample_dxf.py"), os.path.join(MODELS, base + ".json"),
                    "--style", style], check=True, capture_output=True)
    return os.path.join(SAMPLES, name + ".dxf"), style


def sides(model):
    return {x["item"]: x["side"] for x in model["fronts"]}


fail = []
profile = json.load(open(PROFILE))
for name, patterns in EXPECTED.items():
    dxf, style = sample(name)
    prof = profile if style == "codes" else None
    rec = subprocess.run([sys.executable, os.path.join(HERE, "recognition.py"), dxf]
                         + (["--profile", PROFILE] if prof else []), capture_output=True, text=True)
    res = recognise(read(dxf), prof)
    model = build(res, RULES, name, prof)
    rows = Model(model).verify()
    failed = ["%s/%s" % (x["cat"], x["elem"]) for x in rows if x["status"] == "NON-COMPLIANT" and x["cat"] != "Requirements"]
    note = ""
    if style == "codes":
        truth = json.load(open(dxf[:-4] + ".truth.json"))["furniture"]
        code = {t["block"]: t["item"] for t in truth}
        rx = re.compile(r"\b(%s)\b" % "|".join(sorted(code, key=len, reverse=True)))
        failed = [rx.sub(lambda g: code[g.group(1)], f) for f in failed]
        # fronts: read from the block rotation they must all be true; inferred from the plan alone they are measured
        true = {t["block"]: _compass(t["front"]) for t in truth}
        got = sides(model)
        guess = sides(build(recognise(read(dxf), dict(prof, front=None)), RULES, name, dict(prof, front=None)))
        wrong = [b for b, s in got.items() if true[b] != s]
        right = sum(1 for b, s in guess.items() if true[b] == s)
        fixes = [f["block"] for f in res["furniture"] if f["type"] == "unknown"] + (["walls"] if res["walls"].is_empty else [])
        note = " | fronts from rotation %d/%d, inferred %d/%d | fixes beyond the profile: %d" % (
            len(got) - len(wrong), len(got), right, len(guess), len(fixes))
        if wrong or (name != FIRST and len(fixes) > 5):
            fail.append(name + " (fronts %s, fixes %s)" % (wrong, fixes))
    missed = [p for p in patterns if not any(fnmatch.fnmatchcase(f, p) for f in failed)]
    extra = [f for f in failed if not any(fnmatch.fnmatchcase(f, p) for p in patterns)]
    ok = rec.returncode == 0 and not missed and not extra
    print("%-24s %s | NON-COMPLIANT %d, expected found %d/%d%s%s%s" % (
        name, rec.stdout.strip().splitlines()[-1].split(",")[0], len(failed), len(patterns) - len(missed), len(patterns),
        note, "  <-- missed %s" % missed if missed else "", "  <-- unexpected %s" % extra if extra else ""))
    if not ok:
        fail.append(name)
print("import end to end:", "OK" if not fail else "FAILED " + ", ".join(fail))
sys.exit(1 if fail else 0)
