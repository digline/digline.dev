---
seo_title: 'Casi: la risorsa che nessuno costruisce'
lang: it
translation_of: handbook/02-cases.md
description: Ogni team che rilascia una funzionalità LLM ha un prompt e quasi nessuno ha dei casi. Che cos'è un caso, e come averne venti entro questo pomeriggio.
search:
  exclude: true
source: handbook/02-cases.md
source_sha: 67838bc398da
source_commit: 48129ea
model: claude-opus-5
---

# 2. Casi: la risorsa che nessuno costruisce

Ogni team che rilascia una funzionalità basata su un LLM ha un prompt. Quasi nessuno ha dei casi. Questo capitolo parla di perché l'ordine è invertito, e di cosa fare — concretamente, a partire da questo pomeriggio.

## Che cos'è un caso

Un caso è un input che ti interessa, abbinato a ciò che sai sulla risposta giusta.

Tutto qui. Per un bot di assistenza: una domanda posta davvero da un cliente, e se la risposta avrebbe dovuto citare la politica di rimborso. Per un classificatore: un annuncio di lavoro, e la famiglia professionale a cui un recruiter ha confermato che appartiene. Per il [giudice della newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) che ricorre in tutto questo manuale: il titolo e il riassunto di un articolo, e se il lettore ha indicato che valeva la pena leggerlo.

```json
{
  "id": "2026-08-24-controlling-reasoning-effort-in-llms",
  "vars": {
    "source": "Ahead of AI (Raschka)",
    "title": "Controlling Reasoning Effort in LLMs",
    "summary": "How LLMs Learn Low-, Medium-, and High-Effort Reasoning Modes"
  },
  "expected": {
    "marked": true
  },
  "metadata": {
    "link": "https://magazine.sebastianraschka.com/p/controlling-reasoning-effort-in-llms",
    "original_score": 4
  }
}
```

Il lavoro lo fanno tre campi. L'`id` gli dà un nome. I `vars` sono ciò che il sistema riceve. L'`expected` è ciò che sai. I `metadata` servono a chi leggerà il caso più avanti — da dove veniva l'articolo, e il punteggio che il giudice gli aveva dato quella mattina — e nessun check li legge. Non sempre conosci l'output esatto corretto — per un riassunto o una risposta in testo libero non lo conosce nessuno — ma *qualcosa* lo sai sempre: deve citare X, non deve superare N parole, una persona di cui ti fidi l'ha giudicato accettabile. Tutto ciò che sai va in `expected`. Ciò che non sai lo lasci fuori e lo verifichi con qualcosa di più debole.

## Perché il prompt riceve tutte le attenzioni e i casi nessuna

Scrivere un prompt dà la sensazione di costruire qualcosa. Scrivi, il modello risponde, correggi, risponde meglio. Ogni iterazione è una piccola ricompensa. Scrivere casi sembra burocrazia: copi un input, decidi qual è la risposta giusta, la salvi, ripeti. Nessuna ricompensa, nessun progresso visibile, e la funzionalità già funziona — l'hai vista funzionare, l'input l'hai scritto tu.

Così il prompt riceve quaranta iterazioni e i casi zero, e il team rilascia con un prompt calibrato su qualunque cosa l'autore abbia scritto quel pomeriggio. Tre mesi dopo un utente segnala qualcosa di strano. Nessuno può dire se sia una novità, perché non c'è niente con cui confrontare. L'autore prova l'input, sembra a posto, oppure no — in entrambi i casi un solo campione. Il prompt riceve una quarantunesima iterazione, che sistema questo input e in silenzio ne rompe altri due che nessuno aveva provato.

Questo ciclo è il comportamento predefinito. Non è una mancanza di disciplina; è quello che succede quando l'unico riscontro è la risposta successiva del modello.

I casi cambiano il ciclo. Con venti casi, la quarantunesima iterazione è un numero: *diciannove su venti prima, diciassette dopo*. La correzione che ha rotto due cose è visibile nello stesso minuto in cui è stata fatta.

## Da dove vengono i casi

Non dalla tua immaginazione. I casi che inventi alla scrivania mettono alla prova gli input a cui hai già pensato, che sono esattamente quelli che il prompt già gestisce. I casi utili vengono da quattro fonti, e nessuna richiede creatività:

**Correzioni.** Ogni volta che una persona corregge il modello — un recruiter cambia la famiglia professionale, un redattore riscrive il riassunto, il lettore segnala un articolo a cui il giudice ha dato un punteggio basso — quella correzione è un caso etichettato, gratis, e più prezioso di qualsiasi cosa potresti scrivere tu. Nel progetto della newsletter, ogni mattina il lettore dice quali articoli ne valevano davvero la pena; quella risposta è l'`expected` dei casi del giorno. Il programma la registra come effetto collaterale dell'uso normale. Cerca quell'effetto collaterale nel tuo prodotto: quasi sempre c'è, ma non viene registrato.

**Reclami.** Un utente dice «qui ha sbagliato». Prima di toccare il prompt, salva l'input e la risposta giusta come caso. Poi correggi il prompt. Poi esegui i casi. Il reclamo diventa una protezione permanente invece che una toppa isolata — e se la correzione rompe qualcos'altro, lo scopri subito.

**Errori in produzione.** Qualsiasi output malformato, vuoto, fuori dalle regole o imbarazzante. Li hai già nei log; sono i casi che meno vorresti rivedere.

**Casi limite che hai notato.** L'input vuoto. L'input nella lingua sbagliata. L'input da 4000 parole. L'input che nomina il tuo concorrente. Hai visto il modello gestirli in modo strano almeno una volta; scrivili finché te ne ricordi.

L'abitudine che conta più di qualsiasi strumento: **un errore visto, un caso scritto, lo stesso giorno.** Non «più avanti bisognerebbe aggiungere dei test». Quel momento non arriva mai; l'errore sì.

## Quanti, e quali

Venti bastano per cominciare. Non duecento — duecento non li scriverai mai, e venti trasformano già una supposizione in un numero. Nel progetto della newsletter, ventuno casi sono bastati a misurare il rumore del giudice su sei run, e a mostrare che ridurre la porzione di ciascun articolo letta dal giudice, da 1500 caratteri a 400, [non ha peggiorato nulla](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/README.md#reporthtml).

Cosa serve ai venti:

**Entrambe le risposte.** Se ogni caso si aspetta un «sì», un modello che dice sempre sì ottiene il punteggio pieno. La suite della newsletter ha dieci articoli che il lettore voleva e undici che non voleva. Senza gli undici, la debolezza maggiore del giudice — promuovere cose che suonano soltanto rilevanti — resterebbe invisibile.

**La parte noiosa di mezzo, non solo i casi limite.** Una suite di venti input patologici ti dice come il sistema fallisce sotto stress e niente su come si comporta di martedì. Includi input ordinari — come categoria a sé, non come la maggior parte dell'insieme.

**Input stabili.** Un caso che scarica i dati di oggi domani è un caso diverso. Salva nel file un'istantanea dell'input. Il progetto della newsletter conserva nel caso il riassunto dell'articolo, non un URL da riscaricare: gli stessi ventuno input, a ogni run, da agosto.

**Un'etichetta, se puoi.** Per tutto ciò che classifica — positivo/negativo, approva/rifiuta, rilevante/non rilevante — aggiungi l'etichetta. Con le etichette, la tua suite ottiene un dato aggregato: *precision tra 0.60 e 0.67 su sei run della suite della newsletter*, un numero abbastanza stabile su cui mettere una soglia, mentre i singoli casi oscillavano di tre voti su cinque. Senza etichette hai venti verdetti e nessun riepilogo.

## Cosa non sono i casi

**Non sono gli esempi del prompt.** Gli esempi few-shot dentro il prompt sono le rotelle di supporto per il modello. I casi sono tenuti da parte; il modello non li vede mai come esempi. Se riusi gli stessi input per entrambe le cose, stai misurando la capacità del modello di copiare, non di generalizzare.

**Non sono una consegna una tantum.** Un file di casi completo il giorno del rilascio è già vecchio al secondo reclamo. L'insieme cresce alla velocità della produzione — ed è per questo che «un errore, un caso» è una regola e non un progetto.

**Non sono dati sensibili, se il file deve finire da qualche parte.** Un caso costruito su una conversazione reale con un cliente si porta dietro quel cliente. Tieni casi del genere dentro il perimetro da cui provengono, oppure riscrivi l'input con la stessa struttura e dati diversi. Nel progetto della newsletter gli input sono articoli pubblici, quindi anche il file è pubblico; per uno strumento di recruiting, gli annunci di lavoro vanno bene, i CV no.

## La parte che si accumula

Tutto il resto, in un progetto LLM, si deprezza. Il prompt che hai calibrato su un modello rende peggio sul successivo. La soglia che hai scelto va alla deriva. Il giudice cambia idea. I casi non si deprezzano: una risposta giusta a un input reale resta giusta quando cambia il modello, quando cambia il prompt, quando cambi fornitore. Venti casi a marzo sono venti casi a settembre, più quelli che settembre ha aggiunto.

Per questo il lavoro noioso è l'unico che valga la pena fare per primo. Dopo sei mesi, il team con il prompt migliore ha un prompt. Il team con duecento casi reali ha la possibilità di cambiare qualsiasi cosa — modello, prompt, fornitore — e di sapere entro un'ora se è peggiorato. Il prompt è un'opinione; i casi sono la memoria.

## Da fare oggi

1. Trova il punto di correzione nel tuo prodotto — il punto in cui una persona corregge il modello. Se esiste, inizia a registrarlo. Se non esiste, è la prima cosa da costruire, prima di qualsiasi suite.
2. Apri i log. Prendi gli ultimi dieci input che hanno prodotto un reclamo o un output strano. Scrivi per ciascuno la risposta giusta. Sono dieci casi.
3. Prendi dieci input ordinari dagli stessi log — di quelli su cui nessuno si è lamentato. Verifica che l'output andasse bene. Sono venti.
4. Mettili in un file, nel repository, accanto al codice. Salva un'istantanea degli input. Aggiungi le etichette dove servono.
5. D'ora in poi: un errore visto, un caso scritto, lo stesso giorno.

Il prossimo capitolo parla di dove vengono le risposte giuste quando nessuno te ne dà — e di perché la cosa si decide mentre scrivi la funzionalità, non dopo.
