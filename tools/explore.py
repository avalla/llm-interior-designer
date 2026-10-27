# Variant exploration: runs a project once per parameter combination and ranks the results.
# Run INSIDE FreeCAD (MCP execute_code), with the variables PROJECT and GRID defined beforehand:
#   PROJECT = "/Users/andrea/dev/tmp/freecad/projects/apartment-100sqm/project.py"
#   GRID = {"table_x": [5.15, 5.35, 5.55], "table_y": [5.90, 6.10]}
#   T = "/Users/andrea/dev/tmp/freecad/tools/explore.py"; exec(open(T).read(), {"PROJECT": PROJECT, "GRID": GRID})
# The project reads its variable values from PARAMS (see projects/apartment-100sqm/project.py).
# Ranking: fewest blocking, then significant problems, then improvement notes, then the largest smallest margin. The agent still chooses
# and justifies: the ranking is a filter, not a verdict (docs/method.md, section 11: no score compensates a violation).
import itertools
import os
import re

import interiors  # noqa: F401  (loaded by the project; imported here for the results)

keys = list(GRID)
rows = []
for combo in itertools.product(*(GRID[k] for k in keys)):
    params = dict(zip(keys, combo), report=False, quiet=True)
    exec(open(PROJECT).read(), {"__file__": PROJECT, "__name__": "__main__", "PARAMS": params})
    import interiors as I
    res = I.ST.results
    blocking = sum(1 for x in res if x["status"] == I.NON_COMPLIANT and x["sev"] == "blocking")
    significant = sum(1 for x in res if x["status"] == I.NON_COMPLIANT and x["sev"] == "significant")
    improvements = sum(1 for x in res if x["sev"] == "improvement")
    margins = []
    for x in res:
        if x["cat"] in ("Seats", "Clearances") and x["status"] == I.VERIFIED:
            m = re.match(r"([\d.]+) cm", x["measure"])
            t = re.match(r"min ([\d.]+)", x["threshold"])
            if m and t:
                margins.append(float(m.group(1)) - float(t.group(1)))
    failed = [x["cat"] + "/" + x["elem"] for x in res if x["status"] == I.NON_COMPLIANT]
    rows.append((blocking, significant, improvements, -(min(margins) if margins else 0), combo, failed))

rows.sort(key=lambda r: r[:4])
out = os.path.join(os.path.dirname(PROJECT), "output")
os.makedirs(out, exist_ok=True)
L = ["# Variants - %s" % os.path.basename(os.path.dirname(PROJECT)), "",
     "| Rank | %s | Blocking | Significant | Improvement notes | Smallest margin (cm) | Failed checks |" % " | ".join(keys),
     "|---|%s---|---|---|---|---|" % ("---|" * len(keys))]
for i, (bl, sg, imp, negm, combo, failed) in enumerate(rows, 1):
    L.append("| %d | %s | %d | %d | %d | %.0f | %s |" % (i, " | ".join(str(v) for v in combo), bl, sg, imp, -negm,
                                                       ", ".join(failed[:4]) + (" ..." if len(failed) > 4 else "")))
open(os.path.join(out, "variants.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
# leave the document in the chosen (default) state
exec(open(PROJECT).read(), {"__file__": PROJECT, "__name__": "__main__", "PARAMS": {"report": False, "quiet": True}})
