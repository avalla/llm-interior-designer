# Engine regression eval. Run INSIDE FreeCAD:
#   exec(open("/Users/andrea/dev/tmp/freecad/evals/run_engine.py").read(), {})
# For every fixture, runs verify() and checks that each expected "Category/Element" is NON-COMPLIANT (recall),
# then lists NON-COMPLIANT results that no defect expects (possible false positives). Writes evals/results/engine.md.
import fnmatch
import glob
import json
import os

# repository root: INTERIORS_ROOT (CI) or the author's checkout
ROOT = os.path.join(os.environ.get("INTERIORS_ROOT", "/Users/andrea/dev/tmp/freecad"), "evals")
lines = ["# Engine eval", "", "| Fixture | Defect | Expected | Detected |", "|---|---|---|---|"]
extra_lines = []
total = found = 0
for exp_path in sorted(glob.glob(os.path.join(ROOT, "fixtures", "*", "expected.json"))):
    case = os.path.basename(os.path.dirname(exp_path))
    exp = json.load(open(exp_path))
    proj = os.path.join(os.path.dirname(exp_path), "project.py")
    exec(open(proj).read(), {"__file__": proj, "__name__": "__main__", "PARAMS": {"report": False, "quiet": True}})
    import interiors as I
    nc = ["%s/%s" % (x["cat"], x["elem"]) for x in I.ST.results if x["status"] == I.NON_COMPLIANT
          and x["cat"] != "Requirements"]
    used = set()
    for d in exp["defects"]:
        for pat in d["engine"]:
            hit = [k for k in nc if fnmatch.fnmatch(k, pat)]
            used.update(hit)
            total += 1
            found += bool(hit)
            lines.append("| %s | %s %s | `%s` | %s |" % (case, d["id"], d["text"], pat, "yes" if hit else "**NO**"))
    for k in nc:
        if k not in used:
            extra_lines.append("| %s | `%s` |" % (case, k))
    import FreeCAD as App
    App.closeDocument(I.ST.doc.Name)

lines += ["", "**Recall: %d/%d**" % (found, total), "", "## Unexpected NON-COMPLIANT (check for false positives)", "",
          "| Fixture | Result |", "|---|---|"] + (extra_lines or ["| - | none |"])
os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
open(os.path.join(ROOT, "results", "engine.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
