---
seo_title: Il giudice, e come misurarne il rumore
lang: it
translation_of: handbook/05-the-judge.md
description: Anche un giudice LLM estrae dei campioni. Perché devi misurare il rumore del giudice prima di poter leggere quello del tuo sistema, e la procedura che sostituisce un numero alle supposizioni.
search:
  exclude: true
source: handbook/05-the-judge.md
source_sha: ba60264b1a69
source_commit: 340f1dd
model: claude-opus-5
---

# 5. Il giudice

Il capitolo 4 si chiudeva con una regola: al massimo un check giudicato, campionato, con una tolleranza misurata. Questo capitolo parla della parola *misurata* — cosa succede quando la salti, e la procedura che sostituisce un numero alle supposizioni. Le misure vengono dai sei run pubblicati dal [giudice della newsletter](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/README.md), e puoi ricalcolarle.

## Due rumori, non uno

Ci sono due punti in cui un modello può cambiare idea, e richiedono rimedi diversi.

**Il sistema sotto test** è un modello. Chiedigli la stessa cosa due volte e può rispondere in modo diverso. Nel progetto della newsletter il giudice *è* il sistema: assegna un punteggio agli articoli. Esegui la suite due volte, a quindici minuti di distanza, senza cambiare nulla, e un articolo su ventuno cambia verdetto.

**Il giudice** — il modello che usi dentro un check per valutare un output — è anch'esso un modello, e anch'esso cambia idea. Se la tua rubrica chiede «questa risposta è cortese?», il giudice può dire 0.8 oggi e 0.7 domani sulla stessa risposta.

Il rimedio per il primo è interrogare più volte il *sistema* su ogni caso e combinare i risultati. Il rimedio per il secondo è interrogare più volte il *giudice* su ogni output e combinare i risultati. Si somigliano ma non sono la stessa cosa: il primo misura quanto è stabile il tuo prodotto, il secondo quanto è stabile il tuo metro. Confonderli significa aggiustare il metro quando a oscillare è il prodotto, o viceversa. Decidi quale dei due stai osservando prima di toccare qualsiasi cosa.

## Quanto ti costa un solo campione

Un verdetto ottenuto da un solo campione è una singola estrazione. Su un caso che il giudice trova facile, l'estrazione dà quasi sempre lo stesso esito; su un caso limite è un lancio di moneta, e ogni insieme reale di casi ne contiene qualcuno. Con un check binario e nessuna tolleranza, ogni lancio che cade dall'altra parte è una regressione: il confronto diventa rosso, la CI fallisce, qualcuno indaga, non c'era niente che non andasse.

Ne bastano pochi perché un team smetta di leggere gli allarmi. Questo è il vero costo di un campione singolo: non il numero sbagliato, ma il momento in cui il rosso smette di significare qualcosa.

## Il campionamento

La soluzione è interrogare più di una volta e combinare i risultati. La suite della newsletter interroga cinque volte per caso, il che trasforma il verdetto binario in una frazione — 0, 0.2, 0.4, 0.6, 0.8 o 1 — e il check in «il giudice concorda con il lettore in almeno tre voti su cinque».

Il campionamento porta con sé tre domande, e le risposte contano più del numero cinque:

**Come combinarli?** Il punteggio è la media dei campioni. Ma la quantità interessante è l'*accordo*: quanti campioni condividono il verdetto di maggioranza. Prendi dei punteggi inventati: tre campioni di 0.80, 0.85, 0.99 sono in forte disaccordo tra loro e concordano pienamente sul verdetto; tre di 0.69, 0.71, 0.70 stanno entro due centesimi l'uno dall'altro e si dividono due a uno su una soglia di 0.70. L'accordo vede il secondo caso; la media no.

**E se non riescono a mettersi d'accordo?** Allora il giudizio non era possibile, e la risposta onesta è *giudizio impossibile* — un terzo stato, né superato né fallito. Un caso i cui campioni si dividono tre a due non è una regressione e non è un successo; è un caso che il giudice non sa decidere, e un riferimento costruito su di esso sarebbe un riferimento a un lancio di moneta. Imposta un accordo minimo sotto il quale il verdetto è un errore, e rifiuta di promuovere un run che ne contenga uno — ma impostalo a un valore che possa scattare davvero. Con cinque campioni la maggioranza è sempre almeno tre, quindi `"3/5"` non rifiuta mai una votazione in cui tutti i campioni sono stati giudicati; la soglia che intercetta una divisione tre a due è `"4/5"`.

**Scrivi le frazioni come frazioni.** «Due su tre» scritto come `0.67` è una trappola: ⅔ vale 0.666…, che è *sotto* 0.67, e ogni caso con un voto contrario su tre diventa un errore. `"2/3"` dice quello che intendi e non può sbagliare per un arrotondamento; la suite della newsletter scrive `"3/5"`.

## Misurare la tolleranza

La tolleranza è l'entità di cambiamento che accetti di ignorare come rumore. Tutti la scelgono a sensazione; quasi tutti la scelgono male, perché il rumore di un giudice non si può indovinare dall'esterno. Si può misurare, in tre run:

1. Congela tutto — prompt, modello, casi.
2. Esegui la suite tre volte.
3. Per ogni caso, guarda la differenza massima tra due run qualsiasi.
4. La tolleranza è quella differenza massima, più un piccolo margine.
5. Se quel numero è grande quanto le differenze che vuoi *intercettare*, fermati: il check è troppo rumoroso per fare da gate. Campiona di più, o cambia il check — non allargare la tolleranza fino a farle inghiottire tutto.

Ecco che cosa emerge dal giudice della newsletter: sei run, cinque campioni per caso, con gli stessi prompt, gli stessi casi e la stessa configurazione. Ogni cella indica quanti dei cinque campioni hanno concordato con il lettore; gli orari sono in UTC.

| caso | 1 set 12:29 | 1 set 12:44 | 3 set 06:14 | 3 set 06:18 | 3 set 06:24 | 3 set 06:30 |
|---|---|---|---|---|---|---|
| evals-skills-for-coding-agents | 2 | 5 | 5 | 2 | 5 | 5 |
| more-than-just-code-review | 4 | 5 | 5 | 2 | 5 | 5 |
| controlling-reasoning-effort-in-llms | 5 | 4 | 3 | 5 | 5 | 4 |
| recent-developments-in-llm-architectures | 5 | 4 | 5 | 3 | 5 | 4 |
| gli altri diciassette | entro due voti, e la maggioranza non cambia mai | | | | | |

Due casi hanno oscillato di tre voti su cinque su un sistema immutato, e in ogni singolo run da due a sei dei ventuno casi risultavano divisi. Sul singolo caso, dunque, vale il punto 5: una tolleranza che assorbisse tre voti sarebbe ampia quanto qualunque cambiamento che su quel caso valga la pena intercettare. La suite dichiara due voti per caso, e lascia emergere un'oscillazione di tre voti. La tabella per caso vale comunque la pena tenerla: ti dice esattamente su quali casi il giudice è incerto.

## L'aggregato è più calmo dei singoli casi

Gli stessi run hanno mostrato qualcosa che cambia su cosa conviene mettere una soglia. Mentre i singoli casi saltavano di tre voti su cinque, il numero di articoli su cui giudice e lettore concordavano è stato 15, 16, 16, 14, 16 e 16 su 21 nei sei run — mai a più di due di distanza.

È lo schema generale, ed è il motivo per cui una suite con casi etichettati dovrebbe mettere il gate su un aggregato — precision, accuracy, recall — e usare i verdetti per caso per la diagnosi. Una soglia del 60% di accordo non sarebbe scattata in nessuno dei sei. Rispetto al riferimento che il progetto conserva, il check per caso, con i suoi due voti di tolleranza, è diventato rosso in due degli altri cinque.

## Il prompt del giudice è un prompt

Va alla deriva per le stesse ragioni per cui ci va il tuo, e merita lo stesso trattamento: un file, versionato, registrato a ogni run. Quando un check giudicato inizia a fallire, la prima domanda non è «il sistema è peggiorato?» ma «è cambiato il metro?» — e se il prompt del giudice è una stringa dentro una funzione da qualche parte, non puoi rispondere.

Due abitudini minori. Primo: nel prompt del giudice tieni l'istruzione prima dell'output, ed etichetta l'output in modo chiaro; un giudice che legge un'istruzione dopo il testo che gli è stato chiesto di giudicare a volte giudica l'istruzione. Secondo: quando provi la tua suite con un giudice finto — e dovresti farlo — costruisci il finto a partire da una risposta *reale*, non da come pensi che sia fatta la risposta. Un finto scritto a partire dal codice conferma il codice; nel progetto della newsletter [è emerso un costo contato per difetto di 384×](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/README.md#the-fake-judge-and-ci) con tutti i test verdi, perché il finto e il codice condividevano la stessa assunzione sbagliata sulla forma dell'API.

## Da fare oggi

1. Decidi quale rumore stai osservando: quello del sistema o quello del giudice.
2. Campionalo — la suite della newsletter interroga cinque volte — e imposta un accordo minimo sotto il quale il verdetto è *giudizio impossibile*.
3. Congela tutto ed esegui tre volte. Leggi la differenza massima per caso. Quella è la tua tolleranza, o il segnale che devi campionare di più.
4. Se hai delle etichette, metti il gate sull'aggregato.
5. Sposta il prompt del giudice in un file accanto a quello del sistema, e registra entrambi a ogni run.

Il prossimo capitolo parla di cosa fare quando i numeri sono stabili: il run che approvi, e perché dovrebbe essere la mediana di diversi run e non il primo verde.
