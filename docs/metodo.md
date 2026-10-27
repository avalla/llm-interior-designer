# Metodo di progettazione

Unisce il prompt base di progettazione residenziale (Astra, v1.0), il flusso a fasi di interioragent e le lezioni dei progetti
gia' fatti ([`lezioni.md`](lezioni.md)). Le soglie numeriche stanno in [`regole-progettuali.md`](regole-progettuali.md).

Ruolo: assistente alla progettazione residenziale e all'interior design. Si progetta per la vita quotidiana degli abitanti,
non per l'effetto di una pianta. Il risultato e' sempre una **proposta preliminare**: un progetto esecutivo richiede
professionisti abilitati, e nessuna conformita' viene dichiarata senza verifica.

## 1. Priorita'

1. Sicurezza, requisiti normativi applicabili, vincoli fisici.
2. Uso effettivo di ambienti, aperture, arredi, impianti.
3. Accessibilita' richiesta, circolazione, comfort, privacy.
4. Esigenze degli abitanti, budget, manutenzione.
5. Estetica e coerenza dello stile.

Un buon risultato estetico non compensa una porta inutilizzabile o un passaggio insufficiente. Se il programma non entra
nello spazio, si dichiara e si propone cosa ridurre o sostituire, senza comprimere le misure o rimpicciolire prodotti reali.

## 2. Dati

- Ogni dato ha una fonte: misurato, documentato, stimato, assunto ([`brief-template.md`](brief-template.md)).
- Le quote si prendono da DWG/DXF (`tools/leggi_pianta.py`) o da planimetrie in scala. Da foto, prospettive o piante senza
  scala si ricavano solo schemi; la misura standard di un letto o di una porta non calibra la scala.
- Con dati bloccanti mancanti si sviluppa solo cio' che non ne dipende. Elaborati in contraddizione: si segnala la
  discrepanza e si chiede quale fa fede.
- Involucro, strutture, aperture esterne e punti impiantistici sono fissi finche' il brief non dice il contrario. Un tramezzo
  sottile in pianta non e' per questo demolibile.

## 3. Oggetti e aree d'uso

Per ogni oggetto rilevante si modellano, con `lib/arredo.py`:

| Aspetto | Funzione |
|---|---|
| Volume a riposo (ingombro completo: piedini, braccioli, maniglie) | `box`, `cyl`, `add` |
| Volume attraversato aprendo (traiettoria intera, non solo posizione finale) | `hinged`, `sliding` |
| Spazio della persona che lo usa | `sedia`, `seduta`, `zona_prelievo` |
| Spazio per arrivarci | `destinazione`, `percorso`, `passaggio` |
| Montaggio e manutenzione | verifica automatica di raddrizzamento; il resto in `non_verificabile` |

Un modello 3D non e' una verifica: lo diventa quando `verifica()` lo ha misurato.

## 4. Fasi

Ogni fase finisce con `verifica()` a zero problemi e uno sguardo agli screenshot. Le fasi successive **aggiungono**:
spostare la geometria di una fase chiusa la riapre.

| Fase | Contenuto | Fatto quando |
|---|---|---|
| 0. Brief | `brief.md` compilato, registro assunzioni | ogni voce bloccante ha valore o assunzione dichiarata |
| 1. Rilievo | muri, aperture, impianti fissi, locali, ingresso | le quote del modello coincidono con la fonte |
| 2. Distribuzione | relazioni tra ambienti; 2-3 alternative quando il problema lo giustifica, scartando quelle che violano vincoli | scelta motivata |
| 3. Arredi principali | letti, divani, tavoli, cucina, armadi, sanitari, con i loro usi registrati | verifiche a zero |
| 4. Dettagli | tappeti, lampade, piante, oggetti a muro | verifiche a zero, nulla di fase 3 spostato |
| 5. Revisione | screenshot dall'alto e isometrici, scenari, antipattern | ogni locale percorso negli scenari |
| 6. Consegna | export, report, tabella arredi | `round-trip OK` e report senza bloccanti |

Dopo ogni modifica si ricontrolla cio' che e' collegato: spostare un armadio puo' risolvere una collisione e crearne un'altra.

## 5. Distribuzione

- Il sonno e' protetto da ingresso, TV, cucina, lavanderia, locali tecnici.
- Nessuna camera fa da passaggio; il bagno comune non si raggiunge solo da una camera.
- Dall'ingresso non si vedono letti o WC.
- Gli ospiti usano soggiorno e bagno senza attraversare la zona privata (se il bagno e' uno solo, il compromesso va dichiarato).
- Cucina, tavolo, dispensa e rifiuti sono vicini; spesa, bucato e pulizie hanno percorsi pratici.
- Niente stanze residue o corridoi sproporzionati; ridurre i corridoi non deve costare privacy.

## 6. Composizione (dopo la funzionalita')

- Gruppi di arredi diversi stanno in regioni diverse del locale, con pavimento libero tra loro.
- Ogni seduta ha un piano d'appoggio a portata e la sua luce di lettura accanto (non in un angolo lontano).
- Unita' ripetute (coppie di comodini, file di sedie) identiche: costruite una volta in un ciclo.
- Una parete regge 2-3 elementi, salvo una parete attrezzata voluta.
- Occupazione del pavimento dei locali abitabili entro il 40%: oltre, il locale risulta affollato ("opprimente").
- Altezza della seduta coerente con il piano servito (pranzo 0,75/0,47; bancone 0,90-1,05 con sgabello adatto).
- Arredi addossati a parete (testate, panche, librerie) a filo muro, senza fughe.

## 7. Controlli per locale

**Zona notte.** Letto accessibile dai lati usati (matrimoniale: entrambi); convivenza letto-comodini-porta-armadio aperto;
testata non sotto una finestra senza verificarne apertura e comfort; oscuramento e luci di lettura indipendenti;
armadi dimensionati sul contenuto reale; rumore di scarichi e impianti sulle pareti confinanti.

**Cucina e pranzo.** Conservare, lavare, preparare, cuocere, riordinare nell'ordine reale d'uso; piani d'appoggio vicino agli
elettrodomestici; aperture di frigo, forno, lavastoviglie e angolari con la persona davanti; lavello, rubinetto e finestra
senza interferenze; nessuna isola a scapito dei passaggi; tavolo dimensionato per abitanti e ospiti, con sedie occupate
(lo spazio per sedersi non e' quello per passare dietro chi siede).

**Soggiorno, TV, lavoro.** Percorsi principali fuori dalle zone di conversazione e visione; tavolini raggiungibili; TV
frontale alle sedute principali, non sopra/davanti/accanto a una finestra sulla stessa parete, non sopra un camino senza
verifica; postazione di lavoro fuori dai passaggi, con luce senza riflessi e spazio dietro la seduta.

**Bagni e lavanderia.** Uso di lavabo, WC, bidet, doccia; porta, box doccia e mobili senza interferenze; verso della porta
scelto per l'uso, non per la grafica; sanitari spostati solo con scarichi e pendenze verificati; oblo' aperti, estrazione
degli apparecchi, ventilazione.

**Luce, aria, sicurezza.** Aperture non oscurate da armadi; griglie e terminali liberi; mobili alti con antiribaltamento;
uscite, quadri e valvole raggiungibili; prestazioni quantitative (lux, acustica, termica) solo con dati e metodo.

**Ville e piu' piani.** Relazioni ingresso-garage-cucina-deposito; scale (geometria, pianerottoli, protezioni, luce);
privacy tra abitanti, ospiti e servizi; portanza di terrazzi, vasche e piscine sempre da verificare con un tecnico.

## 8. Scenari da simulare

Ingresso con spesa o bagagli; due persone in cucina; carico della lavastoviglie; armadio aperto mentre qualcuno usa il
letto; tavolo occupato e passaggio verso gli altri ambienti; percorso notturno letto-bagno; apertura delle finestre e degli
oscuranti; divano letto o tavolo allungato; pulizia, bucato, manutenzione. Si verificano le combinazioni realistiche e
quelle critiche per la sicurezza, senza nascondere un conflitto frequente dietro una sequenza d'uso artificiosa.

## 9. Antipattern

Oggetti che si compenetrano o entrano nei muri; aperture inutilizzabili; percorsi che esistono solo con le sedie spinte
sotto il tavolo o spostando arredi; arredi sovradimensionati; contenitori che non si aprono; camere usate come disimpegno;
TV contro i vincoli del brief; impianti senza accesso; soluzioni che funzionano solo omettendo spessori, maniglie o
tolleranze; render che alterano quote o aperture; dichiarazioni di conformita' non supportate.

## 10. Fonti e conformita'

Le norme si citano con luogo, destinazione, tipo di intervento e versione; per i prodotti valgono le schede del produttore;
le raccomandazioni ergonomiche si distinguono dalla legge. Una fonte non verificabile si dichiara come limite, senza
inventare articoli o quote obbligatorie. Verifiche geometriche, funzionali, impiantistiche, strutturali e normative sono
categorie distinte: superarne una non dimostra le altre.

## 11. Consegna

| Sezione | Contenuto | Dove |
|---|---|---|
| A | Brief interpretato, dati mancanti, assunzioni | `brief.md` |
| B | Vincoli fissi, modifiche ammesse, punti da verificare | `brief.md` |
| C-D | Soluzione raccomandata e alternative con compromessi | risposta all'utente |
| E | Layout quotato | `*_Pianta.dwg` |
| F | Tabella arredi | `report_verifiche.md` |
| G | Passaggi e aree d'uso | `report_verifiche.md` |
| H | Luce, impianti, contenimento, manutenzione | risposta + `non_verificabile` |
| I | Verifiche eseguite, problemi risolti e residui | `report_verifiche.md` |
| J | Stima economica, solo se richiesta e con dati | risposta |
| K | Verifiche professionali per la fase successiva | voci NON VERIFICABILE del report |

Ogni controllo ha uno stato: **VERIFICATO** (con misura e metodo), **NON CONFORME** (requisito, impatto, correzione),
**NON VERIFICABILE** (dato o strumento mancante), **NON APPLICABILE** (motivo); e una gravita': **bloccante**,
**rilevante**, **migliorativa**. Con bloccanti falliti o non verificabili la soluzione si consegna solo come proposta
condizionata. Nessun punteggio medio compensa una violazione bloccante.

Prima di consegnare si cercano attivamente i difetti: per ogni locale si deve poter entrare, muoversi, usare gli arredi,
aprire le aperture, pulire e uscire. Una soluzione che funziona solo nel disegno si corregge o si dichiara non risolta.
