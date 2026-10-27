# Appartamento ~100 m2 (12.5 x 8.0 m lordi) - generato per FreeCAD 1.1
# Coordinate in metri (convertite in mm), origine = angolo SO esterno, y verso nord.
import FreeCAD as App, FreeCADGui as Gui, Part, math

V = App.Vector
S = 1000.0
H = 2.70  # altezza interna

if App.listDocuments().get("Appartamento"):
    App.closeDocument("Appartamento")
doc = App.newDocument("Appartamento")

# ---------- colori (stile moderno, toni chiari) ----------
WALL = (0.97, 0.97, 0.96); WHITE = (0.95, 0.95, 0.94); OAK = (0.78, 0.64, 0.46)
FLOOR = (0.85, 0.74, 0.58); TILE = (0.80, 0.80, 0.79); BLACK = (0.13, 0.13, 0.14)
GREY = (0.58, 0.59, 0.61); LGREY = (0.84, 0.84, 0.84); GLASS = (0.72, 0.86, 0.95)
STEEL = (0.76, 0.77, 0.79); SAGE = (0.60, 0.68, 0.58); GREEN = (0.33, 0.52, 0.30)
TERRA = (0.74, 0.47, 0.36); DARK = (0.30, 0.30, 0.32); RUG = (0.88, 0.86, 0.82)

groups, CHECK, WALLS = {}, [], []

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

# ---------- aperture (porte e finestre) ----------
OPEN = [
    B(7.00, 7.65, 0, 7.90, 8.05, 2.15),   # porta ingresso (muro N)
    B(6.40, 4.00, 0, 6.60, 4.90, 2.10),   # disimpegno -> soggiorno
    B(6.60, 3.50, 0, 7.40, 3.70, 2.10),   # disimpegno -> camera
    B(8.10, 4.70, 0, 8.90, 4.90, 2.10),   # corridoio -> bagno
    B(10.40, 4.70, 0, 11.10, 4.90, 2.10), # corridoio -> cabina armadio
    B(1.00, -0.05, 0, 5.50, 0.35, 2.40),  # vetrata soggiorno (S)
    B(8.20, -0.05, 0, 10.60, 0.35, 2.40), # portafinestra camera (S)
    B(1.40, 7.65, 1.20, 3.20, 8.05, 2.20),# finestra cucina (N), davanzale sopra il rubinetto
    B(9.55, 7.65, 1.60, 10.15, 8.05, 2.20),# finestra alta bagno (N)
]

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
wall("Tramezzo_Soggiorno", 6.45, 0.3, 6.55, 7.7)
wall("Tramezzo_Camera", 6.55, 3.55, 12.2, 3.65)
wall("Tramezzo_Corridoio_Bagno", 7.95, 4.75, 12.2, 4.85)
wall("Tramezzo_Disimpegno_Bagno", 7.95, 4.85, 8.05, 7.7)
wall("Tramezzo_Bagno_Armadio", 10.25, 4.85, 10.35, 7.7)

box("Solaio", 0, 0, -0.20, 12.5, 8.0, 0, FLOOR, "Strutture", check=False)
box("Pavimento_Bagno", 8.05, 4.85, 0, 10.25, 7.7, 0.004, TILE, "Strutture", check=False)

# ---------- finestre (vetro + telaio nero), tutte su muri N/S ----------
def window(name, yc, x0, x1, z0, z1, mullion=False):
    t = 0.05
    fr = [B(x0, yc-0.05, z0, x0+t, yc+0.05, z1), B(x1-t, yc-0.05, z0, x1, yc+0.05, z1),
          B(x0, yc-0.05, z1-t, x1, yc+0.05, z1), B(x0, yc-0.05, z0, x1, yc+0.05, z0+0.03)]
    if mullion:
        xm = (x0+x1)/2
        fr.append(B(xm-t/2, yc-0.05, z0, xm+t/2, yc+0.05, z1))
    add(name+"_Telaio", Part.makeCompound(fr), BLACK, "Serramenti", check=False)
    add(name+"_Vetro", B(x0+t, yc-0.01, z0+0.03, x1-t, yc+0.01, z1-t), GLASS, "Serramenti", check=False, tr=65)

window("Vetrata_Soggiorno", 0.15, 1.00, 5.50, 0, 2.40, mullion=True)
window("Portafinestra_Camera", 0.15, 8.20, 10.60, 0, 2.40, mullion=True)
window("Finestra_Cucina", 7.85, 1.40, 3.20, 1.20, 2.20, mullion=True)
window("Finestra_Bagno", 7.85, 9.55, 10.15, 1.60, 2.20)

# ---------- porte: anta aperta a 90 gradi + area di rotazione ----------
DOORS = []

def door(name, hx, hy, d, n, w, color=WHITE, hgt=2.10, z0=0.0, leaf=True, kind="Porta"):
    """Cerniera (hx,hy) sul filo muro lato apertura; d = verso anta chiusa, n = verso apertura.
    z0/hgt = quota inferiore/superiore dell'anta (finestre e ante armadio usano lo stesso calcolo)."""
    if leaf:
        xs = [hx + d[0]*a + n[0]*b for a in (0, 0.04) for b in (0, w)]
        ys = [hy + d[1]*a + n[1]*b for a in (0, 0.04) for b in (0, w)]
        add(name+"_Anta", B(min(xs), min(ys), z0+0.01, max(xs), max(ys), hgt), color, "Porte", check=False)
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
    DOORS.append((name, sweep, m, kind))

door("Porta_Ingresso", 7.90, 7.70, (-1, 0), (0, -1), 0.90, color=DARK)
door("Porta_Soggiorno", 6.45, 4.00, (0, 1), (-1, 0), 0.90)
door("Porta_Camera", 6.60, 3.55, (1, 0), (0, -1), 0.80)
door("Porta_Bagno", 8.10, 4.85, (1, 0), (0, 1), 0.80)
door("Porta_Cabina", 10.40, 4.85, (1, 0), (0, 1), 0.70)
# finestre ad anta con apertura verso l'interno (le vetrate di soggiorno e camera sono scorrevoli)
door("Finestra_Cucina_Anta_SX", 1.45, 7.70, (1, 0), (0, -1), 0.825, z0=1.23, hgt=2.15, leaf=False, kind="Finestra")
door("Finestra_Cucina_Anta_DX", 3.15, 7.70, (-1, 0), (0, -1), 0.825, z0=1.23, hgt=2.15, leaf=False, kind="Finestra")
door("Finestra_Bagno_Anta", 9.60, 7.70, (1, 0), (0, -1), 0.50, z0=1.63, hgt=2.15, leaf=False, kind="Finestra")

# ================= ARREDI =================
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

# --- Zona pranzo ---
g = "Pranzo"
cyl("Tavolo_Base", 5.20, 6.40, 0, 0.28, 0.03, BLACK, g, item="Tavolo")
cyl("Tavolo_Gamba", 5.20, 6.40, 0.03, 0.06, 0.69, BLACK, g, item="Tavolo")
cyl("Tavolo_Piano", 5.20, 6.40, 0.72, 0.55, 0.03, OAK, g, item="Tavolo")
for i, (cx, cy, bx, by) in enumerate([(4.45, 6.40, -1, 0), (5.95, 6.40, 1, 0), (5.20, 5.65, 0, -1), (5.20, 7.15, 0, 1)]):
    sh = [B(cx-0.21, cy-0.21, 0.43, cx+0.21, cy+0.21, 0.47), B(cx-0.04, cy-0.04, 0, cx+0.04, cy+0.04, 0.43)]
    if bx:
        xb = cx + bx*0.19
        sh.append(B(min(xb, xb+bx*0.03), cy-0.21, 0.47, max(xb, xb+bx*0.03), cy+0.21, 0.85))
    else:
        yb = cy + by*0.19
        sh.append(B(cx-0.21, min(yb, yb+by*0.03), 0.47, cx+0.21, max(yb, yb+by*0.03), 0.85))
    add("Sedia_%d" % (i+1), Part.makeCompound(sh), BLACK, g)
cyl("Lampada_Tavolo", 5.20, 6.40, 1.75, 0.25, 0.18, BLACK, g, item="Lampada_Tavolo")
cyl("Lampada_Tavolo_Cavo", 5.20, 6.40, 1.93, 0.005, H-1.93, BLACK, g, item="Lampada_Tavolo")

# --- Cucina ---
g = "Cucina"
box("Colonne_Frigo_Forno", 0.30, 5.00, 0, 0.90, 7.70, 2.30, WHITE, g)
box("Zoccolo", 0.90, 7.15, 0, 4.20, 7.70, 0.10, BLACK, g, item="Basi")
box("Basi_Cucina", 0.90, 7.10, 0.10, 4.20, 7.70, 0.86, WHITE, g, item="Basi")
box("Top_Cucina", 0.90, 7.05, 0.86, 4.20, 7.70, 0.90, BLACK, g, item="Basi")
# lavello centrato sotto la finestra, rubinetto basso (top 1.11 < davanzale 1.20);
# piano cottura e cappa sotto i pensili, lontani dalla finestra
box("Piano_Cottura", 3.35, 7.15, 0.90, 3.95, 7.65, 0.905, (0.05, 0.05, 0.05), g)
box("Lavello", 1.90, 7.20, 0.90, 2.70, 7.60, 0.91, STEEL, g)
cyl("Rubinetto", 2.30, 7.63, 0.91, 0.02, 0.20, STEEL, g)
box("Pensili_Est", 3.25, 7.35, 1.50, 4.20, 7.70, 2.30, WHITE, g)
box("Cappa_Integrata", 3.35, 7.35, 1.40, 3.95, 7.70, 1.50, STEEL, g)
box("Isola_Base", 1.80, 5.40, 0, 4.00, 6.10, 0.90, WHITE, g, item="Isola")
box("Isola_Top", 1.75, 5.05, 0.90, 4.05, 6.15, 0.94, OAK, g, item="Isola")
for i, x in enumerate((2.30, 3.00, 3.70)):
    cyl("Sgabello_%d_Seduta" % (i+1), x, 4.85, 0.62, 0.19, 0.05, BLACK, g, item="Sgabello_%d" % i)
    cyl("Sgabello_%d_Gamba" % (i+1), x, 4.85, 0, 0.03, 0.62, BLACK, g, item="Sgabello_%d" % i)
for i, x in enumerate((2.40, 3.40)):
    cyl("Lampada_Isola_%d" % (i+1), x, 5.60, 1.70, 0.12, 0.18, BLACK, g, item="Lamp_Isola_%d" % i)
    cyl("Lampada_Isola_%d_Cavo" % (i+1), x, 5.60, 1.88, 0.005, H-1.88, BLACK, g, item="Lamp_Isola_%d" % i)

# --- Disimpegno / ingresso ---
g = "Disimpegno"
box("Armadio_Ingresso", 6.55, 5.20, 0, 7.00, 6.90, 2.40, WHITE, g)
box("Specchio_Ingresso", 7.93, 5.40, 1.00, 7.95, 6.40, 2.00, GLASS, g, tr=30)
box("Tappeto_Ingresso", 7.05, 6.90, 0, 7.85, 7.40, 0.01, DARK, g, check=False)

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
# armadio Nord a tutta larghezza (chiude l'angolo), armadio Est fino a y=6.60:
# cosi' le ante dei due armadi non si incrociano nell'angolo
box("Armadio_Nord", 10.35, 7.10, 0, 12.20, 7.70, 2.40, WHITE, g)
box("Armadio_Est", 11.60, 4.85, 0, 12.20, 6.60, 2.40, WHITE, g)
for i, (hy, d) in enumerate([(4.85, 1), (5.725, -1), (5.725, 1), (6.60, -1)]):
    door("Armadio_Est_Anta_%d" % (i+1), 11.60, hy, (0, d), (-1, 0), 0.4375, hgt=2.40, leaf=False, kind="Anta armadio")
for i, (hx, d) in enumerate([(10.35, 1), (11.275, -1), (11.275, 1), (12.20, -1)]):
    door("Armadio_Nord_Anta_%d" % (i+1), hx, 7.10, (d, 0), (0, -1), 0.4625, hgt=2.40, leaf=False, kind="Anta armadio")
box("Specchio_Cabina", 10.35, 5.80, 0.30, 10.37, 6.60, 2.00, GLASS, g, tr=30)

doc.recompute()

# ================= VERIFICHE =================
TOL = 1000.0  # 1 cm3
report = []

for dname, sweep, mark, kind in DOORS:
    hits = []
    for item, label, sh in CHECK:
        if sweep.BoundBox.intersect(sh.BoundBox):
            v = sweep.common(sh).Volume
            if v > TOL:
                hits.append("%s (%.0f cm3)" % (label, v/1000))
    for wname, ws in WALLS:
        if sweep.BoundBox.intersect(ws.BoundBox):
            v = sweep.common(ws).Volume
            if v > TOL:
                hits.append("MURO %s (%.0f cm3)" % (wname, v/1000))
    for oname, osw, _, okind in DOORS:
        if oname != dname and sweep.BoundBox.intersect(osw.BoundBox) and sweep.common(osw).Volume > TOL:
            hits.append("%s %s" % (okind.upper(), oname))
    mark.ViewObject.ShapeColor = (0.9, 0.2, 0.2) if hits else (0.3, 0.8, 0.3)
    report.append("%-26s %s" % (dname, "OK" if not hits else "CONFLITTO con " + ", ".join(hits)))

overl = []
for i in range(len(CHECK)):
    for j in range(i+1, len(CHECK)):
        a, b = CHECK[i], CHECK[j]
        if a[0] == b[0] or not a[2].BoundBox.intersect(b[2].BoundBox):
            continue
        v = a[2].common(b[2]).Volume
        if v > TOL:
            overl.append("%s <-> %s (%.0f cm3)" % (a[1], b[1], v/1000))
for item, label, sh in CHECK:
    for wname, ws in WALLS:
        if sh.BoundBox.intersect(ws.BoundBox) and sh.common(ws).Volume > TOL:
            overl.append("%s dentro %s" % (label, wname))

doc.recompute()
print("=== VERIFICA APERTURE (porte, finestre, ante armadi) ===")
print("\n".join(report))
print("=== COMPENETRAZIONI ARREDI ===")
print("\n".join(overl) if overl else "nessuna")
rooms = {"Soggiorno+Cucina": (6.15*7.4), "Camera": (5.65*3.25), "Bagno": (2.2*2.85),
         "Cabina armadio": (1.85*2.85), "Disimpegno+corridoio": (1.40*4.05 + 4.25*1.10)}
print("=== SUPERFICI NETTE (m2) ===")
for k, v in rooms.items():
    print("%-22s %.1f" % (k, v))
print("Totale netto %.1f m2 - lordo %.1f m2" % (sum(rooms.values()), 12.5*8.0))
