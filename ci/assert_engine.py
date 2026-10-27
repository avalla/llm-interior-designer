# Fails the CI job when ci/engine_result.json (written by ci/engine_ci.py) is missing or not ok.
import json
import os
import sys

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine_result.json")
if not os.path.exists(path):
    sys.exit("engine_result.json missing: freecadcmd did not run ci/engine_ci.py")
r = json.load(open(path))
if r.get("error"):
    sys.exit("engine run crashed:\n" + r["error"])
e = r["engine"]
print("engine recall %d/%d, unexpected: %s" % (e["found"], e["total"], e["unexpected"] or "none"))
for name, problems in r["projects"].items():
    print("project %s: %s" % (name, "0 problems" if not problems else problems))
sys.exit(0 if r["ok"] else 1)
