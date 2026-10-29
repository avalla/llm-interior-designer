"""Sidecar of the desktop app (docs/desktop-app.md, D6): JSON lines over stdio, one request per line
{"id": 1, "method": "analyse", "params": {...}} -> {"id": 1, "result": {...}} or {"id": 1, "error": "..."}.
Only JSON goes to stdout; logs go to stderr. `--http PORT` serves the same methods on POST /rpc for UI development in
a browser (localhost only).

Methods
    ping                                   -> {version}
    vocabulary                             -> layer categories, furniture types, front axes (for the mapping UI)
    analyse   {path, profile?}             -> plan scene, mapping, assumptions, results with their place on the plan
    load_profile {path} / save_profile {path, profile}

    uv run --with ezdxf --with shapely python -m app.sidecar.server [--http 8765]
"""
import collections
import json
import os
import re
import sys
import traceback

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "app", "core"))
from app.importer.mapping import mapping  # noqa: E402
from app.importer.recognise import AXES, LAYER_RULES, _pts, read, recognise  # noqa: E402
from app.importer.to_model import build  # noqa: E402
from app.semantics import library  # noqa: E402
from interiors_core.checks import Model  # noqa: E402
from interiors_core.rules import RULES  # noqa: E402

VERSION = "0.1.0"
SEVERITY = {"blocking": 0, "significant": 1, "improvement": 2, "": 3}


def _plan(solids):
    """Plan outline of a shape in the neutral model (list of solids of bands)."""
    polys = [Polygon(b["rings"][0]).buffer(0) for sol in solids or [] for b in sol if len(b["rings"][0]) >= 3]
    return unary_union(polys) if polys else Polygon()


def _rings(geom):
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if g.geom_type == "Polygon" and not g.is_empty:
            out.append([[round(x, 4), round(y, 4)] for x, y in g.exterior.coords])
    return out


def _shape(geom, **kw):
    return dict(rings=_rings(geom), **kw)


def scene(res, model):
    """What the plan viewer draws, in metres."""
    furniture = []
    fronts = {x["item"]: x for x in model.get("fronts", [])}
    for f in res["furniture"]:
        furniture.append(_shape(f["footprint"], item=f.get("item", f["block"]), block=f["block"], type=f.get("type"),
                                hung=bool(f.get("z")) and f["z"][0] > 0, front=fronts.get(f.get("item"))))
    drawn = res["walls"] if not res["walls"].is_empty else unary_union([f["footprint"] for f in res["furniture"]])
    out = dict(bounds=list(drawn.bounds) if not drawn.is_empty else None,
               walls=_rings(res["walls"]),
               rooms=[_shape(r["footprint"], name=r["name"], area=round(r["area"], 2),
                             private=r["name"] in model.get("private", [])) for r in res["rooms"]],
               doors=[_shape(_plan(d["sweep"]), name=d["name"], leaf=_rings(_plan(d["leaf"])))
                      for d in model.get("doors", [])],
               slides=[_shape(_plan(s["closed"]), name=s["name"], open=_rings(_plan(s["open"])))
                       for s in model.get("slides", [])],
               windows=[_shape(box(w["x0"], w["y0"], w["x1"], w["y1"]), name="W_" + w["handle"]) for w in res["windows"]],
               furniture=furniture,
               access=[_shape(_plan(a["zone"]), label=a["label"]) for a in model.get("access", [])],
               wet=[_shape(_plan(w["zone"]), label=w["label"]) for w in model.get("wet", [])],
               targets=[dict(label=k, point=v) for k, v in model.get("targets", {}).items()],
               start=model.get("start"),
               texts=[t for t in res["texts"]])
    return out


def _seat_zone(s, depth=1.5):
    """The zone the seat check measures, up to the first obstacle (`depth`)."""
    (ox, oy), (dx, dy), hw = s["edge"], s["dir"], s["hw"]
    nx, ny = -dy, dx
    return Polygon([(ox + nx * hw, oy + ny * hw), (ox + dx * depth + nx * hw, oy + dy * depth + ny * hw),
                    (ox + dx * depth - nx * hw, oy + dy * depth - ny * hw), (ox - nx * hw, oy - ny * hw)])


def locate(row, model):
    """Where a result row is on the plan: the shapes and points it is about (empty when it has no place)."""
    cat, elem = row["cat"], row["elem"]
    named = model.get("named", {})
    objects = {o["item"]: o for o in model.get("objects", [])}
    doors = {d["name"]: d for d in model.get("doors", [])}
    targets = model.get("targets", {})
    shapes, points = [], []
    if cat == "Robustness" and "/" in elem:
        sub, rest = elem.split("/", 1)
        return locate(dict(row, cat=sub, elem=rest), model)
    if cat in ("Openings", "Handles", "Reveals") and elem in doors:
        shapes.append(_plan(doors[elem]["sweep"]))
    elif cat == "Openings" and elem.endswith(" (open)"):
        s = next((s for s in model.get("slides", []) if s["name"] == elem[:-7]), None)
        if s:
            shapes.append(_plan(s["open"]))
    elif cat == "Seats":
        s = next((s for s in model.get("seats", []) if s["name"] == elem), None)
        if s:
            m = re.match(r"([\d.]+) cm", row["measure"])
            shapes += [_plan(objects[s["name"]]["solids"]) if s["name"] in objects else Polygon(),
                       _seat_zone(s, float(m.group(1)) / 100 if m else 1.5)]
    elif cat == "Clearances":
        c = next((c for c in model.get("clearances", []) if c[0] == elem), None)
        if c:
            shapes += [_plan(named.get(c[1])), _plan(named.get(c[2]))]
    elif cat == "Access zones":
        a = next((a for a in model.get("access", []) if a["label"] == elem), None)
        if a:
            shapes.append(_plan(a["zone"]))
    elif cat in ("Routes", "Privacy") and elem in targets:
        points.append(targets[elem])
    elif cat == "Privacy":
        v = next((v for v in model.get("views", []) if v["label"] == elem), None)
        if v:
            shapes.append(_plan(named.get(v["target"])))
            points.append(v["eye"])
    elif cat == "Light and air":
        r = next((r for r in model.get("rooms", []) if r["name"] == elem.split(" - ")[0]), None)
        if r:
            shapes.append(unary_union([box(*rc) for rc in r["rects"]]))
    elif cat == "Brief constraints" and elem.startswith("TV "):
        shapes.append(_plan(named.get(elem[3:])))
    elif cat == "Safety":
        w = next((w for w in model.get("wet", []) if w["label"] == elem), None)
        if w:
            shapes.append(_plan(w["zone"]))
    elif cat == "Assembly" and elem in objects:
        shapes.append(_plan(objects[elem]["solids"]))
    elif cat == "Geometry":
        for name in re.split(r" <-> |, | inside ", row["measure"]):
            if name in objects:
                shapes.append(_plan(objects[name]["solids"]))
    shapes = [s for s in shapes if not s.is_empty]
    allg = unary_union(shapes + [Point(p) for p in points])
    first = shapes[0].representative_point() if shapes else Point(points[0]) if points else None
    return dict(shapes=[r for s in shapes for r in _rings(s)], points=points,
                bounds=list(allg.bounds) if not allg.is_empty else None,
                anchor=[first.x, first.y] if first else None)


def _room_at(anchor, rooms):
    """The room of a result: where the first shape (or point) it is about lies."""
    if not anchor:
        return ""
    return next((r["name"] for r in rooms if r["footprint"].buffer(0.05).contains(Point(anchor))), "")


THREE_D = ("3DSOLID", "BODY", "MESH", "REGION", "SURFACE", "3DFACE")
MAX_POINTS = 200000


def drawing(doc, res):
    """The drawing as it is, layer by layer, in metres: what the plan viewer shows under the recognised elements, so
    the user always sees the plan and which lines a layer holds. Also counts what the importer cannot read."""
    f = res["units"]["factor"]
    layers, stats, budget = {}, collections.Counter(), MAX_POINTS
    for e in doc.modelspace():
        t = e.dxftype()
        stats[t] += 1
        if t == "POLYLINE" and (e.is_poly_face_mesh or e.is_polygon_mesh):
            stats["3D mesh"] += 1
            continue
        if t in THREE_D or t in ("TEXT", "MTEXT", "DIMENSION", "HATCH", "ATTDEF", "VIEWPORT") or budget <= 0:
            continue
        parts = [e]
        if t == "INSERT":
            try:
                parts = [x for x in e.virtual_entities() if x.dxftype() not in ("TEXT", "MTEXT", "ATTRIB", "HATCH")]
            except Exception:                                   # a broken block is shown as missing, not fatal
                parts = []
        for x in parts:
            pts = _pts(x, f)
            if len(pts) >= 2:
                budget -= len(pts)
                layers.setdefault(e.dxf.layer, []).append([[round(a, 3), round(b, 3)] for a, b in pts])
    return dict(layers=[dict(name=n, category=res["layers"].get(n, "ignored"), lines=v) for n, v in layers.items()],
                stats=dict(stats), truncated=budget <= 0)


def diagnose(res, model, d):
    """What the import found, what is missing, why, and what to do: shown above the plan."""
    walls, rooms = res["walls"], res["rooms"]
    found = dict(walls_m2=round(walls.area, 1) if not walls.is_empty else 0, doors=len(res["doors"]),
                 slides=len(res["slides"]), windows=len(res["windows"]), rooms=len(rooms),
                 furniture=len(res["furniture"]))
    st, out = d["stats"], []
    n = sum(v for k, v in st.items() if k != "3D mesh")
    solid3d = sum(st.get(k, 0) for k in THREE_D) + st.get("3D mesh", 0)
    by_cat = collections.Counter()
    for layer in d["layers"]:
        by_cat[layer["category"]] += len(layer["lines"])
    if n and solid3d >= n / 2:
        out.append(dict(level="error", text="This is a 3D model (%d solids or meshes), not a plan." % solid3d,
                        action="Open the 2D plan (DXF or DWG), or export one from the 3D model."))
    if walls.is_empty and not out:
        out.append(dict(level="error", text="No walls found.",
                        action="In Mapping, choose the layer that holds the walls; check the drawing units."))
    elif not rooms and not out:
        out.append(dict(level="error", text="Walls found, but no closed room: the openings were not recognised, so "
                        "the rooms stay open to the outside.", action="Check the door and window layers in Mapping."))
    if not res["doors"] and by_cat["doors"] and st.get("INSERT", 0) == 0:
        out.append(dict(level="warn", text="Doors are drawn as loose lines and arcs, not as blocks: not read yet.",
                        action="Draw doors as blocks (leaf + swing arc), or wait for exploded-drawing support."))
    if not res["furniture"] and by_cat["furniture"]:
        out.append(dict(level="warn", text="Furniture is drawn as loose lines, not as blocks: not read yet.",
                        action="Furniture as blocks (one per piece) lets the app type it and check its uses."))
    if res["units"]["note"].startswith("undeclared"):
        out.append(dict(level="info", text="Drawing units are not declared: %s." % res["units"]["note"][12:],
                        action="Confirm or override them in Mapping."))
    unknown = sum(1 for f_ in res["furniture"] if f_.get("type") == "unknown")
    if unknown:
        out.append(dict(level="info", text="%d furniture blocks of unknown type." % unknown,
                        action="Type them in Mapping (one choice per code family)."))
    return dict(found=found, notes=out)


def analyse(path, profile=None):
    doc = read(path)
    res = recognise(doc, profile)
    model = build(res, RULES, os.path.basename(path), profile)
    m = mapping(res, model)
    d = drawing(doc, res)
    rows = []
    checkable = model.get("interior") is not None
    if checkable:
        for x in Model(model).verify():
            w = locate(x, model)
            rows.append(dict(x, where=w, room=_room_at(w["anchor"], res["rooms"])))
    rows.sort(key=lambda x: (x["status"] != "NON-COMPLIANT", SEVERITY.get(x["sev"], 3), x["cat"]))
    count = {}
    for x in rows:
        count[x["status"]] = count.get(x["status"], 0) + 1
    sc = scene(res, model)
    sc["drawing"] = d["layers"]
    if not sc["bounds"]:                                     # nothing recognised: frame the drawing itself
        xs = [p[0] for layer in d["layers"] for ln in layer["lines"] for p in ln]
        ys = [p[1] for layer in d["layers"] for ln in layer["lines"] for p in ln]
        sc["bounds"] = [min(xs), min(ys), max(xs), max(ys)] if xs else None
    return dict(name=os.path.basename(path), checkable=checkable, units=res["units"], scene=sc,
                mapping=m, assumptions=model["assumptions"], unrecognised=res["unrecognised"], results=rows,
                summary=count, profile=profile or {}, diagnosis=diagnose(res, model, d))


def vocabulary():
    types = sorted({t for _rx, t, _z in library.FURNITURE})
    return dict(categories=[c for c, _rx in LAYER_RULES] + ["ignored"], types=types, fronts=sorted(AXES))


def handle(method, params):
    if method == "ping":
        return dict(version=VERSION)
    if method == "vocabulary":
        return vocabulary()
    if method == "analyse":
        return analyse(params["path"], params.get("profile"))
    if method == "load_profile":
        return json.load(open(params["path"]))
    if method == "save_profile":
        with open(params["path"], "w") as fh:
            json.dump(params["profile"], fh, indent=1)
        return dict(saved=params["path"])
    raise ValueError("unknown method: %s" % method)


def _answer(req):
    try:
        return dict(id=req.get("id"), result=handle(req["method"], req.get("params") or {}))
    except Exception as e:                                      # the UI shows it; the details go to stderr
        traceback.print_exc(file=sys.stderr)
        return dict(id=req.get("id"), error="%s: %s" % (type(e).__name__, e))


def serve_stdio():
    for line in sys.stdin:
        if line.strip():
            sys.stdout.write(json.dumps(_answer(json.loads(line))) + "\n")
            sys.stdout.flush()


def serve_http(port):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def _head(self, code):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_OPTIONS(self):
            self._head(204)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self._head(200)
            self.wfile.write(json.dumps(_answer(body)).encode())

        def log_message(self, *a):
            pass
    print("sidecar on http://127.0.0.1:%d/rpc" % port, file=sys.stderr)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


if __name__ == "__main__":
    if "--http" in sys.argv:
        serve_http(int(sys.argv[sys.argv.index("--http") + 1]))
    else:
        serve_stdio()
