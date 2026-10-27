# Appartamento ~100 m2 (12.5 x 8.0 m lordi) - generato per FreeCAD 1.1
# v2: ingresso aperto sulla zona giorno, zona notte chiusa da porta scorrevole,
#     aperture nei muri con spazio per controtelai/stipiti, verifiche estese.
# Coordinate in metri (convertite in mm), origine = angolo SO esterno, y verso nord.
import FreeCAD as App, FreeCADGui as Gui, Part, math

V = App.Vector
S = 1000.0
H = 2.70            # altezza interna
FRAME = 0.05        # stipite/controtelaio per lato (porte interne, finestre)
FRAME_BLIND = 0.075 # controtelaio porta blindata
MIN_SPALLA = 0.10   # spalletta minima tra apertura e muro ortogonale
MIN_SEDUTA = 0.60   # spazio libero dietro una seduta per alzarsi
TOL = 1000.0        # 1 cm3

if App.listDocuments().get("Appartamento"):
    App.closeDocument("Appartamento")
doc = App.newDocument("Appartamento")

# ---------- colori (stile moderno, toni chiari) ----------
WALL = (0.97, 0.97, 0.96); WHITE = (0.95, 0.95, 0.94); OAK = (0.78, 0.64, 0.46)
FLOOR = (0.85, 0.74, 0.58); TILE = (0.80, 0.80, 0.79); BLACK = (0.13, 0.13, 0.14)
GREY = (0.58, 0.59, 0.61); GLASS = (0.72, 0.86, 0.95); FRAMEC = (0.62, 0.52, 0.40)
STEEL = (0.76, 0.77, 0.79); SAGE = (0.60, 0.68, 0.58); GREEN = (0.33, 0.52, 0.30)
TERRA = (0.74, 0.47, 0.36); DARK = (0.30, 0.30, 0.32); RUG = (0.88, 0.86, 0.82)

groups, CHECK, WALLS, OPEN = {}, [], [], []
DOORS, SLIDES, SEATS, OPENINGS = [], [], [], []


def grp(n):
    if n not in groups:
        groups[n] = doc.addObject("App::DocumentObjectGroup", n)
    return groups[n]


def add(name, shape, color, g, check=True, tr=0, item=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = color
    o.ViewObject.Transparency = tr
    grp(g).addObject(o)
    if check:
        CHECK.append((item or name, o.Label, shape))
    return o


def B(x0, y0, z0, x1, y1, z1):
    return Part.makeBox((x1-x0)*S, (y1-y0)*S, (z1-z0)*S, V(x0*S, y0*S, z0*S))


def C(cx, cy, z0, r, h):
    return Part.makeCylinder(r*S, h*S, V(cx*S, cy*S, z0*S))


def box(name, x0, y0, z0, x1, y1, z1, color, g, **kw):
    return add(name, B(x0, y0, z0, x1, y1, z1), color, g, **kw)


def cyl(name, cx, cy, z0, r, h, color, g, **kw):
    return add(name, C(cx, cy, z0, r, h), color, g, **kw)


def rel_box(hx, hy, d, n, da, db, z0, z1):
    """Box in coordinate locali della porta: da lungo d, db lungo n, a partire dalla cerniera."""
    xs = [hx + d[0]*a + n[0]*b for a in da for b in db]
    ys = [hy + d[1]*a + n[1]*b for a in da for b in db]
    return B(min(xs), min(ys), z0, max(xs), max(ys), z1)


# ---------- aperture nei muri (luce muro = luce netta + telaio) ----------
def opening(label, x0, y0, x1, y1, z1, net_w, net_h, note=""):
    OPEN.append(B(x0, y0, 0, x1, y1, z1))
    OPENINGS.append((label, net_w, net_h, max(x1-x0, y1-y0) if min(x1-x0, y1-y0) < 0.5 else x1-x0, z1, note))


def jambs(name, x0, y0, x1, y1, z1, fr):
    """Stipiti + traverso dentro l'apertura (muro lungo x se y1-y0 < x1-x0)."""
    if (x1-x0) > (y1-y0):
        parts = [B(x0, y0, 0, x0+fr, y1, z1), B(x1-fr, y0, 0, x1, y1, z1), B(x0, y0, z1-fr, x1, y1, z1)]
    else:
        parts = [B(x0, y0, 0, x1, y0+fr, z1), B(x0, y1-fr, 0, x1, y1, z1), B(x0, y0, z1-fr, x1, y1, z1)]
    add(name+"_Stipiti", Part.makeCompound(parts), WHITE, "Porte", check=False)


def hinged(name, hx, hy, d, n, w, kind="Porta", color=OAK, hgt=2.10, z0=0.0, leaf=True,
           frame=FRAME, handle=True):
    """Anta a battente. Cerniera (hx,hy) sul filo muro lato apertura; d = verso anta chiusa,
    n = verso apertura. Genera: anta aperta a 90 gradi, area di rotazione, maniglia, spalletta."""
    if leaf:
        add(name+"_Anta", rel_box(hx, hy, d, n, (-0.04, 0), (0, w), z0+0.01, hgt), color, "Porte", check=False)
    h = V(hx*S, hy*S, z0*S)
    p1 = h + V(d[0], d[1], 0)*(w*S)
    p2 = h + V(n[0], n[1], 0)*(w*S)
    pm = h + V(d[0]+n[0], d[1]+n[1], 0)*(w*S/math.sqrt(2))
    face = Part.Face(Part.Wire([Part.LineSegment(h, p1).toShape(),
                                Part.Arc(p1, pm, p2).toShape(),
                                Part.LineSegment(p2, h).toShape()]))
    sweep = face.extrude(V(0, 0, (hgt-z0-0.02)*S)); sweep.translate(V(0, 0, 0.01*S))
    mark = face.extrude(V(0, 0, 0.004*S)); mark.translate(V(0, 0, 0.005*S))
    m = add(name+"_AreaApertura", mark, (0.3, 0.8, 0.3), "Verifica_Porte", check=False, tr=40)
    hnd = probe = None
    if handle:
        # maniglia (sporgenza 7 cm) sul lato verso il muro, con anta aperta a 90 gradi
        hnd = rel_box(hx, hy, d, n, (-0.11, -0.04), (w-0.12, w-0.04), 0.95, 1.10)
        # spalletta: tra filo apertura (cerniera - telaio) e muro ortogonale servono MIN_SPALLA
        probe = rel_box(hx, hy, d, n, (-frame-MIN_SPALLA+0.005, -frame), (0.005, 0.10), 0.10, 2.0)
    DOORS.append(dict(name=name, sweep=sweep, mark=m, kind=kind, handle=hnd, probe=probe))


def sliding(name, closed, opened, color=OAK):
    """Porta scorrevole esterno muro: anta chiusa (rovere, visibile sul muro bianco) + binario
    sopra la corsa completa; la posizione aperta viene verificata."""
    add(name+"_Anta", B(*closed), color, "Porte", check=False)
    shp = B(*opened)
    x0, y0, _, x1, y1, _ = opened
    cx0, cy0, _, cx1, cy1, _ = closed
    add(name+"_Binario", B(min(x0, cx0), min(y0, cy0), 2.15, max(x1, cx1), max(y1, cy1), 2.22),
        BLACK, "Porte", check=False)
    m = add(name+"_AreaScorrimento", B(x0, y0, 0.005, x1, y1, 0.009), (0.3, 0.8, 0.3), "Verifica_Porte", check=False, tr=40)
    SLIDES.append(dict(name=name, shape=shp, mark=m, closed=B(*closed)))


def window(name, yc, x0, x1, z0, z1, mullion=False):
    """Serramento con controtelaio da FRAME per lato; il foro nel muro e' maggiorato di conseguenza."""
    rx0, rx1 = x0-FRAME, x1+FRAME
    rz0, rz1 = (z0-FRAME if z0 > 0 else 0.0), z1+FRAME
    OPEN.append(B(rx0, yc-0.20, rz0, rx1, yc+0.20, rz1))
    OPENINGS.append((name, x1-x0, z1-z0, rx1-rx0, rz1-rz0, "davanzale %.2f" % z0 if z0 > 0 else "a pavimento"))
    ct = [B(rx0, yc-0.06, rz0, x0, yc+0.06, rz1), B(x1, yc-0.06, rz0, rx1, yc+0.06, rz1),
          B(x0, yc-0.06, z1, x1, yc+0.06, rz1)]
    if z0 > 0:
        ct.append(B(x0, yc-0.06, rz0, x1, yc+0.06, z0))
    add(name+"_Controtelaio", Part.makeCompound(ct), FRAMEC, "Serramenti", check=False)
    t = 0.05
    fr = [B(x0, yc-0.05, z0, x0+t, yc+0.05, z1), B(x1-t, yc-0.05, z0, x1, yc+0.05, z1),
          B(x0, yc-0.05, z1-t, x1, yc+0.05, z1), B(x0, yc-0.05, z0, x1, yc+0.05, z0+0.03)]
    if mullion:
        xm = (x0+x1)/2
        fr.append(B(xm-t/2, yc-0.05, z0, xm+t/2, yc+0.05, z1))
    add(name+"_Telaio", Part.makeCompound(fr), BLACK, "Serramenti", check=False)
    add(name+"_Vetro", B(x0+t, yc-0.01, z0+0.03, x1-t, yc+0.01, z1-t), GLASS, "Serramenti", check=False, tr=65)


# ================= SERRAMENTI E PORTE =================
window("Vetrata_Soggiorno", 0.15, 1.00, 5.50, 0, 2.40, mullion=True)     # scorrevole alzante
window("Portafinestra_Camera", 0.15, 8.20, 10.60, 0, 2.40, mullion=True) # scorrevole
window("Finestra_Cucina", 7.85, 1.40, 3.20, 1.20, 2.20, mullion=True)    # 2 ante verso interno
window("Finestra_Bagno", 7.85, 9.55, 10.15, 1.60, 2.20)                  # 1 anta verso interno
hinged("Finestra_Cucina_Anta_SX", 1.45, 7.70, (1, 0), (0, -1), 0.825, z0=1.23, hgt=2.15, leaf=False, kind="Finestra", handle=False)
hinged("Finestra_Cucina_Anta_DX", 3.15, 7.70, (-1, 0), (0, -1), 0.825, z0=1.23, hgt=2.15, leaf=False, kind="Finestra", handle=False)
hinged("Finestra_Bagno_Anta", 9.60, 7.70, (1, 0), (0, -1), 0.50, z0=1.63, hgt=2.15, leaf=False, kind="Finestra", handle=False)

# porta d'ingresso blindata 90x210: luce muro 105x220, spalletta 15 cm verso il muro del bagno
opening("Porta_Ingresso", 6.75, 7.65, 7.80, 8.05, 2.20, 0.90, 2.10, "blindata, controtelaio 7,5 cm")
jambs("Porta_Ingresso", 6.75, 7.70, 7.80, 8.00, 2.20, FRAME_BLIND)
hinged("Porta_Ingresso", 7.725, 7.70, (-1, 0), (0, -1), 0.90, color=DARK, frame=FRAME_BLIND)

# camera: porta 80x210 spostata di 15 cm dall'angolo, ora si apre dal disimpegno notte
opening("Porta_Camera", 6.70, 3.50, 7.60, 3.70, 2.15, 0.80, 2.10)
jambs("Porta_Camera", 6.70, 3.55, 7.60, 3.65, 2.15, FRAME)
hinged("Porta_Camera", 6.75, 3.55, (1, 0), (0, -1), 0.80)

# bagno: porta 80x210 con spalletta 15 cm, lavabo fuori dall'area di rotazione
opening("Porta_Bagno", 8.20, 4.70, 9.10, 4.90, 2.15, 0.80, 2.10)
jambs("Porta_Bagno", 8.20, 4.75, 9.10, 4.85, 2.15, FRAME)
hinged("Porta_Bagno", 8.25, 4.85, (1, 0), (0, 1), 0.80)

# zona notte: scorrevole esterno muro lato giorno, luce 90, anta 100, parcheggio verso sud
opening("Porta_Zona_Notte", 6.40, 3.75, 6.60, 4.65, 2.15, 0.90, 2.10, "scorrevole esterno muro")
sliding("Porta_Zona_Notte", (6.40, 3.70, 0.01, 6.44, 4.70, 2.15), (6.40, 2.70, 0.01, 6.44, 3.70, 2.15))

# cabina armadio: scorrevole esterno muro lato corridoio, luce 70, anta 80, parcheggio verso ovest
opening("Porta_Cabina", 10.50, 4.70, 11.20, 4.90, 2.15, 0.70, 2.10, "scorrevole esterno muro")
sliding("Porta_Cabina", (10.45, 4.69, 0.01, 11.25, 4.73, 2.15), (9.65, 4.69, 0.01, 10.45, 4.73, 2.15))

# ================= MURI =================
def wall(name, x0, y0, x1, y1):
    s = B(x0, y0, 0, x1, y1, H)
    for o in OPEN:
        if s.BoundBox.intersect(o.BoundBox):
            s = s.cut(o)
    WALLS.append((name, s))
    return add(name, s, WALL, "Strutture", check=False)


wall("Muro_Sud", 0, 0, 12.5, 0.3)
wall("Muro_Nord", 0, 7.7, 12.5, 8.0)
wall("Muro_Ovest", 0, 0.3, 0.3, 7.7)
wall("Muro_Est", 12.2, 0.3, 12.5, 7.7)
wall("Tramezzo_Soggiorno", 6.45, 0.3, 6.55, 4.75)       # tolto il tratto verso l'ingresso
wall("Tramezzo_Camera", 6.55, 3.55, 12.2, 3.65)
wall("Tramezzo_Corridoio_Nord", 6.45, 4.75, 12.2, 4.85)  # chiude la zona notte verso l'ingresso
wall("Tramezzo_Ingresso_Bagno", 7.95, 4.85, 8.05, 7.7)
wall("Tramezzo_Bagno_Armadio", 10.25, 4.85, 10.35, 7.7)

box("Solaio", 0, 0, -0.20, 12.5, 8.0, 0, FLOOR, "Strutture", check=False)
box("Pavimento_Bagno", 8.05, 4.85, 0, 10.25, 7.7, 0.004, TILE, "Strutture", check=False)

# ================= ARREDI =================
def chair(name, cx, cy, bx, by, g):
    sh = [B(cx-0.21, cy-0.21, 0.43, cx+0.21, cy+0.21, 0.47), B(cx-0.04, cy-0.04, 0, cx+0.04, cy+0.04, 0.43)]
    if bx:
        xb = cx + bx*0.19
        sh.append(B(min(xb, xb+bx*0.03), cy-0.21, 0.47, max(xb, xb+bx*0.03), cy+0.21, 0.85))
    else:
        yb = cy + by*0.19
        sh.append(B(cx-0.21, min(yb, yb+by*0.03), 0.47, cx+0.21, max(yb, yb+by*0.03), 0.85))
    add(name, Part.makeCompound(sh), BLACK, g)
    SEATS.append((name, name, (cx + bx*0.22, cy + by*0.22), (bx, by), 0.21))


# --- Soggiorno ---
g = "Soggiorno"
box("Mobile_TV", 0.30, 1.40, 0.15, 0.75, 3.40, 0.55, OAK, g)
box("TV_65", 0.31, 1.75, 0.95, 0.36, 3.05, 1.70, BLACK, g)
box("Tappeto", 1.20, 0.80, 0, 4.00, 3.60, 0.01, RUG, g, check=False)
box("Divano_Seduta", 3.40, 1.20, 0.01, 4.30, 3.60, 0.42, GREY, g, item="Divano")
box("Divano_Schienale", 4.30, 1.00, 0.01, 4.50, 3.80, 0.80, GREY, g, item="Divano")
box("Divano_Bracciolo_S", 3.40, 1.00, 0.01, 4.30, 1.20, 0.60, GREY, g, item="Divano")
box("Divano_Bracciolo_N", 3.40, 3.60, 0.01, 4.30, 3.80, 0.60, GREY, g, item="Divano")
box("Divano_Chaise", 2.60, 3.00, 0.01, 3.40, 3.80, 0.42, GREY, g, item="Divano")
box("Divano_Cuscini", 4.10, 1.25, 0.42, 4.30, 3.55, 0.72, SAGE, g, item="Divano")
box("Tavolino_Base", 2.00, 1.90, 0.01, 2.50, 2.50, 0.33, BLACK, g, item="Tavolino")
box("Tavolino_Piano", 1.90, 1.80, 0.33, 2.60, 2.60, 0.38, OAK, g, item="Tavolino")
box("Poltrona_Seduta", 1.30, 0.60, 0.01, 2.10, 1.25, 0.42, TERRA, g, item="Poltrona")
box("Poltrona_Schienale", 1.30, 0.42, 0.01, 2.10, 0.60, 0.82, TERRA, g, item="Poltrona")
cyl("Lampada_Base", 4.95, 0.75, 0, 0.15, 0.03, BLACK, g, item="Lampada_Terra")
cyl("Lampada_Stelo", 4.95, 0.75, 0.03, 0.015, 1.50, BLACK, g, item="Lampada_Terra")
cyl("Lampada_Paralume", 4.95, 0.75, 1.50, 0.20, 0.25, WHITE, g, item="Lampada_Terra")
lib = [B(5.95, 0.60, 0, 6.45, 2.60, 0.03)]
for z in (0.40, 0.80, 1.20, 1.60, 1.97):
    lib.append(B(5.95, 0.60, z, 6.45, 2.60, z+0.03))
lib += [B(5.95, 0.60, 0, 6.45, 0.63, 2.0), B(5.95, 2.57, 0, 6.45, 2.60, 2.0), B(5.95, 1.585, 0, 6.45, 1.615, 2.0)]
add("Libreria", Part.makeCompound(lib), OAK, g)
cyl("Pianta_Vaso", 5.85, 3.35, 0, 0.20, 0.45, TERRA, g, item="Pianta")
add("Pianta_Foglie", Part.makeSphere(0.35*S, V(5.85*S, 3.35*S, 0.95*S)), GREEN, g, item="Pianta")

# --- Zona pranzo: tavolo spostato per avere >= 60 cm dietro ogni sedia ---
g = "Pranzo"
TX, TY = 5.35, 6.10
cyl("Tavolo_Base", TX, TY, 0, 0.28, 0.03, BLACK, g, item="Tavolo")
cyl("Tavolo_Gamba", TX, TY, 0.03, 0.06, 0.69, BLACK, g, item="Tavolo")
cyl("Tavolo_Piano", TX, TY, 0.72, 0.55, 0.03, OAK, g, item="Tavolo")
for i, (dx, dy) in enumerate([(-1, 0), (1, 0), (0, -1), (0, 1)]):   # 1=ovest 2=est 3=sud 4=nord
    chair("Sedia_%d" % (i+1), TX + dx*0.75, TY + dy*0.75, dx, dy, g)
cyl("Lampada_Tavolo", TX, TY, 1.75, 0.25, 0.18, BLACK, g, item="Lampada_Tavolo")
cyl("Lampada_Tavolo_Cavo", TX, TY, 1.93, 0.005, H-1.93, BLACK, g, item="Lampada_Tavolo")

# --- Cucina (isola accorciata a 2,00 m per far posto al tavolo) ---
g = "Cucina"
box("Colonne_Frigo_Forno", 0.30, 5.00, 0, 0.90, 7.70, 2.30, WHITE, g)
box("Zoccolo", 0.90, 7.15, 0, 4.20, 7.70, 0.10, BLACK, g, item="Basi")
box("Basi_Cucina", 0.90, 7.10, 0.10, 4.20, 7.70, 0.86, WHITE, g, item="Basi")
box("Top_Cucina", 0.90, 7.05, 0.86, 4.20, 7.70, 0.90, BLACK, g, item="Basi")
box("Piano_Cottura", 3.35, 7.15, 0.90, 3.95, 7.65, 0.905, (0.05, 0.05, 0.05), g)
box("Lavello", 1.90, 7.20, 0.90, 2.70, 7.60, 0.91, STEEL, g)
cyl("Rubinetto", 2.30, 7.63, 0.91, 0.02, 0.20, STEEL, g)
box("Pensili_Est", 3.25, 7.35, 1.50, 4.20, 7.70, 2.30, WHITE, g)
box("Cappa_Integrata", 3.35, 7.35, 1.40, 3.95, 7.70, 1.50, STEEL, g)
box("Isola_Base", 1.80, 5.40, 0, 3.70, 6.10, 0.90, WHITE, g, item="Isola")
box("Isola_Top", 1.75, 5.05, 0.90, 3.75, 6.15, 0.94, OAK, g, item="Isola")
for i, x in enumerate((2.15, 2.75, 3.35)):
    cyl("Sgabello_%d_Seduta" % (i+1), x, 4.85, 0.62, 0.19, 0.05, BLACK, g, item="Sgabello_%d" % (i+1))
    cyl("Sgabello_%d_Gamba" % (i+1), x, 4.85, 0, 0.03, 0.62, BLACK, g, item="Sgabello_%d" % (i+1))
    SEATS.append(("Sgabello_%d" % (i+1), "Sgabello_%d" % (i+1), (x, 4.66), (0, -1), 0.19))
for i, x in enumerate((2.35, 3.15)):
    cyl("Lampada_Isola_%d" % (i+1), x, 5.60, 1.70, 0.12, 0.18, BLACK, g, item="Lamp_Isola_%d" % i)
    cyl("Lampada_Isola_%d_Cavo" % (i+1), x, 5.60, 1.88, 0.005, H-1.88, BLACK, g, item="Lamp_Isola_%d" % i)

# --- Ingresso (aperto sulla zona giorno) ---
g = "Ingresso"
box("Armadio_Ingresso", 6.95, 4.85, 0, 7.95, 5.30, 2.40, WHITE, g)
hinged("Armadio_Ingresso_Anta_1", 6.95, 5.30, (1, 0), (0, 1), 0.50, hgt=2.40, leaf=False, kind="Anta armadio", handle=False)
hinged("Armadio_Ingresso_Anta_2", 7.95, 5.30, (-1, 0), (0, 1), 0.50, hgt=2.40, leaf=False, kind="Anta armadio", handle=False)
box("Specchio_Ingresso", 7.93, 5.85, 1.00, 7.95, 6.65, 2.00, GLASS, g, tr=30)
box("Tappeto_Ingresso", 6.90, 6.90, 0, 7.65, 7.40, 0.01, DARK, g, check=False)

# --- Disimpegno notte ---
g = "Disimpegno_Notte"
box("Vano_Tecnico", 11.75, 3.65, 0, 12.20, 4.75, 2.40, WHITE, g)
hinged("Vano_Tecnico_Anta", 11.75, 3.70, (0, 1), (-1, 0), 0.90, hgt=2.40, leaf=False, kind="Anta armadio", handle=False)

# --- Camera da letto ---
g = "Camera"
box("Tappeto_Camera", 9.30, 0.60, 0, 11.60, 3.30, 0.01, RUG, g, check=False)
box("Letto_Testiera", 12.08, 0.95, 0.01, 12.20, 2.95, 1.10, GREY, g, item="Letto")
box("Letto_Telaio", 10.00, 1.00, 0.05, 12.08, 2.90, 0.35, OAK, g, item="Letto")
box("Letto_Materasso", 10.05, 1.05, 0.35, 12.05, 2.85, 0.60, WHITE, g, item="Letto")
box("Letto_Piumone", 10.05, 1.05, 0.60, 11.50, 2.85, 0.65, SAGE, g, item="Letto")
box("Letto_Cuscino_1", 11.60, 1.15, 0.60, 12.00, 1.85, 0.72, WHITE, g, item="Letto")
box("Letto_Cuscino_2", 11.60, 2.05, 0.60, 12.00, 2.75, 0.72, WHITE, g, item="Letto")
for i, (y0, y1) in enumerate([(0.45, 0.90), (2.95, 3.40)]):
    box("Comodino_%d" % (i+1), 11.70, y0, 0.01, 12.15, y1, 0.45, OAK, g)
    cyl("Abatjour_%d" % (i+1), 11.92, (y0+y1)/2, 0.45, 0.10, 0.30, WHITE, g)
box("Scrivania_Piano", 6.55, 0.80, 0.72, 7.15, 2.20, 0.75, OAK, g, item="Scrivania")
box("Scrivania_Gamba_1", 7.08, 0.82, 0, 7.13, 0.87, 0.72, BLACK, g, item="Scrivania")
box("Scrivania_Gamba_2", 7.08, 2.13, 0, 7.13, 2.18, 0.72, BLACK, g, item="Scrivania")
box("Sedia_Scrivania_Seduta", 7.25, 1.27, 0.43, 7.67, 1.69, 0.47, BLACK, g, item="Sedia_Scrivania")
box("Sedia_Scrivania_Schienale", 7.64, 1.27, 0.47, 7.67, 1.69, 0.85, BLACK, g, item="Sedia_Scrivania")
box("Sedia_Scrivania_Gamba", 7.42, 1.44, 0, 7.50, 1.52, 0.43, BLACK, g, item="Sedia_Scrivania")
SEATS.append(("Sedia_Scrivania", "Sedia_Scrivania", (7.67, 1.48), (1, 0), 0.21))

# --- Bagno ---
g = "Bagno"
box("Mobile_Lavabo", 8.05, 5.80, 0.55, 8.55, 6.60, 0.85, OAK, g, item="Lavabo")
box("Lavabo", 8.10, 5.90, 0.85, 8.50, 6.50, 0.97, WHITE, g, item="Lavabo")
cyl("Rubinetto_Lavabo", 8.12, 6.20, 0.97, 0.015, 0.20, STEEL, g, item="Lavabo")
box("Specchio_Bagno", 8.05, 5.85, 1.10, 8.07, 6.55, 1.90, GLASS, g, tr=30)
box("WC_Sospeso", 9.70, 5.97, 0.25, 10.25, 6.33, 0.40, WHITE, g, item="WC")
box("WC_Coperchio", 9.72, 5.99, 0.40, 10.20, 6.31, 0.43, WHITE, g, item="WC")
box("Bidet_Sospeso", 9.70, 5.20, 0.25, 10.25, 5.56, 0.40, WHITE, g)
box("Piatto_Doccia", 8.05, 6.70, 0.004, 9.45, 7.70, 0.03, WHITE, g)
box("Vetro_Doccia", 8.05, 6.70, 0.03, 8.85, 6.71, 2.00, GLASS, g, tr=60)
cyl("Soffione", 8.45, 7.45, 2.05, 0.12, 0.02, STEEL, g, item="Soffione")
box("Soffione_Braccio", 8.43, 7.45, 2.07, 8.47, 7.70, 2.10, STEEL, g, item="Soffione")
box("Scaldasalviette", 10.20, 6.45, 0.50, 10.25, 6.95, 1.50, STEEL, g)
box("Lavatrice", 9.65, 7.10, 0, 10.25, 7.70, 0.85, WHITE, g)

# --- Cabina armadio ---
g = "Cabina_Armadio"
# cabina "a giorno" (senza ante, come d'uso nelle cabine armadio): sistema a L con angolo
# accessibile in diagonale -> nessuna anta che apre contro il fianco dell'altro modulo
def open_wardrobe(name, x0, y0, x1, y1, along, posts, rails, shelves_mod, drawer_mod):
    """Modulo a giorno profondo 60 cm. along='y' (fronte verso -x) o 'x' (fronte verso -y).
    posts = coordinate dei montanti lungo il modulo; rails/shelves_mod/drawer_mod = indici dei vani."""
    p = []
    for c in posts:
        p.append(B(c-0.01, y0, 0, c+0.01, y1, 2.40) if along == "x" else B(x0, c-0.01, 0, x1, c+0.01, 2.40))
    p.append(B(x0, y0, 2.38, x1, y1, 2.40))                       # cielo
    p.append(B(x0, y0, 2.00, x1, y1, 2.02))                       # cappelliera
    for i in range(len(posts)-1):
        a0, a1 = posts[i]+0.01, posts[i+1]-0.01
        if along == "y":
            seg = lambda z0, z1, d0=0.0: B(x0+d0, a0, z0, x1, a1, z1)
        else:
            seg = lambda z0, z1, d0=0.0: B(a0, y0+d0, z0, a1, y1, z1)
        if i in shelves_mod:
            for z in (0.40, 0.75, 1.10, 1.45):
                p.append(seg(z, z+0.02))
        if i in drawer_mod:
            p.append(seg(0.0, 0.70))                               # cassettiera
            p.append(seg(1.25, 1.27))
    add(name, Part.makeCompound(p), WHITE, g)
    for i in rails:
        a0, a1 = posts[i]+0.01, posts[i+1]-0.01
        if along == "y":
            r = Part.makeCylinder(0.012*S, (a1-a0)*S, V((x0+x1)/2*S, a0*S, 1.85*S), V(0, 1, 0))
        else:
            r = Part.makeCylinder(0.012*S, (a1-a0)*S, V(a0*S, (y0+y1)/2*S, 1.85*S), V(1, 0, 0))
        add("%s_Bastone_%d" % (name, i+1), r, STEEL, g, item=name)


open_wardrobe("Cabina_Modulo_Est", 11.60, 4.85, 12.20, 7.70, "y",
              posts=[4.86, 5.80, 6.75, 7.69], rails=[0, 1], shelves_mod=[2], drawer_mod=[0])
open_wardrobe("Cabina_Modulo_Nord", 10.35, 7.10, 11.60, 7.70, "x",
              posts=[10.36, 10.98, 11.59], rails=[1], shelves_mod=[0], drawer_mod=[])
box("Specchio_Cabina", 10.35, 5.20, 0.30, 10.37, 6.00, 2.00, GLASS, g, tr=30)
# zone di prelievo davanti ai moduli (min 70 cm liberi per stare davanti e prendere le cose)
FRONT_ZONES = [
    ("Cabina: davanti modulo est", B(10.90, 4.86, 0.05, 11.595, 7.09, 1.80), ("Cabina_Modulo_Est",)),
    ("Cabina: davanti modulo nord", B(10.38, 6.40, 0.05, 11.59, 7.095, 1.80), ("Cabina_Modulo_Nord",)),
    ("Ingresso: davanti armadio", B(6.96, 5.305, 0.05, 7.92, 6.00, 1.80), ("Armadio_Ingresso",)),
]

doc.recompute()

# ================= VERIFICHE =================
def hits_of(shape, skip_items=(), skip_doors=(), walls=True):
    out = []
    for item, label, sh in CHECK:
        if item in skip_items or not shape.BoundBox.intersect(sh.BoundBox):
            continue
        v = shape.common(sh).Volume
        if v > TOL:
            out.append("%s (%.0f cm3)" % (label, v/1000))
    if walls:
        for wname, ws in WALLS:
            if shape.BoundBox.intersect(ws.BoundBox) and shape.common(ws).Volume > TOL:
                out.append("MURO " + wname)
    return out


results = {"aperture": [], "maniglie": [], "spallette": [], "sedute": [], "passaggi": [], "compenetrazioni": [],
           "prelievo": []}
for label, zone, own in FRONT_ZONES:
    results["prelievo"].append((label, hits_of(zone, skip_items=own)))

# 1) rotazione ante e scorrimento porte
for dd in DOORS:
    hits = hits_of(dd["sweep"])
    for o in DOORS:
        if o["name"] != dd["name"] and dd["sweep"].BoundBox.intersect(o["sweep"].BoundBox) \
                and dd["sweep"].common(o["sweep"]).Volume > TOL:
            hits.append("%s %s" % (o["kind"].upper(), o["name"]))
    for sl in SLIDES:
        for key in ("shape", "closed"):
            if dd["sweep"].common(sl[key]).Volume > TOL:
                hits.append("SCORREVOLE %s" % sl["name"])
    dd["mark"].ViewObject.ShapeColor = (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3)
    results["aperture"].append((dd["name"], hits))
for sl in SLIDES:
    hits = hits_of(sl["shape"])
    for dd in DOORS:
        if sl["shape"].common(dd["sweep"]).Volume > TOL:
            hits.append("%s %s" % (dd["kind"].upper(), dd["name"]))
    sl["mark"].ViewObject.ShapeColor = (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3)
    results["aperture"].append((sl["name"] + " (scorrevole aperta)", hits))

# 2) maniglia con anta aperta a 90 gradi, 3) spalletta per stipite
for dd in DOORS:
    if dd["handle"] is not None:
        results["maniglie"].append((dd["name"], hits_of(dd["handle"])))
        results["spallette"].append((dd["name"], [w for w in hits_of(dd["probe"]) if w.startswith("MURO")]))

# 4) spazio libero dietro le sedute (misurato fino a 1,5 m)
for name, item, (ox, oy), (dx, dy), hw in SEATS:
    px, py = (-dy, dx)
    zone = rel_box(ox, oy, (dx, dy), (px, py), (0.002, 1.5), (-hw, hw), 0.05, 1.00)
    free = 1.5
    for it, label, sh in CHECK + [(w, w, s) for w, s in WALLS]:
        if it == item or not zone.BoundBox.intersect(sh.BoundBox):
            continue
        c = zone.common(sh)
        if c.Volume > TOL:
            dist = min((v.Point.x/S - ox)*dx + (v.Point.y/S - oy)*dy for v in c.Vertexes)
            free = min(free, dist)
    results["sedute"].append((name, free))

# 5) passaggi minimi tra elementi (distanza in pianta)
PASSAGES = [
    ("Ingresso -> zona notte: sedia est / armadio ingresso", "Sedia_2", "Armadio_Ingresso", 0.80),
    ("Ingresso -> zona notte: sedia sud / tramezzo", "Sedia_3", "Tramezzo_Soggiorno", 0.80),
    ("Ingresso: sedia est / muro bagno", "Sedia_2", "Tramezzo_Ingresso_Bagno", 0.80),
    ("Cucina: isola / basi", "Isola_Top", "Top_Cucina", 0.90),
    ("Cucina: isola / colonne", "Isola_Top", "Colonne_Frigo_Forno", 0.80),
    ("Disimpegno notte: larghezza", "Tramezzo_Camera", "Tramezzo_Corridoio_Nord", 1.00),
    ("Camera: lato letto sud", "Letto_Telaio", "Muro_Sud", 0.60),
    ("Camera: lato letto nord", "Letto_Telaio", "Tramezzo_Camera", 0.60),
    ("Cabina: passaggio davanti modulo est", "Cabina_Modulo_Est", "Tramezzo_Bagno_Armadio", 0.90),
    ("Cabina: passaggio davanti modulo nord", "Cabina_Modulo_Nord", "Tramezzo_Corridoio_Nord", 0.90),
]
for label, a, b, mn in PASSAGES:
    dist = doc.getObject(a).Shape.distToShape(doc.getObject(b).Shape)[0] / S
    results["passaggi"].append((label, dist, mn))

# 6) arredi che si compenetrano o entrano nei muri
for i in range(len(CHECK)):
    for j in range(i+1, len(CHECK)):
        a, b = CHECK[i], CHECK[j]
        if a[0] != b[0] and a[2].BoundBox.intersect(b[2].BoundBox) and a[2].common(b[2]).Volume > TOL:
            results["compenetrazioni"].append("%s <-> %s" % (a[1], b[1]))
for item, label, sh in CHECK:
    for wname, ws in WALLS:
        if sh.BoundBox.intersect(ws.BoundBox) and sh.common(ws).Volume > TOL:
            results["compenetrazioni"].append("%s dentro %s" % (label, wname))

doc.recompute()

# ================= REPORT =================
def ok(lst):
    return "OK" if not lst else "PROBLEMA: " + ", ".join(lst)


print("=== 1. APERTURA ANTE / SCORREVOLI ===")
for n, h in results["aperture"]:
    print("%-34s %s" % (n, ok(h)))
print("=== 2. MANIGLIE CON ANTA APERTA A 90 GRADI ===")
for n, h in results["maniglie"]:
    print("%-34s %s" % (n, ok(h)))
print("=== 3. SPALLETTE >= %.0f cm (stipite/controtelaio) ===" % (MIN_SPALLA*100))
for n, h in results["spallette"]:
    print("%-34s %s" % (n, ok(h)))
print("=== 4. SPAZIO DIETRO LE SEDUTE (min %.0f cm) ===" % (MIN_SEDUTA*100))
for n, f in results["sedute"]:
    print("%-34s %3.0f cm  %s" % (n, f*100, "OK" if f >= MIN_SEDUTA else "PROBLEMA"))
print("=== 5. PASSAGGI ===")
for label, dist, mn in results["passaggi"]:
    print("%-52s %3.0f cm (min %3.0f)  %s" % (label, dist*100, mn*100, "OK" if dist >= mn - 1e-6 else "PROBLEMA"))
print("=== 5b. ZONE DI PRELIEVO DAVANTI AGLI ARMADI (min 70 cm) ===")
for n, h in results["prelievo"]:
    print("%-34s %s" % (n, ok(h)))
print("=== 6. COMPENETRAZIONI ARREDI ===")
print("\n".join(results["compenetrazioni"]) if results["compenetrazioni"] else "nessuna")
print("=== 7. LUCI NETTE / LUCI MURO ===")
for label, nw, nh, rw, rh, note in OPENINGS:
    print("%-24s netta %3.0fx%3.0f  muro %3.0fx%3.0f  %s" % (label, nw*100, nh*100, rw*100, rh*100, note))

rooms = {
    "Zona giorno (sogg.+cucina+ingresso)": 6.15*4.55 + 7.65*2.85,
    "Camera": 5.65*3.25,
    "Bagno": 2.20*2.85,
    "Cabina armadio": 1.85*2.85,
    "Disimpegno notte": 5.65*1.10,
}
print("=== SUPERFICI NETTE (m2) ===")
for k, v in rooms.items():
    print("%-36s %.1f" % (k, v))
print("Totale netto %.1f m2 - lordo %.1f m2" % (sum(rooms.values()), 12.5*8.0))
problems = sum(1 for _, h in results["aperture"] + results["maniglie"] + results["spallette"] + results["prelievo"] if h) \
    + sum(1 for _, f in results["sedute"] if f < MIN_SEDUTA) \
    + sum(1 for _, d, m in results["passaggi"] if d < m - 1e-6) + len(results["compenetrazioni"])
print("TOTALE PROBLEMI:", problems)
