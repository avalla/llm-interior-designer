"""Mapping data for the confirmation UI (docs/desktop-app.md, section 4): what the importer decided about each layer,
block and furniture front, with the candidates, their confidence and the evidence, and what to confirm first.
The UI's answers are a studio profile (format in recognise.py); `proposal()` writes the profile that keeps every
automatic choice, so the user only edits what is wrong, and the next drawing of the same studio starts from it.

    uv run --with ezdxf --with shapely python -m app.importer.mapping plan.dxf [--profile p.json] [--write new.json]
"""
import json
import sys

from .recognise import read, recognise
from .to_model import build

CONFIRM = 0.7         # below this confidence a choice is listed for confirmation


def _conf(c):
    return c[0]["confidence"] if c else 0.0


def mapping(res, model):
    used = {}
    for f in res["furniture"]:
        used.setdefault(f["block"], []).append(f)
    layers = [dict(name=n, applied=res["layers"][n], candidates=c) for n, c in res["layer_candidates"].items()]
    blocks = [dict(name=b, count=len(fs), applied=fs[0]["type"], candidates=fs[0]["type_candidates"])
              for b, fs in sorted(used.items())]
    note = res["units"]["note"]
    confirm = [("units", "drawing units", "x %g" % res["units"]["factor"], 0.6 if "door widths" in note else 0.3)] \
        if note.startswith("undeclared") else []
    confirm += [("layer", x["name"], x["applied"], _conf(x["candidates"])) for x in layers
                if x["candidates"] and _conf(x["candidates"]) < CONFIRM]
    confirm += [("block", x["name"], x["applied"], _conf(x["candidates"])) for x in blocks
                if _conf(x["candidates"]) < CONFIRM]
    confirm += [("front", x["item"], x["side"], x["confidence"]) for x in model.get("fronts", [])
                if x["confidence"] < CONFIRM]
    return dict(units=res["units"], layers=layers, blocks=blocks, fronts=model.get("fronts", []),
                confirm=[dict(kind=k, name=n, applied=a, confidence=c) for k, n, a, c in confirm])


def proposal(m, profile=None):
    """Studio profile keeping every applied choice (the user edits only the wrong ones)."""
    p = dict(profile or {})
    p["layers"] = {x["name"]: x["applied"] for x in m["layers"] if x["applied"] != "ignored"}
    p["blocks"] = dict((profile or {}).get("blocks", {}))
    for b in m["blocks"]:
        if b["applied"] != "unknown" and not any(c["why"] == "studio profile" for c in b["candidates"]):
            p["blocks"].setdefault(b["name"], b["applied"])
    return p


if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
    from interiors_core.rules import RULES
    prof = json.load(open(sys.argv[sys.argv.index("--profile") + 1])) if "--profile" in sys.argv else None
    res = recognise(read(sys.argv[1]), prof)
    m = mapping(res, build(res, RULES, os.path.basename(sys.argv[1]), prof))
    print("units: factor %g (%s)" % (m["units"]["factor"], m["units"]["note"]))
    print("layers: %s" % ", ".join("%s=%s" % (x["name"], x["applied"]) for x in m["layers"] if x["applied"] != "ignored"))
    print("blocks: %d, unknown: %s" % (len(m["blocks"]), ", ".join(x["name"] for x in m["blocks"]
                                                                 if x["applied"] == "unknown") or "none"))
    print("to confirm (%d):" % len(m["confirm"]))
    for c in m["confirm"]:
        print("  %-5s %-28s %-12s %.1f" % (c["kind"], c["name"], c["applied"], c["confidence"]))
    if "--write" in sys.argv:
        json.dump(proposal(m, prof), open(sys.argv[sys.argv.index("--write") + 1], "w"), indent=1)
