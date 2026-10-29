"""Recognition of a 2D architectural plan (DXF, or DWG through ODA File Converter) into plan elements.
docs/desktop-app.md, section 4. Every element carries the evidence it came from (layer, block, handle) so the user
can confirm or fix it; nothing here guesses silently: what is not recognised is listed in `unrecognised`.

Studio profile (JSON, every key optional; the mapping UI writes it, app/importer/mapping.py proposes it):
    {"units": "cm",                                   drawing units when $INSUNITS is missing or wrong
     "layers": {"0-M30": "walls"},                    layer -> walls | doors | windows | furniture | texts | ignored
     "blocks": {"AR*": "wardrobe"},                   block-name glob -> furniture type (app/semantics/library.py)
     "front": "-y"}                                   block axis that is the front of furniture blocks

    uv run --with ezdxf --with shapely python -m app.importer.recognise plan.dxf [--profile profile.json]
"""
import glob
import json
import math
import os
import re
import sys

import ezdxf
from ezdxf import path as dxfpath
from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import polygonize, unary_union

# layer name -> category; a studio profile ({"layers": {"MY_WALLS": "walls"}}) takes precedence
LAYER_RULES = [
    ("walls", r"MUR|WALL|PARET|A-WALL|TRAMEZ"),
    ("doors", r"PORT|DOOR|A-DOOR|INFISS.*INT"),
    ("windows", r"FINESTR|WINDOW|SERRAMENT|A-GLAZ|VETRAT"),
    ("furniture", r"ARRED|FURN|MOBIL|A-FURN|ELETTRODOM|SANITAR"),
    ("texts", r"TEST|TEXT|NOMI|LOCALI|ROOM|A-AREA-IDEN"),
]
UNITS = {1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0}
UNIT_NAMES = {"in": 0.0254, "ft": 0.3048, "mm": 0.001, "cm": 0.01, "m": 1.0}
AXES = {"-y": (0, -1), "+y": (0, 1), "-x": (-1, 0), "+x": (1, 0)}
AUTO = 0.5            # a layer candidate below this confidence is proposed, not applied
AREA_TEXT = re.compile(r"^\s*[\d.,]+\s*(m2|m²|mq)\s*$", re.I)


def classify_layers(doc, profile=None):
    """layer -> category, plus the candidates behind each choice: profile (1.0), layer name (0.8, 0.5 when two
    categories match), content (what the layer holds: 0.3-0.6). The best candidate is applied when >= AUTO."""
    fixed = (profile or {}).get("layers", {})
    stats = {}
    for e in doc.modelspace():
        st = stats.setdefault(e.dxf.layer, dict(n=0, text=0, insert=0, arc_blocks=0, attrib_blocks=0, lines=0))
        st["n"] += 1
        t = e.dxftype()
        if t in ("TEXT", "MTEXT"):
            st["text"] += 1
        elif t == "INSERT":
            st["insert"] += 1
            blk = doc.blocks.get(e.dxf.name)
            if blk is not None and any(x.dxftype() == "ARC" for x in blk):
                st["arc_blocks"] += 1
            if e.attribs:
                st["attrib_blocks"] += 1
        elif t in ("LINE", "LWPOLYLINE", "POLYLINE", "HATCH", "ARC"):
            st["lines"] += 1
    cats, cands = {}, {}
    names = [layer.dxf.name for layer in doc.layers]
    names += [n for n in stats if n not in names]               # used but missing from the layer table
    for n in names:
        c = []
        if n in fixed:
            c.append(dict(category=fixed[n], confidence=1.0, why="studio profile"))
        by_name = [cat for cat, rx in LAYER_RULES if re.search(rx, n, re.I)]
        for cat in by_name:
            c.append(dict(category=cat, confidence=0.8 if len(by_name) == 1 else 0.5, why="layer name"))
        st = stats.get(n)
        if st and st["n"]:
            share = lambda k: st[k] / st["n"]  # noqa: E731
            if share("text") >= 0.8:
                c.append(dict(category="texts", confidence=0.6, why="%d texts" % st["text"]))
            if share("insert") >= 0.8:
                if st["arc_blocks"] >= st["insert"] / 2:
                    c.append(dict(category="doors", confidence=0.6, why="blocks with a swing arc"))
                elif st["attrib_blocks"] >= st["insert"] / 2:
                    c.append(dict(category="windows", confidence=0.5, why="blocks with attributes"))
                else:
                    c.append(dict(category="furniture", confidence=0.5, why="%d blocks" % st["insert"]))
            if share("lines") >= 0.8 and st["n"] >= 8:
                c.append(dict(category="walls", confidence=0.3, why="%d lines/outlines/hatches" % st["n"]))
        c.sort(key=lambda x: -x["confidence"])
        cands[n] = c
        cats[n] = c[0]["category"] if c and c[0]["confidence"] >= AUTO else "ignored"
    return cats, cands


def _units_from_doors(doc, cats):
    """Undeclared units: the one that makes the median door swing radius 60-130 cm, when exactly one does."""
    radii = sorted(a.dxf.radius * abs(e.dxf.xscale) for e in doc.modelspace()
                   if e.dxftype() == "INSERT" and cats.get(e.dxf.layer) == "doors" and doc.blocks.get(e.dxf.name)
                   for a in doc.blocks.get(e.dxf.name) if a.dxftype() == "ARC")
    if radii:
        r = radii[len(radii) // 2]
        fits = [u for u, k in UNIT_NAMES.items() if 0.60 <= r * k <= 1.30]
        if len(fits) == 1:
            return UNIT_NAMES[fits[0]], "undeclared: %s from the door widths (median %g), confirm" % (fits[0], r)
    return None, "undeclared: assumed millimetres, confirm against a known dimension"


def _pts(entity, f):
    """WCS points of a flattened entity, in metres."""
    try:
        return [(v.x * f, v.y * f) for v in dxfpath.make_path(entity).flattening(0.5)]
    except (TypeError, ValueError):
        return []


ODA_PATHS = ["/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter",       # default install places
             r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe", "/usr/bin/ODAFileConverter"]


def read(path, oda=None):
    """DXF directly; DWG through the ODA File Converter (user-installed): `oda`, else its default install places."""
    if path.lower().endswith(".dwg"):
        from ezdxf.addons import odafc
        found = [p for p in ODA_PATHS if os.path.isfile(p)] + sorted(glob.glob(   # Windows installs carry the version
            r"C:\Program Files\ODA\ODAFileConverter*\ODAFileConverter.exe"), reverse=True)
        oda = oda or (found[0] if found else None)
        if oda:
            ezdxf.options.set("odafc-addon", "win_exec_path" if sys.platform == "win32" else "unix_exec_path", oda)
        if not odafc.is_installed():
            raise RuntimeError("DWG needs the ODA File Converter (free, opendesign.com); it was not found. "
                               "Install it, or save the drawing as DXF from AutoCAD")
        return odafc.readfile(path)
    return ezdxf.readfile(path)


def recognise(doc, profile=None):
    f = UNITS.get(doc.header.get("$INSUNITS", 0))
    units_note = "declared" if f else "undeclared: assumed millimetres, confirm against a known dimension"
    cats, cands = classify_layers(doc, profile)
    if (profile or {}).get("units"):
        f, units_note = UNIT_NAMES[profile["units"]], "studio profile"
    elif not f:
        f, units_note = _units_from_doors(doc, cats)
    f = f or 0.001
    front = AXES.get((profile or {}).get("front"))
    msp = doc.modelspace()
    res = dict(units=dict(factor=f, note=units_note), layers=cats, layer_candidates=cands, walls=None, doors=[],
               slides=[], windows=[], furniture=[], rooms=[], texts=[], unrecognised=[])
    proxies = sum(1 for e in msp if e.dxftype() in ("ACAD_PROXY_ENTITY",) or e.dxftype().startswith("AEC"))
    if proxies:
        res["unrecognised"].append(dict(kind="proxy entities (AutoCAD Architecture objects?)", count=proxies,
                                        hint="EXPORTTOAUTOCAD in AutoCAD, then import again"))
    wall_rings, hatch_rings, wall_lines = [], [], []
    for e in msp:
        cat, t = cats.get(e.dxf.layer, "ignored"), e.dxftype()
        if cat == "walls":
            if t in ("LWPOLYLINE", "POLYLINE") and e.is_closed:
                p = _pts(e, f)
                if len(p) >= 3:
                    wall_rings.append(p)
            elif t in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
                p = _pts(e, f)
                if len(p) >= 2:
                    wall_lines.append(LineString(p))
            elif t == "HATCH":
                for bp in e.paths:
                    vs = getattr(bp, "vertices", None)
                    if vs:
                        hatch_rings.append([(v[0] * f, v[1] * f) for v in vs])
        elif t == "INSERT" and cat in ("doors", "windows", "furniture"):
            _insert(e, cat, f, res, front)
        elif cat == "texts" and t in ("TEXT", "MTEXT"):
            s = e.dxf.text if t == "TEXT" else e.plain_text()
            p = e.dxf.insert
            res["texts"].append(dict(text=s.strip(), xy=[p.x * f, p.y * f], handle=e.dxf.handle))
    # walls: closed outlines with the even-odd rule (outer rings and holes alike, duplicates dropped); hatches only when
    # there are no outlines (they usually repeat them); rings closed by loose lines
    walls = _even_odd(wall_rings or hatch_rings)
    if wall_lines:
        walls = walls.union(_even_odd([list(p.exterior.coords) for p in polygonize(unary_union(wall_lines))]))
    res["walls"] = walls
    _rooms(res)
    return res


def _even_odd(rings):
    out, seen = Polygon(), set()
    for r in rings:
        p = Polygon(r).buffer(0)
        key = tuple(round(v, 3) for v in p.bounds) + (round(p.area, 4),)
        if p.is_empty or key in seen:
            continue
        seen.add(key)
        out = out.symmetric_difference(p)
    return out


def _insert(e, cat, f, res, front=None):
    ents = list(e.virtual_entities())
    name, handle = e.dxf.name, e.dxf.handle
    pts = [p for x in ents for p in _pts(x, f)]
    if not pts:
        res["unrecognised"].append(dict(kind="empty block", block=name, handle=handle))
        return
    arcs = [x for x in ents if x.dxftype() == "ARC"]
    if cat == "doors" and arcs:
        a = arcs[0]
        c = a.ocs().to_wcs(a.dxf.center)
        hinge, r = (c.x * f, c.y * f), a.dxf.radius * f * abs(e.dxf.xscale)
        ap = _pts(a, f)
        ends = [ap[0], ap[-1]]
        # the open leaf is the line drawn from the hinge to one end of the arc; the other end is the closed leaf
        lines = [_pts(x, f) for x in ents if x.dxftype() == "LINE"]
        open_end = next((q for q in ends for ln in lines if min(math.dist(ln[0], q), math.dist(ln[-1], q)) < 0.01
                         and min(math.dist(ln[0], hinge), math.dist(ln[-1], hinge)) < 0.01), None)
        if open_end is None:
            res["unrecognised"].append(dict(kind="door without open leaf line", block=name, handle=handle))
            return
        closed_end = ends[1] if open_end == ends[0] else ends[0]
        unit = lambda q: [round((q[0] - hinge[0]) / r, 6), round((q[1] - hinge[1]) / r, 6)]  # noqa: E731
        res["doors"].append(dict(block=name, handle=handle, hinge=list(hinge), w=r, d=unit(closed_end), n=unit(open_end)))
    elif cat == "doors":
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        res["slides"].append(dict(block=name, handle=handle, closed=[min(xs), min(ys), max(xs), max(ys)],
                                  open=None, note="sliding direction not drawn: confirm"))
    elif cat == "windows":
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        att = {a.dxf.tag.upper(): a.dxf.text for a in e.attribs}
        num = lambda k: float(att[k]) * f if k in att and re.fullmatch(r"[\d.]+", att[k]) else None  # noqa: E731
        h, sill = num("H"), num("DAVANZALE") if "DAVANZALE" in att else num("SILL")
        horizontal = max(xs) - min(xs) >= max(ys) - min(ys)
        res["windows"].append(dict(block=name, handle=handle, horizontal=horizontal,
                                   x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys),
                                   yc=(min(ys) + max(ys)) / 2, xc=(min(xs) + max(xs)) / 2,
                                   z0=sill, z1=(sill or 0) + h if h else None,
                                   note="" if h else "height and sill not in the drawing: profile defaults"))
    else:
        outline = unary_union([Polygon(_pts(x, f)).buffer(0) for x in ents
                               if x.dxftype() in ("LWPOLYLINE", "POLYLINE") and x.is_closed and len(_pts(x, f)) >= 3])
        if outline.is_empty:
            outline = Polygon(pts).convex_hull
        res["furniture"].append(dict(block=name, handle=handle, footprint=outline, rotation=e.dxf.rotation, type=None,
                                     front=_front(e, front) if front else None))


def _front(e, axis):
    """The block's front axis in plan: mirrored by negative scales, then turned by the insert rotation."""
    ax, ay = axis[0] * (1 if e.dxf.xscale >= 0 else -1), axis[1] * (1 if e.dxf.yscale >= 0 else -1)
    t = math.radians(e.dxf.rotation)
    return (round(ax * math.cos(t) - ay * math.sin(t), 6), round(ax * math.sin(t) + ay * math.cos(t), 6))


def _closer(walls, p0, p1):
    """Rectangle that closes the opening p0-p1 across its wall, as thick as the thinner wall stub beside it (the other
    may be widened by a perpendicular wall); None when no wall stands beside the opening."""
    L = math.dist(p0, p1)
    if L < 1e-6:
        return None
    d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    n = (-d[1], d[0])
    at = lambda a, b: (p0[0] + d[0] * a + n[0] * b, p0[1] + d[1] * a + n[1] * b)  # noqa: E731 - local axes
    rect = lambda a0, a1, b0, b1: Polygon([at(a0, b0), at(a1, b0), at(a1, b1), at(a0, b1)])  # noqa: E731
    spans = []
    for a0, a1 in ((-0.30, -0.02), (L + 0.02, L + 0.30)):
        stub = walls.intersection(rect(a0, a1, -0.40, 0.40))
        if not stub.is_empty:
            across = [(x - p0[0]) * n[0] + (y - p0[1]) * n[1] for g in getattr(stub, "geoms", [stub])
                      for x, y in getattr(g, "exterior", g).coords]
            spans.append((min(across), max(across)))
    if not spans:
        return None
    b0, b1 = min(spans, key=lambda t: t[1] - t[0])
    return rect(-0.30, L + 0.30, b0, b1)


def _rooms(res):
    """Rooms = the free space between walls, with every opening closed across its wall by a rectangle as thick as the
    wall beside it (_closer); the convex hull of the wall around the opening when that fails."""
    walls = res["walls"]
    if walls.is_empty:
        return
    spans = []
    for d in res["doors"]:
        h, w, dd = d["hinge"], d["w"], d["d"]
        spans.append(((h[0], h[1]), (h[0] + dd[0] * w, h[1] + dd[1] * w)))
    for s in res["slides"]:
        x0, y0, x1, y1 = s["closed"]
        spans.append(((x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)) if x1 - x0 >= y1 - y0 else
                     (((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)))
    for w in res["windows"]:
        spans.append(((w["x0"], w["yc"]), (w["x1"], w["yc"])) if w["horizontal"] else
                     ((w["xc"], w["y0"]), (w["xc"], w["y1"])))
    closers = []
    for p0, p1 in spans:
        c = _closer(walls, p0, p1)
        if c is None:
            c = walls.intersection(LineString([p0, p1]).buffer(0.35, cap_style=2)).convex_hull
        closers.append(c)
    solid = unary_union([walls] + closers)
    frame = box(*solid.bounds)
    free = frame.difference(solid)
    texts = [t for t in res["texts"] if not AREA_TEXT.match(t["text"])]
    for p in getattr(free, "geoms", [free]):
        if p.area < 0.5 or p.touches(frame.exterior) or p.intersects(frame.exterior):
            continue
        names = [t["text"] for t in texts if p.contains(Point(t["xy"]))]
        res["rooms"].append(dict(name=names[0] if names else None, footprint=p, area=p.area,
                                 note="" if names else "no room name inside"))


def to_json(res):
    def conv(v):
        if hasattr(v, "geom_type"):
            return mapping(v)
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        if isinstance(v, list):
            return [conv(x) for x in v]
        if isinstance(v, tuple):
            return [conv(x) for x in v]
        return v
    return conv(res)


if __name__ == "__main__":
    src = sys.argv[1]
    prof = json.load(open(sys.argv[sys.argv.index("--profile") + 1])) if "--profile" in sys.argv else None
    r = recognise(read(src), prof)
    print("layers:", {k: v for k, v in r["layers"].items() if v != "ignored"})
    print("walls %.1f m2, doors %d, slides %d, windows %d, furniture %d, rooms %d, unrecognised %d" % (
        r["walls"].area, len(r["doors"]), len(r["slides"]), len(r["windows"]), len(r["furniture"]), len(r["rooms"]),
        len(r["unrecognised"])))
    for rm in r["rooms"]:
        print("  room %-16s %.1f m2 %s" % (rm["name"], rm["area"], rm["note"]))
