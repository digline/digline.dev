---
seo_title: 'Prima del prompt: costruire una feature che si possa misurare'
lang: it
translation_of: handbook/00-before-the-prompt.md
description: 'Quattro decisioni vengono prima del prompt e determinano se una feature LLM sia valutabile o no: restituire la decisione come struttura, rendere deterministico l''input, registrare ogni chiamata e salvare un errore come errore.'
search:
  exclude: true
source: handbook/00-before-the-prompt.md
source_sha: dfa436056f03
source_commit: c51c251
model: claude-opus-5
---

# 0. Prima del prompt

Il prompt è la parte centrale del lavoro, non il suo inizio. Quattro decisioni lo precedono, ciascuna poco costosa nel pomeriggio in cui la prendi e quasi irrecuperabile una volta che la feature è in produzione — e insieme decidono se tutto il resto di questo manuale sia realizzabile o no.

## Perché l'ordine viene sbagliato

L'ordine abituale è scrivere il prompt, rilasciare e occuparsi del resto quando qualcuno si lamenta. Sembra iniziare dalla parte difficile. In realtà è iniziare dall'unica parte malleabile: il prompt resta economico da cambiare, e tutto ciò che gli sta attorno si irrigidisce. La forma della risposta diventa il contratto su cui vengono scritti il renderer, il client e le righe salvate, e le righe già scritte sono le righe che hai. Così l'attenzione va alla parte che tra un anno sarà ancora economica, e salta le quattro che non lo saranno.

Quello che segue è la forma comune di una feature LLM in produzione, ricavata dal codice di un sistema più che misurata su di esso: il codice assembla un contesto, una sola chiamata al modello decide cosa dire, torna della prosa. Il [capitolo 3](../../handbook/03-ground-truth.md) smonta quel sistema dall'altro capo e si chiede da dove potrebbe venire il suo ground truth. Questo è l'elenco delle decisioni che gliene avrebbero dato uno. Qui non c'è nessun numero — niente è stato eseguito.

## 1. Restituisci la decisione, non solo la prosa

Se la feature sceglie — quali elementi menzionare, quali tralasciare, in che ordine — la scelta è il comportamento che vorrai misurare, e la prosa ne è una resa. Un sistema che restituisce gli id che ha scelto, in ordine, accanto alla frase che ha scritto si può verificare meccanicamente con delle assert, e offre al giudizio di una persona qualcosa da indicare. Uno che restituisce solo la frase non può, qualunque cosa gli aggiungi dopo: ogni check che scrivi legge prosa, e così fa ogni discussione sul fatto che la scelta fosse giusta.

Oggi è un campo nella risposta e un parse. Più tardi è il contratto tra il modello e tutto ciò che sta a valle, e un contratto è un cambiamento di quelli costosi.

**Dove la cosa si complica:** non tutte le feature scelgono. Se ciò che vendi è la prosa stessa — una riscrittura, una traduzione, una replica in una conversazione — non c'è nessuna selezione da restituire, e ti porti dietro solo le decisioni 3 e 4. La maggior parte delle feature non è così: selezionano, ordinano, instradano o estraggono, e chiamano il risultato un riassunto.

## 2. Rendi deterministico l'input

Gli stessi dati salvati in ingresso, lo stesso contesto assemblato in uscita. Una query che prende le prime N righe senza un ordinamento lascia quella scelta al database, e due run sugli stessi dati possono differire senza che il modello abbia cambiato idea.

Il costo evidente è che non c'è niente da congelare, quindi non c'è nessun caso. Quello che fa male più a lungo è l'attribuzione: ogni differenza tra due run ha due possibili autori e nessun modo per distinguerli, e un run rosso che nessuno riesce ad attribuire è il modo in cui un team impara a non leggere più il rosso.

Oggi è un ordinamento su una query. Più tardi è quello, più ogni run registrato prima della correzione, eseguito su un input che nessuno può riprodurre.

## 3. Registra la chiamata dal primo giorno

L'input assemblato come l'ha ricevuto il modello, la risposta come è arrivata, quale modello ha risposto e quando. Quattro campi.

È l'unico punto che il giorno in cui lo scrivi non serve a nulla: nessuna feature lo legge, nessuna schermata lo mostra, ed è la prima cosa messa in discussione in review. È anche l'unico che non si può aggiungere in ritardo a nessun prezzo. Gli altri sono costosi da introdurre a posteriori; questo non è recuperabile a posteriori, perché quello che avrebbe contenuto non c'è più.

**Dove la cosa si complica:** non è gratis, e un capitolo che dicesse il contrario sbaglierebbe. L'input assemblato è il dato che è entrato, quindi il record lo eredita, e con esso le regole su dove può risiedere ([capitolo 8](../../handbook/08-for-teams-building-for-others.md)): stesso perimetro, stessa conservazione. E prendi *quale modello ha risposto* dalla risposta, non da quello che hai chiesto — il giorno in cui un provider ripunta un alias quelli sono due fatti diversi.

## 4. Fai in modo che un errore non assomigli a una risposta vuota

Una chiamata fallita e una chiamata che davvero non aveva niente da dire sono due fatti. Salvati come la stessa riga diventano uno, e quello che diventano è il più silenzioso: un'interruzione di servizio si legge come una mattinata tranquilla.

È la decisione che fa marcire il registro che hai appena costruito: ogni conteggio fatto su quelle righe legge il silenzio come consenso, e resta sbagliato per tutto il tempo in cui le righe vengono conservate. Né si possono sistemare dopo, per data o per inferenza, per la ragione che il capitolo 3 dà a proposito della reinterpretazione di un'etichetta ambigua. Restano ambigue.

Oggi è uno stato in più. Più tardi è uno stato in più, e nessuno storico.

## Poi il prompt

Adesso scrivilo, e nota cosa hanno fatto le quattro decisioni: il prompt è la parte della feature più economica da cambiare, che è dove doveva stare dall'inizio. La struttura è il contratto, il prompt è il modo in cui viene riempita, e un prompt migliore è un diff in un solo file di cui niente a valle deve sapere nulla.

## Gli invarianti vengono prima dei casi

Un invariante è qualcosa che vale per un output corretto in ogni giorno possibile, quali che siano i dati. Il capitolo 3 elenca quelli che questa forma di feature ottiene: ogni id scelto era nell'input, l'elemento richiesto compare, un input vuoto produce una selezione vuota.

Vale la pena aggiungere *quando* puoi scriverli. Un invariante non ha bisogno di ground truth, di etichette, di casi né di un giudice — è un'affermazione sul sistema, non su una risposta. È l'unico check che può esistere il giorno dopo il prompt, prima che il lavoro del [capitolo 2](../../handbook/02-cases.md) sia iniziato, e la cosa più economica di questo manuale. Quasi nessuno li scrive.

## Il gesto, dove la persona già si trova

Poi un gesto, nel percorso che la persona sta già seguendo, con cui può dissentire. Il capitolo 3 parla di cosa chiedere, di perché la domanda ovvia registra due cose insieme e di quanto questo sia lontano dall'essere risolto per una persona che non sei tu.

Quello che viene prima è più piccolo: il gesto ha bisogno di un oggetto. Senza la decisione 1 non c'è niente a cui agganciarlo, e un «non mi piace» finisce su un paragrafo — registra che una mattinata è andata male, che non è un fatto su nessuna decisione presa dal sistema. Con la struttura, lo stesso clic cade su un elemento, in una posizione, con un id. Costruisci le due cose nella stessa settimana, oppure il gesto raccoglierà la cosa sbagliata per un anno.

Solo allora la suite.

## In una pagina

```text
What has to be true before the prompt is worth writing?
├── the decision comes back as data ..... the ids it chose, in order, beside the prose
├── the input cannot move on its own .... same data in, same assembled context out
├── every call is written down .......... the input · the reply · which model · when
└── a failure is not an empty answer .... two outcomes, two rows, never one

                                     ── the prompt ──
                   the only part of this you can still change tomorrow

And then, in this order, what those four have made possible:
├── invariants .......................... true on every possible day, no model needed
├── one judgement gesture ............... where the person already is, attached to the ids
└── a suite ............................. cases, checks, a reference → chapters 1 to 8
```

## Farlo oggi

Sette domande, una per passo. Rispondi su una lavagna prima che sia scritta una riga della feature; la colonna di destra è ciò tra cui stai scegliendo.

| La domanda | Quanto costa rispondere in ritardo |
|---|---|
| 1. La feature dice *quali* cose ha scelto, come dato, e non solo in prosa? | Non si può verificare nulla con delle assert, e nessun gesto può indicare una scelta. |
| 2. A parità di dati salvati, arriva al modello lo stesso contesto? | Nessun input da congelare, quindi nessun caso — e nessun run rosso che si possa attribuire. |
| 3. Su ogni chiamata vengono scritti l'input assemblato, la risposta, il modello che ha risposto e l'ora? | L'unica cosa che non si può aggiungere dopo a nessun prezzo. |
| 4. Riesci a distinguere una chiamata fallita da un autentico «niente da segnalare»? | Un'interruzione di servizio viene salvata come una mattinata tranquilla, e ogni conteggio su quelle righe legge il silenzio come consenso. |
| 5. Il prompt è la sola cosa che deve cambiare quando vuoi una risposta diversa? | Il prompt smette di essere economico: cambiarlo diventa un cambiamento a tutto ciò che sta a valle. |
| 6. Che cosa vale per un output corretto in ogni giorno possibile, e si può verificare senza modello? | Parti dall'estremo più costoso, un giudice, su un sistema di cui nessuno ha dimostrato la coerenza. |
| 7. In quello che una persona già fa, dove potrebbe dire che questo era sbagliato — e a cosa è agganciato quel gesto? | Il dissenso non arriva mai, oppure arriva come un'etichetta che significa due cose. |

Il capitolo successivo parla di ciò che hai una volta che questi elementi sono al loro posto, e di perché la cosa al suo centro sembra una funzione e non lo è.
