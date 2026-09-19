---
seo_title: Ground truth quando nessuno te ne dà una
lang: it
translation_of: handbook/03-ground-truth.md
description: 'Da dove viene la risposta attesa quando non ci sono dati etichettati: congela l''input, copri le forme, cattura il disaccordo e progetta la funzionalità in modo che un giudizio abbia qualcosa a cui agganciarsi.'
search:
  exclude: true
source: handbook/03-ground-truth.md
source_sha: 74e7f304be5e
source_commit: d778c40
model: claude-opus-5
---

# 3. Ground truth: quando nessuno te ne dà una

Il capitolo 2 diceva di trovare il punto in cui una persona corregge il modello. Questo capitolo è per quando quel punto non esiste — o esiste e registra qualcosa di diverso da quello che pensi. È scritto a partire da tre sistemi: il [giudice della newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f), il cui codice e i cui casi sono pubblici ma il cui registro di ogni elemento giudicato non lo è — i numeri qui sotto sono letti da quel registro, come lo mostra [Bad evals, my own](../../blog/bad-evals-my-own.md); un secondo giudice dello stesso autore che seleziona i thread di Reddit a cui vale la pena rispondere (privato, descritto nello stesso articolo); e una funzionalità di prodotto descritta solo nella sua forma. Ciascuno di essi non è riuscito a produrre ground truth in un modo diverso.

## Congela l'input, non il mondo

Un caso è una fotografia di una situazione. Che i dati di domani saranno diversi è irrilevante: stai testando quello che il sistema fa di fronte a quella situazione, non i dati.

Quindi l'input entra nel caso per intero, così come il modello l'ha visto quel giorno. Riscaricare un articolo oggi metterebbe un input diverso sotto una vecchia etichetta. Il progetto della newsletter salva il riassunto che ha giudicato — ma solo per gli elementi mostrati al suo lettore, quindi 144 elementi giudicati e mai mostrati hanno un punteggio e nessun input. Anche se etichettati, non potrebbero essere rieseguiti.

## Copri le forme, non campionare

Il modo ovvio di ottenere casi è esportare ogni record etichettato. Il giudice di Reddit lo ha fatto il 2026-09-11 e ha ottenuto 144 casi. 109 di essi erano thread che il lettore aveva ignorato e che il giudice aveva scartato: la stessa mattina ordinaria, ripetuta all'infinito. Accuracy su quell'insieme era 0.85. Precision sull'unico verdetto che contava era 0.52. Il volume metteva in buona luce i giorni facili e non diceva nulla di quelli difficili.

Scegli invece i casi per la loro forma: l'input affollato, quello vuoto, l'elemento urgente sepolto sotto il rumore, il campo mancante, due priorità in conflitto. Quella lista non è un risultato. Il giorno ordinario è una delle forme, e il capitolo 2 ha ragione a dire che deve esserci — come forma, non come sedimento di ogni mattina.

## Un'etichetta non è un giudizio

Il giudice di Reddit chiedeva al suo lettore, ogni mattina, cosa avesse fatto con ciascun thread: commentato, votato o ignorato. `ignored` diventava `skip` nella suite. Poi il lettore ha guardato nove thread che aveva ignorato e che il giudice aveva contrassegnato come `comment`, e ha scoperto che in almeno cinque il giudice aveva ragione secondo le proprie regole. Erano stati ignorati perché era il quarto thread di quella mattina, o perché il lettore aveva già commentato due volte in quel forum quel giorno.

Quindi `ignored` significava *il giudice ha sbagliato* e *non c'era tempo*, e ogni caso costruito su quell'etichetta era la lettura di una risposta che non ha mai detto quale delle due. **Non reinterpretarla a posteriori** — per data, per la confidenza del giudice, per quello che dovevi aver inteso. Significa inventare un valore atteso per proprio conto. I vecchi record restano ambigui, e da essi non si ricava nessun caso nuovo.

La correzione sta alla tastiera. Qualunque tasto svuoti la lista della mattina deve scrivere *deferred*, il valore che non afferma nulla, non *declined*. Altrimenti l'etichetta ambigua torna sotto un nome nuovo nel giro di una mattina. I negativi scritti prima della correzione non sono recuperabili.

Quella distinzione non elimina l'ambiguità, perché `declined` chiede comunque cosa *hai fatto*. Un thread lasciato perdere perché il lettore aveva già commentato due volte in quel forum resta un `declined`, resta un negativo. Per eliminarla serve una domanda sulla regola — non *hai commentato?* ma *questo avrebbe dovuto essere un commento?* — e nessuno dei due giudici la pone.

## Il disaccordo è l'evento

Rileggere gli output buoni non insegna nulla e convince di molte cose. L'unico momento che vale la pena catturare è quando una persona avrebbe risposto in modo diverso dal modello. Nessuno dei due giudici lo fa ancora: entrambi esportano ogni etichetta esplicita, accordi compresi.

**Il progetto della newsletter è il controesempio**, ed è più utile di un successo. Al suo lettore vengono mostrati gli elementi a cui il giudice ha dato 4 o 5, completati fino a cinque, con la domanda *quali ti interessano? (invio = nessuno)*. L'unica risposta esplicita è *sì*, e può essere data solo a elementi che il giudice ha già scelto. Gli elementi non mostrati non hanno etichetta; 265 su 446 non sono mai stati nemmeno valutati. L'invio è ambiguo. L'unica strada verso un disaccordo — selezionare un elemento a basso punteggio aggiunto per riempimento — era stata aperta sedici volte al 6 settembre, e percorsa zero. Il metodo non produce **alcun disaccordo catturabile**, non perché il lettore non sia mai stato in disaccordo, ma perché non gli è mai stato chiesto dove avrebbe potuto esserlo.

La ground truth deve essere un sottoprodotto del lavoro che la persona già fa. Entrambi i giudici chiedono alla fine di una mattina che il lettore stava comunque vivendo; una domanda che è un comando separato da eseguire più tardi è una seccatura. In un prodotto la persona non sei tu, ed è il caso difficile, che qui non è stato risolto.

## Quando la selezione non è mai stata un dato

Il terzo sistema ha la forma più comune di funzionalità LLM in produzione, e quanto segue è stato ricavato dal suo codice, non da prove eseguite su di esso. Un prodotto scrive a ogni utente un briefing mattutino. Il codice assembla un contesto e lo passa a una singola chiamata al modello. Il modello decide quali elementi menzionare, in che ordine, con quale ragionamento, e se dire qualcosa o no.

La risposta è prosa con dentro dei link. Niente la analizza o la valida. Un elemento è identificabile solo se il modello l'ha racchiuso in un link che porta un id, e niente verifica che quell'id esista nell'input.

Nei due giudici le etichette erano ambigue. Qui **la selezione esiste solo dentro la prosa**. Non c'è niente su cui asserire, e niente a cui il giudizio di un utente possa agganciarsi: un pulsante di feedback non avrebbe alcun oggetto da indicare. Due cose ordinarie peggiorano la situazione. Una chiamata al modello fallita e un autentico «niente da segnalare» salvano la stessa riga — un'assenza travestita da risposta. E alcune delle query che costruiscono il contesto prendono N righe senza alcun ordinamento, quindi quali elementi arrivino al modello dipende dal database: due run sugli stessi dati possono differire senza che il modello cambi idea, e non c'è nessun input da congelare.

La funzionalità funziona, e niente di tutto questo emerge in revisione. Semplicemente non può essere valutata. **Se la tua ground truth sarà raccoglibile si decide quando scrivi la funzionalità**, non dopo. Un sistema che emette la propria decisione come struttura — gli elementi scelti, in ordine, con i loro id — può essere verificato in modo deterministico e può portare il giudizio di una persona. Uno che emette solo prosa no, qualunque cosa tu ci attacchi sopra dopo.

La correzione è una forma: emetti prima la selezione; valida i suoi id rispetto all'input; salva un fallimento come fallimento; lascia che la prosa sia una resa della selezione.

## Cosa puoi asserire a quel punto

Con la selezione come dato, la maggior parte di ciò che conta è stabile per ogni giorno possibile e non richiede alcun modello: ogni id è nell'input, quindi niente è inventato e niente proviene dai dati di un altro utente; l'elemento che deve comparire compare; un input vuoto produce una selezione vuota. Solo l'ordinamento — la cosa urgente è per prima? — richiede un giudice. Nessuna di queste verifiche è ancora stata eseguita su quel sistema; sono ciò che la struttura rende possibile.

## La crescita, e il limite onesto

Parti da poche forme scelte. Lascia che ogni fallimento in produzione diventi un caso, e non cancellarne mai nessuno: un caso che ha trovato un difetto è un muro che regge, e rimuoverlo è l'unico modo per scoprire cosa stava reggendo. L'exporter del progetto della newsletter fa il contrario: rigenera il suo file per intero.

Venti casi non ti dicono che il sistema è corretto. Ti dicono che non è peggiorato su venti situazioni che qualcuno ha giudicato rappresentative. Un gate di regressione, non una dimostrazione.

## Farlo oggi

1. Trova dove vive la decisione della tua funzionalità. Se sta solo nella prosa, cambia l'output prima di scrivere anche un solo caso. Se non puoi ancora cambiarlo, non puoi valutare la funzionalità. È già di per sé un risultato, e la cosa da fare oggi è registrare l'input assemblato e la risposta, perché domani non ci saranno più.
2. Verifica che i tuoi input siano deterministici. Una query che tronca senza un ordinamento è il primo bug.
3. Guarda la risposta che i tuoi utenti danno non facendo nulla. Assicurati che non affermi nulla.
4. Chiedi della regola, non del comportamento, e solo dove la persona avrebbe risposto in modo diverso.
5. Scegli cinque forme. Scrivi un caso per ciascuna.

Il prossimo capitolo parla di cosa verificare su quei casi — e del perché vengono prima i check che non hanno bisogno di alcun modello.
