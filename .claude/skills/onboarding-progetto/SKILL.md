---
name: onboarding-progetto
description: Avvia un nuovo progetto di arredamento o distribuzione interna: raccoglie file di partenza, tipo di intervento, abitanti, tipologia di arredamento e vincoli, compila il brief e porta il rilievo nel modello. Usare per "nuovo progetto", "partiamo da questa pianta", "arreda questa casa".
---

# Onboarding progetto

Obiettivo: un `progetti/<nome>/` con `brief.md` compilato e `progetto.py` in **FASE = 1** (involucro rilevato), pronto per
la skill `arredamento`. Il metodo di riferimento e' [`docs/metodo.md`](../../../docs/metodo.md), sezioni 1-2.

## Passi

1. **File di partenza.** Chiedi i file disponibili: DWG/DXF, PDF in scala, foto, rilievo, schede di arredi da conservare.
   Copiali in `progetti/<nome-breve>/input/` (cartella esclusa da git: sono dati del cliente). Per DWG/DXF esegui `uv run --with ezdxf python tools/leggi_pianta.py <file>` e annota unita', estensione, quote e segmenti
   fuori squadra. Per PDF/foto senza scala dichiara che le misure saranno `stimato` e chiedi almeno una quota nota.
   Fatto quando sai quali misure sono `misurato`/`documentato` e quali no.

2. **Domande bloccanti.** Fai insieme (con `AskUserQuestion`, al massimo 4 per giro) le domande che cambiano la soluzione,
   in quest'ordine, saltando quelle gia' risolte dai file:
   1. **Tipo di intervento**: solo arredo / riorganizzazione interna / ristrutturazione / nuova costruzione; cosa si puo'
      toccare (tramezzi, porte, finestre, impianti).
   2. **Tipologia di arredamento**: moderno, scandinavo, japandi, industriale, classico contemporaneo, mid-century, altro;
      clima desiderato (es. "non opprimente"); riferimenti visivi.
   3. **Abitanti**: quanti, eta', esigenze motorie, animali, ospiti abituali, lavoro da casa.
   4. **Programma**: ambienti indispensabili e desiderabili.
   Fatto quando le quattro voci hanno risposta o assunzione esplicita.

3. **Domande di dettaglio.** Raccogli il resto del brief, proponendo un default per ogni voce cosi' l'utente conferma invece
   di scrivere: altezze nette e travi; orientamento e affacci; impianti fissi (colonne di scarico, quadro, caldaia,
   radiatori/split); piano, ascensore e misure della cabina (trasporto arredi); abitudini in cucina e numero di posti a
   tavola con ospiti; contenimento (metri di abiti appesi, scarpe, valigie); lavanderia; oscuramento e TV in camera;
   arredi da conservare e prodotti scelti con misure; elementi vietati (es. TV vicino alle finestre); budget e tempi;
   formati di consegna e versione di AutoCAD (Windows / Mac / LT).
   Fatto quando ogni riga di [`docs/brief-template.md`](../../../docs/brief-template.md) ha valore, default confermato
   o "da confermare".

4. **Cartella di progetto.** Crea `progetti/<nome-breve>/`, copia `progetti/_modello/progetto.py` e `docs/brief-template.md`
   come `brief.md`, compila il brief con le fonti e il registro assunzioni (impatto di ogni assunzione sbagliata).

5. **Rilievo (FASE 1).** In `progetto.py`: `nuovo()` con `interno` e altezza, poi finestre, porte, muri, locali e `ingresso()`
   dalla fonte. Esegui in FreeCAD, guarda lo screenshot dall'alto e confronta: ogni quota della fonte coincide con il modello
   (stessa estensione, stessi fori). Le differenze vanno nel registro assunzioni. Fatto quando `verifica()` gira e le quote
   coincidono.

6. **Passaggio di consegne.** Riassumi all'utente: cosa e' misurato e cosa assunto, le domande ancora aperte che bloccano,
   e la proposta di prossimo passo (skill `arredamento`, eventualmente con 2-3 alternative di distribuzione).
