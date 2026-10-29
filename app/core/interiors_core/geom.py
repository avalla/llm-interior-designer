"""2.5D geometry: a solid is a list of bands (plan polygon, z0, z1); a shape is a list of solids.
Every shape the checks use is made of vertical prisms, so volumes and distances are exact:
  common volume = sum of area(Pa & Pb) x z overlap;  distance = min of hypot(plan distance, z gap)."""
import math

from shapely.geometry import Polygon


class Band:
    __slots__ = ("poly", "rings", "z0", "z1", "bounds")

    def __init__(self, rings, z0, z1):
        self.rings = rings
        poly = Polygon()
        for r in rings:                    # outer boundaries and holes alike: symmetric difference builds both
            p = Polygon(r).buffer(0)
            poly = poly.symmetric_difference(p)
        self.poly = poly if poly.is_valid else poly.buffer(0)
        self.z0, self.z1 = z0, z1
        x0, y0, x1, y1 = self.poly.bounds if not self.poly.is_empty else (0, 0, 0, 0)
        self.bounds = (x0, y0, z0, x1, y1, z1)


class Solid:
    __slots__ = ("bands", "bounds")

    def __init__(self, bands):
        self.bands = bands
        b = [x.bounds for x in bands]
        self.bounds = (min(x[0] for x in b), min(x[1] for x in b), min(x[2] for x in b),
                       max(x[3] for x in b), max(x[4] for x in b), max(x[5] for x in b)) if b else None


def shape(data):
    """JSON (list of solids, each a list of {rings, z}) -> list of Solid; None stays None."""
    if data is None:
        return None
    return [Solid([Band(b["rings"], b["z"][0], b["z"][1]) for b in sol]) for sol in data if sol]


def bounds(sh):
    b = [s.bounds for s in sh]
    return (min(x[0] for x in b), min(x[1] for x in b), min(x[2] for x in b),
            max(x[3] for x in b), max(x[4] for x in b), max(x[5] for x in b))


def _touch(a, b):
    """Bounding boxes intersect or touch (as FreeCAD BoundBox.intersect)."""
    return a[0] <= b[3] and b[0] <= a[3] and a[1] <= b[4] and b[1] <= a[4] and a[2] <= b[5] and b[2] <= a[5]


def touch(sa, sb):
    return _touch(bounds(sa), bounds(sb))


def common_volume(sa, sb):
    v = 0.0
    for a in sa:
        for b in sb:
            if not _touch(a.bounds, b.bounds):
                continue
            for ba in a.bands:
                for bb in b.bands:
                    dz = min(ba.z1, bb.z1) - max(ba.z0, bb.z0)
                    if dz > 0 and _touch(ba.bounds, bb.bounds):
                        v += ba.poly.intersection(bb.poly).area * dz
    return v


def distance(sa, sb):
    d = math.inf
    for a in sa:
        for b in sb:
            for ba in a.bands:
                for bb in b.bands:
                    gz = max(0.0, max(ba.z0, bb.z0) - min(ba.z1, bb.z1))
                    d = min(d, math.hypot(ba.poly.distance(bb.poly), gz))
    return d
