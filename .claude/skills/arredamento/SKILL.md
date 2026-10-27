---
name: arredamento
description: Distribuisce e arreda un progetto in progetti/<nome>/progetto.py a fasi, fino a verifiche a zero. Usare per nuove stanze, spostare muri/porte/finestre, arredare, applicare correzioni emerse da una review.
---

# Arredamento

Prima di disegnare leggi [`docs/metodo.md`](../../../docs/metodo.md) (fasi, controlli per locale, composizione),
[`docs/lezioni.md`](../../../docs/lezioni.md) e il `brief.md` del progetto. Le soglie sono in
[`docs/regole-progettuali.md`](../../../docs/regole-progettuali.md); `progetti/appartamento-100mq/progetto.py` e' l'esempio
da cui copiare gli schemi. Senza `brief.md` parti dalla skill `onboarding-progetto`.

## Passi

1. **Distribuzione.** Se il programma lo giustifica, abbozza 2-3 alternative realmente diverse (posizione di zona notte,
   cucina, bagni rispetto a impianti e luce), scarta quelle che violano vincoli e scegli motivando. Porte: spalletta >= 15 cm,
   scorrevoli nei corridoi stretti e negli angoli. Fatto quando ogni locale ha accesso e i locali abitabili hanno finestra.

2. **Arredi principali (FASE = 2).** Letti, divani, tavoli, cucina, armadi, sanitari. Per ogni arredo registra subito l'uso:
   `sedia`/`seduta` per chi siede, `zona_prelievo` davanti ai contenitori, `destinazione` dove una persona deve arrivare,
   `passaggio` per le strettoie, `tv`, `coerenza_altezze`. Disegna le zone di verifica con la soglia piena (L11).
   Fatto quando ogni arredo con un uso ha la sua registrazione.

3. **Verifica.** Esegui il progetto in FreeCAD. Il riepilogo deve chiudere con `TOTALE PROBLEMI: 0`. Per ogni NON CONFORME
   correggi il progetto, non la soglia, e rilancia; ricontrolla gli elementi collegati alla correzione. Le note migliorative
   si risolvono quando costano poco, altrimenti si dichiarano. Fatto quando il report e' a zero.

4. **Dettagli (FASE = 3).** Tappeti, lampade, piante, oggetti a parete: si aggiungono senza spostare nulla della fase 2
   e si ri-verificano (una lampada puo' chiudere un percorso: L06). Fatto quando la verifica e' di nuovo a zero.

5. **Controprova.** Per ogni verifica nuova o modificata in `lib/arredo.py`, reintroduci il difetto che deve trovare (oggetti
   di prova con prefisso `TEST_`, poi rilancia il progetto per pulire) e mostra che viene segnalato.

6. **Revisione visiva.** Screenshot `Top` e `Isometric`. Cerca cio' che le verifiche non misurano: gruppi che si contendono la
   stessa regione, pareti sovraccariche, sedute senza piano d'appoggio o luce, porte e serramenti poco leggibili, locali che
   sembrano affollati. Simula gli scenari di `docs/metodo.md` sezione 8. Fatto quando hai descritto cosa hai guardato e cosa
   hai corretto.

7. **Export e lezioni.** Se servono i file, skill `export-autocad`. Ogni difetto trovato dall'utente che le verifiche non
   avevano visto diventa una lezione `Lnn` in `docs/lezioni.md` e, quando misurabile, una verifica nuova.

## Resoconto

Cosa e' cambiato e perche'; scelte di default prese; esito di `verifica()` con le misure (non solo "OK"); controprove;
note migliorative accettate; voci NON VERIFICABILE con il professionista che le chiude.
