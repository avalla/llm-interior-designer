# Progetto base: interni in FreeCAD via MCP

Base riutilizzabile per progettare e verificare arredamenti (appartamenti, ville, singoli locali) in FreeCAD, pilotato dal
server MCP `freecad`, con consegna per AutoCAD. Ogni risultato e' una **proposta preliminare**, mai un progetto esecutivo.

## Prerequisiti di ogni sessione

- FreeCAD aperto, workbench **MCP Addon**, **Start RPC Server** cliccato. Controlla con `get_rpc_status`; se non risponde,
  chiedi all'utente di avviarlo (e' un clic nella GUI).
- `/Applications/ODAFileConverter.app` per DWG <-> DXF, `uv` per gli script ezdxf.

## Struttura

| Percorso | Ruolo |
|---|---|
| `lib/arredo.py` | motore: primitive, porte/finestre/scorrevoli, registrazione degli usi, `verifica()`, `esporta()` |
| `progetti/<nome>/progetto.py` | il progetto, a fasi; si rilancia dopo ogni modifica |
| `progetti/<nome>/brief.md` | brief, fonti dei dati, registro assunzioni |
| `progetti/<nome>/input/` | file di partenza del cliente (piante, PDF, foto, schede): esclusi da git |
| `progetti/<nome>/output/` | FCStd, DWG 2D/3D, STEP, PNG, `report_verifiche.md`: prodotti, esclusi da git |
| `progetti/_modello/progetto.py` | scheletro per un nuovo progetto |
| `progetti/appartamento-100mq/` | esempio completo, da cui copiare gli schemi |
| `tools/` | `leggi_pianta.py` (DWG/DXF in ingresso), `esporta.sh`, `annota_pianta.py`, `esporta_3d_dwg.py` |
| `docs/metodo.md` | il metodo: priorita', fasi, controlli per locale, scenari, antipattern, formato di consegna |
| `docs/regole-progettuali.md` | fonte unica delle soglie (minimo / comfort / fonte) |
| `docs/brief-template.md` | brief da compilare in onboarding |
| `docs/lezioni.md` | lezioni apprese `Lnn`, da rileggere prima di progettare e da aggiornare dopo |
| `archivio/` | versioni precedenti, solo consultazione |

## Comandi

- Modello + verifiche, in FreeCAD via `execute_code`:
  `P = ".../progetti/<nome>/progetto.py"; exec(open(P).read(), {"__file__": P, "__name__": "__main__"})`.
  Stampa i NON CONFORME e chiude con `TOTALE PROBLEMI: N`; il dettaglio va in `output/report_verifiche.md`.
- Export: `import arredo; arredo.esporta()` in FreeCAD, poi `tools/esporta.sh progetti/<nome>`, che chiude con `round-trip OK`.
- Pianta di partenza: `uv run --with ezdxf python tools/leggi_pianta.py <file.dwg|dxf>`.

## Convenzioni

- Il modello vive nello script: le modifiche si fanno in `progetto.py`, mai a mano nel `.FCStd`.
- Metri, origine all'angolo SO esterno, y verso nord; `interno` = filo interno dei muri perimetrali.
- `window()` e `opening()` prima dei `wall()` che attraversano; i fori includono gia' controtelai e stipiti.
- Ogni arredo con un uso registra quell'uso (`sedia`, `zona_prelievo`, `destinazione`, `passaggio`, `tv`, `coerenza_altezze`):
  senza registrazione, la verifica non lo vede. Pezzi dello stesso mobile condividono `item=`.
- I testi della pianta (quote, etichette) stanno nel progetto; superfici e simboli delle scorrevoli sono calcolati.
- Una verifica nuova si aggiunge in `lib/arredo.py`, con la sua soglia in `REGOLE` e in `docs/regole-progettuali.md`, e si
  dimostra con una controprova (lezione L04).

## Skill (`.claude/skills/`)

- `onboarding-progetto`: avviare un progetto nuovo, dalle domande iniziali al rilievo nel modello.
- `arredamento`: distribuire e arredare a fasi fino a verifiche a zero.
- `review-layout`: giudicare una pianta (modello, DWG, foto, schizzo, segnalazioni) con misure e stati, senza modificarla.
- `export-autocad`: consegnare DWG 2D/3D, STEP e report.
