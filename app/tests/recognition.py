# Scores plan recognition (app/importer/recognise.py) against the ground truth written by make_sample_dxf.py.
#   uv run --with ezdxf --with shapely python app/tests/recognition.py [app/build/samples/<name>.dxf] [--profile p.json]
# Matching: walls by area overlap (IoU); doors by hinge (3 cm), width (1 cm) and both leaf directions; sliding doors and
# furniture by footprint IoU >= 0.9; windows by both ends (2 cm); rooms by IoU >= 0.9 and name.
import json
import math
import os
import sys

from shapely.geometry import box, shape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from app.importer.recognise import read, recognise  # noqa: E402

prof = json.load(open(sys.argv[sys.argv.index("--profile") + 1])) if "--profile" in sys.argv else None
args = [a for a in sys.argv[1:] if a.endswith(".dxf")]
src = args[0] if args else os.path.join(HERE, "..", "build", "samples", "apartment-100sqm.dxf")
truth = json.load(open(src[:-4] + ".truth.json"))
r = recognise(read(src), prof)


def iou(a, b):
    u = a.union(b).area
    return a.intersection(b).area / u if u else 0.0


def score(label, gt, found, match):
    used, hits, misses = set(), 0, []
    for g in gt:
        k = next((i for i, f in enumerate(found) if i not in used and match(g, f)), None)
        if k is None:
            misses.append(g.get("name") or g.get("item"))
        else:
            used.add(k)
            hits += 1
    extra = len(found) - len(used)
    missed = ("  missed: " + ", ".join(map(str, misses))) if misses else ""
    print("%-10s recall %2d/%-2d  extra %d%s" % (label, hits, len(gt), extra, missed))
    return hits, len(gt), extra


walls_iou = iou(shape(truth["walls"]), r["walls"])
print("units      %s (factor %g)" % (r["units"]["note"], r["units"]["factor"]))
print("walls      IoU %.3f (truth %.2f m2, found %.2f m2)" % (walls_iou, shape(truth["walls"]).area, r["walls"].area))
tot = [score("doors", truth["doors"], r["doors"], lambda g, f: math.dist(g["hinge"], f["hinge"]) < 0.03
             and abs(g["w"] - f["w"]) < 0.01 and math.dist(g["d"], f["d"]) < 0.02 and math.dist(g["n"], f["n"]) < 0.02),
       score("slides", truth["slides"], r["slides"], lambda g, f: iou(box(*g["closed"]), box(*f["closed"])) >= 0.9),
       score("windows", truth["windows"], r["windows"], lambda g, f: abs(g["x0"] - f["x0"]) < 0.02
             and abs(g["x1"] - f["x1"]) < 0.02 and abs(g["yc"] - f["yc"]) < 0.10
             and (f["z0"] is None or abs(g["z0"] - f["z0"]) < 0.01)),
       score("rooms", truth["rooms"], r["rooms"], lambda g, f: iou(shape(g["footprint"]), f["footprint"]) >= 0.9
             and (f["name"] or "").upper() == g["name"].upper()),
       score("furniture", truth["furniture"], r["furniture"], lambda g, f: iou(shape(g["footprint"]), f["footprint"]) >= 0.9)]
for rm in r["rooms"]:
    g = max(truth["rooms"], key=lambda t: iou(shape(t["footprint"]), rm["footprint"]))
    print("   room %-16s %.2f m2, best truth %s IoU %.3f" % (rm["name"], rm["area"], g["name"],
                                                            iou(shape(g["footprint"]), rm["footprint"])))
hit, n = sum(t[0] for t in tot), sum(t[1] for t in tot)
print("elements recognised %d/%d (%.0f%%), walls IoU %.3f, unrecognised notes %d" % (hit, n, 100.0 * hit / n, walls_iou,
                                                                                       len(r["unrecognised"])))
sys.exit(0 if hit == n and walls_iou > 0.99 else 1)
