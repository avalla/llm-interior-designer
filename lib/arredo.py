"""Motore per progetti di interni in FreeCAD, eseguito via MCP (execute_code).

Un progetto (progetti/<nome>/progetto.py) chiama nuovo(), disegna con wall/hinged/sliding/window/box/...,
registra usi e vincoli (seduta, zona_prelievo, passaggio, destinazione, stanza, tv, ...), poi verifica()
ed eventualmente esporta(). Coordinate in metri, y verso nord. Soglie: docs/regole-progettuali.md.
"""
import FreeCAD as App
import Part
import collections
import datetime
import json
import math
import os

V = App.Vector
S = 1000.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Fonte unica delle soglie numeriche: docs/regole-progettuali.md. Tenere i due allineati.
REGOLE = dict(
    telaio=0.05, telaio_blindata=0.075,      # stipite/controtelaio per lato
    spalletta=0.10,                          # filo foro -> muro ortogonale lato cerniera
    maniglia=0.07,                           # sporgenza maniglia con anta a 90 gradi
    seduta_min=0.75, seduta_comfort=0.90,    # bordo piano -> ostacolo: alzarsi / passare dietro chi siede
    prelievo=0.70,                           # libero davanti ad armadi e vani
    raggio_persona=0.30,                     # percorsi: larghezza minima 60 cm
    rai=1 / 8,                               # superficie finestrata / pavimento, locali abitabili
    occupazione=0.40,                        # impronta arredi / pavimento oltre cui il locale e' affollato
    tv_finestra=1.0,                         # distanza minima TV - finestra sulla stessa parete
    altezza_seduta=(0.25, 0.32),             # piano - seduta
    montaggio_margine=0.02,                  # diagonale di raddrizzamento < altezza locale - margine
    tol=1000.0,                              # 1 cm3, sotto e' contatto
)

COL = dict(
    WALL=(0.97, 0.97, 0.96), WHITE=(0.95, 0.95, 0.94), OAK=(0.78, 0.64, 0.46), FLOOR=(0.85, 0.74, 0.58),
    TILE=(0.80, 0.80, 0.79), BLACK=(0.13, 0.13, 0.14), GREY=(0.58, 0.59, 0.61), GLASS=(0.72, 0.86, 0.95),
    FRAME=(0.62, 0.52, 0.40), STEEL=(0.76, 0.77, 0.79), SAGE=(0.60, 0.68, 0.58), GREEN=(0.33, 0.52, 0.30),
    TERRA=(0.74, 0.47, 0.36), DARK=(0.30, 0.30, 0.32), RUG=(0.88, 0.86, 0.82),
)

NON_VERIFICABILI = [
    ("Impianti", "scarichi, adduzioni, prese, quadri, climatizzazione non modellati"),
    ("Strutture", "architravi, portanza, demolibilita' dei tramezzi: servono rilievo e strutturista"),
    ("Normativa locale", "regolamento edilizio comunale e requisiti di accessibilita' da verificare con il tecnico"),
    ("Prodotti", "ingombri indicativi: sostituire con schede tecniche dei produttori"),
    ("Luce, acustica, comfort termico", "nessun dato o metodo quantitativo applicato"),
    ("Trasporto arredi", "ascensore, scale e percorsi condominiali non noti"),
]

GRAVITA = ("bloccante", "rilevante", "migliorativa")


class _Stato:
    pass


ST = _Stato()


# ============================== documento e primitive ==============================
def nuovo(nome, cartella, interno, altezza=2.70):
    """Crea il documento. interno = (x0, y0, x1, y1) del filo interno dei muri perimetrali."""
    if App.listDocuments().get(nome):
        App.closeDocument(nome)
    ST.doc = App.newDocument(nome)
    ST.nome, ST.dir, ST.H, ST.interno = nome, cartella, altezza, interno
    ST.groups, ST.CHECK, ST.WALLS, ST.OPEN = {}, [], [], []
    ST.DOORS, ST.SLIDES, ST.SEATS, ST.OPENINGS = [], [], [], []
    ST.FRONT, ST.PASS, ST.TARGETS, ST.PATHS = [], [], {}, []
    ST.START, ST.ROOMS, ST.WINDOWS, ST.TV, ST.HEIGHTS = None, [], [], [], []
    ST.NONVER = list(NON_VERIFICABILI)
    ST.ANN = dict(quote=[], testi=[], note="")
    ST.risultati = []
    return ST.doc


def grp(n):
    if n not in ST.groups:
        ST.groups[n] = ST.doc.addObject("App::DocumentObjectGroup", n)
    return ST.groups[n]


def add(name, shape, color, g, check=True, tr=0, item=None):
    """Aggiunge un solido. check=True lo rende un ostacolo per tutte le verifiche;
    pezzi dello stesso mobile condividono item= cosi' non si segnalano tra loro."""
    o = ST.doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = color
    o.ViewObject.Transparency = tr
    grp(g).addObject(o)
    if check:
        ST.CHECK.append((item or name, o.Label, shape, g))
    return o


def B(x0, y0, z0, x1, y1, z1):
    return Part.makeBox((x1 - x0) * S, (y1 - y0) * S, (z1 - z0) * S, V(x0 * S, y0 * S, z0 * S))


def C(cx, cy, z0, r, h):
    return Part.makeCylinder(r * S, h * S, V(cx * S, cy * S, z0 * S))


def box(name, x0, y0, z0, x1, y1, z1, color, g, **kw):
    return add(name, B(x0, y0, z0, x1, y1, z1), color, g, **kw)


def cyl(name, cx, cy, z0, r, h, color, g, **kw):
    return add(name, C(cx, cy, z0, r, h), color, g, **kw)


def rel_box(hx, hy, d, n, da, db, z0, z1):
    """Box in coordinate locali: da lungo d, db lungo n, a partire da (hx, hy)."""
    xs = [hx + d[0] * a + n[0] * b for a in da for b in db]
    ys = [hy + d[1] * a + n[1] * b for a in da for b in db]
    return B(min(xs), min(ys), z0, max(xs), max(ys), z1)


# ============================== muri e aperture ==============================
def opening(label, x0, y0, x1, y1, z1, net_w, net_h, note=""):
    """Foro nel muro (luce muro) per una porta. Va dichiarato prima dei muri che attraversa."""
    ST.OPEN.append(B(x0, y0, 0, x1, y1, z1))
    ST.OPENINGS.append((label, net_w, net_h, max(x1 - x0, y1 - y0), z1, note))


def wall(name, x0, y0, x1, y1):
    s = B(x0, y0, 0, x1, y1, ST.H)
    for o in ST.OPEN:
        if s.BoundBox.intersect(o.BoundBox):
            s = s.cut(o)
    ST.WALLS.append((name, s))
    return add(name, s, COL["WALL"], "Strutture", check=False)


def jambs(name, x0, y0, x1, y1, z1, fr):
    """Stipiti + traverso dentro il foro."""
    if (x1 - x0) > (y1 - y0):
        parts = [B(x0, y0, 0, x0 + fr, y1, z1), B(x1 - fr, y0, 0, x1, y1, z1), B(x0, y0, z1 - fr, x1, y1, z1)]
    else:
        parts = [B(x0, y0, 0, x1, y0 + fr, z1), B(x0, y1 - fr, 0, x1, y1, z1), B(x0, y0, z1 - fr, x1, y1, z1)]
    add(name + "_Stipiti", Part.makeCompound(parts), COL["WHITE"], "Porte", check=False)


def hinged(name, hx, hy, d, n, w, kind="Porta", color=None, hgt=2.10, z0=0.0, leaf=True,
           frame=None, handle=True):
    """Anta a battente. Cerniera (hx, hy) sul filo muro lato apertura; d = verso anta chiusa,
    n = verso apertura. Genera anta aperta a 90 gradi, area di rotazione, maniglia e spalletta da verificare."""
    frame = REGOLE["telaio"] if frame is None else frame
    leaf_shape = rel_box(hx, hy, d, n, (-0.04, 0), (0, w), z0 + 0.01, hgt)
    if leaf:
        add(name + "_Anta", leaf_shape, color or COL["OAK"], "Porte", check=False)
    h = V(hx * S, hy * S, z0 * S)
    p1 = h + V(d[0], d[1], 0) * (w * S)
    p2 = h + V(n[0], n[1], 0) * (w * S)
    pm = h + V(d[0] + n[0], d[1] + n[1], 0) * (w * S / math.sqrt(2))
    face = Part.Face(Part.Wire([Part.LineSegment(h, p1).toShape(), Part.Arc(p1, pm, p2).toShape(),
                                Part.LineSegment(p2, h).toShape()]))
    sweep = face.extrude(V(0, 0, (hgt - z0 - 0.02) * S))
    sweep.translate(V(0, 0, 0.01 * S))
    mark = face.extrude(V(0, 0, 0.004 * S))
    mark.translate(V(0, 0, 0.005 * S))
    m = add(name + "_AreaApertura", mark, (0.3, 0.8, 0.3), "Verifica_Porte", check=False, tr=40)
    hnd = probe = None
    if handle:
        m_ = REGOLE["maniglia"]
        hnd = rel_box(hx, hy, d, n, (-0.04 - m_, -0.04), (w - 0.12, w - 0.04), 0.95, 1.10)
        probe = rel_box(hx, hy, d, n, (-frame - REGOLE["spalletta"] + 0.005, -frame), (0.005, 0.10), 0.10, 2.0)
    ST.DOORS.append(dict(name=name, sweep=sweep, mark=m, kind=kind, handle=hnd, probe=probe,
                         leaf=leaf_shape if (leaf and z0 < 0.5) else None))


def sliding(name, closed, opened, color=None):
    """Scorrevole esterno muro: anta chiusa + binario sulla corsa; la posizione aperta viene verificata."""
    add(name + "_Anta", B(*closed), color or COL["OAK"], "Porte", check=False)
    x0, y0, _, x1, y1, _ = opened
    cx0, cy0, _, cx1, cy1, _ = closed
    add(name + "_Binario", B(min(x0, cx0), min(y0, cy0), 2.15, max(x1, cx1), max(y1, cy1), 2.22),
        COL["BLACK"], "Porte", check=False)
    m = add(name + "_AreaScorrimento", B(x0, y0, 0.005, x1, y1, 0.009), (0.3, 0.8, 0.3), "Verifica_Porte",
            check=False, tr=40)
    ST.SLIDES.append(dict(name=name, shape=B(*opened), mark=m, closed=B(*closed), c=closed, o=opened))


def window(name, yc, x0, x1, z0, z1, stanza, mullion=False):
    """Serramento su muro orientato lungo x (centro muro y = yc), con controtelaio; foro maggiorato.
    stanza = locale servito, per il rapporto aeroilluminante."""
    fr = REGOLE["telaio"]
    rx0, rx1 = x0 - fr, x1 + fr
    rz0, rz1 = (z0 - fr if z0 > 0 else 0.0), z1 + fr
    ST.OPEN.append(B(rx0, yc - 0.20, rz0, rx1, yc + 0.20, rz1))
    ST.OPENINGS.append((name, x1 - x0, z1 - z0, rx1 - rx0, rz1 - rz0,
                        "davanzale %.2f" % z0 if z0 > 0 else "a pavimento"))
    ct = [B(rx0, yc - 0.06, rz0, x0, yc + 0.06, rz1), B(x1, yc - 0.06, rz0, rx1, yc + 0.06, rz1),
          B(x0, yc - 0.06, z1, x1, yc + 0.06, rz1)]
    if z0 > 0:
        ct.append(B(x0, yc - 0.06, rz0, x1, yc + 0.06, z0))
    add(name + "_Controtelaio", Part.makeCompound(ct), COL["FRAME"], "Serramenti", check=False)
    t = 0.05
    frs = [B(x0, yc - 0.05, z0, x0 + t, yc + 0.05, z1), B(x1 - t, yc - 0.05, z0, x1, yc + 0.05, z1),
           B(x0, yc - 0.05, z1 - t, x1, yc + 0.05, z1), B(x0, yc - 0.05, z0, x1, yc + 0.05, z0 + 0.03)]
    if mullion:
        xm = (x0 + x1) / 2
        frs.append(B(xm - t / 2, yc - 0.05, z0, xm + t / 2, yc + 0.05, z1))
    add(name + "_Telaio", Part.makeCompound(frs), COL["BLACK"], "Serramenti", check=False)
    glass = B(x0 + t, yc - 0.01, z0 + 0.03, x1 - t, yc + 0.01, z1 - t)
    add(name + "_Vetro", glass, COL["GLASS"], "Serramenti", check=False, tr=65)
    ST.WINDOWS.append(dict(name=name, yc=yc, x0=x0, x1=x1, z0=z0, z1=z1, stanza=stanza, glass=glass))


# ============================== registrazione di usi e vincoli ==============================
def seduta(name, own, edge_xy, direzione, hw):
    """Seduta servita da un piano: spazio misurato dal bordo del piano verso l'esterno.
    own = item da ignorare (la seduta stessa e il piano)."""
    ST.SEATS.append((name, tuple(own), edge_xy, direzione, hw))


def sedia(name, cx, cy, bx, by, g, piano_item, bordo):
    """Sedia attorno a un piano: (bx, by) = verso dello schienale; bordo = distanza centro piano -> bordo."""
    sh = [B(cx - 0.21, cy - 0.21, 0.43, cx + 0.21, cy + 0.21, 0.47), B(cx - 0.04, cy - 0.04, 0, cx + 0.04, cy + 0.04, 0.43)]
    if bx:
        xb = cx + bx * 0.19
        sh.append(B(min(xb, xb + bx * 0.03), cy - 0.21, 0.47, max(xb, xb + bx * 0.03), cy + 0.21, 0.85))
    else:
        yb = cy + by * 0.19
        sh.append(B(cx - 0.21, min(yb, yb + by * 0.03), 0.47, cx + 0.21, max(yb, yb + by * 0.03), 0.85))
    add(name, Part.makeCompound(sh), COL["BLACK"], g)
    tx, ty = cx - bx * 0.75, cy - by * 0.75
    seduta(name, (name, piano_item), (tx + bx * bordo, ty + by * bordo), (bx, by), 0.21)


def zona_prelievo(label, x0, y0, x1, y1, own):
    """Volume che deve restare libero davanti ad armadi/vani (profondita' >= REGOLE['prelievo'])."""
    ST.FRONT.append((label, B(x0, y0, 0.05, x1, y1, 1.80), tuple(own), min(x1 - x0, y1 - y0)))


def passaggio(label, a, b, minimo, comfort=None):
    """Distanza in pianta tra due oggetti (per nome) con minimo e obiettivo di comfort."""
    ST.PASS.append((label, a, b, minimo, comfort))


def ingresso(x, y):
    ST.START = (x, y)


def destinazione(label, x, y):
    """Punto dove una persona deve poter arrivare dall'ingresso (davanti a un arredo o un sanitario)."""
    ST.TARGETS[label] = (x, y)


def percorso(label, da, a):
    """Percorso tra due destinazioni: verificato e misurato (es. notturno letto -> bagno)."""
    ST.PATHS.append((label, da, a))


def stanza(nome, rects, label_xy, abitabile=True, tipo="", righe=None):
    """Locale: rettangoli di pavimento netto, posizione dell'etichetta in pianta."""
    area = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in rects)
    ST.ROOMS.append(dict(nome=nome, rects=rects, xy=label_xy, abitabile=abitabile, tipo=tipo,
                         area=area, righe=righe or [nome.upper()]))
    return area


def tv(name):
    ST.TV.append(name)


def coerenza_altezze(label, z_piano, z_seduta):
    ST.HEIGHTS.append((label, z_piano, z_seduta))


def non_verificabile(categoria, motivo):
    ST.NONVER.append((categoria, motivo))


def quote(points, horizontal, base):
    """Catena di quote in pianta (mm nel DWG): punti in metri lungo x (horizontal) o y."""
    ST.ANN["quote"].append(([p * S for p in points], horizontal, base * S))


def etichetta(testo, x, y, h=0.07):
    ST.ANN["testi"].append((testo, x * S, y * S, h * S))


def nota(testo):
    ST.ANN["note"] = testo


# ============================== verifiche ==============================
def _r(cat, elem, misura, soglia, stato, grav, metodo, nota_=""):
    # la gravita' descrive un problema: un controllo superato la conserva solo come nota migliorativa
    if stato == "VERIFICATO" and grav != "migliorativa":
        grav = ""
    ST.risultati.append(dict(cat=cat, elem=elem, misura=misura, soglia=soglia, stato=stato,
                             grav=grav, metodo=metodo, nota=nota_))


def hits_of(shape, skip_items=(), walls=True):
    out = []
    for item, label, sh, _g in ST.CHECK:
        if item in skip_items or not shape.BoundBox.intersect(sh.BoundBox):
            continue
        v = shape.common(sh).Volume
        if v > REGOLE["tol"]:
            out.append("%s (%.0f cm3)" % (label, v / 1000))
    if walls:
        for wname, ws in ST.WALLS:
            if shape.BoundBox.intersect(ws.BoundBox) and shape.common(ws).Volume > REGOLE["tol"]:
                out.append("MURO " + wname)
    return out


def _items():
    """Bounding box aggregata per mobile (item) in metri."""
    agg = {}
    for item, label, sh, g in ST.CHECK:
        bb = sh.BoundBox
        a = agg.setdefault(item, [bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax, g])
        a[:6] = [min(a[0], bb.XMin), min(a[1], bb.YMin), min(a[2], bb.ZMin),
                 max(a[3], bb.XMax), max(a[4], bb.YMax), max(a[5], bb.ZMax)]
    return {k: [v / S for v in a[:6]] + [a[6]] for k, a in agg.items()}


def _room_of(x, y):
    for r in ST.ROOMS:
        for x0, y0, x1, y1 in r["rects"]:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return r["nome"]
    return "-"


# --- griglia in pianta per percorsi e occupazione ---
CELL = 0.05


def _rects_ostacoli(zmax=1.0):
    rects = []
    for _n, ws in ST.WALLS:
        for w in ws.slice(V(0, 0, 1), 1.0 * S):
            bb = w.BoundBox
            rects.append((bb.XMin / S, bb.YMin / S, bb.XMax / S, bb.YMax / S))
    for _item, _l, sh, _g in ST.CHECK:
        for sol in (sh.Solids or [sh]):
            bb = sol.BoundBox
            if bb.ZMin < zmax * S and bb.ZMax > 0.05 * S:
                rects.append((bb.XMin / S, bb.YMin / S, bb.XMax / S, bb.YMax / S))
    for dd in ST.DOORS:
        if dd["leaf"] is not None:
            bb = dd["leaf"].BoundBox
            rects.append((bb.XMin / S, bb.YMin / S, bb.XMax / S, bb.YMax / S))
    for sl in ST.SLIDES:
        bb = sl["shape"].BoundBox
        rects.append((bb.XMin / S, bb.YMin / S, bb.XMax / S, bb.YMax / S))
    return rects


def _grid(rects, inflate):
    X0, Y0, X1, Y1 = ST.interno
    nx, ny = int(round((X1 - X0) / CELL)), int(round((Y1 - Y0) / CELL))
    g = bytearray(nx * ny)
    for x0, y0, x1, y1 in rects:
        x0, y0, x1, y1 = x0 - inflate, y0 - inflate, x1 + inflate, y1 + inflate
        i0 = max(0, int(math.ceil((x0 - X0) / CELL - 0.5)))
        i1 = min(nx - 1, int(math.floor((x1 - X0) / CELL - 0.5)))
        j0 = max(0, int(math.ceil((y0 - Y0) / CELL - 0.5)))
        j1 = min(ny - 1, int(math.floor((y1 - Y0) / CELL - 0.5)))
        for j in range(j0, j1 + 1):
            row = j * nx
            for i in range(i0, i1 + 1):
                g[row + i] = 1
    return g, nx, ny


def _cell(x, y, nx, ny):
    X0, Y0 = ST.interno[0], ST.interno[1]
    i, j = int((x - X0) / CELL), int((y - Y0) / CELL)
    return (i, j) if 0 <= i < nx and 0 <= j < ny else None


def _bfs(g, nx, ny, start):
    dist = [-1] * (nx * ny)
    c = _cell(start[0], start[1], nx, ny)
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


def verifica(scrivi_report=True):
    """Esegue tutte le verifiche, stampa il riepilogo e scrive output/report_verifiche.md.
    Ritorna il numero di NON CONFORME bloccanti + rilevanti."""
    ST.risultati = []
    R = REGOLE

    # 1) ante, finestre, scorrevoli: traiettoria completa libera
    for dd in ST.DOORS:
        hits = hits_of(dd["sweep"])
        for o in ST.DOORS:
            if o["name"] != dd["name"] and dd["sweep"].BoundBox.intersect(o["sweep"].BoundBox) \
                    and dd["sweep"].common(o["sweep"]).Volume > R["tol"]:
                hits.append("%s %s" % (o["kind"], o["name"]))
        for sl in ST.SLIDES:
            if dd["sweep"].common(sl["shape"]).Volume > R["tol"] or dd["sweep"].common(sl["closed"]).Volume > R["tol"]:
                hits.append("scorrevole " + sl["name"])
        dd["mark"].ViewObject.ShapeColor = (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3)
        _r("Aperture", dd["name"], "collisioni: " + (", ".join(hits) if hits else "nessuna"), "traiettoria libera",
           "NON CONFORME" if hits else "VERIFICATO", "bloccante", "intersezione 3D del volume spazzato dall'anta 0-90 gradi")
    for sl in ST.SLIDES:
        hits = hits_of(sl["shape"])
        hits += ["%s %s" % (d["kind"], d["name"]) for d in ST.DOORS if sl["shape"].common(d["sweep"]).Volume > R["tol"]]
        sl["mark"].ViewObject.ShapeColor = (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3)
        _r("Aperture", sl["name"] + " (aperta)", "collisioni: " + (", ".join(hits) if hits else "nessuna"),
           "corsa libera", "NON CONFORME" if hits else "VERIFICATO", "bloccante", "intersezione 3D anta in posizione aperta")

    # 2) maniglie e 3) spallette
    for dd in ST.DOORS:
        if dd["handle"] is None:
            continue
        h = hits_of(dd["handle"])
        _r("Maniglie", dd["name"], ", ".join(h) if h else "libera", "%.0f cm liberi a 90 gradi" % (R["maniglia"] * 100),
           "NON CONFORME" if h else "VERIFICATO", "rilevante", "intersezione 3D maniglia con anta aperta")
        p = [w for w in hits_of(dd["probe"]) if w.startswith("MURO")]
        _r("Spallette", dd["name"], ", ".join(p) if p else ">= soglia", ">= %.0f cm" % (R["spalletta"] * 100),
           "NON CONFORME" if p else "VERIFICATO", "rilevante", "sonda tra filo foro e muro ortogonale")

    # 4) sedute: dal bordo del piano all'ostacolo
    for name, own, (ox, oy), (dx, dy), hw in ST.SEATS:
        zone = rel_box(ox, oy, (dx, dy), (-dy, dx), (0.002, 1.5), (-hw, hw), 0.05, 1.00)
        free = 1.5
        for it, _l, sh, _g in ST.CHECK + [(w, w, s, "") for w, s in ST.WALLS]:
            if it in own or not zone.BoundBox.intersect(sh.BoundBox):
                continue
            c = zone.common(sh)
            if c.Volume > R["tol"]:
                free = min(free, min((v.Point.x / S - ox) * dx + (v.Point.y / S - oy) * dy for v in c.Vertexes))
        ok = free >= R["seduta_min"]
        _r("Sedute", name, "%.0f cm" % (free * 100),
           "min %.0f (alzarsi) / comfort %.0f (passare dietro)" % (R["seduta_min"] * 100, R["seduta_comfort"] * 100),
           "VERIFICATO" if ok else "NON CONFORME", "bloccante" if not ok else ("migliorativa" if free < R["seduta_comfort"] else ""),
           "distanza bordo piano -> primo ostacolo (max 150)",
           "sotto obiettivo comfort: non si passa dietro chi siede" if ok and free < R["seduta_comfort"] else "")

    # 5) passaggi e zone di prelievo
    for label, a, b, mn, cf in ST.PASS:
        d = ST.doc.getObject(a).Shape.distToShape(ST.doc.getObject(b).Shape)[0] / S
        ok = d >= mn - 1e-6
        low = cf and d < cf
        _r("Passaggi", label, "%.0f cm" % (d * 100), "min %.0f" % (mn * 100) + (" / comfort %.0f" % (cf * 100) if cf else ""),
           "VERIFICATO" if ok else "NON CONFORME", "bloccante" if not ok else ("migliorativa" if low else ""),
           "distanza minima in pianta %s - %s" % (a, b), "sotto obiettivo comfort" if ok and low else "")
    for label, zone, own, depth in ST.FRONT:
        h = hits_of(zone, skip_items=own)
        ok = not h and depth >= R["prelievo"] - 1e-6
        _r("Zone di prelievo", label, ("ostacoli: " + ", ".join(h)) if h else "libera, %.0f cm" % (depth * 100),
           ">= %.0f cm liberi" % (R["prelievo"] * 100), "VERIFICATO" if ok else "NON CONFORME", "bloccante",
           "intersezione 3D della zona davanti al mobile")

    # 6) percorsi dall'ingresso (griglia 5 cm, persona larga 60 cm)
    rects = _rects_ostacoli()
    g, nx, ny = _grid(rects, R["raggio_persona"])
    if ST.START:
        dist = _bfs(g, nx, ny, ST.START)
        for label, (x, y) in ST.TARGETS.items():
            c = _cell(x, y, nx, ny)
            k = c[1] * nx + c[0] if c else None
            if k is None or g[k]:
                _r("Percorsi", label, "punto dentro un ingombro", "raggiungibile dall'ingresso con 60 cm", "NON CONFORME",
                   "bloccante", "griglia 5 cm, ostacoli gonfiati di 30 cm", "spostare il punto o l'arredo")
            elif dist[k] < 0:
                _r("Percorsi", label, "non raggiungibile", "raggiungibile dall'ingresso con 60 cm", "NON CONFORME",
                   "bloccante", "griglia 5 cm, ostacoli gonfiati di 30 cm")
            else:
                _r("Percorsi", label, "%.1f m dall'ingresso" % (dist[k] * CELL), "raggiungibile con 60 cm",
                   "VERIFICATO", "", "griglia 5 cm, ostacoli gonfiati di 30 cm")
    for label, da, a in ST.PATHS:
        dist = _bfs(g, nx, ny, ST.TARGETS[da])
        c = _cell(*ST.TARGETS[a], nx, ny)
        k = c[1] * nx + c[0]
        ok = dist[k] >= 0
        _r("Percorsi", label, ("%.1f m" % (dist[k] * CELL)) if ok else "interrotto", "continuo con 60 cm",
           "VERIFICATO" if ok else "NON CONFORME", "" if ok else "bloccante", "griglia 5 cm, ostacoli gonfiati di 30 cm")

    # 7) locali: rapporto aeroilluminante e occupazione
    occ, onx, ony = _grid([r for r in _rects_ostacoli(zmax=0.30)], 0.0)
    X0, Y0 = ST.interno[0], ST.interno[1]
    for r in ST.ROOMS:
        win = [w for w in ST.WINDOWS if w["stanza"] == r["nome"]]
        sup = sum((w["x1"] - w["x0"]) * (w["z1"] - w["z0"]) for w in win)
        if r["abitabile"]:
            need = r["area"] * R["rai"]
            _r("Luce e aria", r["nome"], "%.1f m2 finestrati" % sup, ">= %.1f m2 (1/8 di %.1f)" % (need, r["area"]),
               "VERIFICATO" if sup >= need else "NON CONFORME", "bloccante" if sup < need else "",
               "somma luci nette dei serramenti del locale")
            cells = tot = 0
            for x0, y0, x1, y1 in r["rects"]:
                for j in range(int((y0 - Y0) / CELL), int((y1 - Y0) / CELL)):
                    for i in range(int((x0 - X0) / CELL), int((x1 - X0) / CELL)):
                        if 0 <= i < onx and 0 <= j < ony:
                            tot += 1
                            cells += occ[j * onx + i]
            ratio = cells / tot if tot else 0
            _r("Luce e aria", r["nome"] + " - occupazione", "%.0f%% del pavimento" % (ratio * 100),
               "<= %.0f%%" % (R["occupazione"] * 100), "VERIFICATO",
               "migliorativa" if ratio > R["occupazione"] else "", "impronta arredi a terra su griglia 5 cm",
               "locale affollato" if ratio > R["occupazione"] else "")
        elif r["tipo"] == "bagno":
            _r("Luce e aria", r["nome"], "finestra %.2f m2" % sup if win else "nessuna finestra", "finestra o aerazione forzata",
               "VERIFICATO" if win else "NON VERIFICABILE", "" if win else "rilevante",
               "presenza serramento apribile", "" if win else "progettare l'aerazione forzata")
        else:
            _r("Luce e aria", r["nome"], "-", "locale non abitabile", "NON APPLICABILE", "", "-")

    # 8) vincolo TV / finestre
    for name in ST.TV:
        tvs = ST.doc.getObject(name).Shape
        cy = (tvs.BoundBox.YMin + tvs.BoundBox.YMax) / 2 / S
        worst = None
        for w in ST.WINDOWS:
            d = tvs.distToShape(w["glass"])[0] / S
            same = abs(cy - w["yc"]) < 0.5
            if worst is None or (same, -d) > (worst[0], -worst[1]):
                worst = (same, d, w["name"])
        if worst is None:
            _r("Vincoli brief", "TV " + name, "nessuna finestra", "TV lontana da finestre", "VERIFICATO", "", "-")
        else:
            same, d, wn = worst
            bad = same and d < R["tv_finestra"]
            _r("Vincoli brief", "TV " + name, "%.2f m da %s (%s)" % (d, wn, "stessa parete" if same else "altra parete"),
               "non sopra/davanti/accanto a finestra sulla stessa parete (>= %.1f m)" % R["tv_finestra"],
               "NON CONFORME" if bad else "VERIFICATO", "bloccante" if bad else ("migliorativa" if d < 1.5 else ""),
               "distanza 3D TV - vetro", "valutare riflessi" if not bad and d < 1.5 else "")

    # 9) ergonomia altezze piano / seduta
    lo, hi = R["altezza_seduta"]
    for label, zp, zs in ST.HEIGHTS:
        dz = zp - zs
        ok = lo <= dz <= hi
        _r("Ergonomia", label, "piano %.2f / seduta %.2f (diff %.2f)" % (zp, zs, dz), "diff %.2f-%.2f" % (lo, hi),
           "VERIFICATO" if ok else "NON CONFORME", "" if ok else "rilevante", "quote di progetto")

    # 10) montaggio arredi alti (raddrizzamento in opera)
    for item, (x0, y0, z0, x1, y1, z1, g_) in _items().items():
        h = z1 - z0
        if h <= 2.0:
            continue
        diag = math.hypot(h, min(x1 - x0, y1 - y0))
        ok = diag <= ST.H - R["montaggio_margine"]
        _r("Montaggio", item, "diagonale %.2f m" % diag, "<= %.2f (altezza locale - margine)" % (ST.H - R["montaggio_margine"]),
           "VERIFICATO" if ok else "NON CONFORME", "" if ok else "rilevante", "ipotenusa altezza x profondita'",
           "" if ok else "montare in opera o a moduli")

    # 11) compenetrazioni
    pairs = []
    C_ = ST.CHECK
    for i in range(len(C_)):
        for j in range(i + 1, len(C_)):
            a, b = C_[i], C_[j]
            if a[0] != b[0] and a[2].BoundBox.intersect(b[2].BoundBox) and a[2].common(b[2]).Volume > R["tol"]:
                pairs.append("%s <-> %s" % (a[1], b[1]))
    for _item, label, sh, _g in C_:
        for wname, ws in ST.WALLS:
            if sh.BoundBox.intersect(ws.BoundBox) and sh.common(ws).Volume > R["tol"]:
                pairs.append("%s dentro %s" % (label, wname))
    _r("Geometria", "Compenetrazioni arredi/muri", ", ".join(pairs) if pairs else "nessuna", "nessuna",
       "NON CONFORME" if pairs else "VERIFICATO", "bloccante" if pairs else "", "intersezione 3D a coppie")

    for cat, motivo in ST.NONVER:
        _r("Non verificabili", cat, "-", "-", "NON VERIFICABILE", "rilevante", "-", motivo)

    ST.doc.recompute()
    problemi = [x for x in ST.risultati if x["stato"] == "NON CONFORME" and x["grav"] in ("bloccante", "rilevante")]
    miglior = [x for x in ST.risultati if x["grav"] == "migliorativa"]
    cnt = collections.Counter(x["stato"] for x in ST.risultati)
    print("=== VERIFICHE %s: %s ===" % (ST.nome, ", ".join("%s %d" % kv for kv in sorted(cnt.items()))))
    for x in problemi:
        print("NON CONFORME [%s] %s / %s: %s (soglia %s)" % (x["grav"], x["cat"], x["elem"], x["misura"], x["soglia"]))
    for x in miglior:
        print("migliorativa  %s / %s: %s (%s)" % (x["cat"], x["elem"], x["misura"], x["nota"] or x["soglia"]))
    if scrivi_report:
        path = _report()
        print("report:", path)
    print("TOTALE PROBLEMI:", len(problemi))
    return len(problemi)


def _report():
    out = os.path.join(ST.dir, "output")
    os.makedirs(out, exist_ok=True)
    rs = ST.risultati
    bloc = [x for x in rs if x["stato"] == "NON CONFORME" and x["grav"] == "bloccante"]
    stato = ("PROPOSTA PRELIMINARE: verifiche geometriche e funzionali superate; restano le voci NON VERIFICABILI"
             if not bloc else "NON CONSEGNABILE: %d verifiche bloccanti non superate" % len(bloc))
    L = ["# Verifiche - %s" % ST.nome, "",
         "Generato da `lib/arredo.py` il %s. Brief: [`brief.md`](../brief.md). Soglie: `docs/regole-progettuali.md`."
         % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "", "**Esito:** " + stato, "",
         "## Riepilogo", "", "| Stato | Bloccante | Rilevante | Migliorativa | Totale |", "|---|---|---|---|---|"]
    for st in ("VERIFICATO", "NON CONFORME", "NON VERIFICABILE", "NON APPLICABILE"):
        sub = [x for x in rs if x["stato"] == st]
        L.append("| %s | %d | %d | %d | %d |" % (st, *[sum(1 for x in sub if x["grav"] == g) for g in GRAVITA], len(sub)))
    L += ["", "## I. Verifiche eseguite", "", "| Categoria | Elemento | Misura | Soglia | Stato | Gravita' | Metodo | Nota |",
          "|---|---|---|---|---|---|---|---|"]
    for x in rs:
        L.append("| %(cat)s | %(elem)s | %(misura)s | %(soglia)s | %(stato)s | %(grav)s | %(metodo)s | %(nota)s |" % x)
    L += ["", "## Locali", "", "| Locale | Superficie netta | Abitabile |", "|---|---|---|"]
    for r in ST.ROOMS:
        L.append("| %s | %.1f m2 | %s |" % (r["nome"], r["area"], "si" if r["abitabile"] else "no"))
    L += ["", "## Luci nette / luci muro", "", "| Apertura | Luce netta | Luce muro | Note |", "|---|---|---|---|"]
    for label, nw, nh, rw, rh, note in ST.OPENINGS:
        L.append("| %s | %.0f x %.0f | %.0f x %.0f | %s |" % (label, nw * 100, nh * 100, rw * 100, rh * 100, note))
    L += ["", "## F. Arredi (ingombri indicativi)", "", "| ID | Locale | L x P x H (cm) | Posizione x, y (m) | Fonte |",
          "|---|---|---|---|---|"]
    for item, (x0, y0, z0, x1, y1, z1, g) in sorted(_items().items(), key=lambda kv: kv[1][6]):
        L.append("| %s | %s | %.0f x %.0f x %.0f | %.2f, %.2f | ingombro indicativo |" % (
            item, _room_of((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0) * 100, (y1 - y0) * 100, (z1 - z0) * 100, x0, y0))
    with open(os.path.join(out, "report_verifiche.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    return os.path.join(out, "report_verifiche.md")


# ============================== export ==============================
LAYER = {"Strutture": "MURI", "Serramenti": "SERRAMENTI", "Porte": "PORTE", "Verifica_Porte": "APERTURE"}


def esporta():
    """Salva FCStd e STEP in output/, e in build/ i dati per tools/esporta.sh (pianta, layer, mesh, annotazioni)."""
    import Import
    import importDXF
    out, build = os.path.join(ST.dir, "output"), os.path.join(ST.dir, "build")
    os.makedirs(out, exist_ok=True)
    os.makedirs(build, exist_ok=True)
    doc = ST.doc
    doc.saveAs(os.path.join(out, ST.nome + ".FCStd"))
    solids = [o for o in doc.Objects if o.TypeId == "Part::Feature" and "Area" not in o.Name]
    Import.export(solids, os.path.join(out, ST.nome + "_3D.step"))

    def section(o, g):
        parts = [o.Shape] if g in ("Strutture", "Serramenti") or "Area" in o.Name else (o.Shape.Solids or [o.Shape])
        edges = []
        for s in parts:
            bb = s.BoundBox
            zc = 1000.0 if (g in ("Strutture", "Serramenti") and bb.ZMin < 1000.0 < bb.ZMax) else (bb.ZMin + bb.ZMax) / 2
            for w in s.slice(V(0, 0, 1), zc):
                w = w.copy()
                w.translate(V(0, 0, -zc))
                edges.append(w)
        return Part.makeCompound(edges)

    plan = App.newDocument("Pianta_DXF")
    mapping = {}
    for o in doc.Objects:
        if o.TypeId != "Part::Feature" or o.Name.startswith(("Solaio", "Pavimento")) or "Binario" in o.Name:
            continue
        g = o.getParentGroup().Label if o.getParentGroup() else "Altro"
        sec = section(o, g)
        if not sec.Edges:
            continue
        f = plan.addObject("Part::Feature", o.Name)
        f.Shape = sec
        mapping[f.Label] = LAYER.get(g, "ARREDI")
    plan.recompute()
    importDXF.export(plan.Objects, os.path.join(build, "pianta_raw.dxf"))
    App.closeDocument("Pianta_DXF")
    App.setActiveDocument(doc.Name)
    json.dump(mapping, open(os.path.join(build, "layers.json"), "w"))

    data = []
    for o in solids:
        pts, tris = o.Shape.tessellate(5.0)
        g = o.getParentGroup().Label if o.getParentGroup() else "Altro"
        data.append({"name": o.Label, "group": g, "color": list(o.ViewObject.ShapeColor[:3]),
                     "tr": o.ViewObject.Transparency,
                     "v": [[round(p.x, 1), round(p.y, 1), round(p.z, 1)] for p in pts], "f": tris})
    json.dump(data, open(os.path.join(build, "mesh3d.json"), "w"))

    # annotazioni: quote, etichette, stanze con superfici calcolate, simboli scorrevoli, cartiglio
    wb = [ws.BoundBox for _n, ws in ST.WALLS]
    gx0, gy0 = min(b.XMin for b in wb) / S, min(b.YMin for b in wb) / S
    gx1, gy1 = max(b.XMax for b in wb) / S, max(b.YMax for b in wb) / S
    netta = sum(r["area"] for r in ST.ROOMS)
    scorrevoli = []
    for sl in ST.SLIDES:
        cx0, cy0, _, cx1, cy1, _ = sl["c"]
        ox0, oy0, _, ox1, oy1, _ = sl["o"]
        if (cx1 - cx0) < (cy1 - cy0):          # anta lungo y, spessore lungo x
            xm = (cx0 + cx1) / 2
            wall_hi = any(b.XMin / S >= cx1 - 1e-6 and b.XMin / S <= cx1 + 0.05 for b in wb)
            off = cx0 - 0.12 if wall_hi else cx1 + 0.12
            a = (off, (cy0 + cy1) / 2 + 0.25 * ((cy0 + cy1) - (oy0 + oy1)) / 2)
            b_ = (off, (oy0 + oy1) / 2 - 0.25 * ((cy0 + cy1) - (oy0 + oy1)) / 2)
            leaf = ((xm, cy0), (xm, cy1))
        else:
            ym = (cy0 + cy1) / 2
            wall_hi = any(b.YMin / S >= cy1 - 1e-6 and b.YMin / S <= cy1 + 0.05 for b in wb)
            off = cy0 - 0.12 if wall_hi else cy1 + 0.12
            a = ((cx0 + cx1) / 2 + 0.25 * ((cx0 + cx1) - (ox0 + ox1)) / 2, off)
            b_ = ((ox0 + ox1) / 2 - 0.25 * ((cx0 + cx1) - (ox0 + ox1)) / 2, off)
            leaf = ((cx0, ym), (cx1, ym))
        scorrevoli.append([[p * S for p in leaf[0]], [p * S for p in leaf[1]], [p * S for p in a], [p * S for p in b_]])
    ann = dict(
        quote=ST.ANN["quote"], testi=ST.ANN["testi"], scorrevoli=scorrevoli,
        stanze=[(r["righe"] + [("%.1f m²" % r["area"]).replace(".", ",")], r["xy"][0] * S, r["xy"][1] * S)
                for r in ST.ROOMS],
        titolo="%s - PIANTA   Sup. lorda %s m²  -  Sup. netta %s m²   Quote in mm - stampa consigliata 1:50"
               % (ST.nome.upper(), ("%.1f" % ((gx1 - gx0) * (gy1 - gy0))).replace(".", ","),
                  ("%.1f" % netta).replace(".", ",")),
        note=ST.ANN["note"], centro=(gx0 + gx1) / 2 * S, base=gy0 * S,
    )
    json.dump(ann, open(os.path.join(build, "annotazioni.json"), "w"), ensure_ascii=False)
    print("export FreeCAD ok ->", out, "| ora: tools/esporta.sh", ST.dir)
