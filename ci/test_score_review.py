# Unit test of evals/score_review.py on synthetic findings (lesson: "bed" once matched "bedroom").
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
case = "ci-scorer"
fixture = os.path.join(ROOT, "evals", "fixtures", case)
os.makedirs(fixture, exist_ok=True)
try:
    json.dump({"defects": [
        {"id": "T1", "text": "bed under window", "engine": [], "keywords": [["bed"], ["window"]]},
        {"id": "T2", "text": "sofa orientation", "engine": [], "keywords": [["sofa"], ["orient*"]]},
        {"id": "T3", "text": "never mentioned", "engine": [], "keywords": [["piano"]]},
    ]}, open(os.path.join(fixture, "expected.json"), "w"))
    findings = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
    findings.write("# Review mentions bed and window in the title\n\n"
                   "**Bedroom - window.** The bedroom has a window.\n\n"
                   "**Living - sofa.** The sofa orientation faces the wall.\n")
    findings.close()
    out = subprocess.run([sys.executable, os.path.join(ROOT, "evals", "score_review.py"), case, findings.name],
                         capture_output=True, text=True, check=True).stdout
    rows = {line.split("|")[1].strip(): line.split("|")[3].strip() for line in out.splitlines()
            if line.startswith("| T")}
    assert rows == {"T1": "**NO**", "T2": "yes", "T3": "**NO**"}, rows   # title ignored, "bedroom" is not "bed"
    print("score_review OK")
finally:
    for f in ("expected.json",):
        p = os.path.join(fixture, f)
        if os.path.exists(p):
            os.remove(p)
    os.rmdir(fixture)
    res = os.path.join(ROOT, "evals", "results", "%s-score.md" % case)
    if os.path.exists(res):
        os.remove(res)
