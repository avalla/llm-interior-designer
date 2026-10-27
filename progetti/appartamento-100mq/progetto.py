# Appartamento ~100 m2 (12.5 x 8.0 m lordi). Brief e assunzioni: brief.md.
# Eseguire in FreeCAD via MCP:
#   P = "/Users/andrea/dev/tmp/freecad/progetti/appartamento-100mq/progetto.py"
#   exec(open(P).read(), {"__file__": P, "__name__": "__main__"})
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import arredo  # noqa: E402
importlib.reload(arredo)
from arredo import *  # noqa: E402,F403

nuovo("Appartamento", HERE, interno=(0.30, 0.30, 12.20, 7.70), altezza=2.70)
c = COL
FB = REGOLE["telaio_blindata"]
FR = REGOLE["telaio"]

# ======================= FASE 1 - INVOLUCRO, APERTURE, MURI =======================
window("Vetrata_Soggiorno", 0.15, 1.00, 5.50, 0, 2.40, "Zona giorno", mullion=True)       # scorrevole alzante
window("Portafinestra_Camera", 0.15, 8.20, 10.60, 0, 2.40, "Camera", mullion=True)        # scorrevole
window("Finestra_Cucina", 7.85, 1.40, 3.20, 1.20, 2.20, "Zona giorno", mullion=True)      # 2 ante verso interno
window("Finestra_Bagno", 7.85, 9.55, 10.15, 1.60, 2.20, "Bagno")                          # 1 anta verso interno
hinged("Finestra_Cucina_Anta_SX", 1.45, 7.70, (1, 0), (0, -1), 0.825, z0=1.23, hgt=2.15, leaf=False, kind="Finestra", handle=False)
hinged("Finestra_Cucina_Anta_DX", 3.15, 7.70, (-1, 0), (0, -1), 0.825, z0=1.23, hgt=2.15, leaf=False, kind="Finestra", handle=False)
hinged("Finestra_Bagno_Anta", 9.60, 7.70, (1, 0), (0, -1), 0.50, z0=1.63, hgt=2.15, leaf=False, kind="Finestra", handle=False)

opening("Porta_Ingresso", 6.75, 7.65, 7.80, 8.05, 2.20, 0.90, 2.10, "blindata, controtelaio 7,5 cm")
jambs("Porta_Ingresso", 6.75, 7.70, 7.80, 8.00, 2.20, FB)
hinged("Porta_Ingresso", 7.725, 7.70, (-1, 0), (0, -1), 0.90, color=c["DARK"], frame=FB)

opening("Porta_Camera", 6.70, 3.50, 7.60, 3.70, 2.15, 0.80, 2.10)
jambs("Porta_Camera", 6.70, 3.55, 7.60, 3.65, 2.15, FR)
hinged("Porta_Camera", 6.75, 3.55, (1, 0), (0, -1), 0.80)

opening("Porta_Bagno", 8.20, 4.70, 9.10, 4.90, 2.15, 0.80, 2.10)
jambs("Porta_Bagno", 8.20, 4.75, 9.10, 4.85, 2.15, FR)
hinged("Porta_Bagno", 8.25, 4.85, (1, 0), (0, 1), 0.80)

opening("Porta_Zona_Notte", 6.40, 3.75, 6.60, 4.65, 2.15, 0.90, 2.10, "scorrevole esterno muro")
sliding("Porta_Zona_Notte", (6.40, 3.70, 0.01, 6.44, 4.70, 2.15), (6.40, 2.70, 0.01, 6.44, 3.70, 2.15))
opening("Porta_Cabina", 10.50, 4.70, 11.20, 4.90, 2.15, 0.70, 2.10, "scorrevole esterno muro")
sliding("Porta_Cabina", (10.45, 4.69, 0.01, 11.25, 4.73, 2.15), (9.65, 4.69, 0.01, 10.45, 4.73, 2.15))

wall("Muro_Sud", 0, 0, 12.5, 0.3)
wall("Muro_Nord", 0, 7.7, 12.5, 8.0)
wall("Muro_Ovest", 0, 0.3, 0.3, 7.7)
wall("Muro_Est", 12.2, 0.3, 12.5, 7.7)
wall("Tramezzo_Soggiorno", 6.45, 0.3, 6.55, 4.75)
wall("Tramezzo_Camera", 6.55, 3.55, 12.2, 3.65)
wall("Tramezzo_Corridoio_Nord", 6.45, 4.75, 12.2, 4.85)
wall("Tramezzo_Ingresso_Bagno", 7.95, 4.85, 8.05, 7.7)
wall("Tramezzo_Bagno_Armadio", 10.25, 4.85, 10.35, 7.7)
box("Solaio", 0, 0, -0.20, 12.5, 8.0, 0, c["FLOOR"], "Strutture", check=False)
box("Pavimento_Bagno", 8.05, 4.85, 0, 10.25, 7.7, 0.004, c["TILE"], "Strutture", check=False)

stanza("Zona giorno", [(0.30, 0.30, 6.45, 4.85), (0.30, 4.85, 7.95, 7.70)], (2.90, 4.45))
stanza("Camera", [(6.55, 0.30, 12.20, 3.55)], (8.70, 2.60))
stanza("Bagno", [(8.05, 4.85, 10.25, 7.70)], (9.30, 6.25), abitabile=False, tipo="bagno")
stanza("Cabina armadio", [(10.35, 4.85, 12.20, 7.70)], (10.77, 6.25), abitabile=False, righe=["CABINA", "ARMADIO"])
stanza("Disimpegno notte", [(6.55, 3.65, 12.20, 4.75)], (9.30, 4.30), abitabile=False)

# ======================= FASE 2 - ARREDI PRINCIPALI =======================
g = "Soggiorno"
box("Mobile_TV", 0.30, 1.40, 0.15, 0.75, 3.40, 0.55, c["OAK"], g)
box("TV_65", 0.31, 1.75, 0.95, 0.36, 3.05, 1.70, c["BLACK"], g)
box("Divano_Seduta", 3.40, 1.20, 0.01, 4.30, 3.60, 0.42, c["GREY"], g, item="Divano")
box("Divano_Schienale", 4.30, 1.00, 0.01, 4.50, 3.80, 0.80, c["GREY"], g, item="Divano")
box("Divano_Bracciolo_S", 3.40, 1.00, 0.01, 4.30, 1.20, 0.60, c["GREY"], g, item="Divano")
box("Divano_Bracciolo_N", 3.40, 3.60, 0.01, 4.30, 3.80, 0.60, c["GREY"], g, item="Divano")
box("Divano_Chaise", 2.60, 3.00, 0.01, 3.40, 3.80, 0.42, c["GREY"], g, item="Divano")
box("Divano_Cuscini", 4.10, 1.25, 0.42, 4.30, 3.55, 0.72, c["SAGE"], g, item="Divano")
box("Tavolino_Base", 2.00, 1.90, 0.01, 2.50, 2.50, 0.33, c["BLACK"], g, item="Tavolino")
box("Tavolino_Piano", 1.90, 1.80, 0.33, 2.60, 2.60, 0.38, c["OAK"], g, item="Tavolino")
box("Poltrona_Seduta", 1.30, 0.60, 0.01, 2.10, 1.25, 0.42, c["TERRA"], g, item="Poltrona")
box("Poltrona_Schienale", 1.30, 0.42, 0.01, 2.10, 0.60, 0.82, c["TERRA"], g, item="Poltrona")
lib = [B(5.95, 0.60, 0, 6.45, 2.60, 0.03)]
for z in (0.40, 0.80, 1.20, 1.60, 1.97):
    lib.append(B(5.95, 0.60, z, 6.45, 2.60, z + 0.03))
lib += [B(5.95, 0.60, 0, 6.45, 0.63, 2.0), B(5.95, 2.57, 0, 6.45, 2.60, 2.0), B(5.95, 1.585, 0, 6.45, 1.615, 2.0)]
add("Libreria", Part.makeCompound(lib), c["OAK"], g)
tv("TV_65")

g = "Pranzo"
TX, TY, TR = 5.35, 6.10, 0.55
cyl("Tavolo_Base", TX, TY, 0, 0.28, 0.03, c["BLACK"], g, item="Tavolo")
cyl("Tavolo_Gamba", TX, TY, 0.03, 0.06, 0.69, c["BLACK"], g, item="Tavolo")
cyl("Tavolo_Piano", TX, TY, 0.72, TR, 0.03, c["OAK"], g, item="Tavolo")
for i, (dx, dy) in enumerate([(-1, 0), (1, 0), (0, -1), (0, 1)]):   # 1=ovest 2=est 3=sud 4=nord
    sedia("Sedia_%d" % (i + 1), TX + dx * 0.75, TY + dy * 0.75, dx, dy, g, "Tavolo", TR)
coerenza_altezze("Tavolo / sedie", 0.75, 0.47)

g = "Cucina"
box("Colonne_Frigo_Forno", 0.30, 5.00, 0, 0.90, 7.70, 2.30, c["WHITE"], g)
box("Zoccolo", 0.90, 7.15, 0, 4.20, 7.70, 0.10, c["BLACK"], g, item="Basi")
box("Basi_Cucina", 0.90, 7.10, 0.10, 4.20, 7.70, 0.86, c["WHITE"], g, item="Basi")
box("Top_Cucina", 0.90, 7.05, 0.86, 4.20, 7.70, 0.90, c["BLACK"], g, item="Basi")
box("Isola_Base", 1.80, 5.40, 0, 3.70, 6.10, 0.90, c["WHITE"], g, item="Isola")
box("Isola_Top", 1.75, 5.05, 0.90, 3.75, 6.15, 0.94, c["OAK"], g, item="Isola")
for i, x in enumerate((2.15, 2.75, 3.35)):
    n = "Sgabello_%d" % (i + 1)
    cyl(n + "_Seduta", x, 4.85, 0.62, 0.19, 0.05, c["BLACK"], g, item=n)
    cyl(n + "_Gamba", x, 4.85, 0, 0.03, 0.62, c["BLACK"], g, item=n)
    seduta(n, (n, "Isola"), (x, 5.05), (0, -1), 0.19)
coerenza_altezze("Isola / sgabelli", 0.94, 0.67)

g = "Ingresso"
box("Armadio_Ingresso", 6.95, 4.85, 0, 7.95, 5.30, 2.40, c["WHITE"], g)
hinged("Armadio_Ingresso_Anta_1", 6.95, 5.30, (1, 0), (0, 1), 0.50, hgt=2.40, leaf=False, kind="Anta armadio", handle=False)
hinged("Armadio_Ingresso_Anta_2", 7.95, 5.30, (-1, 0), (0, 1), 0.50, hgt=2.40, leaf=False, kind="Anta armadio", handle=False)
zona_prelievo("Ingresso: davanti armadio", 6.96, 5.305, 7.92, 6.01, ("Armadio_Ingresso",))

g = "Disimpegno_Notte"
box("Vano_Tecnico", 11.75, 3.65, 0, 12.20, 4.75, 2.40, c["WHITE"], g)
hinged("Vano_Tecnico_Anta", 11.75, 3.70, (0, 1), (-1, 0), 0.90, hgt=2.40, leaf=False, kind="Anta armadio", handle=False)

g = "Camera"
box("Letto_Testiera", 12.08, 0.95, 0.01, 12.20, 2.95, 1.10, c["GREY"], g, item="Letto")
box("Letto_Telaio", 10.00, 1.00, 0.05, 12.08, 2.90, 0.35, c["OAK"], g, item="Letto")
box("Letto_Materasso", 10.05, 1.05, 0.35, 12.05, 2.85, 0.60, c["WHITE"], g, item="Letto")
box("Letto_Piumone", 10.05, 1.05, 0.60, 11.50, 2.85, 0.65, c["SAGE"], g, item="Letto")
box("Letto_Cuscino_1", 11.60, 1.15, 0.60, 12.00, 1.85, 0.72, c["WHITE"], g, item="Letto")
box("Letto_Cuscino_2", 11.60, 2.05, 0.60, 12.00, 2.75, 0.72, c["WHITE"], g, item="Letto")
for i, (y0, y1) in enumerate([(0.45, 0.90), (2.95, 3.40)]):
    box("Comodino_%d" % (i + 1), 11.70, y0, 0.01, 12.15, y1, 0.45, c["OAK"], g)
    cyl("Abatjour_%d" % (i + 1), 11.92, (y0 + y1) / 2, 0.45, 0.10, 0.30, c["WHITE"], g)
box("Scrivania_Piano", 6.55, 0.80, 0.72, 7.15, 2.20, 0.75, c["OAK"], g, item="Scrivania")
box("Scrivania_Gamba_1", 7.08, 0.82, 0, 7.13, 0.87, 0.72, c["BLACK"], g, item="Scrivania")
box("Scrivania_Gamba_2", 7.08, 2.13, 0, 7.13, 2.18, 0.72, c["BLACK"], g, item="Scrivania")
box("Sedia_Scrivania_Seduta", 7.25, 1.27, 0.43, 7.67, 1.69, 0.47, c["BLACK"], g, item="Sedia_Scrivania")
box("Sedia_Scrivania_Schienale", 7.64, 1.27, 0.47, 7.67, 1.69, 0.85, c["BLACK"], g, item="Sedia_Scrivania")
box("Sedia_Scrivania_Gamba", 7.42, 1.44, 0, 7.50, 1.52, 0.43, c["BLACK"], g, item="Sedia_Scrivania")
seduta("Sedia_Scrivania", ("Sedia_Scrivania", "Scrivania"), (7.15, 1.48), (1, 0), 0.21)
coerenza_altezze("Scrivania / sedia", 0.75, 0.47)

g = "Bagno"
box("Mobile_Lavabo", 8.05, 5.80, 0.55, 8.55, 6.60, 0.85, c["OAK"], g, item="Lavabo")
box("Lavabo", 8.10, 5.90, 0.85, 8.50, 6.50, 0.97, c["WHITE"], g, item="Lavabo")
cyl("Rubinetto_Lavabo", 8.12, 6.20, 0.97, 0.015, 0.20, c["STEEL"], g, item="Lavabo")
box("WC_Sospeso", 9.70, 5.97, 0.25, 10.25, 6.33, 0.40, c["WHITE"], g, item="WC")
box("WC_Coperchio", 9.72, 5.99, 0.40, 10.20, 6.31, 0.43, c["WHITE"], g, item="WC")
box("Bidet_Sospeso", 9.70, 5.20, 0.25, 10.25, 5.56, 0.40, c["WHITE"], g)
box("Piatto_Doccia", 8.05, 6.70, 0.004, 9.45, 7.70, 0.03, c["WHITE"], g)
box("Vetro_Doccia", 8.05, 6.70, 0.03, 8.85, 6.71, 2.00, c["GLASS"], g, tr=60)
box("Lavatrice", 9.65, 7.10, 0, 10.25, 7.70, 0.85, c["WHITE"], g)

g = "Cabina_Armadio"


def open_wardrobe(name, x0, y0, x1, y1, along, posts, rails, shelves_mod, drawer_mod):
    """Modulo a giorno profondo 60 cm (along='y': fronte verso -x; 'x': fronte verso -y)."""
    p = []
    for q in posts:
        p.append(B(q - 0.01, y0, 0, q + 0.01, y1, 2.40) if along == "x" else B(x0, q - 0.01, 0, x1, q + 0.01, 2.40))
    p += [B(x0, y0, 2.38, x1, y1, 2.40), B(x0, y0, 2.00, x1, y1, 2.02)]
    for i in range(len(posts) - 1):
        a0, a1 = posts[i] + 0.01, posts[i + 1] - 0.01
        seg = (lambda z0, z1: B(x0, a0, z0, x1, a1, z1)) if along == "y" else (lambda z0, z1: B(a0, y0, z0, a1, y1, z1))
        if i in shelves_mod:
            p += [seg(z, z + 0.02) for z in (0.40, 0.75, 1.10, 1.45)]
        if i in drawer_mod:
            p += [seg(0.0, 0.70), seg(1.25, 1.27)]
    add(name, Part.makeCompound(p), c["WHITE"], g)
    for i in rails:
        a0, a1 = posts[i] + 0.01, posts[i + 1] - 0.01
        if along == "y":
            r = Part.makeCylinder(0.012 * S, (a1 - a0) * S, V((x0 + x1) / 2 * S, a0 * S, 1.85 * S), V(0, 1, 0))
        else:
            r = Part.makeCylinder(0.012 * S, (a1 - a0) * S, V(a0 * S, (y0 + y1) / 2 * S, 1.85 * S), V(1, 0, 0))
        add("%s_Bastone_%d" % (name, i + 1), r, c["STEEL"], g, item=name)


open_wardrobe("Cabina_Modulo_Est", 11.60, 4.85, 12.20, 7.70, "y", [4.86, 5.80, 6.75, 7.69], [0, 1], [2], [0])
open_wardrobe("Cabina_Modulo_Nord", 10.35, 7.10, 11.60, 7.70, "x", [10.36, 10.98, 11.59], [1], [0], [])
zona_prelievo("Cabina: davanti modulo est", 10.89, 4.86, 11.595, 7.09, ("Cabina_Modulo_Est",))
zona_prelievo("Cabina: davanti modulo nord", 10.38, 6.39, 11.59, 7.095, ("Cabina_Modulo_Nord",))

# ======================= FASE 3 - DETTAGLI, LUCI, DECORO =======================
box("Tappeto", 1.20, 0.80, 0, 4.00, 3.60, 0.01, c["RUG"], "Soggiorno", check=False)
# luce di lettura accanto alla poltrona: nella posizione di prima chiudeva l'accesso al divano (25 cm)
cyl("Lampada_Base", 1.05, 0.70, 0, 0.15, 0.03, c["BLACK"], "Soggiorno", item="Lampada_Terra")
cyl("Lampada_Stelo", 1.05, 0.70, 0.03, 0.015, 1.50, c["BLACK"], "Soggiorno", item="Lampada_Terra")
cyl("Lampada_Paralume", 1.05, 0.70, 1.50, 0.20, 0.25, c["WHITE"], "Soggiorno", item="Lampada_Terra")
cyl("Pianta_Vaso", 5.85, 3.35, 0, 0.20, 0.45, c["TERRA"], "Soggiorno", item="Pianta")
add("Pianta_Foglie", Part.makeSphere(0.35 * S, V(5.85 * S, 3.35 * S, 0.95 * S)), c["GREEN"], "Soggiorno", item="Pianta")
cyl("Lampada_Tavolo", TX, TY, 1.75, 0.25, 0.18, c["BLACK"], "Pranzo", item="Lampada_Tavolo")
cyl("Lampada_Tavolo_Cavo", TX, TY, 1.93, 0.005, 2.70 - 1.93, c["BLACK"], "Pranzo", item="Lampada_Tavolo")
for i, x in enumerate((2.35, 3.15)):
    cyl("Lampada_Isola_%d" % (i + 1), x, 5.60, 1.70, 0.12, 0.18, c["BLACK"], "Cucina", item="Lamp_Isola_%d" % i)
    cyl("Lampada_Isola_%d_Cavo" % (i + 1), x, 5.60, 1.88, 0.005, 2.70 - 1.88, c["BLACK"], "Cucina", item="Lamp_Isola_%d" % i)
box("Piano_Cottura", 3.35, 7.15, 0.90, 3.95, 7.65, 0.905, (0.05, 0.05, 0.05), "Cucina")
box("Lavello", 1.90, 7.20, 0.90, 2.70, 7.60, 0.91, c["STEEL"], "Cucina")
cyl("Rubinetto", 2.30, 7.63, 0.91, 0.02, 0.20, c["STEEL"], "Cucina")       # top 1.11 < davanzale 1.20
box("Pensili_Est", 3.25, 7.35, 1.50, 4.20, 7.70, 2.30, c["WHITE"], "Cucina")
box("Cappa_Integrata", 3.35, 7.35, 1.40, 3.95, 7.70, 1.50, c["STEEL"], "Cucina")
box("Specchio_Ingresso", 7.93, 5.85, 1.00, 7.95, 6.65, 2.00, c["GLASS"], "Ingresso", tr=30)
box("Tappeto_Ingresso", 6.90, 6.90, 0, 7.65, 7.40, 0.01, c["DARK"], "Ingresso", check=False)
box("Tappeto_Camera", 9.30, 0.60, 0, 11.60, 3.30, 0.01, c["RUG"], "Camera", check=False)
box("Specchio_Bagno", 8.05, 5.85, 1.10, 8.07, 6.55, 1.90, c["GLASS"], "Bagno", tr=30)
cyl("Soffione", 8.45, 7.45, 2.05, 0.12, 0.02, c["STEEL"], "Bagno", item="Soffione")
box("Soffione_Braccio", 8.43, 7.45, 2.07, 8.47, 7.70, 2.10, c["STEEL"], "Bagno", item="Soffione")
box("Scaldasalviette", 10.20, 6.45, 0.50, 10.25, 6.95, 1.50, c["STEEL"], "Bagno")
box("Specchio_Cabina", 10.35, 5.20, 0.30, 10.37, 6.00, 2.00, c["GLASS"], "Cabina_Armadio", tr=30)

# ======================= USI, PERCORSI, PASSAGGI =======================
ingresso(7.10, 7.25)
destinazione("Zona giorno: divano (fronte seduta)", 3.00, 2.00)
destinazione("Zona giorno: poltrona", 2.70, 1.10)
destinazione("Zona giorno: tavolo lato est", 6.75, 6.10)
destinazione("Cucina: lavello", 2.30, 6.60)
destinazione("Cucina: colonne frigo/forno", 1.30, 6.00)
destinazione("Ingresso: armadio", 7.45, 5.70)
destinazione("Camera: lato letto sud", 11.00, 0.65)
destinazione("Camera: lato letto nord", 11.00, 3.22)
destinazione("Camera: scrivania", 8.00, 1.48)
destinazione("Bagno: lavabo", 8.90, 6.20)
destinazione("Bagno: WC", 9.30, 6.15)
destinazione("Bagno: doccia", 9.00, 7.20)
destinazione("Cabina: davanti ai moduli", 11.10, 6.00)
destinazione("Disimpegno: vano tecnico", 11.30, 4.20)
percorso("Percorso notturno letto -> WC", "Camera: lato letto nord", "Bagno: WC")

passaggio("Ingresso -> zona notte: sedia est / armadio ingresso", "Sedia_2", "Armadio_Ingresso", 0.80, 0.90)
passaggio("Ingresso -> zona notte: sedia sud / tramezzo", "Sedia_3", "Tramezzo_Soggiorno", 0.80, 0.90)
passaggio("Cucina: isola / basi", "Isola_Top", "Top_Cucina", 0.90, 1.10)
passaggio("Cucina: isola / colonne", "Isola_Top", "Colonne_Frigo_Forno", 0.80, 0.90)
passaggio("Disimpegno notte: larghezza", "Tramezzo_Camera", "Tramezzo_Corridoio_Nord", 1.00, 1.10)
passaggio("Camera: lato letto sud", "Letto_Telaio", "Muro_Sud", 0.60, 0.70)
passaggio("Camera: lato letto nord", "Letto_Telaio", "Tramezzo_Camera", 0.60, 0.70)
passaggio("Cabina: passaggio davanti modulo est", "Cabina_Modulo_Est", "Tramezzo_Bagno_Armadio", 0.90, 1.00)

non_verificabile("Vetrata soggiorno 4,60 m al foro", "architrave da dimensionare (strutturista)")

# ======================= ANNOTAZIONI DI PIANTA =======================
quote([0, 0.95, 5.55, 8.15, 10.65, 12.5], True, -0.5)
quote([0, 0.3, 6.45, 6.55, 12.2, 12.5], True, -0.9)
quote([0, 12.5], True, -1.3)
quote([0, 0.3, 1.35, 3.25, 6.75, 7.80, 9.50, 10.20, 12.2, 12.5], True, 8.6)
quote([0, 0.3, 7.7, 8.0], False, -0.6)
quote([0, 8.0], False, -1.0)
quote([0, 0.3, 3.55, 3.65, 4.75, 4.85, 7.7, 8.0], False, 13.1)
for t, x, y in [
    ("P 90x210 blindata - foro 105x220", 7.275, 8.25), ("P 90x210 scorrevole", 5.70, 4.20),
    ("P 80x210 - foro 90x215", 7.15, 2.55), ("P 80x210", 8.65, 4.56), ("P 70x210 scorrevole", 10.85, 4.42),
    ("V.T.", 11.975, 4.20), ("F 180x100 davanzale h120 - 2 ante", 2.30, 8.25), ("F 60x60 h160", 9.85, 8.25),
    ("PF 450x240 scorrevole", 3.25, -0.25), ("PF 240x240 scorrevole", 9.40, -0.25),
]:
    etichetta(t, x, y)
nota("Fori nei muri maggiorati di 5 cm per lato per controtelai/stipiti (7,5 cm porta blindata)  -  "
     "V.T. = vano tecnico  -  vetrata 4,60 m: architrave da dimensionare (strutturista)")

verifica()
