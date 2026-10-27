# Regole progettuali

Fonte unica delle soglie. `lib/arredo.py` (dizionario `REGOLE`) le rispecchia: cambiando una soglia qui, si aggiorna anche li'.
Ogni regola distingue **minimo** (sotto: NON CONFORME), **comfort** (sotto: nota migliorativa) e **fonte**.
Le soglie normative sono indicative: per un progetto reale fanno fede il regolamento edilizio comunale e il tecnico abilitato.

## Porte e finestre

| Regola | Minimo | Comfort | Fonte | Verifica |
|---|---|---|---|---|
| Luce muro porta interna | netta + 5 cm per lato, h 215 | - | pratica di posa controtelai | automatica (foro generato) |
| Luce muro porta blindata | netta + 7,5 cm per lato, h 220 | - | pratica di posa | automatica |
| Spalletta lato cerniera | 10 cm | 15 cm | stipite + maniglia | automatica |
| Maniglia con anta a 90 gradi | 7 cm liberi dal muro | - | ingombro maniglie comuni | automatica |
| Traiettoria anta / scorrevole | libera da arredi, sanitari, altre ante | - | Astra par. 7 | automatica (3D) |
| Porta in corridoio < 1,20 m | preferire scorrevole | - | esperienza progetti | manuale |
| Luce muro finestra | serramento + 5 cm per lato | - | controtelaio | automatica |
| Anta finestra verso interno | libera sopra il davanzale (rubinetti, cappe, pensili) | - | lezione L07 | automatica (3D) |
| Rapporto aeroilluminante locali abitabili | 1/8 del pavimento | - | DM 5/7/1975 (indicativo) | automatica |
| Bagno | finestra apribile o aerazione forzata | - | DM 5/7/1975 (indicativo) | automatica / NON VERIFICABILE |
| Apertura > 2,5 m in muro esterno | architrave da strutturista | - | - | NON VERIFICABILE |

## Arredi, sedute, passaggi

| Regola | Minimo | Comfort | Fonte | Verifica |
|---|---|---|---|---|
| Bordo piano (tavolo, isola, scrivania) -> ostacolo dietro la seduta | 75 cm (alzarsi) | 90 cm (passare dietro chi siede) | ergonomia corrente | automatica |
| Altezza piano - seduta | 25-32 cm | - | ergonomia corrente | automatica |
| Percorso dall'ingresso a ogni zona d'uso | larghezza 60 cm continua | - | Astra par. 21 | automatica (griglia 5 cm) |
| Passaggio principale | 80 cm | 90 cm | ergonomia corrente | automatica (per coppia di oggetti) |
| Corsia cucina isola/basi | 90 cm | 110 cm | ergonomia corrente | automatica |
| Lati letto matrimoniale | 60 cm | 70 cm | ergonomia corrente | automatica |
| Zona di prelievo davanti ad armadi e vani | 70 cm liberi | 90 cm | ergonomia corrente | automatica |
| Angolo tra due armadi a L | cabina a giorno o modulo angolare, niente battenti nell'angolo | - | lezione L01 | manuale |
| Disimpegno / corridoio | 100 cm | 110 cm | ergonomia corrente | automatica |
| Occupazione pavimento locali abitabili | - | <= 40% | interioragent (target VLM 0,4) | automatica |
| TV rispetto alle finestre | non sopra/davanti/accanto sulla stessa parete (>= 1 m) | parete laterale >= 1,5 m | Astra par. 11 | automatica |
| Montaggio arredi alti | diagonale (altezza x profondita') <= altezza locale - 2 cm | - | pratica di montaggio | automatica |

## Superfici minime (riferimento DM 5/7/1975, indicativo)

| Locale | Minimo |
|---|---|
| Camera doppia | 14 m2 |
| Camera singola | 9 m2 |
| Soggiorno | 14 m2 |
| Cabina armadio, disimpegno, vano tecnico | locali non abitabili: nessun obbligo di finestra |
