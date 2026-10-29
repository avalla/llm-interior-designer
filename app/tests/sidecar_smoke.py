# The desktop app's sidecar over its real transport (JSON lines on stdio), on the sample drawings of import_e2e.py.
#   uv run --with ezdxf --with shapely python app/tests/sidecar_smoke.py      (after import_e2e.py wrote the samples)
# Asserts: answers keep the request id; errors come back as errors, not as a dead process; every NON-COMPLIANT and
# NOT VERIFIABLE result that concerns a place has one on the plan (clicking it in the UI must show something);
# a plan that cannot be checked yet still comes back with its mapping and something to draw.
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SAMPLES = os.path.join(ROOT, "app", "build", "samples")
PROFILE = json.load(open(os.path.join(HERE, "profiles", "studio-codes.json")))
NO_PLACE = ("Requirements", "Not verifiable", "Ergonomics")     # results about the whole plan, not a place

# INTERIORS_SIDECAR=/path/to/interiors-sidecar tests a packaged sidecar (PyInstaller), run outside the repository
CMD = os.environ.get("INTERIORS_SIDECAR", "").split() or [sys.executable, "-m", "app.sidecar.server"]
p = subprocess.Popen(CMD, cwd=ROOT if CMD[0] == sys.executable else os.path.expanduser("~"), stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)   # tracebacks of expected errors


def ask(i, method, params=None):
    p.stdin.write(json.dumps(dict(id=i, method=method, params=params or {})) + "\n")
    p.stdin.flush()
    answer = json.loads(p.stdout.readline())
    assert answer["id"] == i, answer
    return answer


fail = []
assert ask(1, "ping")["result"]["version"]
if "error" not in ask(2, "no_such_method"):
    fail.append("unknown method did not return an error")
if "error" not in ask(3, "analyse", dict(path=os.path.join(SAMPLES, "missing.dxf"))):
    fail.append("missing file did not return an error")
if not os.path.isfile(os.path.join(SAMPLES, "b-judgement-codes.dxf")):
    # no FreeCAD models here (the Windows packaging job): one room drawn on the spot, checked end to end
    import ezdxf
    os.makedirs(SAMPLES, exist_ok=True)
    doc = ezdxf.new("R2018")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    for ring in ([(0, 0), (5000, 0), (5000, 4000), (0, 4000)], [(300, 300), (4700, 300), (4700, 3700), (300, 3700)]):
        msp.add_lwpolyline(ring, close=True, dxfattribs={"layer": "MURI"})
    blk = doc.blocks.new("ARR_Sofa")
    blk.add_lwpolyline([(0, 0), (2000, 0), (2000, 900), (0, 900)], close=True)
    msp.add_blockref("ARR_Sofa", (1500, 400), dxfattribs={"layer": "ARREDI"})
    msp.add_text("SOGGIORNO", height=150, dxfattribs={"layer": "TESTI"}).set_placement((2500, 2500))
    doc.saveas(os.path.join(SAMPLES, "minimal.dxf"))
    r = ask(10, "analyse", dict(path=os.path.join(SAMPLES, "minimal.dxf")))["result"]
    d = r["diagnosis"]["found"]
    ok = r["checkable"] and d["rooms"] == 1 and d["furniture"] == 1 and r["results"] and r["scene"]["drawing"]
    print("minimal plan: checkable %s, found %s, results %d" % (r["checkable"], d, len(r["results"])))
    p.stdin.close()
    p.wait(timeout=10)
    print("sidecar smoke:", "OK" if ok and not fail else "FAILED %s" % fail)
    sys.exit(0 if ok and not fail else 1)
cases = [("apartment-100sqm", None), ("a-planted-checks", None), ("b-judgement-codes", PROFILE)]
for i, (name, prof) in enumerate(cases, start=10):
    r = ask(i, "analyse", dict(path=os.path.join(SAMPLES, name + ".dxf"), profile=prof))["result"]
    lost = ["%s/%s" % (x["cat"], x["elem"]) for x in r["results"] if x["status"] in ("NON-COMPLIANT", "NOT VERIFIABLE")
            and x["cat"] not in NO_PLACE and not x["where"]["bounds"]]
    print("%-22s results %3d, %s, without a place: %s" % (name, len(r["results"]), r["summary"], lost or "none"))
    fail += lost
raw = ask(20, "analyse", dict(path=os.path.join(SAMPLES, "b-judgement-codes.dxf")))["result"]
if raw["checkable"] or not raw["mapping"]["confirm"] or not raw["scene"]["furniture"] or not raw["scene"]["bounds"]:
    fail.append("unmapped drawing: expected not checkable, with mapping and furniture to draw")
print("unmapped b-judgement-codes: checkable %s, to confirm %d, furniture drawn %d" % (
    raw["checkable"], len(raw["mapping"]["confirm"]), len(raw["scene"]["furniture"])))
p.stdin.close()
p.wait(timeout=10)
print("sidecar smoke:", "OK" if not fail else "FAILED %s" % fail)
sys.exit(1 if fail else 0)
