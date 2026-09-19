---
seo_title: Che cosa stai davvero rilasciando
lang: it
translation_of: handbook/01-what-you-are-shipping.md
description: 'Una chiamata a un modello sembra una funzione ma non lo è: lo stesso prompt, campionato due volte, dà due risposte. Quanto ti costa, e perché i test ordinari non riescono a vederlo.'
search:
  exclude: true
source: handbook/01-what-you-are-shipping.md
source_sha: 29449261b5b7
source_commit: 356a3c8
model: claude-opus-5
---

# 1. Che cosa stai davvero rilasciando

Se vieni dal software tradizionale, la prima cosa da disimparare è che cos'è una funzione.

## Una funzione, e la cosa che sembra una funzione

Da trent'anni vale questo: dato lo stesso input, lo stesso codice produce lo stesso output. Su questo si regge tutta l'ingegneria del software — test, debugging, code review, «funziona sulla mia macchina». Puoi ragionare su una funzione perché è una corrispondenza fissa tra input e output.

Una chiamata a un modello linguistico sembra una funzione. Ha un input (il prompt) e un output (il completamento). Nel tuo codice sta tra due funzioni ordinarie. Non lo è.

Un modello linguistico produce una *distribuzione di probabilità* sui possibili token successivi, e poi ne estrae un campione. Il campionamento è il punto: è ciò che permette allo stesso modello di scrivere una poesia e una query SQL. Significa anche che lo stesso prompt, inviato due volte, può tornare con due risposte diverse — ed entrambe sono «corrette» nell'unico senso che il modello conosce, cioè che entrambe erano probabili.

Puoi portare la temperatura a zero e ridurre la variazione. Non puoi eliminarla, e per la maggior parte dei compiti utili non vuoi farlo: un modello a temperatura zero è peggiore proprio nelle cose per cui l'hai comprato.

## Che effetto ha tutto questo sulle tue intuizioni

**«L'ho provato e funziona.»** L'hai eseguito una volta. Hai estratto un campione dalla distribuzione. Il campione successivo può essere diverso. Nel [giudice per la newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) che questo manuale usa come esempio ricorrente, gli stessi ventuno articoli valutati due volte con un prompt identico hanno prodotto venti verdetti identici e uno diverso. Uno su ventuno non è un bug. È la natura della cosa.

**«Ho sistemato il prompt.»** Hai cambiato la distribuzione. Ora produce la risposta che volevi per l'input che hai provato. Produce anche risposte leggermente diverse per ogni altro input, e quelle non le hai guardate. Le modifiche al prompt sono globali; la tua attenzione era locale.

**«Non è cambiato niente, quindi funziona ancora.»** Il tuo codice non è cambiato. Il modello dietro l'API sì: i provider aggiornano, riaddestrano, dichiarano obsolete delle versioni e ripuntano gli alias senza un changelog che tu leggerai. La cronologia git dice che il sistema è invariato. I tuoi utenti dicono che è peggiorato. Hanno ragione entrambi.

**«È sopra la soglia.»** Una soglia intercetta ciò che sta *sotto soglia*. Non intercetta ciò che è *peggiore del mese scorso*. Prendi dei numeri inventati: un punteggio che scivola da 0.91 a 0.78 è ancora sopra 0.7, ancora verde, e tredici punti peggiore per chi riceve la risposta.

## Che cosa stai davvero rilasciando, allora

Non una funzione. Un sistema il cui comportamento è una distribuzione, che deriva da solo, che cambia globalmente quando lo modifichi localmente, e di cui nessuno nel tuo team ha visto più di una manciata di campioni.

Sembra allarmante. È gestibile — ma solo con strumenti adatti alla sua natura, e quelli del software tradizionale non lo sono. `assert output == expected` non significa nulla di fronte a una distribuzione. La code review non può vedere un cambiamento avvenuto dalla parte del provider. Una demo dimostra un campione.

Ciò che è adatto alla cosa è quello che faresti con qualsiasi altra misura affetta da rumore: prendere più campioni, confrontarli con un riferimento registrato, e considerare reale un cambiamento solo quando è più grande del rumore. Non è un'idea nuova. È così che funziona un laboratorio. Semplicemente non è il modo in cui ai team di sviluppo è stato insegnato a lavorare, perché fino a poco tempo fa niente nello stack si comportava così.

## Le quattro cose che ti servono

Tutto il resto di questo manuale si riduce a quattro cose, e l'ordine conta:

1. **Casi** — un insieme di input che ti interessano, con quello che sai sulle risposte giuste. Tenuti fuori dal prompt. In crescita nel tempo. Questo è il patrimonio, e ne parla il [capitolo 2](../../handbook/02-cases.md); il [capitolo 3](../../handbook/03-ground-truth.md) parla di dove prendere le risposte quando nessuno te ne dà.
2. **Checks** — che cosa verifichi su ogni output. Prima quelli che non richiedono un modello; per ultimi quelli che richiedono un giudice, perché un giudice è un'altra distribuzione. [Capitolo 4](../../handbook/04-checks.md), [capitolo 5](../../handbook/05-the-judge.md).
3. **Un riferimento** — un run che hai esaminato e approvato, registrato insieme al prompt e al commit che l'ha prodotto, in modo che ogni run futuro abbia qualcosa con cui essere confrontato. [Capitolo 6](../../handbook/06-the-reference.md).
4. **Una routine** — quando eseguire, quando andare a verificare, che cosa fare quando il confronto diventa rosso. [Capitolo 7](../../handbook/07-maintenance.md).

Se sviluppi software per altri, c'è una quinta cosa — che cosa puoi mostrare al cliente e che cosa non deve mai uscire dal suo perimetro — nel [capitolo 8](../../handbook/08-for-teams-building-for-others.md).

## Un'abitudine prima di proseguire

Apri il progetto in cui hai una chiamata a un LLM. Trova l'input con cui l'hai provata quando l'hai scritta. Invialo di nuovo, adesso, cinque volte.

Se tutte e cinque le risposte sono uguali, bene: hai un compito con poco rumore, e il resto di questo manuale ti risulterà facile. Se differiscono, hai appena visto ciò di cui parla questo capitolo, sul tuo sistema, in un minuto. In ogni caso ora sai qualcosa che non sapevi prima di eseguirlo, che è esattamente il punto.
