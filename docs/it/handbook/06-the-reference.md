---
seo_title: 'Il riferimento: una soglia non è un riferimento'
lang: it
translation_of: handbook/06-the-reference.md
description: Un punteggio può calare parecchio e superare comunque la sua soglia in entrambi i giorni. A intercettarlo è l'unico numero che metti per iscritto e rispetto al quale accetti di essere misurato.
search:
  exclude: true
source: handbook/06-the-reference.md
source_sha: 7fe35576a20c
source_commit: 340f1dd
model: claude-opus-5
---

# 6. Il riferimento

Finora tutto produce numeri. Questo capitolo parla dell'unico numero che conta più degli altri: quello che metti per iscritto e rispetto al quale accetti di essere misurato.

## Una soglia non è un riferimento

La maggior parte dei team che testano una funzionalità LLM, quando la testano, ha una soglia: il punteggio deve essere superiore a 0.7. Risponde a una domanda — *è accettabile?* — ed è cieca rispetto all'altra — *è come era prima?*

Ecco un esempio con numeri inventati. Una funzionalità che al rilascio ha ottenuto 0.91 e oggi ottiene 0.78 supera la soglia in entrambi i giorni. Niente diventa rosso. Eppure qualcosa è cambiato di tredici punti, e chi la usa ha percepito il cambiamento prima di qualsiasi test. Per vederlo devi aver messo per iscritto quello 0.91. Questo è il riferimento: un run della tua suite che hai esaminato, giudicato corretto e registrato — punteggi, il prompt che li ha prodotti, il commit, la data — in modo che ogni run successivo possa essere confrontato con esso invece che con una linea.

La soglia dice qual è il livello minimo. Il riferimento dice da dove sei partito. Servono entrambi, e il secondo è quello che quasi nessuno conserva.

## Cosa contiene un riferimento

Un file, nel repository, accanto al codice. Nel [progetto newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) è [`.digline/alessandro/baselines/brief-judge.json`](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/.digline/alessandro/baselines/brief-judge.json), committato come qualsiasi altro file. Dentro:

- **I verdetti** — ogni check su ogni caso, con il suo punteggio, la sua soglia e la sua tolleranza. Non un riepilogo: la tabella completa, così un confronto successivo può dire *quale* caso si è spostato.
- **Gli aggregati**, se i casi sono etichettati — precision 0.667 e accuracy 0.762, dieci su quindici e sedici su ventuno — con i conteggi che li hanno prodotti.
- **Il testo del prompt** che ha prodotto il run, alla lettera, con il suo hash. Non un rimando a un file che nel frattempo può essere cambiato; il testo stesso, congelato.
- **Il commit** su cui si trovava il codice, e se il working tree era pulito.
- **La configurazione** della suite — quali check, quali soglie — sotto forma di hash, così che un confronto tra regole diverse lo dichiari invece di risultare privo di senso senza che nessuno se ne accorga. Il confronto viene comunque eseguito: segnala che la suite è cambiata rispetto al riferimento, e mette quella frase accanto a numeri misurati con altre regole. Quello che l'hash rifiuta è la promozione — un run la cui configurazione non è quella in vigore non può diventare il riferimento.

Dal fatto che il prompt sia *dentro* il file derivano due conseguenze. Primo, il riferimento è riproducibile anche se non hai mai committato il prompt separatamente — una situazione frequente durante una giornata di esperimenti. Secondo, quando un run successivo differisce, il confronto può mostrare il diff del prompt proprio accanto al diff dei punteggi: *hai cambiato queste tre righe; questi due casi si sono spostati.* Questo accostamento è la cosa più utile che un confronto possa mostrare, ed esiste solo se il prompt viaggia insieme al run.

## La promozione: un atto deliberato

Un run non diventa il riferimento perché è l'ultimo o perché è verde. Qualcuno lo promuove. È una decisione — *ecco com'è fatto un risultato buono, accetto di essere misurato rispetto a questo* — e deve essere percepita come tale. Nel progetto newsletter è un comando, `digline promote`, e il risultato è un commit che contiene un file leggibile da chi fa la revisione.

Tre cose che una promozione dovrebbe rifiutare, perché ciascuna renderebbe il riferimento una menzogna:

- Un run prodotto con una **configurazione diversa** da quella della suite attuale: i suoi numeri sono stati misurati con altre regole.
- Un run con **un qualsiasi check in errore** — un *non è stato possibile giudicare* — perché un riferimento è uno stato approvato e un errore non è uno stato.
- Un run di un **tenant diverso** da quello per cui stai promuovendo, se la tua suite ha dei perimetri (capitolo 8).

Se il tuo strumento non li rifiuta, rifiutali tu. Un riferimento di cui non ti puoi fidare è peggio di nessun riferimento, perché trasforma ogni confronto successivo in una discussione.

## Non il primo run verde

Il primo run che passa è quello che più viene voglia di promuovere, ed è quello sbagliato. Hai appena letto il capitolo 5: il giudice oscilla, e un singolo run è una sola estrazione. Se lo promuovi, il riferimento registra il campione fortunato; ogni run successivo viene confrontato con quello fortunato e sembra peggiore di quanto sia.

Una singola estrazione può cadere da una parte o dall'altra. Tre run della suite newsletter il 3 settembre, a undici minuti di distanza e senza nulla di modificato, hanno concordato con il lettore su 16, 14 e 16 articoli su 21. Un riferimento preso dal secondo dei tre segnalerebbe gli altri due come migliori di due articoli — un *miglioramento* che nessuno ha prodotto.

La procedura che lo sostituisce costa tre run:

1. Esegui tre volte sul sistema congelato.
2. Guarda i casi che differiscono tra un run e l'altro. Per ciascuno, annota quale run contiene il valore intermedio.
3. Promuovi il run che si trova al centro più spesso. In caso di parità, decidi in base al costo.

Quel run è il riferimento. Registra il comportamento tipico, non il migliore né il peggiore, e un confronto successivo con esso significa quello che dice.

## Cosa cambia il riferimento e cosa no

**Un prompt migliore.** L'hai modificato, il confronto mostra due casi migliorati e nessuna regressione, il diff ti convince. Promuovi. Il vecchio riferimento resta nella storia di git; il nuovo porta con sé il nuovo testo del prompt.

**Una soglia alzata.** Hai deciso che il livello minimo debba essere 0.70, non 0.60. È un cambio di configurazione: il confronto continua a funzionare — e ti dice che la soglia si è spostata, così il ribaltamento si legge come un cambio di regola e non come un cambio di modello — ma la promozione viene rifiutata finché la configurazione non corrisponde. Cambia la regola, esegui, promuovi: tre passaggi, tutti visibili in una pull request.

**Un caso nuovo.** Aggiungere un caso non invalida il riferimento: compare come *nuovo* nel confronto successivo, senza una controparte con cui confrontarlo. Dopo averlo esaminato, promuovi ed entra a far parte del registro.

**Un cambio di modello.** Il provider ha aggiornato il modello, nel tuo codice non è cambiato nulla, il confronto mostra quattro casi peggiorati. È esattamente la situazione per cui esiste il riferimento. Non promuovi il run peggiore. Indaghi, se serve sistemi il prompt e promuovi quando sei tornato al livello di prima — oppure accetti deliberatamente il nuovo comportamento, e la promozione è la traccia che l'hai fatto.

**Il riferimento non cambia perché è passato del tempo.** Un riferimento di marzo è valido a settembre se nel frattempo non è stato promosso nulla. La sua età è un'informazione, non un difetto: dice che da marzo nessuno ha approvato niente, il che o va bene o è un rilievo.

## Dove sta il riferimento

Nel repository, committato, revisionato. Non su un server, non in una dashboard, non nella memoria di chi l'ha eseguito. Tre motivi che non sono questione di preferenze:

Ci si può fare il **diff**. Due riferimenti, due file, `git diff`. Ogni numero che si è spostato, ogni riga di prompt che è cambiata, in un'unica vista.

Si può **revisionare**. Una promozione è una pull request. Qualcuno diverso dall'autore vede i numeri e il prompt prima che diventino lo standard.

Si può **mostrare**. Quando un cliente — o un auditor, o il tuo stesso team fra sei mesi — chiede che cosa è stato testato e approvato e quando, la risposta è un file con un hash di commit e una data, non uno screenshot.

## Da fare oggi

1. Congela il prompt e i casi. Esegui la suite tre volte.
2. Scegli il run mediano con la procedura descritta sopra. Promuovilo. Committa il file.
3. Apri il file. Verifica che il testo del prompt sia lì dentro, alla lettera. Se il tuo strumento non ce lo mette, mettilo tu — una copia del prompt accanto al riferimento, nello stesso commit.
4. Fai una piccola modifica al prompt. Esegui. Confronta. Leggi il diff del prompt accanto al diff dei punteggi. Quella vista è la ragione di tutto ciò che c'è in questo capitolo.

Il prossimo capitolo parla di come mantenere tutto questo in vita: quando eseguire, che cosa deve indurti a guardare, e cosa fare la mattina in cui il confronto è rosso e tu non hai cambiato nulla.
