"""Recognised plan -> neutral model for interiors_core (docs/desktop-app.md, sections 3-5).
A 2D plan has no heights and no uses: heights come from the profile defaults below and from the furniture type
(recognised from the block name, app/semantics/library.py FURNITURE); every default is listed in `assumptions`.
Uses come from the furniture semantics library, plus the entrance and one destination for each room the library
left without one.

    uv run --with ezdxf --with shapely python -m app.importer.to_model plan.dxf [--profile p.json]  -> core checks
"""
import fnmatch
import math
import re
import sys

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from ..semantics import library
from .recognise import read, recognise

CELL = 0.05          # route grid of interiors_core.checks
DEFAULTS = dict(room_height=2.70, door_height=2.10, window_sill=0.90, window_height=1.40, furniture_height=0.75)


def _band(poly, z0, z1):
    rings = [list(poly.exterior.coords)] + [list(r.coords) for r in poly.interiors]
    return {"rings": [[list(p) for p in r] for r in rings], "z": [z0, z1]}


def _solids(geom, z0, z1):
    return [[_band(p, z0, z1)] for p in getattr(geom, "geoms", [geom]) if p.geom_type == "Polygon" and not p.is_empty]


def _rel_box(h, d, n, da, db, z0, z1):
    xs = [h[0] + d[0] * a + n[0] * b for a in da for b in db]
    ys = [h[1] + d[1] * a + n[1] * b for a in da for b in db]
    return [[_band(box(min(xs), min(ys), max(xs), max(ys)), z0, z1)]]


def _rects(poly):
    """Rectangles covering a room (exact for rooms with square corners): vertical strips between vertex abscissae."""
    xs = sorted({round(x, 4) for x, _y in poly.exterior.coords})
    out = []
    for xa, xb in zip(xs, xs[1:]):
        part = poly.intersection(box(xa, poly.bounds[1] - 1, xb, poly.bounds[3] + 1))
        for p in getattr(part, "geoms", [part]):
            if p.geom_type == "Polygon" and p.area > 1e-6:
                out.append(list(p.bounds))
    return out


def _windows(model, walls, windows, A):
    """Windows, plus the wall below the sill and above the head (the plan cuts walls at about 1.2-1.7 m)."""
    H, parts = model["height"], []
    for w in windows:
        z0 = w["z0"] if w["z0"] is not None else DEFAULTS["window_sill"]
        z1 = w["z1"] if w["z1"] is not None else z0 + DEFAULTS["window_height"]
        if w["z0"] is None:
            A.append("window %s: sill %.2f m and height %.2f m assumed" % (w["handle"], z0, z1 - z0))
        h = w["horizontal"]
        a0, a1 = (w["x0"], w["x1"]) if h else (w["y0"], w["y1"])
        c = w["yc"] if h else w["xc"]
        cols = [(a0 - 0.15, a0 - 0.06), (a1 + 0.06, a1 + 0.15)]          # the two wall stubs just beside the opening
        stubs = [walls.intersection(box(u, c - 0.5, v, c + 0.5) if h else box(c - 0.5, u, c + 0.5, v)) for u, v in cols]
        stubs = [s for s in stubs if not s.is_empty]
        span = (lambda s: s.bounds[3] - s.bounds[1]) if h else (lambda s: s.bounds[2] - s.bounds[0])
        near = min(stubs, key=span) if stubs else Polygon()     # the thinner stub: a perpendicular wall widens the other
        if near.is_empty:
            A.append("window %s: no wall beside it, sill and head not modelled" % w["handle"])
            gap = Polygon()
        else:
            b = near.bounds
            gap = (box(w["x0"] - 0.10, b[1], w["x1"] + 0.10, b[3]) if h else
                   box(b[0], w["y0"] - 0.10, b[2], w["y1"] + 0.10)).difference(walls)
        if z0 > 0:
            parts.append((gap, 0.0, z0))
        parts.append((gap, z1, H))
        glass = box(w["x0"] + 0.05, w["yc"] - 0.01, w["x1"] - 0.05, w["yc"] + 0.01)
        model["windows"].append(dict(name="W_" + w["handle"], yc=w["yc"], x0=w["x0"], x1=w["x1"], z0=z0, z1=z1,
                                     room=None, glass=_solids(glass, z0 + 0.03, z1 - 0.05),
                                     box=[w["x0"], w["y0"], w["x1"], w["y1"]]))
    for i, (g, z0, z1) in enumerate([(walls, 0.0, H)] + parts):
        model["walls"].append(dict(name="Wall_%d" % i, solids=_solids(g, z0, z1)))


def _rooms(model, rooms):
    """Rooms (rectangles for the core), kind and privacy from the name; each window serves the room it faces most
    (the largest share of the floor within 40 cm of it), not the first room that happens to be near."""
    for k, r in enumerate(rooms):
        rname = r["name"] = r["name"] or "Room %d" % (k + 1)
        fp = r["footprint"]
        model["rooms"].append(dict(
            name=rname, rects=_rects(fp), xy=list(fp.representative_point().coords[0]), area=r["area"], lines=[rname],
            habitable=not re.search(r"BAGN|BATH|WC|HALL|DISIMP|CORRID|RIPOST|CLOSET|CABINA|LAVANDER", rname, re.I),
            kind="bathroom" if re.search(r"BAGN|BATH|WC", rname, re.I) else ""))
        if re.search(r"CAMERA|LETTO|BEDROOM", rname, re.I):
            model["private"].append(rname)
    for w in model["windows"]:
        near = box(*w["box"]).buffer(0.40, join_style="mitre")
        share = {r["name"]: r["footprint"].intersection(near).area for r in rooms}
        best = max(share, key=share.get, default=None)
        w["room"] = best if best and share[best] > 0 else None


def _doors(model, res, rules):
    """Hinged doors as in lib/interiors.py hinged(): swept volume, leaf, handle, reveal probe.
    Returns the door that opens onto the outside (the entrance) and the point just inside it."""
    walls, entrance = res["walls"], None
    outside = box(*walls.bounds).buffer(1.0).difference(unary_union([r["footprint"] for r in res["rooms"]] + [walls]))
    for d in res["doors"]:
        h, dd, nn, w, hg = d["hinge"], d["d"], d["n"], d["w"], DEFAULTS["door_height"]
        at = lambda a, b: (h[0] + dd[0] * a + nn[0] * b, h[1] + dd[1] * a + nn[1] * b)  # noqa: E731 - local axes
        arc = [at(w * math.cos(t), w * math.sin(t)) for t in [i * math.pi / 96 for i in range(49)]]
        name = "Door_" + d["handle"]
        fr, rv, hd = rules["frame"], rules["reveal"], rules["handle"]
        model["doors"].append(dict(name=name, kind="Door", own=None, geo=dict(hinge=h, d=dd, n=nn, w=w, z0=0, hgt=hg),
                                   sweep=_solids(Polygon([tuple(h)] + arc), 0.01, hg - 0.01),
                                   leaf=_rel_box(h, dd, nn, (-0.04, 0), (0, w), 0.01, hg),
                                   handle=_rel_box(h, dd, nn, (-0.04 - hd, -0.04), (w - 0.12, w - 0.04), 0.95, 1.10),
                                   probe=_rel_box(h, dd, nn, (-fr - rv + 0.005, -fr), (0.005, 0.10), 0.10, 2.0)))
        if entrance is None and outside.buffer(0.05).contains(Point(at(w / 2, -0.3))):
            entrance = (name, Point(at(w / 2, 0.5)))
    return entrance


def _slides(model, res, A):
    """The open position is rarely drawn: the leaf parks along the wall, on the side where it stays against the wall
    without hitting walls or furniture."""
    walls = res["walls"]
    obstacles = unary_union([walls] + [f["footprint"] for f in res["furniture"]])
    for s in res["slides"]:
        x0, y0, x1, y1 = s["closed"]
        L, along_x = max(x1 - x0, y1 - y0), (x1 - x0) >= (y1 - y0)
        options = []
        for sign in (-1, 1):
            o = box(x0 + sign * L, y0, x1 + sign * L, y1) if along_x else box(x0, y0 + sign * L, x1, y1 + sign * L)
            options.append((o.intersection(obstacles).area, -o.buffer(0.03).intersection(walls).area, sign, o))
        hit, _adj, sign, o = min(options, key=lambda t: t[:2])
        model["slides"].append(dict(name="Slide_" + s["handle"], open=_solids(o, 0.01, 2.15),
                                    closed=_solids(box(x0, y0, x1, y1), 0.01, 2.15)))
        side = ("west" if sign < 0 else "east") if along_x else ("south" if sign < 0 else "north")
        A.append("sliding door %s: open position not drawn, assumed parked %s along the wall%s" % (
            s["handle"], side, "" if hit < 1e-6 else " (both sides obstructed: check)"))


def _furniture(model, furniture, A, profile=None):
    """Type and heights: studio profile (block-name globs), else block-name keywords (library.FURNITURE); the candidates
    stay on the element for the mapping UI. Overlaps a plan draws on purpose go to `stacked`."""
    globs = (profile or {}).get("blocks", {})
    names = [f["block"][4:] if f["block"].startswith("ARR_") else f["block"] for f in furniture]
    for f, item in zip(furniture, names):
        fixed = next((t for g, t in globs.items() if fnmatch.fnmatchcase(f["block"].upper(), g.upper())), None)
        f["type_candidates"] = ([dict(type=fixed, confidence=1.0, why="studio profile")] if fixed else []) + \
            library.type_candidates(f["block"])
        if fixed and fixed not in library.TYPE_Z:
            A.append("block %s: profile type %s unknown to the library" % (f["block"], fixed))
            fixed = None
        rule = (fixed, library.TYPE_Z[fixed]) if fixed else library.furniture_type(f["block"])
        if rule is None:
            rule = ("unknown", (0.0, DEFAULTS["furniture_height"]))
            A.append("block %s: type unknown, height %.2f m assumed" % (f["block"], rule[1][1]))
        f["type"], f["z"] = rule
        f["item"] = item = item if names.count(item) == 1 else "%s#%s" % (item, f["handle"])   # one block, many inserts
        if f["z"] is None:
            continue
        z0, z1 = f["z"]
        model["objects"].append(dict(item=item, label=item, group=f["type"], solids=_solids(f["footprint"], z0, z1)))
        model["named"][item] = _solids(f["footprint"], z0, z1)
        if f["type"] == "tv":
            model["tv"].append(item)
            model["named"][item] = _solids(f["footprint"], 0.95, z1)      # screen above its unit (default)
            A.append("TV %s: screen assumed from 0.95 m to %.2f m" % (item, z1))
    model["doc_names"] = [o["label"] for o in model["objects"]]
    model["stacked"] = library.stacked([f for f in furniture if f["z"] is not None])


def _plan(solids):
    return unary_union([Polygon(b["rings"][0]) for sol in solids for b in sol])


def _uses(model, res, entrance, A):
    """Uses from the furniture semantics library; the route start in front of the entrance, moved to the nearest free
    floor when furniture stands there; one destination in the free floor of each room the library left without one."""
    modelled = [f for f in res["furniture"] if f["z"] is not None]
    walk = [f for f in modelled if f["z"][0] < 1.0 and f["z"][1] > 0.05]     # what the route grid sees (cut at 1 m)
    rooms = {r["name"]: r["footprint"] for r in res["rooms"]}
    for f in modelled:
        c = f["footprint"].representative_point()
        f["room"] = next((n for n, fp in rooms.items() if fp.contains(c)), None) or \
            min(rooms, key=lambda n: rooms[n].distance(c), default="-")
    floor_area = unary_union(list(rooms.values()))
    struct = box(*floor_area.bounds).buffer(1.0, join_style="mitre").difference(floor_area)
    obst = unary_union([res["walls"]] + [f["footprint"] for f in walk]
                       + [box(*_plan(d["leaf"]).bounds) for d in model["doors"]]
                       + [box(*_plan(s["open"]).bounds) for s in model["slides"]])
    U = library.uses(modelled, rooms, struct, obst, (model["interior"][0], model["interior"][1], CELL), model["rules"], A)
    model["seats"] = U["seats"]
    model["access"] = [dict(label=a["label"], own=a["own"], depth=model["rules"]["access"],
                            zone=_solids(a["zone"], 0.05, 1.80)) for a in U["access"]]
    for c in U["clearances"]:
        for name, poly in (c["a"], c["b"]):
            model["named"].setdefault(name, _solids(poly, 0.0, 1.0))
        model["clearances"].append([c["label"], c["a"][0], c["b"][0], c["min"], c["comfort"]])
    model["wet"] = [dict(label=w["label"], zone=_solids(w["zone"], 0.0, 1.20)) for w in U["wet"]]
    model["elec"] = U["elec"]
    model["fronts"] = U["fronts"]          # for the mapping UI; the checks do not read it
    model["targets"] = {k: list(v) for k, v in U["targets"].items()}
    taken = unary_union([f["footprint"] for f in walk])
    for r in res["rooms"]:
        if any(r["footprint"].contains(Point(p)) for p in model["targets"].values()):
            continue
        free = r["footprint"].buffer(-0.35).difference(taken.buffer(0.35))
        parts = sorted(getattr(free, "geoms", [free]), key=lambda p: -p.area)
        ok = parts and not parts[0].is_empty
        p = parts[0].representative_point() if ok else r["footprint"].representative_point()
        model["targets"]["Room: " + r["name"]] = [p.x, p.y]
        if not ok:
            A.append("room %s: no free floor 60 cm wide found" % r["name"])
    if entrance is None:
        A.append("entrance not found: no door between a room and the outside; routes not checked")
        return
    name, p = entrance
    model["views"] = [dict(label=v["label"], eye=[p.x, p.y], eye_z=1.60, target=v["target"]) for v in U["views"]]
    room = next((r["footprint"] for r in res["rooms"] if r["footprint"].buffer(0.6).contains(p)), None)
    free = room.buffer(-0.31).difference(taken.buffer(0.31)) if room is not None else None
    if free is not None and not free.is_empty and not free.contains(p):
        q = min((g.exterior.interpolate(g.exterior.project(p)) for g in getattr(free, "geoms", [free])), key=p.distance)
        A.append("entrance: %s; the floor in front of it is taken, routes start %.2f m away" % (name, p.distance(q)))
        p = q
    else:
        A.append("entrance: %s (door opening onto the outside)" % name)
    model["start"] = [p.x, p.y]


def build(res, rules, name="imported", profile=None):
    """Neutral model of a recognised plan. Without walls (layers or units not understood yet) only the furniture types
    are filled in, for the mapping UI; the model is not checkable (`interior` is None)."""
    A = []
    if res["walls"].is_empty or not res["rooms"]:
        model = dict(name=name, interior=None, assumptions=A, objects=[], named={}, tv=[], fronts=[])
        A.append("no walls recognised: confirm the wall layer and the drawing units" if res["walls"].is_empty else
                 "walls found but no closed room: check the wall layer (outlines or hatches) and the openings")
        _furniture(model, res["furniture"], A, profile)
        return model
    model = dict(name=name, height=DEFAULTS["room_height"], interior=list(res["walls"].bounds), rules=rules,
                 assumptions=A, plan_2d=True, start=None, walls=[], objects=[], named={}, doc_names=[], doors=[],
                 slides=[], seats=[], access=[], rooms=[], windows=[], tv=[], heights=[], elec=[], wet=[], private=[],
                 views=[], viewpoints=[], intimate=[], accepted=[], requirements=[], not_verifiable=[], targets={},
                 routes=[], clearances=[], reference=[])
    _windows(model, res["walls"], res["windows"], A)
    _rooms(model, res["rooms"])
    entrance = _doors(model, res, rules)
    _slides(model, res, A)
    _furniture(model, res["furniture"], A, profile)
    _uses(model, res, entrance, A)
    return model


if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
    from interiors_core.checks import Model
    from interiors_core.rules import RULES
    import json
    prof = json.load(open(sys.argv[sys.argv.index("--profile") + 1])) if "--profile" in sys.argv else None
    res = recognise(read(sys.argv[1]), prof)
    data = build(res, RULES, os.path.basename(sys.argv[1]), prof)
    m = Model(data)
    rs = m.verify()
    for a in data["assumptions"]:
        print("assumption:", a)
    for x in rs:
        if x["status"] != "VERIFIED" or x["sev"]:
            print("%-14s %-13s %-40s %s %s" % (x["status"], x["sev"], x["cat"] + "/" + x["elem"], x["measure"], x["note"]))
    print("rows %d, NON-COMPLIANT %d" % (len(rs), sum(1 for x in rs if x["status"] == "NON-COMPLIANT")))
