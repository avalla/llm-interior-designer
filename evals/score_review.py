# Scores a review against the planted defects of a fixture.
# Usage: python3 evals/score_review.py <fixture> [findings.md]
#   default findings file: evals/results/<fixture>-review.md
# A defect counts as found when one block of the findings (paragraph, bullet or table row) contains at least one
# keyword of EVERY keyword group of that defect (case-insensitive, whole words; a trailing * matches a prefix,
# e.g. "orient*"). Headings are not findings. Recall = found / planted.
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
case = sys.argv[1]
findings = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "results", "%s-review.md" % case)
exp = json.load(open(os.path.join(ROOT, "fixtures", case, "expected.json")))
text = open(findings).read().lower()
blocks = [b for b in re.split(r"\n\s*\n|\n(?=\s*[-*|#]|\s*\d+\.)", text) if b.strip() and not b.lstrip().startswith("#")]


def has(block, kw):
    kw = kw.strip().lower()
    pat = r"\b" + re.escape(kw[:-1]) if kw.endswith("*") else r"\b" + re.escape(kw) + r"\b"
    return re.search(pat, block) is not None


found = 0
rows = []
for d in exp["defects"]:
    hit = next((b for b in blocks if all(any(has(b, k) for k in grp) for grp in d["keywords"])), None)
    found += bool(hit)
    rows.append("| %s | %s | %s |" % (d["id"], d["text"], "yes" if hit else "**NO**"))

out = ["# Review eval - %s" % case, "", "Findings: `%s`" % os.path.relpath(findings, os.path.dirname(ROOT)), "",
       "| Defect | Description | Found |", "|---|---|---|"] + rows + ["", "**Recall: %d/%d**" % (found, len(exp["defects"]))]
dst = os.path.join(ROOT, "results", "%s-score.md" % case)
os.makedirs(os.path.dirname(dst), exist_ok=True)
open(dst, "w").write("\n".join(out) + "\n")
print("\n".join(out))
