# Progettazione d'interni con FreeCAD e Claude Code

Base di lavoro per progettare **distribuzione interna e arredamento** di appartamenti e ville parlando con un agente
(Claude Code), che costruisce il modello 3D in FreeCAD, lo **verifica** con regole di uso reale (porte che si aprono,
spazio dietro le sedie, percorsi, luce naturale, montaggio degli armadi...) e consegna i file per **AutoCAD**.

Il risultato e' sempre una **proposta preliminare**: strutture, impianti e conformita' normativa restano da verificare con
professionisti abilitati. Il report di ogni progetto elenca esplicitamente cio' che non e' stato possibile verificare.

## Cosa fa

- **Onboarding**: raccoglie file di partenza (DWG/DXF/PDF/foto), tipo di intervento, abitanti, tipologia di arredamento,
  vincoli; compila un brief con la fonte di ogni dato e il registro delle assunzioni.
- **Modello**: muri, porte (con telai e spallette), finestre (con controtelai), scorrevoli, arredi, a fasi:
  involucro -> arredi principali -> dettagli.
- **Verifiche automatiche** su ogni esecuzione, con stato (VERIFICATO / NON CONFORME / NON VERIFICABILE / NON APPLICABILE)
  e gravita' (bloccante / rilevante / migliorativa):

  | Verifica | Cosa controlla |
  |---|---|
  | Aperture | traiettoria completa di porte, ante di finestre e armadi, scorrevoli: nessun urto in 3D |
  | Maniglie e spallette | maniglia libera con anta a 90 gradi, almeno 10 cm per lo stipite |
  | Sedute | dal bordo del piano: 75 cm per alzarsi, 90 per passare dietro chi siede |
  | Zone di prelievo | 70 cm liberi davanti ad armadi e vani |
  | Passaggi | larghezze minime e di comfort tra coppie di elementi |
  | Percorsi | ogni zona d'uso raggiungibile dall'ingresso con 60 cm continui (griglia 5 cm) |
  | Luce e aria | finestre >= 1/8 del pavimento, aerazione dei bagni, affollamento del locale |
  | Vincoli del brief | es. TV non accanto a una finestra sulla stessa parete |
  | Ergonomia | altezza seduta coerente con il piano |
  | Montaggio | armadi alti raddrizzabili nel locale |
  | Geometria | nessun oggetto che si compenetra o entra nei muri |

- **Consegna**: pianta DWG 2D con quote, layer e superfici; DWG 3D apribile anche da AutoCAD LT e Mac; STEP a solidi;
  anteprima PNG; `report_verifiche.md` con verifiche, locali, luci dei fori e tabella arredi.

## Requisiti

| Componente | Versione / note |
|---|---|
| macOS | i percorsi del progetto sono per macOS |
| [FreeCAD](https://www.freecad.org) | 1.1 (provato con 1.1.4) |
| Addon **FreeCAD MCP** | da [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp), cartella `addon/FreeCADMCP` |
| [Claude Code](https://claude.com/claude-code) | con il server MCP `freecad` registrato |
| [uv](https://docs.astral.sh/uv/) | esegue il server MCP (`uvx`) e gli script `ezdxf` |
| [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter) | gratuito, in `/Applications`: conversione DWG <-> DXF |

## Installazione

1. **FreeCAD**: `brew install --cask freecad` (oppure dal sito).
2. **Addon MCP** dentro FreeCAD:
   ```bash
   git clone --depth 1 https://github.com/neka-nat/freecad-mcp.git /tmp/freecad-mcp
   mkdir -p ~/Library/Application\ Support/FreeCAD/v1-1/Mod/
   cp -r /tmp/freecad-mcp/addon/FreeCADMCP ~/Library/Application\ Support/FreeCAD/v1-1/Mod/
   ```
   Riavvia FreeCAD. Per aggiornare l'addon in futuro si ripete la copia con un clone recente.
3. **Server MCP** in Claude Code (una volta sola, valido per tutti i progetti):
   ```bash
   claude mcp add --scope user freecad -- uvx freecad-mcp
   ```
4. **ODA File Converter**: scarica il `.dmg` per il tuo processore dalla pagina indicata sopra e trascina l'app in
   `/Applications`. Serve per produrre e leggere i DWG.
5. In FreeCAD (Preferenze, oppure dalla console Python) imposta il percorso del convertitore, se vuoi aprire/salvare DWG
   anche dall'interfaccia di FreeCAD:
   `/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter`.

## Avvio di una sessione

1. Apri FreeCAD, scegli il workbench **MCP Addon** (menu *View -> Workbench*) e clicca **Start RPC Server**.
   Nel Report view compare `RPC Server started at 127.0.0.1:9875`.
2. Apri Claude Code **in questa cartella**: carica `CLAUDE.md` -> `AGENTS.md` e le skill di `.claude/skills/`.
3. Chiedi cosa ti serve, oppure usa direttamente una skill:

| Skill | Quando |
|---|---|
| `/onboarding-progetto` | nuovo progetto: domande iniziali, brief, rilievo della pianta di partenza |
| `/arredamento` | distribuire e arredare, fino a verifiche a zero |
| `/review-layout` | giudicare una pianta, un DWG, una foto o uno schizzo, senza modificare nulla |
| `/export-autocad` | produrre DWG 2D/3D, STEP e report |

Le skill si attivano anche da sole quando la richiesta corrisponde ("partiamo da questa pianta", "cosa ne pensi?",
"passami i DWG").

## Come funziona

```
brief.md ──> progetto.py ──(MCP execute_code)──> FreeCAD: modello 3D
                 │                                   │
                 │                         lib/arredo.py verifica()
                 │                                   │
                 │                      output/report_verifiche.md
                 │                                   │
                 └──── arredo.esporta() ──> output/*.FCStd, *.step + build/ (pianta, mesh, annotazioni)
                                                     │
                                  tools/esporta.sh ──> output/*_Pianta.dwg, *_3D.dwg, *_Pianta.png
                                                       (ODA File Converter + ezdxf, con controllo round-trip)
```

- Il **modello vive nello script** `progetti/<nome>/progetto.py`: ogni modifica si fa li' e si rilancia; il `.FCStd` e'
  un prodotto, non la fonte.
- `lib/arredo.py` e' il motore comune: primitive, porte, finestre, scorrevoli, registrazione degli usi
  (`sedia`, `zona_prelievo`, `destinazione`, `passaggio`, `tv`, ...), verifiche ed export.
- Le soglie stanno in `docs/regole-progettuali.md` (minimo / comfort / fonte) e nel dizionario `REGOLE` del motore.

### Comandi a mano

Eseguire un progetto (dal tool MCP `execute_code`, o dalla console Python di FreeCAD):

```python
P = "/Users/andrea/dev/tmp/freecad/progetti/appartamento-100mq/progetto.py"
exec(open(P).read(), {"__file__": P, "__name__": "__main__"})
```

Esportare:

```python
import arredo; arredo.esporta()          # in FreeCAD, dopo aver eseguito il progetto
```
```bash
tools/esporta.sh progetti/appartamento-100mq     # nel terminale: chiude con "round-trip OK"
```

Leggere una pianta di partenza:

```bash
uv run --with ezdxf python tools/leggi_pianta.py progetti/<nome>/input/pianta.dwg
```

## Struttura

```
AGENTS.md / CLAUDE.md      istruzioni per l'agente
README.md                  questo file
lib/arredo.py              motore: modello, verifiche, export
tools/                     leggi_pianta.py, esporta.sh, annota_pianta.py, esporta_3d_dwg.py
docs/
  metodo.md                priorita', fasi, controlli per locale, scenari, antipattern, formato di consegna
  regole-progettuali.md    soglie
  brief-template.md        brief da compilare
  lezioni.md               lezioni apprese (L01, L02, ...)
progetti/
  _modello/progetto.py     scheletro per un nuovo progetto
  appartamento-100mq/      esempio completo
    brief.md, progetto.py
    input/                 file del cliente        (esclusi da git)
    output/                file prodotti           (esclusi da git)
archivio/                  versioni precedenti, solo consultazione
.claude/skills/            onboarding-progetto, arredamento, review-layout, export-autocad
```

## Aprire i risultati in AutoCAD

| File | AutoCAD Windows | AutoCAD Mac | AutoCAD LT |
|---|---|---|---|
| `*_Pianta.dwg` (2D, quote, layer) | Apri | Apri | Apri |
| `*_3D.dwg` (mesh colorate, un layer per locale) | Apri | Apri | Apri (visualizzazione) |
| `*_3D.step` (solidi modificabili) | `IMPORT` | non supportato | non supportato |

I DWG sono in formato AutoCAD 2018, unita' millimetri.

## Limiti

- Verifiche **geometriche e funzionali**: impianti, strutture, normativa locale, acustica e illuminotecnica non sono
  modellati e compaiono nel report come NON VERIFICABILE.
- Gli arredi sono **ingombri indicativi**: per un progetto reale vanno sostituiti con le misure delle schede prodotto.
- Le misure valgono quanto la fonte: da foto o piante senza scala si ottengono solo schemi, dichiarati come stimati.
- I percorsi assoluti (`/Users/andrea/dev/tmp/freecad/...`) negli esempi vanno adattati se la cartella viene spostata.

## Riferimenti

- Metodo: prompt base di progettazione residenziale (Astra) e flusso a fasi di
  [interioragent](https://github.com/KunalMGupta/interioragent), integrati in `docs/metodo.md`.
- Ponte FreeCAD <-> MCP: [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp).
- Licenza: MIT, vedi `LICENSE`.
