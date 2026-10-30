# Exports every project and eval fixture to the neutral model used by app/core (docs/desktop-app.md, section 3),
# with the results of lib/interiors.py as the parity reference. Run with headless FreeCAD:
#   INTERIORS_ROOT=$PWD /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd app/tools/export_model.py
# Output: app/build/models/<name>.json (generated, not committed).
# MUTANTS=1 also writes app/build/mutants/: apartment-100sqm with each piece of furniture shifted by +-20 cm in x and y,
# re-verified by the FreeCAD engine, so parity is tested on many NON-COMPLIANT results, not only on clean layouts.
# Every solid is stored as z bands: between two consecutive vertex heights a solid made of vertical prisms has a constant
# plan section, so (section, z0, z1) is exact; a sphere becomes its bounding cylinder (one band at the equator).
import glob
import json
import os
import traceback

import FreeCAD as App

ROOT = os.environ.get("INTERIORS_ROOT", os.getcwd())
OUT = os.path.join(ROOT, "app", "build", "models")
MUT = os.path.join(ROOT, "app", "build", "mutants")
V = App.Vector
S = 1000.0


def bands(sol):
    bb = sol.BoundBox
    zs = sorted({round(v.Point.z, 3) for v in sol.Vertexes} | {round(bb.ZMin, 3), round(bb.ZMax, 3)})
    out = []
    for za, zb in zip(zs, zs[1:]):
        if zb - za < 0.5:          # thinner than 0.5 mm: numerical noise
            continue
        wires = sol.slice(V(0, 0, 1), (za + zb) / 2)
        rings = [[[round(p.x / S, 5), round(p.y / S, 5)] for p in w.discretize(QuasiDeflection=0.1)] for w in wires]
        if rings:
            out.append({"rings": rings, "z": [za / S, zb / S]})
    return out


def solids(shape):
    return [bands(s) for s in (shape.Solids or [shape])] if shape is not None else None


def export(name, engine, folder=OUT):
    ST = engine.ST
    named = set(ST.TV) | {t for _l, _e, _z, t in ST.VIEWS} | {t for t in ST.INTIMATE if ST.doc.getObject(t) is not None}
    for _l, a, b, _mn, _cf in ST.CLEAR:
        named |= {a, b}
    model = dict(
        name=name, height=ST.H, interior=list(ST.interior), rules=engine.RULES,
        walls=[dict(name=n, solids=solids(s)) for n, s in ST.WALLS],
        objects=[dict(item=it, label=lb, group=g, solids=solids(sh)) for it, lb, sh, g in ST.CHECK],
        named={n: solids(ST.doc.getObject(n).Shape) for n in sorted(named)},
        doc_names=[o.Name for o in ST.doc.Objects],
        doors=[dict(name=d["name"], kind=d["kind"], own=d["own"], geo=d["geo"], sweep=solids(d["sweep"]), leaf=solids(d["leaf"]),
                    handle=solids(d["handle"]), probe=solids(d["probe"])) for d in ST.DOORS],
        slides=[dict(name=s["name"], open=solids(s["shape"]), closed=solids(s["closed"]), c=list(s["c"]), o=list(s["o"]))
                for s in ST.SLIDES],
        seats=[dict(name=n, own=list(own), edge=list(e), dir=list(d), hw=hw) for n, own, e, d, hw in ST.SEATS],
        access=[dict(label=lb, zone=solids(z), own=list(own), depth=dp) for lb, z, own, dp in ST.ACCESS],
        rooms=[dict(r, rects=[list(x) for x in r["rects"]], xy=list(r["xy"])) for r in ST.ROOMS],
        windows=[{k: (solids(v) if k == "glass" else v) for k, v in w.items()} for w in ST.WINDOWS],
        tv=list(ST.TV), heights=[list(h) for h in ST.HEIGHTS], elec=list(ST.ELEC),
        wet=[dict(label=lb, zone=solids(z)) for lb, z in ST.WET],
        private=list(ST.PRIVATE), views=[dict(label=lb, eye=list(e), eye_z=z, target=t) for lb, e, z, t in ST.VIEWS],
        viewpoints=[dict(label=v["label"], eyes=[list(e) for e in v["eyes"]]) for v in ST.VIEWPOINTS],
        intimate=list(ST.INTIMATE), accepted=[dict(a) for a in ST.ACCEPTED],
        requirements=[dict(r, verified_by=list(r["verified_by"]), satisfied_by=list(r["satisfied_by"])) for r in ST.REQS],
        not_verifiable=[list(x) for x in ST.NOTVERIF],
        start=list(ST.START) if ST.START else None,
        targets={k: list(v) for k, v in ST.TARGETS.items()},
        routes=[list(r) for r in ST.ROUTES],
        clearances=[list(c) for c in ST.CLEAR],
        reference=ST.results,
    )
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name + ".json")
    json.dump(model, open(path, "w"))
    return path


def shift(engine, item, dx, dy):
    """Move every part of one piece of furniture (registered uses such as seat edges stay where they were)."""
    ST, v = engine.ST, V(dx * S, dy * S, 0)
    for i, (it, lb, sh, g) in enumerate(ST.CHECK):
        if it == item:
            moved = sh.translated(v)
            ST.CHECK[i] = (it, lb, moved, g)
            ST.doc.getObjectsByLabel(lb)[0].Shape = moved


runs = [p for p in sorted(glob.glob(os.path.join(ROOT, "projects", "*", "project.py"))) if "/_template/" not in p]
runs += sorted(glob.glob(os.path.join(ROOT, "evals", "fixtures", "*", "project.py")))
for proj in runs:
    name = os.path.basename(os.path.dirname(proj))
    try:
        exec(open(proj).read(), {"__file__": proj, "__name__": "__main__", "PARAMS": {"quiet": True, "report": False}})
        import interiors as I
        print("exported", export(name, I))
        if os.environ.get("MUTANTS") and name == "apartment-100sqm":
            items = sorted({it for it, _l, _s, g in I.ST.CHECK})
            for item in items:
                for dx, dy in ((0.20, 0.20), (-0.20, -0.20)):
                    shift(I, item, dx, dy)
                    I.verify(write_report=False, quiet=True)
                    export("%s~%s~%+.2f~%+.2f" % (name, item, dx, dy), I, MUT)
                    shift(I, item, -dx, -dy)
            print("mutants: %d" % (2 * len(items)))
        App.closeDocument(I.ST.doc.Name)
    except Exception:  # noqa: BLE001 - report and go on; parity.py fails on the error file (freecadcmd drops exit codes)
        print("FAILED", name, traceback.format_exc())
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(os.path.join(os.path.dirname(OUT), "export_errors.txt"), "a") as f:
            f.write("%s\n%s\n" % (name, traceback.format_exc()))
