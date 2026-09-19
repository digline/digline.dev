---
seo_title: 'Check: prima i deterministici, il giudice per ultimo'
lang: it
translation_of: handbook/04-checks.md
description: 'Come trasformare l''output di un LLM in un verdetto, e la regola che fa risparmiare più tempo nella valutazione: usa un modello per giudicare solo ciò che nient''altro può giudicare.'
search:
  exclude: true
source: handbook/04-checks.md
source_sha: bf59e8257331
source_commit: d778c40
model: claude-opus-5
---

# 4. Check: prima i deterministici, il giudice per ultimo

Un caso dice che cosa entra e che cosa sai della risposta giusta. Un check è il modo in cui trasformi un output in un verdetto. Questo capitolo parla di come scegliere i check — e di una regola che sembra troppo semplice per contare qualcosa e che fa risparmiare più tempo di qualsiasi altra cosa qui dentro: **usa un modello per giudicare solo ciò che nient'altro può giudicare.**

## Due tipi di check

**I check deterministici** non richiedono alcun modello. Guardano l'output e rispondono a una domanda in modo meccanico: contiene questa frase, è JSON valido, rispetta questo schema, sta sotto le 200 parole, costa meno di un centesimo, contiene un codice fiscale. Stesso output, stesso verdetto, ogni volta, all'istante, gratis.

**I check giudicati** chiedono a un modello di valutare l'output: questa risposta è cortese, risponde alla domanda, è supportata dai documenti recuperati, è migliore della versione precedente. Possono esprimere cose che nessuna regex può esprimere. Sono anche una seconda distribuzione sopra la prima — anche il giudice estrae dei campioni — e ogni check giudicato eredita il rumore, il costo e la latenza di una chiamata al modello.

La maggior parte dei team ricorre subito al giudice, perché è la parte interessante. Questo capitolo sostiene l'ordine opposto.

## Perché prima i deterministici

Prendi il [giudice della newsletter](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/suite.py). Il suo output è un piccolo oggetto JSON: un punteggio da 1 a 5 e una motivazione di una frase. Prima di chiedere a un qualsiasi modello se il punteggio è *buono*, tre cose si possono verificare senza alcun modello:

- L'output è JSON valido con esattamente quei due campi? (`JsonSchema`)
- Il punteggio è un intero tra 1 e 5? (lo stesso schema)
- La chiamata è costata meno del budget? (`CostBudget`)

Questi tre intercettano i fallimenti che in produzione capitano davvero: il modello che racchiude il JSON in un testo discorsivo, il modello che si inventa un punteggio di 0, il prompt che cresce finché ogni chiamata costa il triplo di prima. Li intercettano gratis, in modo deterministico, a ogni run. E quando uno di questi fallisce, l'errore è inequivocabile — nessuno discute su «JSON non valido».

Solo dopo viene la domanda che richiede un giudice — «questo punteggio è in accordo con quello che voleva il lettore?» — e nel progetto della newsletter anche a quella si è rivelato possibile rispondere senza modello, perché i voti del lettore stesso sono registrati. Il check è quattordici righe di Python: *il giudice ha detto ≥4 esattamente quando il lettore l'ha segnalato?* Nessun secondo modello, nessun rumore introdotto dal check stesso.

La forma generale: **ogni check che riesci a rendere deterministico è una fonte di rumore in meno tra te e la risposta.** Una suite con cinque check deterministici e un giudice ha un solo segnale rumoroso da calibrare. Una suite con sei giudici ne ha sei.

## Che cosa intercettano i deterministici

Un breve catalogo, in base al fallimento per cui ciascuno esiste:

| Fallimento che hai già visto | Check |
|---|---|
| La risposta ha dimenticato la riga obbligatoria (un disclaimer, una firma, una formula legale) | `Contains` |
| La risposta ha citato qualcosa che non deve mai citare (un concorrente, un nome interno, «in quanto modello di IA») | `NotContains` |
| L'output doveva essere strutturato ed è tornato in prosa | `IsJson`, `JsonSchema` |
| Le risposte si allungano ogni settimana, o devono stare dentro i limiti di un canale | `Length` |
| La risposta deve essere *vicina* a una nota, non identica | `Levenshtein`, graduato |
| L'output è arrivato a una persona e conteneva un IBAN, un codice fiscale, un'email | `PiiAbsent` |
| Una modifica al prompt ha raddoppiato i token, e nessuno se n'è accorto fino alla fattura | `CostBudget` |
| La funzionalità va bene ma gli utenti aspettano quattro secondi | `LatencyBudget` |

Due di questi meritano una nota. `PiiAbsent` è quello che si salta e poi si rimpiange: un LLM che ha dati dei clienti nel contesto, prima o poi, ne ripeterà una parte in un output dove non dovrebbero stare, e nessun giudice riconosce un IBAN valido in modo affidabile quanto un checksum. E i budget sono graduati, non pass/fail: un costo che sale lentamente *restando* dentro il limite si vede comunque come una variazione rispetto al riferimento, ed è così che ti accorgi che il prompt sta crescendo prima che superi la soglia.

## Quando il giudice è lo strumento giusto

Ci sono domande a cui niente di meccanico può rispondere:

- *Questa risposta è cortese?* — non esiste una regex per il tono.
- *Risponde alla domanda che è stata posta?* — richiede di capire entrambe.
- *Ogni affermazione in questo riassunto è supportata dalla fonte?* — la domanda centrale di qualunque sistema di retrieval.
- *Questa riscrittura è migliore dell'originale?* — una preferenza, non una regola.

Per queste, un check giudicato è l'unica opzione, e ne esistono due forme. Una **rubrica** — descrivi il criterio in una frase, il giudice restituisce un punteggio in [0, 1] e una motivazione. E la **fedeltà** — il giudice conta le affermazioni nell'output e quante ne supporta il contesto fornito; il check fa la divisione. La seconda è quella adatta a tutto ciò che recupera documenti, ed è più utile di una rubrica perché produce un conteggio su cui si può discutere, non un'impressione.

Qualunque tu usi, tre regole, che nascono tutte dallo stesso fatto — il giudice è una distribuzione:

1. **Soglia e tolleranza sono obbligatorie**, non valori predefiniti. Un check giudicato con un implicito «passa qualsiasi cosa sopra 0» resta verde per sempre e non dice nulla. Imposta la soglia dove il sistema si trova in modo misurabile; imposta la tolleranza a partire dal rumore misurato (il capitolo 5 spiega come).
2. **Campiona.** Un giudizio per caso è una sola estrazione. Chiedi tre o cinque volte e combina — altrimenti passerai il mese successivo a inseguire regressioni che sono solo il giudice che cambia idea.
3. **Tieni il prompt del giudice fisso quanto quello del tuo sistema.** È un prompt. Va alla deriva per gli stessi motivi. Deve stare in un file, essere versionato e venire registrato a ogni run, esattamente come il prompt sotto test.

## Il giudice è tuo

Una cosa vale la pena dirla chiaramente, perché su questo gli strumenti differiscono: il giudice è una funzione che fornisci tu. Chiama il modello che vuoi, nel modo che vuoi, e lo strumento di valutazione si limita a comporre la domanda e a leggere il punteggio. Due conseguenze. Nei test, inietti un giudice finto e ogni check giudicato diventa deterministico. E il ragionamento del giudice, che cita l'output giudicato, viene scritto nel run, accanto all'output. L'unica chiamata a cui prende parte è quella del giudice stesso, verso il modello che hai scelto; lo strumento non ha un server proprio a cui inviarla. Il capitolo 8 parla di quando nemmeno quel run deve spostarsi.

## Mettere insieme una suite

Per una prima suite, lo schema che ha retto:

- **Un check strutturale** sulla forma dell'output. Intercetta i fallimenti imbarazzanti e non costa nulla.
- **Uno o due check sul contenuto** — un `Contains` per la frase obbligatoria, un `NotContains` per quella vietata, `PiiAbsent` se l'output arriva a una persona.
- **I budget**, sempre, graduati.
- **Al massimo un check giudicato**, campionato, per ciò che ha davvero bisogno di un giudizio. Se ti accorgi di volerne tre, chiediti se due di questi non potrebbero essere invece casi con una risposta nota.

Cinque o sei check su venti casi. Gira in pochi minuti, costa centesimi, ed è già più di quello che ha la stragrande maggioranza delle funzionalità LLM in produzione.

## Da fare oggi

1. Elenca gli ultimi cinque fallimenti prodotti dalla tua funzionalità. Per ciascuno, chiediti: *una regex, uno schema o un contatore avrebbero potuto intercettarlo?* La maggior parte delle volte la risposta è sì.
2. Scrivili prima come check deterministici. Eseguili sui tuoi venti casi. Alcuni falliranno già oggi — è proprio questo il punto.
3. Solo allora scrivi l'unico check giudicato per la domanda che ha davvero bisogno di un modello. Dagli una soglia e una tolleranza. Campionalo.
4. Se un check giudicato fallisce su un caso, guarda la motivazione prima di guardare il prompt. Spesso è il caso a essere sbagliato, non il sistema.

Il prossimo capitolo parla di quell'unico check giudicato: quanto oscilla, come misurare l'oscillazione, e come evitare che trasformi ogni martedì in un falso allarme.
