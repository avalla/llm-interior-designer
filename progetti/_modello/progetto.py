# <NOME PROGETTO>. Brief e registro assunzioni: brief.md. Esempio completo: ../appartamento-100mq/progetto.py
# Eseguire in FreeCAD via MCP:
#   P = "/Users/andrea/dev/tmp/freecad/progetti/<cartella>/progetto.py"
#   exec(open(P).read(), {"__file__": P, "__name__": "__main__"})
# FASE = 1 costruisce solo l'involucro (rilievo), 2 aggiunge gli arredi principali, 3 dettagli e decoro.
# Le fasi successive AGGIUNGONO: non spostano la geometria delle fasi precedenti.
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import arredo  # noqa: E402
importlib.reload(arredo)
from arredo import *  # noqa: E402,F403

FASE = 1
nuovo("Progetto", HERE, interno=(0.30, 0.30, 0.30, 0.30), altezza=2.70)   # filo interno muri perimetrali
c = COL

# ======================= FASE 1 - RILIEVO: INVOLUCRO, APERTURE, MURI, LOCALI =======================
# Ordine obbligato: window()/opening() PRIMA dei wall() che attraversano.
# window("Finestra_X", yc, x0, x1, davanzale, h_sup, "Locale")
# opening("Porta_X", x0, y0, x1, y1, h_foro, luce_netta, h_netta); jambs(...); hinged(...) / sliding(...)
# wall("Muro_X", x0, y0, x1, y1)
# stanza("Locale", [(x0, y0, x1, y1)], (x_etichetta, y_etichetta), abitabile=True)
# ingresso(x, y)

if FASE >= 2:
    # ======================= FASE 2 - ARREDI PRINCIPALI (letti, divani, tavoli, cucina, armadi) =======================
    # Per ogni arredo registra l'USO: sedia()/seduta(), zona_prelievo(), passaggio(), destinazione(), tv(), coerenza_altezze()
    pass

if FASE >= 3:
    # ======================= FASE 3 - DETTAGLI, LUCI, DECORO =======================
    pass

# ======================= ANNOTAZIONI DI PIANTA (prima dell'export) =======================
# quote([...], True, y_linea) / quote([...], False, x_linea); etichetta("P 80x210", x, y); nota("...")

verifica()
