"""Checks on the neutral model, ported from lib/interiors.py verify(): same categories, rows, order and wording.
Thresholds come with the model (RULES of the engine that exported it); docs/design-rules.md is their source."""
import collections
import fnmatch
import json
import math

import numpy
import shapely
from shapely.geometry import LineString, Polygon

from . import geom
from .rules import HABITABLE, THROUGH

VERIFIED, NON_COMPLIANT, NOT_VERIF, NOT_APPL = "VERIFIED", "NON-COMPLIANT", "NOT VERIFIABLE", "NOT APPLICABLE"
ACCEPTED = "ACCEPTED"
SEVERITY = ("blocking", "significant", "improvement")
CELL = 0.05


def _zone(ox, oy, d, n, da, db, z0, z1):
    """Box in local axes from (ox, oy): da along d, db along n (any direction, not only the plan axes)."""
    pts = [(ox + d[0] * a + n[0] * b, oy + d[1] * a + n[1] * b) for a, b in ((da[0], db[0]), (da[1], db[0]),
                                                                         (da[1], db[1]), (da[0], db[1]))]
    return [geom.Solid([geom.Band([pts], z0, z1)])]


class Model:
    def __init__(self, data):
        self.data = data
        self.name, self.H, self.interior, self.R = data["name"], data["height"], data["interior"], data["rules"]
        self.tol = self.R["tol"] / 1e9                       # rules keep FreeCAD units (mm3)
        sh = geom.shape
        self.walls = [(w["name"], sh(w["solids"])) for w in data["walls"]]
        self.check = [(o["item"], o["label"], sh(o["solids"]), o["group"]) for o in data["objects"]]
        self.named = {k: sh(v) for k, v in data["named"].items()}
        self.doc_names = set(data["doc_names"])
        self.doors = [dict(d, sweep=sh(d["sweep"]), leaf=sh(d["leaf"]), handle=sh(d["handle"]), probe=sh(d["probe"]))
                      for d in data["doors"]]
        self.slides = [dict(name=s["name"], shape=sh(s["open"]), closed=sh(s["closed"])) for s in data["slides"]]
        self.seats = data["seats"]
        self.access = [dict(a, zone=sh(a["zone"])) for a in data["access"]]
        self.rooms, self.tv, self.heights, self.elec = data["rooms"], data["tv"], data["heights"], set(data["elec"])
        self.windows = [dict(w, glass=sh(w["glass"])) for w in data["windows"]]
        self.wet = [dict(w, zone=sh(w["zone"])) for w in data["wet"]]
        self.private, self.views, self.reqs = data["private"], data["views"], data["requirements"]
        self.viewpoints, self.intimate = data.get("viewpoints", []), data.get("intimate", [])
        self.accepted = data.get("accepted", [])
        self.notverif = data["not_verifiable"]
        self.start = tuple(data["start"]) if data["start"] else None
        self.targets = {k: tuple(v) for k, v in data["targets"].items()}
        self.routes, self.clear = data["routes"], data["clearances"]
        self.results = []

    @classmethod
    def load(cls, path):
        return cls(json.load(open(path)))

    def _r(self, cat, elem, measure, threshold, status, sev, method, note=""):
        if status == VERIFIED and sev != "improvement":
            sev = ""
        self.results.append(dict(cat=cat, elem=elem, measure=measure, threshold=threshold, status=status,
                                 sev=sev, method=method, note=note))

    def hits_of(self, sh, skip_items=(), walls=True):
        out = []
        for item, lbl, s, _g in self.check:
            if item in skip_items or not geom.touch(sh, s):
                continue
            v = geom.common_volume(sh, s)
            if v > self.tol:
                out.append("%s (%.0f cm3)" % (lbl, v * 1e6))
        if walls:
            for wname, ws in self.walls:
                if geom.touch(sh, ws) and geom.common_volume(sh, ws) > self.tol:
                    out.append("WALL " + wname)
        return out

    def items(self):
        """Aggregated bounding box per piece of furniture (item)."""
        agg = {}
        for item, _l, sh, g in self.check:
            b = geom.bounds(sh)
            a = agg.setdefault(item, list(b) + [g])
            a[:6] = [min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]), max(a[4], b[4]), max(a[5], b[5])]
        return agg

    def room_of(self, x, y):
        for r in self.rooms:
            for x0, y0, x1, y1 in r["rects"]:
                if x0 <= x <= x1 and y0 <= y <= y1:
                    return r["name"]
        return "-"

    def entered_from(self, nx, ny, dist, k, room):
        """Room the route from the entrance comes from when it enters `room` (same walk as the FreeCAD engine, L23)."""
        X0, Y0 = self.interior[0], self.interior[1]
        while dist[k] > 0:
            i, j = k % nx, k // nx
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if 0 <= a < nx and 0 <= b < ny and dist[b * nx + a] == dist[k] - 1:
                    k = b * nx + a
                    break
            rn = self.room_of(X0 + (k % nx + 0.5) * CELL, Y0 + (k // nx + 0.5) * CELL)
            if rn not in (room, "-"):
                return rn
        return "the entrance"

    # 1) leaves, windows, sliding doors; 2) handles; 3) reveals
    def openings(self):
        NC, tol = NON_COMPLIANT, self.tol
        for dd in self.doors:
            hits = self.hits_of(dd["sweep"])
            for o in self.doors:
                if o["name"] != dd["name"] and geom.touch(dd["sweep"], o["sweep"]) \
                        and geom.common_volume(dd["sweep"], o["sweep"]) > tol:
                    hits.append("%s %s" % (o["kind"], o["name"]))
            for sl in self.slides:
                if geom.common_volume(dd["sweep"], sl["shape"]) > tol or geom.common_volume(dd["sweep"], sl["closed"]) > tol:
                    hits.append("sliding " + sl["name"])
            self._r("Openings", dd["name"], "collisions: " + (", ".join(hits) if hits else "none"), "clear trajectory",
                    NC if hits else VERIFIED, "blocking", "3D intersection of the volume swept by the leaf 0-90 degrees")
        for sl in self.slides:
            hits = self.hits_of(sl["shape"])
            hits += ["%s %s" % (d["kind"], d["name"]) for d in self.doors if geom.common_volume(sl["shape"], d["sweep"]) > tol]
            self._r("Openings", sl["name"] + " (open)", "collisions: " + (", ".join(hits) if hits else "none"),
                    "clear travel", NC if hits else VERIFIED, "blocking", "3D intersection of the leaf in open position")
        R = self.R
        for dd in self.doors:
            if dd["handle"] is None:
                continue
            h = self.hits_of(dd["handle"])
            self._r("Handles", dd["name"], ", ".join(h) if h else "clear", "%.0f cm clear at 90 degrees" % (R["handle"] * 100),
                    NC if h else VERIFIED, "significant", "3D intersection of the handle with the leaf open")
            p = [w for w in self.hits_of(dd["probe"]) if w.startswith("WALL")]
            self._r("Reveals", dd["name"], ", ".join(p) if p else ">= threshold", ">= %.0f cm" % (R["reveal"] * 100),
                    NC if p else VERIFIED, "significant", "probe between opening edge and perpendicular wall")

    # 4) seats: from the surface edge to the first obstacle, along the seat direction
    def seat_checks(self):
        R = self.R
        for s in self.seats:
            (ox, oy), (dx, dy), hw, own = s["edge"], s["dir"], s["hw"], set(s["own"])
            zone = _zone(ox, oy, (dx, dy), (-dy, dx), (0.002, 1.5), (-hw, hw), 0.05, 1.00)
            zb = zone[0].bands[0]
            free = 1.5
            for it, sh in [(it, sh) for it, _l, sh, _g in self.check] + [(w, ws) for w, ws in self.walls]:
                if it in own or not geom.touch(zone, sh) or geom.common_volume(zone, sh) <= self.tol:
                    continue
                for sol in sh:
                    for b in sol.bands:
                        if min(b.z1, zb.z1) - max(b.z0, zb.z0) <= 0:
                            continue
                        c = zb.poly.intersection(b.poly)
                        if c.is_empty:
                            continue
                        for g in getattr(c, "geoms", [c]):
                            for x, y in getattr(g, "exterior", g).coords:
                                free = min(free, (x - ox) * dx + (y - oy) * dy)
            ok, low = free >= R["seat_min"], free < R["seat_comfort"]
            self._r("Seats", s["name"], "%.0f cm" % (free * 100),
                    "min %.0f (stand up) / comfort %.0f (walk behind)" % (R["seat_min"] * 100, R["seat_comfort"] * 100),
                    VERIFIED if ok else NON_COMPLIANT, "blocking" if not ok else ("improvement" if low else ""),
                    "surface edge -> first obstacle (max 150)",
                    "below comfort target: nobody can walk behind a seated person" if ok and low else "")

    # 5) clearances and access zones
    def clearances(self):
        for lbl, a, b, mn, cf in self.clear:
            d = geom.distance(self.named[a], self.named[b])
            ok = d >= mn - 1e-6
            low = cf and d < cf - 1e-6                        # same tolerance as the minimum: 110 cm meets 110
            thr = "min %.0f" % (mn * 100) + (" / comfort %.0f" % (cf * 100) if cf else "")
            self._r("Clearances", lbl, "%.0f cm" % (d * 100), thr,
                    VERIFIED if ok else NON_COMPLIANT, "blocking" if not ok else ("improvement" if low else ""),
                    "minimum plan distance %s - %s" % (a, b), "below comfort target" if ok and low else "")
        for a in self.access:
            h = self.hits_of(a["zone"], skip_items=set(a["own"]))
            ok = not h and a["depth"] >= self.R["access"] - 1e-6
            self._r("Access zones", a["label"], ("obstacles: " + ", ".join(h)) if h else "clear, %.0f cm" % (a["depth"] * 100),
                    ">= %.0f cm clear" % (self.R["access"] * 100), VERIFIED if ok else NON_COMPLIANT, "blocking",
                    "3D intersection of the zone in front of the unit")

    # plan grid for routes and occupancy: same rectangles, inflation and search as the FreeCAD engine; walls that are not
    # rectangles (an imported plan has one polygon per wall run, an L or a U) are rasterised as polygons, not as boxes
    def obstacle_rects(self, zmax=1.0):
        rects = []
        for _n, ws in self.walls:
            for s in ws:
                for b in s.bands:
                    if b.z0 <= 1.0 < b.z1:                    # walls cut at 1 m, as in the FreeCAD engine
                        for p in getattr(b.poly, "geoms", [b.poly]):
                            rects.append(p.bounds if abs(p.area - p.envelope.area) < 1e-9 else p)
        for _item, _l, sh, _g in self.check:
            for s in sh:
                bb = s.bounds
                if bb[2] < zmax and bb[5] > 0.05:
                    p = s.bands[0].poly
                    if self.data.get("plan_2d") and abs(p.area - p.envelope.area) > 1e-6:
                        rects.append(p)               # one outline per block (an L sofa, a bed with its headboard)
                    else:
                        rects.append((bb[0], bb[1], bb[3], bb[4]))
        for dd in self.doors:
            if dd["leaf"] is not None:
                bb = geom.bounds(dd["leaf"])
                rects.append((bb[0], bb[1], bb[3], bb[4]))
        for sl in self.slides:
            bb = geom.bounds(sl["shape"])
            rects.append((bb[0], bb[1], bb[3], bb[4]))
        return rects

    def grid(self, rects, inflate):
        X0, Y0, X1, Y1 = self.interior
        nx, ny = int(round((X1 - X0) / CELL)), int(round((Y1 - Y0) / CELL))
        g = bytearray(nx * ny)
        for r in rects:
            if hasattr(r, "geom_type"):                       # polygon: cells whose centre lies in the inflated shape
                p = r.buffer(inflate, join_style=2) if inflate else r
                bx0, by0, bx1, by1 = p.bounds
                i0, i1 = max(0, int((bx0 - X0) / CELL) - 1), min(nx - 1, int((bx1 - X0) / CELL) + 1)
                j0, j1 = max(0, int((by0 - Y0) / CELL) - 1), min(ny - 1, int((by1 - Y0) / CELL) + 1)
                ii, jj = numpy.meshgrid(numpy.arange(i0, i1 + 1), numpy.arange(j0, j1 + 1))
                inside = shapely.intersects_xy(p, X0 + (ii + 0.5) * CELL, Y0 + (jj + 0.5) * CELL)
                for i, j in zip(ii[inside], jj[inside]):
                    g[int(j) * nx + int(i)] = 1
                continue
            x0, y0, x1, y1 = r[0] - inflate, r[1] - inflate, r[2] + inflate, r[3] + inflate
            i0 = max(0, int(math.ceil((x0 - X0) / CELL - 0.5)))
            i1 = min(nx - 1, int(math.floor((x1 - X0) / CELL - 0.5)))
            j0 = max(0, int(math.ceil((y0 - Y0) / CELL - 0.5)))
            j1 = min(ny - 1, int(math.floor((y1 - Y0) / CELL - 0.5)))
            for j in range(j0, j1 + 1):
                row = j * nx
                for i in range(i0, i1 + 1):
                    g[row + i] = 1
        return g, nx, ny

    def cell(self, x, y, nx, ny):
        X0, Y0 = self.interior[0], self.interior[1]
        i, j = int((x - X0) / CELL), int((y - Y0) / CELL)
        return (i, j) if 0 <= i < nx and 0 <= j < ny else None

    def bfs(self, g, nx, ny, start):
        dist = [-1] * (nx * ny)
        c = self.cell(start[0], start[1], nx, ny)
        if c is None or g[c[1] * nx + c[0]]:
            return dist
        q = collections.deque([c])
        dist[c[1] * nx + c[0]] = 0
        while q:
            i, j = q.popleft()
            d = dist[j * nx + i]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if 0 <= a < nx and 0 <= b < ny:
                    k = b * nx + a
                    if not g[k] and dist[k] < 0:
                        dist[k] = d + 1
                        q.append((a, b))
        return dist

    # 6) routes from the entrance (5 cm grid, person 60 cm wide)
    def route_checks(self):
        NC = NON_COMPLIANT
        self._rects = self.obstacle_rects()
        g, nx, ny = self.grid(self._rects, self.R["person_radius"])
        self._nx, self._ny = nx, ny
        method = "5 cm grid, obstacles inflated by 30 cm"
        self._dist_start = self.bfs(g, nx, ny, self.start) if self.start else None
        if self.start:
            dist = self._dist_start
            for lbl, (x, y) in self.targets.items():
                c = self.cell(x, y, nx, ny)
                k = c[1] * nx + c[0] if c else None
                if k is None or g[k]:
                    self._r("Routes", lbl, "point inside a footprint", "reachable from the entrance at 60 cm", NC,
                            "blocking", method, "move the point or the furniture")
                elif dist[k] < 0:
                    self._r("Routes", lbl, "unreachable", "reachable from the entrance at 60 cm", NC, "blocking", method)
                else:
                    self._r("Routes", lbl, "%.1f m from the entrance" % (dist[k] * CELL), "reachable at 60 cm",
                            VERIFIED, "", method)
        for lbl, src, dst in self.routes:
            dist = self.bfs(g, nx, ny, self.targets[src])
            c = self.cell(*self.targets[dst], nx, ny)
            k = c[1] * nx + c[0]
            ok = dist[k] >= 0
            self._r("Routes", lbl, ("%.1f m" % (dist[k] * CELL)) if ok else "interrupted", "continuous at 60 cm",
                    VERIFIED if ok else NC, "" if ok else "blocking", method)

    # 7) rooms: daylight ratio and occupancy
    def rooms_checks(self):
        R, NC = self.R, NON_COMPLIANT
        occ, onx, ony = self.grid(self.obstacle_rects(zmax=0.30), 0.0)
        X0, Y0 = self.interior[0], self.interior[1]
        for r in self.rooms:
            win = [w for w in self.windows if w["room"] == r["name"]]
            glazed = sum((w["x1"] - w["x0"]) * (w["z1"] - w["z0"]) for w in win)
            if r["habitable"]:
                need = r["area"] * R["daylight"]
                self._r("Light and air", r["name"], "%.1f m2 glazed" % glazed, ">= %.1f m2 (1/8 of %.1f)" % (need, r["area"]),
                        VERIFIED if glazed >= need else NC, "blocking" if glazed < need else "",
                        "sum of net window areas serving the room")
                cells = tot = 0
                for x0, y0, x1, y1 in r["rects"]:
                    for j in range(int((y0 - Y0) / CELL), int((y1 - Y0) / CELL)):
                        for i in range(int((x0 - X0) / CELL), int((x1 - X0) / CELL)):
                            if 0 <= i < onx and 0 <= j < ony:
                                tot += 1
                                cells += occ[j * onx + i]
                ratio = cells / tot if tot else 0
                low = ratio < R["occupancy_min"] - 1e-6
                self._r("Light and air", r["name"] + " - occupancy", "%.0f%% of the floor" % (ratio * 100),
                        "%.0f-%.0f%%" % (R["occupancy_min"] * 100, R["occupancy"] * 100), NC if low else VERIFIED,
                        "significant" if low else ("improvement" if ratio > R["occupancy"] else ""),
                        "floor-standing footprint on a 5 cm grid",
                        "under-furnished: only what a check needs? (L26)" if low else
                        ("crowded room" if ratio > R["occupancy"] else ""))
            elif r["kind"] == "bathroom":
                self._r("Light and air", r["name"], "window %.2f m2" % glazed if win else "no window",
                        "window or mechanical ventilation", VERIFIED if win else NOT_VERIF, "" if win else "significant",
                        "presence of an opening window", "" if win else "design mechanical ventilation")
            else:
                self._r("Light and air", r["name"], "-", "non-habitable room", NOT_APPL, "", "-")

    # 7b) programme by room kind (L24, L26); imported plans without a kind are skipped
    def programme(self):
        R, NC = self.R, NON_COMPLIANT
        centres = [((x0 + x1) / 2, (y0 + y1) / 2) for x0, y0, _z0, x1, y1, _z1, _g in self.items().values()]
        for r in self.rooms:
            k = r.get("kind", "")
            if k in R["min_area"]:
                need = R["min_area"][k]
                ok = r["area"] >= need - 1e-6
                self._r("Programme", r["name"] + " - area", "%.1f m2" % r["area"],
                        ">= %.1f m2 (%s, indicative)" % (need, k.replace("_", " ")), VERIFIED if ok else NC,
                        "" if ok else "significant", "net floor area by room kind")
            if k in R["service_area"]:
                lim = R["service_area"][k] * R["service_factor"]
                ok = r["area"] <= lim + 1e-6
                self._r("Programme", r["name"] + " - area", "%.1f m2" % r["area"],
                        "<= %.1f m2 (%.0f x %.1f reference)" % (lim, R["service_factor"], R["service_area"][k]),
                        VERIFIED if ok else NC, "" if ok else "significant",
                        "net floor area against the reference of its contents",
                        "" if ok else "sized on the leftover, not on its contents (L24)")
            if k and k not in HABITABLE and k != "corridor":
                n = sum(1 for cx, cy in centres if self.room_of(cx, cy) == r["name"])
                self._r("Programme", r["name"] + " - contents", "%d objects" % n, ">= 1 object", VERIFIED if n else NC,
                        "" if n else "significant", "furniture whose centre lies in the room",
                        "" if n else "empty room: give it its programme or declare it (L26)")

    # 8) TV / window; 9) ergonomics; 10) assembly
    def tv_checks(self):
        R = self.R
        for name in self.tv:
            tvs = self.named[name]
            b = geom.bounds(tvs)
            cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
            worst = None
            for w in self.windows:
                d = geom.distance(tvs, w["glass"])
                same = abs((cy if w.get("axis", "x") == "x" else cx) - w["yc"]) < 0.5   # yc: the wall's centre line
                if worst is None or (same, -d) > (worst[0], -worst[1]):
                    worst = (same, d, w["name"])
            if worst is None:
                self._r("Brief constraints", "TV " + name, "no windows", "TV away from windows", VERIFIED, "", "-")
            else:
                same, d, wn = worst
                bad = same and d < R["tv_window"]
                self._r("Brief constraints", "TV " + name, "%.2f m from %s (%s)" % (d, wn, "same wall" if same else "other wall"),
                        "not above/in front of/next to a window on the same wall (>= %.1f m)" % R["tv_window"],
                        NON_COMPLIANT if bad else VERIFIED, "blocking" if bad else ("improvement" if d < 1.5 else ""),
                        "3D distance TV - glass", "check reflections" if not bad and d < 1.5 else "")

    def ergonomics(self):
        lo, hi = self.R["seat_height"]
        for lbl, zp, zs in self.heights:
            dz = zp - zs
            ok = lo <= dz <= hi
            self._r("Ergonomics", lbl, "surface %.2f / seat %.2f (diff %.2f)" % (zp, zs, dz), "diff %.2f-%.2f" % (lo, hi),
                    VERIFIED if ok else NON_COMPLIANT, "" if ok else "significant", "design heights")

    def assembly(self):
        m = self.R["assembly_margin"]
        for item, (x0, y0, z0, x1, y1, z1, _g) in self.items().items():
            h = z1 - z0
            if h <= 2.0:
                continue
            diag = math.hypot(h, min(x1 - x0, y1 - y0))
            ok = diag <= self.H - m
            self._r("Assembly", item, "diagonal %.2f m" % diag, "<= %.2f (room height - margin)" % (self.H - m),
                    VERIFIED if ok else NON_COMPLIANT, "" if ok else "significant", "hypotenuse of height x depth",
                    "" if ok else "assemble in place or in modules")

    # 10a) wet zones; 10b) privacy; 10c) sightlines
    def safety(self):
        for w in self.wet:
            h = [lb for it, lb, sh, _g in self.check if it in self.elec and geom.touch(w["zone"], sh)
                 and geom.common_volume(w["zone"], sh) > self.tol]
            self._r("Safety", w["label"], ("electrical items inside: " + ", ".join(h)) if h else "no electrical item",
                    "no electrical item in the splash zone", NON_COMPLIANT if h else VERIFIED, "blocking" if h else "",
                    "3D intersection of the splash zone with items declared electrical()")

    def privacy(self):
        if self.start and self.private:
            priv = [tuple(rc) for r in self.rooms if r["name"] in self.private for rc in r["rects"]]
            gp, nx, ny = self.grid(self._rects + priv, self.R["person_radius"])
            dist_p = self.bfs(gp, nx, ny, self.start)
            for lbl, (x, y) in self.targets.items():
                if self.room_of(x, y) in self.private:
                    continue
                c = self.cell(x, y, nx, ny)
                k = c[1] * nx + c[0]
                if self._dist_start[k] < 0:
                    continue          # unreachable at all: already a Routes failure
                ok = dist_p[k] >= 0
                self._r("Privacy", lbl, "reachable without crossing %s" % ", ".join(self.private) if ok else
                        "reachable only through " + ", ".join(self.private), "shared zones never through a private room",
                        VERIFIED if ok else NON_COMPLIANT, "" if ok else "significant", "route search with private rooms blocked")
        # 10b2) bedrooms and bathrooms entered from circulation, never through a living room (L23)
        if self.start:
            nx, ny = self._nx, self._ny
            for r in self.rooms:
                if r.get("kind", "") not in ("bedroom", "single_bedroom", "bathroom"):
                    continue
                inside = [(lbl, xy) for lbl, xy in self.targets.items() if self.room_of(*xy) == r["name"]]
                if not inside:
                    continue
                lbl, (x, y) = inside[0]
                c = self.cell(x, y, nx, ny)
                k = c[1] * nx + c[0] if c else None
                if k is None or self._dist_start[k] < 0:
                    continue
                via = self.entered_from(nx, ny, self._dist_start, k, r["name"])
                bad = next((q.get("kind", "") for q in self.rooms if q["name"] == via), "") in THROUGH
                self._r("Privacy", r["name"] + ": entered from", via, "a hall, corridor or stair hall, never a living room",
                        NON_COMPLIANT if bad else VERIFIED, "significant" if bad else "",
                        "room before the door on the route from the entrance (to %s)" % lbl,
                        "the living room is a corridor (L23)" if bad else "")

        def seen(ex, ey, ez, b):
            p1 = ((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2)
            return [w for w, ws in self.walls if _segment_hits((ex, ey, ez), p1, ws)]

        for v in self.views:
            blocked = seen(v["eye"][0], v["eye"][1], v["eye_z"], geom.bounds(self.named[v["target"]]))
            self._r("Privacy", v["label"], ("blocked by " + blocked[0]) if blocked else "visible", "not visible with doors open",
                    VERIFIED if blocked else NON_COMPLIANT, "" if blocked else "significant",
                    "3D sightline eye -> object centre vs walls")
        # 10c2) intimate objects from every viewpoint (L25); eyes in the object's own room do not count
        for target in self.intimate:
            if target not in self.named:
                self._r("Privacy", target + " from viewpoints", "object missing", "intimate object exists", NON_COMPLIANT,
                        "blocking", "object lookup")
                continue
            b = geom.bounds(self.named[target])
            home = self.room_of((b[0] + b[3]) / 2, (b[1] + b[4]) / 2)
            for vp in self.viewpoints:
                eyes = [e for e in vp["eyes"] if self.room_of(e[0], e[1]) != home]
                if not eyes:
                    continue
                vis = [who for ex, ey, ez, who in eyes if not seen(ex, ey, ez, b)]
                self._r("Privacy", "%s from %s" % (target, vp["label"]),
                        ("visible from " + ", ".join(vis)) if vis else "screened by walls", "not visible with doors open",
                        NON_COMPLIANT if vis else VERIFIED, "significant" if vis else "",
                        "3D sightline eye -> object centre vs walls (%d eyes)" % len(eyes))

    # 10d) robustness: margins smaller than the placement tolerance of two elements
    def robustness(self):
        tol2 = 2 * self.R["placement"]
        fragile = []
        for x in self.results:
            if x["cat"] in ("Seats", "Clearances") and x["status"] == VERIFIED:
                meas = float(x["measure"].split()[0]) / 100
                mn = float(x["threshold"].split()[1]) / 100
                if meas - mn < tol2 - 1e-6:
                    fragile.append((x["cat"] + "/" + x["elem"], meas - mn))
        for dd in self.doors:
            b = geom.bounds(dd["sweep"])
            zone = (b[0] - tol2, b[1] - tol2, b[2] - tol2, b[3] + tol2, b[4] + tol2, b[5] + tol2)
            near = min([geom.distance(dd["sweep"], sh) for it, _l, sh, _g in self.check
                        if it != dd["own"] and geom._touch(zone, geom.bounds(sh))] or [9])
            if near < tol2 and not self.hits_of(dd["sweep"], walls=False):
                fragile.append(("Openings/" + dd["name"], near))
        for elem, m in fragile:
            self._r("Robustness", elem, "margin %.0f cm" % (m * 100), ">= %.0f cm (2 x placement tolerance)" % (tol2 * 100),
                    NON_COMPLIANT, "significant", "measure - minimum, or swept leaf - nearest object",
                    "works only with near-zero tolerance: widen it")
        if not fragile:
            self._r("Robustness", "Seats, clearances, door swings", "all margins >= %.0f cm" % (tol2 * 100),
                    "no fragile measure", VERIFIED, "", "measure - minimum")

    # 11) interpenetrations
    def geometry(self):
        pairs = []
        C = self.check
        stacked = {frozenset(p) for p in self.data.get("stacked", [])}   # a 2D plan draws a chair under its table
        for i in range(len(C)):
            for j in range(i + 1, len(C)):
                a, b = C[i], C[j]
                if a[0] != b[0] and frozenset((a[0], b[0])) not in stacked and geom.touch(a[2], b[2]) \
                        and geom.common_volume(a[2], b[2]) > self.tol:
                    pairs.append("%s <-> %s" % (a[1], b[1]))
        for _item, lbl, sh, _g in self.check:
            for wname, ws in self.walls:
                if geom.touch(sh, ws) and geom.common_volume(sh, ws) > self.tol:
                    pairs.append("%s inside %s" % (lbl, wname))
        self._r("Geometry", "Furniture/wall interpenetrations", ", ".join(pairs) if pairs else "none", "none",
                NON_COMPLIANT if pairs else VERIFIED, "blocking" if pairs else "", "pairwise 3D intersection")

    # 11b) client acceptances (L28)
    def acceptance(self):
        NC = NON_COMPLIANT
        for ac in self.accepted:
            hit = [x for x in self.results if x["status"] == NC
                   and fnmatch.fnmatch("%s/%s" % (x["cat"], x["elem"]), ac["pattern"])]
            for x in hit:
                x["status"] = ACCEPTED
                x["note"] = (x["note"] + "; " if x["note"] else "") + "accepted by %s on %s: %s" % (
                    ac["by"], ac["date"], ac["reason"])
            self._r("Acceptance", ac["pattern"],
                    "%d result(s) accepted by %s on %s" % (len(hit), ac["by"], ac["date"]) if hit else "no failing check matched",
                    ">= 1 NON-COMPLIANT result", VERIFIED if hit else NC, "" if hit else "significant",
                    "pattern against the results",
                    ac["reason"] if hit else "stale acceptance: the defect is gone or the pattern is wrong (L28)")

    # 12) requirements traceability (brief -> design -> checks)
    def requirements(self):
        NC = NON_COMPLIANT
        for rq in self.reqs:
            missing = [o for o in rq["satisfied_by"] if o not in self.doc_names]
            linked = [x for x in self.results if any(fnmatch.fnmatch("%s/%s" % (x["cat"], x["elem"]), p)
                                                     for p in rq["verified_by"])]
            failed = [x for x in linked if x["status"] == NC]
            elem = "%s %s" % (rq["id"], rq["text"])
            if missing:
                self._r("Requirements", elem, "missing objects: " + ", ".join(missing), "implemented", NC, "blocking",
                        "object lookup")
            elif failed:
                self._r("Requirements", elem, "%d/%d linked checks failed" % (len(failed), len(linked)),
                        "all linked checks pass", NC, min((x["sev"] for x in failed), key=SEVERITY.index), "traceability",
                        ", ".join("%s/%s" % (x["cat"], x["elem"]) for x in failed))
            elif rq["manual"] is True:
                self._r("Requirements", elem, "judged in review", "-", NOT_VERIF, "", "manual: review-layout / pre-mortem")
            elif rq["manual"]:
                ok = rq.get("manual_ok", False)          # resolved by the exporter (the core has no project folder)
                self._r("Requirements", elem, "judged in %s" % rq["manual"] if ok else
                        "review %s missing or without %s" % (rq["manual"], rq["id"]), "review file citing the id",
                        VERIFIED if ok else NC, "" if ok else "significant", "manual: review file")
            elif not linked:
                self._r("Requirements", elem, "no linked check", ">= 1 automatic check", NC, "significant", "traceability",
                        "add a check or mark the requirement manual")
            else:
                self._r("Requirements", elem, "%d linked checks passed" % len(linked), "all linked checks pass", VERIFIED, "",
                        "traceability")
        for cat, reason in self.notverif:
            self._r("Not verifiable", cat, "-", "-", NOT_VERIF, "significant", "-", reason)

    def verify(self):
        self.results = []
        self.openings()
        self.seat_checks()
        self.clearances()
        self.route_checks()
        self.rooms_checks()
        self.programme()
        self.tv_checks()
        self.ergonomics()
        self.assembly()
        self.safety()
        self.privacy()
        self.robustness()
        self.geometry()
        self.acceptance()
        self.requirements()
        return self.results


def _segment_hits(p0, p1, sh, eps=0.001):
    """3D segment p0-p1 against a 2.5D shape: for each band, the part of the segment inside its z range,
    tested in plan (within 1 mm, as the FreeCAD engine's distToShape < 1 mm)."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    for sol in sh:
        for b in sol.bands:
            if z1 == z0:
                if not b.z0 <= z0 <= b.z1:
                    continue
                ta, tb = 0.0, 1.0
            else:
                ta, tb = sorted(((b.z0 - z0) / (z1 - z0), (b.z1 - z0) / (z1 - z0)))
                ta, tb = max(ta, 0.0), min(tb, 1.0)
                if ta > tb:
                    continue
            seg = LineString([(x0 + (x1 - x0) * ta, y0 + (y1 - y0) * ta), (x0 + (x1 - x0) * tb, y0 + (y1 - y0) * tb)]) \
                if tb > ta else Polygon()
            if seg.is_empty:
                continue
            if seg.distance(b.poly) < eps:
                return True
    return False
