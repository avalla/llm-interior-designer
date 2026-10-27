---
name: export-autocad
description: Esporta un progetto per AutoCAD (pianta DWG 2D con quote e layer, DWG 3D, STEP) con report verifiche. Usare per "passami i file", DWG, DXF, STEP, AutoCAD.
---

# Export AutoCAD

## Passi

1. **Progetto a zero problemi.** Esegui `progetti/<nome>/progetto.py` in FreeCAD; deve chiudere con `TOTALE PROBLEMI: 0`.
   Con problemi aperti, risolvili (skill `arredamento`) o chiedi se l'utente vuole comunque una proposta condizionata.

2. **Annotazioni.** Se muri o aperture sono cambiati, aggiorna in `progetto.py` le catene `quote()` e le `etichetta()` di
   porte e finestre, usando le luci muro del report. Superfici dei locali, cartiglio e simboli delle scorrevoli si
   aggiornano da soli.

3. **Export.** In FreeCAD: `import arredo; arredo.esporta()`. Poi `tools/esporta.sh progetti/<nome>`: deve chiudere con
   `round-trip OK`.

4. **Anteprima.** Apri `output/<Nome>_Pianta.png` (generata dal DWG riletto): testi sovrapposti a quote o arredi, quote
   illeggibili, porte e scorrevoli riconoscibili, finestre visibili. Correggi posizioni in `progetto.py` e ripeti dal passo 3.
   Fatto quando l'anteprima e' pulita.

## Consegna

| File in `progetti/<nome>/output/` | Uso |
|---|---|
| `<Nome>_Pianta.dwg` | pianta 2D, AutoCAD 2018+, layer MURI/SERRAMENTI/PORTE/APERTURE/ARREDI/QUOTE/TESTI |
| `<Nome>_3D.dwg` | 3D a mesh: si apre con Apri ovunque, anche AutoCAD LT e Mac (L08) |
| `<Nome>_3D.step` | 3D a solidi: comando `IMPORT`, solo AutoCAD per Windows |
| `<Nome>_Pianta.png` | anteprima |
| `report_verifiche.md` | verifiche con stati e gravita', locali, luci muro, tabella arredi |

Dichiara cosa e' stato verificato (round-trip con conteggio entita') e cosa no (apertura in AutoCAD vero, se non disponibile),
e riporta le voci NON VERIFICABILE con il professionista che le chiude.
