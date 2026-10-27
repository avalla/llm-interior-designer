---
name: review-layout
description: Revisione critica di una pianta o di un arredo (modello FreeCAD, DWG/DXF, screenshot, foto o schizzo dell'utente) con misure, stati e gravita'. Usare per "verifica", "controlla", "cosa ne pensi", segnalazioni da valutare.
---

# Review layout

Una review **misura e giudica**; il progetto resta invariato finche' l'utente non conferma le modifiche (L09), poi si passa
alla skill `arredamento`. Riferimenti: [`docs/metodo.md`](../../../docs/metodo.md) (controlli per locale, scenari,
antipattern), [`docs/regole-progettuali.md`](../../../docs/regole-progettuali.md).

## Passi

1. **Fonte.** Identifica cosa stai guardando. DWG/DXF: `tools/leggi_pianta.py`. Immagine o schizzo: misure dalla scala delle
   quote visibili, dichiarate come `stimato`. Elenca le differenze rispetto al `progetto.py` corrente (muri tolti, arredi
   spostati, elementi nuovi). Fatto quando ogni differenza visibile e' elencata.

2. **Segnalazioni dell'utente.** Per ognuna: misura, soglia, verdetto (fondata / parzialmente / non fondata). Una segnalazione
   fondata che `verifica()` non trovava e' un buco delle verifiche: dillo apertamente e proponi la verifica che lo chiude.

3. **Passata completa.** Applica a ogni locale i controlli della sezione 7 di `metodo.md`, gli scenari della sezione 8 e gli
   antipattern della sezione 9. Le misure dal modello si prendono in FreeCAD con codice di sola lettura (`distToShape`,
   `common`, bounding box) o rilanciando `verifica()` sul progetto invariato. Fatto quando ogni controllo ha uno stato.

4. **Proposte.** Per ogni problema: correzione concreta con coordinate, effetti sugli altri locali (una correzione ne risolve
   o ne crea altre: collegale), compromessi. Separa cio' che il disegno risolve da cio' che richiede un professionista.

## Formato

Per ogni punto: misura, soglia, stato (VERIFICATO / NON CONFORME / NON VERIFICABILE / NON APPLICABILE), gravita'
(bloccante / rilevante / migliorativa), proposta. Tabelle quando ci sono piu' misure dello stesso tipo. Chiudi con un
riepilogo in due righe e le domande che bloccano l'applicazione delle modifiche.
