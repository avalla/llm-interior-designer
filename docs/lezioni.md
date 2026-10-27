# Lezioni apprese

Una lezione per difetto trovato dall'utente o da una controprova. L'identificativo `Lnn` e' stabile: non si rinumera e non
si riusa. Formato: cosa e' successo, regola che ne deriva, dove e' applicata (verifica automatica o passo di una skill).
Si aggiunge una lezione ogni volta che l'utente trova un difetto che le verifiche non avevano visto.

**L01 - Collisione non e' uso.** Un'anta d'armadio in una nicchia di 50 cm non urtava nulla, ma davanti non c'era spazio per
prendere le cose. Regola: ogni contenitore ha una zona di prelievo di 70 cm. Applicata: `zona_prelievo()`.

**L02 - Maniglie e spallette.** Porte con la cerniera a 5 cm dal muro: telaio impossibile, maniglia contro la parete a 90 gradi.
Regola: spalletta >= 10 cm e maniglia verificata. Applicata: `hinged()` + verifica Maniglie/Spallette.

**L03 - Sedersi non e' passare.** Tavolo tondo in un angolo con 18-33 cm dietro le sedie. Regola: misurare dal bordo del piano,
75 cm per alzarsi, 90 per passare dietro chi siede. Applicata: `sedia()` / `seduta()`.

**L04 - Controprova.** Una verifica che non e' mai fallita non e' dimostrata. Regola: ogni verifica nuova si prova
reintroducendo il difetto che deve trovare. Applicata: skill `arredamento`, passo Controprova.

**L05 - Leggibilita'.** Un'anta bianca su muro bianco e una scorrevole disegnata come linea sottile risultavano "porta mancante".
Regola: ante in colore diverso dal muro, scorrevoli con binario in 3D e simbolo (anta spessa + freccia) in pianta.
Applicata: `hinged()`, `sliding()`, `tools/annota_pianta.py`.

**L06 - Percorsi continui.** Una lampada da terra lasciava 25 cm tra se' e il divano: divano e poltrona irraggiungibili, pur
senza collisioni. Regola: ogni zona d'uso deve essere raggiungibile dall'ingresso con 60 cm continui; la luce di lettura sta
accanto alla sua seduta. Applicata: `destinazione()` + verifica Percorsi.

**L07 - Verificare all'altezza giusta.** Cappa davanti alla finestra della cucina e rubinetto sotto l'anta: in pianta tutto
libero. Regola: le ante delle finestre si verificano in 3D sopra il davanzale. Applicata: `hinged(z0=davanzale)` per le finestre.

**L08 - Formati AutoCAD.** AutoCAD per Mac e LT non importano STEP. Regola: consegnare sempre anche il DWG 3D a mesh.
Applicata: skill `export-autocad`.

**L09 - Review senza modifiche.** Quando l'utente chiede un'analisi, la risposta e' solo analisi con misure; le modifiche partono
su conferma. Applicata: skill `review-layout`.

**L10 - Pianta per solido.** Tagliare un mobile composto a meta' altezza mostrava solo le gambe delle sedie. Regola: in pianta
ogni solido si taglia a meta' della propria altezza. Applicata: `arredo.esporta()`.

**L11 - Soglie e arrotondamenti.** Zone di prelievo disegnate 5 mm sotto i 70 cm risultavano NON CONFORMI. Regola: disegnare
le zone di verifica con la soglia piena, non al limite. Applicata: skill `arredamento`.
