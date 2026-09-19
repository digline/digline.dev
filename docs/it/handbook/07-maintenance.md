---
seo_title: 'Manutenzione: eseguire la suite come pratica'
lang: it
translation_of: handbook/07-maintenance.md
description: Quando dovrebbe essere eseguita una suite di valutazione, che cosa dovrebbe farti guardare e cosa fare la mattina in cui la CI diventa rossa e non hai cambiato proprio niente.
search:
  exclude: true
source: handbook/07-maintenance.md
source_sha: 0117d185cb00
source_commit: d52f054
model: claude-opus-5
---

# 7. Manutenzione

Una suite eseguita una volta sola è una demo. Questo capitolo parla della parte che la rende una pratica: quando viene eseguita, che cosa dovrebbe farti guardare e cosa fare la mattina in cui diventa rossa e non hai cambiato niente.

## I cinque inneschi

Succede qualcosa; la suite viene eseguita; il confronto dice se è peggiorato. I qualcosa possibili sono cinque, e richiedono risposte diverse.

### 1. Hai cambiato qualcosa

Il prompt, il modello, il retrieval, il codice attorno alla chiamata. Questo è l'innesco che ti aspetti, quello di cui si occupa la CI: ogni pull request esegue la suite e la confronta con il riferimento. Il rosso blocca il merge; le righe sotto il titolo dicono quali casi si sono spostati e di quanto; il diff del prompt sta lì accanto.

La risposta è quella ordinaria: guarda i casi che sono regrediti, decidi se il cambiamento ne vale la pena, correggi o accetta. L'unica regola: un confronto rosso non si risolve mai allargando la tolleranza o abbassando la soglia. Quelle sono modifiche alle regole, e le modifiche alle regole passano dalla porta principale (capitolo 6), non dalla correzione di una build che fallisce.

### 2. Il provider ha cambiato qualcosa

Nel tuo repository non si è mosso niente. Si è mosso il modello dietro l'API: un aggiornamento, una deprecazione, un alias ripuntato, un cambiamento nel comportamento predefinito. La cronologia dei commit dice «nessuna modifica». Il confronto, se è stato eseguito, dice quattro casi peggiori.

*Se è stato eseguito* è il punto. La CI parte sui push, e nessuno ha fatto push. Questo innesco ha bisogno di una pianificazione: un job notturno o settimanale che esegue la suite contro il riferimento senza alcuna modifica da parte tua. Un risultato rosso con un diff pulito è la firma del provider: l'unico errore che nessuna code review, nessun test del tuo codice e nessuna attenzione possono intercettare, e quello che la maggior parte dei team scopre dagli utenti.

Nel [progetto newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) è un workflow settimanale che esegue il giudice vero e confronta. Costa circa sette centesimi a settimana. È l'assicurazione più economica del repository.

La risposta è diversa da quella dell'innesco 1: non sei stato tu, quindi non puoi annullarlo. Le opzioni, in ordine: fissa la versione del modello se il provider lo consente e stavi usando un alias; adegua il prompt al nuovo comportamento e promuovi quando sei tornato ai livelli di prima; oppure accetta il nuovo comportamento come riferimento, deliberatamente, con la promozione come traccia del fatto che l'hai visto e hai deciso.

### 3. Un caso reale è andato storto

Lo segnala un utente. Lo mostra un log. Qualcuno del team nota una risposta che non sarebbe dovuta uscire. La suite non l'ha intercettata perché non aveva quell'input.

La risposta è l'abitudine del capitolo 2, ed è la frase più importante di questo manuale: **un errore visto, un caso scritto, lo stesso giorno.** Prima di toccare il prompt, salva l'input e la risposta giusta come caso. Esegui la suite: il nuovo caso fallisce, ed è corretto così; compare come *nuovo*, senza niente con cui confrontarlo. Poi correggi il prompt. Poi esegui di nuovo: il nuovo caso passa, e gli altri venti ti dicono se la correzione ha rotto qualcosa. Poi promuovi.

Salta il primo passo e avrai rattoppato un input senza imparare niente. Fallo, e quell'errore diventa una protezione permanente.

### 4. Le regole si sono mosse

Qualcuno ha alzato una soglia, stretto una tolleranza, aggiunto un check, ne ha tolto un altro. Il confronto viene comunque eseguito, e ti dice che la configurazione è diversa da quella del riferimento: così un caso passato da pass a fail si legge come una modifica alle regole, non come una modifica del modello. La promozione viene rifiutata finché il riferimento non è ristabilito con le nuove regole.

La risposta è breve: esegui con le nuove regole, guarda, promuovi. Il senso del rifiuto è che una modifica alle regole non è mai invisibile: produce sempre una promozione che qualcuno può vedere in review.

### 5. Un caso ha smesso di essere giudicabile

Un check restituisce *could not judge*: i campioni del giudice si sono divisi, l'output aveva la forma sbagliata, il provider è andato in timeout. Non è né pass né fail, e blocca la promozione.

Le risposte sono due, e solo due. Se il caso è davvero ambiguo — i campioni si dividono perché si dividerebbe anche una persona — sospendilo, con una motivazione scritta, così resta nella suite come lacuna visibile invece di sparire in silenzio. Se la colpa è del check — forma sbagliata, prompt sbagliato nel giudice — correggi il check. Quello che non devi fare è abbassare l'accordo minimo finché la divisione non diventa un pass: così *sconosciuto* diventa *va bene* senza che nessuno l'abbia deciso.

## I dieci minuti settimanali

Gli inneschi sono reattivi. La pratica che tiene onesta una suite è un gesto piccolo, noioso e pianificato:

1. Apri il confronto della run pianificata. Verde o rosso, leggi gli aggregati — precisione, accuratezza — rispetto al riferimento. Due numeri, trenta secondi.
2. Guarda l'elenco dei casi che si sono spostati, anche entro la tolleranza. Un caso che si sposta un po' ogni settimana ti sta dicendo qualcosa prima di superare il limite.
3. Controlla il numero di casi. Se non è cresciuto dalla settimana scorsa, chiediti se in produzione non è andato storto niente o se nessuno l'ha scritto. Di solito è la seconda.
4. Controlla l'età del riferimento. Un riferimento di quattro mesi fa su una funzionalità che è cambiata due volte è un riferimento che nessuno ha riapprovato.
5. Se qualcosa ai punti 1–4 richiede una decisione, prendila subito — promuovi, sospendi, aggiungi un caso — e fai commit.

Dieci minuti, una volta a settimana, a carico di chi è responsabile della funzionalità. Saltali per un mese e la suite è ancora lì; saltali per un trimestre e torna a essere una demo.

## Ciò che peggiora senza che te ne accorga

Tre guasti lenti che nessun innesco intercetta, perché ogni passo è troppo piccolo per far scattare un allarme:

**Deriva dei costi.** Ogni modifica al prompt aggiunge una frase; nessuno ne toglie una. Il check di budget dà un punteggio graduale proprio perché un costo *entro* il limite risulti comunque come un cambiamento rispetto al riferimento. Guarda il numero, non solo il colore.

**Casi che marciscono.** Un caso la cui risposta attesa era giusta a marzo può essere sbagliata a settembre perché il prodotto è cambiato: la finestra per i rimborsi si è spostata, la tassonomia si è arricchita di una categoria. Una suite con casi marci fallisce per i motivi sbagliati e insegna alle persone a ignorare il rosso. Quando un caso fallisce e l'output sembra giusto, controlla il caso prima del prompt.

**Deriva del riferimento per promozioni successive.** Ogni promozione accetta una piccola perdita: «un caso peggiore, ma il diff è più pulito». Dieci promozioni dopo, il riferimento è dieci piccole perdite sotto il punto di partenza, e ogni singolo confronto era verde. La difesa è l'aggregato nel file: confronta la precisione di questo mese non con il riferimento della settimana scorsa, ma con il primo che hai approvato. Git ce l'ha.

## Da fare oggi

1. Aggiungi la run pianificata — una a settimana basta — con il giudice vero. Che sia l'unico job a partire quando nessuno ha fatto push.
2. Metti la revisione da dieci minuti in calendario, a carico di chi è responsabile della funzionalità.
3. Scrivi la regola «un errore, un caso» dove il team la veda: il README della suite, il template delle pull request, il topic del canale.
4. La prossima volta che il confronto è rosso e non hai cambiato niente, non toccare la tolleranza. Leggi il diff. È vuoto. È il provider, e adesso sai che aspetto ha.

L'ultimo capitolo è per i team che costruiscono funzionalità LLM per conto di altri: dove la stessa suite diventa la risposta a una domanda che il cliente farà, e dove una parte di ciò che contiene non deve mai uscire dal loro perimetro.
