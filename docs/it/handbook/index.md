---
title: Manuale
seo_title: 'Manuale: tenere sotto controllo una funzionalità LLM'
lang: it
translation_of: handbook/index.md
description: 'Otto capitoli sulla valutazione delle applicazioni LLM nella pratica: casi, ground truth, check, il giudice, il riferimento, manutenzione. Parlano del problema, non dello strumento.'
search:
  exclude: true
source: handbook/index.md
source_sha: 0b5b5820ed85
source_commit: d7f3b56
model: claude-opus-5
---

# Manuale

Otto capitoli su come tenere sotto controllo una funzionalità LLM, per chi ne ha
una in produzione e non ha ancora passato la brutta settimana. Parlano del
problema, non dello strumento: niente di quanto segue richiede digline
installato, e la maggior parte dei numeri viene da un piccolo progetto pubblico
che puoi consultare tu stesso. Inizia dal primo capitolo e leggili in ordine:
ciascuno si appoggia al precedente.

- **[1. Che cosa stai davvero rilasciando](../../handbook/01-what-you-are-shipping.md)** —
  perché una chiamata al modello sembra una funzione e non lo è, e quanto ti
  costa.
- **[2. Casi: la risorsa che nessuno costruisce](../../handbook/02-cases.md)** — ogni team ha
  un prompt, quasi nessuno ha dei casi. Che cos'è un caso, e come averne venti
  entro questo pomeriggio.
- **[3. Ground truth: quando nessuno te ne dà una](../../handbook/03-ground-truth.md)** — da
  dove vengono le risposte corrette quando non ci sono dati etichettati, e
  perché la cosa si decide quando scrivi la funzionalità.
- **[4. Check: prima i deterministici, il giudice per ultimo](../../handbook/04-checks.md)** —
  come trasformare un output in un verdetto, e la regola che fa risparmiare più
  tempo: usa un modello per giudicare solo ciò che nient'altro può giudicare.
- **[5. Il giudice](../../handbook/05-the-judge.md)** — i due rumori, perché devi misurare
  quello del giudice prima di poter leggere quello del tuo sistema, e la
  procedura che sostituisce le congetture con un numero.
- **[6. Il riferimento](../../handbook/06-the-reference.md)** — una soglia non è un
  riferimento. L'unico numero che metti nero su bianco e in base al quale
  accetti di essere misurato.
- **[7. Manutenzione](../../handbook/07-maintenance.md)** — quando viene eseguita la suite,
  che cosa dovrebbe farti andare a guardare, e che fare la mattina in cui
  diventa rossa e non hai cambiato niente.
- **[8. Per i team che sviluppano per altri](../../handbook/08-for-teams-building-for-others.md)**
  — la stessa suite che svolge due compiti in più quando la funzionalità LLM
  appartiene a un cliente, e l'unica regola che non ammette eccezioni.
