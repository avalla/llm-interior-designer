# Engine regression for CI, run with headless FreeCAD:
#   INTERIORS_ROOT=$PWD freecadcmd ci/engine_ci.py
# 1) evals/run_engine.py: every planted defect detected, no unexpected NON-COMPLIANT result
# 2) every project in projects/ (except _template) verifies with 0 problems
# freecadcmd does not reliably propagate exit codes, so the outcome is written to ci/engine_result.json and
# asserted by a separate step (ci/assert_engine.py).
import glob
import json
import os
import re
import traceback

ROOT = os.environ.get("INTERIORS_ROOT", os.getcwd())
out = {"ok": False, "engine": None, "projects": {}, "error": None}
try:
    import FreeCAD as App

    exec(open(os.path.join(ROOT, "evals", "run_engine.py")).read(), {"__name__": "__main__"})
    md = open(os.path.join(ROOT, "evals", "results", "engine.md")).read()
    m = re.search(r"\*\*Recall: (\d+)/(\d+)\*\*", md)
    unexpected = md.split("## Unexpected NON-COMPLIANT")[1]
    out["engine"] = {"found": int(m.group(1)), "total": int(m.group(2)),
                     "unexpected": [ln for ln in unexpected.splitlines() if ln.startswith("| ") and "| - |" not in ln
                                    and "Fixture" not in ln]}
    for proj in sorted(glob.glob(os.path.join(ROOT, "projects", "*", "project.py"))):
        if "/_template/" in proj:
            continue
        exec(open(proj).read(), {"__file__": proj, "__name__": "__main__", "PARAMS": {"quiet": True, "report": False}})
        import interiors as I
        problems = [x["cat"] + "/" + x["elem"] for x in I.ST.results
                    if x["status"] == I.NON_COMPLIANT and x["sev"] in ("blocking", "significant")]
        out["projects"][os.path.basename(os.path.dirname(proj))] = problems
        App.closeDocument(I.ST.doc.Name)
    e = out["engine"]
    out["ok"] = e["found"] == e["total"] and not e["unexpected"] and not any(out["projects"].values())
except Exception:  # noqa: BLE001 - the assert step reports it
    out["error"] = traceback.format_exc()
json.dump(out, open(os.path.join(ROOT, "ci", "engine_result.json"), "w"), indent=2)
print(json.dumps(out, indent=2))
