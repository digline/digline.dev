---
title: Inizia qui
template: start.html
lang: it
translation_of: start.md
description: Cos'è una regressione degli LLM, perché i test ordinari non la rilevano e cosa fa digline al riguardo — in parole semplici.
search:
  exclude: true
source: start.md
source_sha: 4a378d5bd6f6
source_commit: 933f4e0
model: claude-opus-5
---

# Inizia qui

Se sai già cos'è una regressione silenziosa, passa direttamente alla [Guida](../product/guide.md). Questa pagina è per tutti gli altri.

## Il problema, in una storia

Ho un piccolo script che ogni mattina legge qualche centinaio di articoli sull'IA e chiede a un modello linguistico di scegliere i cinque che valgono la lettura. Funzionava. Poi un giorno ha iniziato a tralasciare quelli buoni.

Niente era andato in crash. Nessun test era fallito. Il codice era lo stesso della settimana precedente. Era cambiato il *comportamento* del modello — una modifica al prompt qui, un aggiornamento del modello là — e il comportamento non è qualcosa che un test unitario verifica. Lo script restituiva sempre cinque articoli. Solo che erano i cinque sbagliati.

Questa è una **regressione degli LLM**: il tuo sistema continua a funzionare, a rispondere, a passare i test, ed è silenziosamente peggiore di prima.

## Perché i tuoi test non la vedono

I test ordinari confrontano un output con un valore atteso. Un modello linguistico non ti dà un valore atteso. Fagli la stessa domanda due volte e potresti ottenere due risposte diverse, entrambe accettabili. Così i team o smettono di testare il comportamento del modello, oppure scrivono un test che passa oggi e non sa dirti niente su domani.

Le domande concrete, alla fine, sono queste:

- Confrontato con *cosa*? Serve un riferimento: il comportamento che hai accettato per ultimo.
- Peggiore di *quanto*? Un punteggio che passa da 0.88 a 0.86 può essere rumore. Da 0.88 a 0.73 è una regressione. Senza sapere quanto il sistema oscilli da solo, non puoi distinguere i due casi.
- Chi decide cosa significa «giusto», e dove è messa per iscritto questa decisione?

## Cosa fa digline

digline è un gate che metti davanti a quella domanda. Scrivi una volta per tutte cosa ti aspetti dal tuo sistema, sotto forma di un insieme di check: quelli deterministici (la risposta è JSON valido, non contiene numeri di telefono, cita il nome del cliente) e quelli giudicati (un secondo modello valuta la risposta rispetto a una griglia di valutazione). Li esegui sul tuo sistema. Quando il risultato ti soddisfa, lo **promuovi**: diventa il baseline, un file committato nel tuo repository accanto al codice.

Da quel momento ogni run viene confrontato con quel baseline, e il report risponde all'unica domanda che conta:

> Niente è peggiorato rispetto al riferimento. 2 check si sono spostati entro il rumore. Ogni caso è stato giudicabile. 1 caso è sospeso. La suite è invariata rispetto al riferimento. 1 file sotto test è cambiato dopo il riferimento.

oppure

> 14 check sono peggiorati rispetto al riferimento. 7 casi non sono stati giudicabili. Nessun caso è sospeso. La suite è invariata rispetto al riferimento. I file sotto test sono gli stessi del riferimento.

Il baseline è un file in git. Ha una cronologia, si può confrontare con diff, e nessuno lo promuove tranne te. Non c'è una dashboard a cui accedere né un servizio che riceve i tuoi dati: digline gira dove gira il tuo codice.

## Trenta secondi, in immagini

<video controls preload="none" poster="/assets/video/ep01-poster.jpg"
       width="1920" height="1080"
       style="width:100%; height:auto; aspect-ratio:16/9; background:#0f1117">
  <source src="/assets/video/ep01.mp4" type="video/mp4">
  Il tuo browser non supporta il tag video. <a href="/assets/video/ep01.mp4">Scarica il video</a>.
</video>

*Episodio 1 di una breve serie sulla regressione degli LLM. Ospitato su questo sito — nessun player di terze parti, nessun cookie.*

## Dove andare adesso

- [Perché](../why.md) — il ragionamento dietro le scelte di progetto, se vuoi contestarlo.
- [Guida](../product/guide.md) — installalo e arriva al tuo primo `compare` in pochi minuti.
- [Come si colloca digline](../comparison/index.md) — se usi già uno strumento di eval e vuoi sapere cosa cambia.

Dieci parole che incontrerai lungo la strada: **run**, **baseline**, **confronto**, **promozione**, **check**, **giudizio**, **tolleranza**, **noise floor**, **regressione**, **gate**. Ciascuna è spiegata la prima volta che compare nella Guida.
