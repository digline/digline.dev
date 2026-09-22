---
seo_title: Per i team che sviluppano per altri
lang: it
translation_of: handbook/08-for-teams-building-for-others.md
description: 'Una sola suite di valutazione, tre parti interessate: che cosa servono allo sviluppatore, alla società di consulenza e al cliente dagli stessi run, e la regola che non ammette eccezioni.'
search:
  exclude: true
source: handbook/08-for-teams-building-for-others.md
source_sha: 1f9246774e8e
source_commit: c51c251
model: claude-opus-5
---

# 8. Per i team che sviluppano per altri

Tutto quello che precede vale per chiunque abbia un LLM in produzione. Questo capitolo si rivolge a un gruppo più ristretto: società di consulenza, software house, chiunque costruisca e mantenga una funzionalità basata su LLM per un cliente che non sviluppa e che è proprietario dei dati su cui la funzionalità lavora. Se è il tuo caso, la stessa suite svolge altri due compiti — e uno di questi ha una regola che non ammette eccezioni.

## Tre soggetti, una sola suite

In un prodotto che sviluppi per te stesso c'è una sola parte interessata. Qui ce ne sono tre, e dagli stessi numeri vogliono cose diverse.

**Lo sviluppatore** vuole quello che descrivono i sette capitoli precedenti: casi, check, un riferimento, un confronto in CI.

**La società di consulenza** — la tua azienda — mantiene questa funzionalità per più clienti contemporaneamente. Deve poter rispondere, per ciascuno di essi, alla domanda *la release di martedì scorso ha peggiorato l'assistente del cliente A?* — e deve poterlo fare senza detenere i dati del cliente A, e senza che i numeri del cliente A si trovino mai nello stesso posto di quelli del cliente B.

**Il cliente** è proprietario dei dati e non legge codice. Ha due diritti: a un verdetto comprensibile su un sistema che non può ispezionare, e a che i suoi dati non escano dalle sue infrastrutture. E ha una domanda, che prima o poi porrà, in una riunione o in un audit:

> *Che cosa avete testato, quando, con quale versione, e chi lo ha approvato?*

Una dashboard non risponde a questo. Una dashboard mostra com'è oggi. La domanda riguarda una data, un commit, un artefatto che qualcuno possa aprire sei mesi dopo e che nel frattempo non sia cambiato. Il file di riferimento del capitolo 6 è quell'artefatto — ed è per questo che sta nel repository e non sul server di un fornitore: un file che puoi consegnare, con un hash e una data, è una prova; una schermata ospitata da qualcun altro no.

## La regola: il payload resta dov'è nato, il verdetto viaggia

Prendi un esempio inventato in uno strumento di recruiting, numeri compresi: entra il CV di un candidato, esce una classifica, e un check giudicato chiede se la classifica sia giustificata. Il run contiene ora tre tipi di cose:

- **Il verdetto**: nome del check, pass o fail, punteggio 0.81, soglia 0.70, tolleranza, costo. Numeri su come si è comportato il sistema.
- **Il payload**: il CV, il testo della classifica e la *motivazione* del giudice — che cita il CV per spiegare il punteggio.
- **L'aggregato**: precision 0.75 sull'insieme, 12 veri positivi, 4 falsi.

Alla società di consulenza servono il primo e il terzo per fare il suo lavoro. Sul secondo non ha alcun diritto, e non le serve. La regola quindi è meccanica: **un run che attraversa il confine tra il cliente e la società di consulenza viene prima oscurato** — motivazioni rimosse, metadati del payload rimossi, verdetti e numeri conservati. Non come un'opzione che qualcuno si ricorda di attivare sull'export; ma come proprietà del run stesso, verificata quando il file viene letto, così che un documento che dichiara di essere oscurato non possa contenere una motivazione.

Ne discendono tre conseguenze, e ciascuna è una decisione di progettazione che dovrai affrontare qualunque strumento tu usi:

**Il giudice viene eseguito dentro il perimetro.** La sua motivazione cita i dati. Può essere calcolata solo dove i dati possono stare. Quello che esce è il punteggio che ha prodotto, mai la frase.

**L'identificatore del caso non è payload — quindi non deve mai contenerne.** Deve attraversare il confine, perché è così che un verdetto ritrova la sua controparte nel riferimento. `order-12345-mario-rossi` come id porta il nome di un cliente nel repository della società di consulenza. Quando i casi sono generati dalla produzione, anche l'id deve essere generato — una data, un numero progressivo, un hash breve — senza alcun modo di far passare un identificatore applicativo.

**I prompt non sono automaticamente sicuri.** Un prompt è lavoro della società di consulenza, ma spesso contiene le regole di business del cliente, e quelle sono del cliente. Per impostazione predefinita tieni il prompt dentro il perimetro; lascia che sia la suite a dichiarare, in codice che passa dalla review, che i suoi prompt possono viaggiare.

## Che cosa riceve il cliente

Non il repository. Un **report**: un documento autonomo — un unico file HTML, stampabile — che risponde, in quest'ordine, alle domande *è peggiorato?*, *quali check e di quanto*, *che cosa era sotto test e che cosa è cambiato*, *quando, con quale versione, approvato da chi*. Scritto per chi non legge codice, generato dallo stesso confronto che ha visto lo sviluppatore, così che i due non possano mai discordare.

Il report viene generato dentro il perimetro del cliente, dove le motivazioni sono disponibili, e può includerle: per il cliente, la spiegazione del giudice sul perché un caso è fallito è la riga più utile della pagina. La versione oscurata dello stesso report — verdetti, niente motivazioni — è quella che la società di consulenza conserva.

Due abitudini che danno valore al report:

**Un riferimento per ogni consegna.** Quando il cliente accetta una release, quell'accettazione è una promozione. Il file di riferimento registra lo stato che ha accettato; il report successivo si confronta con quello. «È peggiorato da quando l'hai accettato» è una frase che entrambe le parti possono verificare.

**L'aggregato nel contratto.** Con casi etichettati, una suite ha un numero — precision 0.75, nell'esempio inventato qui sopra — abbastanza stabile da poter essere messo per iscritto: *il classificatore concorda con i tuoi revisori su almeno il 70% dei casi confermati.* Fissalo al livello in cui il sistema si colloca, in base alle misurazioni, al momento dell'accettazione, non dove l'una o l'altra parte vorrebbe che fosse. La soglia è l'impegno; il confronto è il modo in cui entrambe le parti lo tengono d'occhio.

## Che cosa conserva la società di consulenza

Per ogni cliente, nel repository di quel cliente o in una directory per cliente che non si possa confondere con quella di un altro: la suite, i riferimenti, i run oscurati. Mai un unico archivio in cui i verdetti del cliente A stanno accanto a quelli del cliente B — basta un refuso per scambiare gli uni con gli altri. I perimetri sono directory, e lo strumento dovrebbe rifiutarsi di confrontare o promuovere attraverso di essi, così che l'errore sia impossibile e non soltanto sconsigliato.

Tra un cliente e l'altro, la società di consulenza vede solo ciò che viaggia: quali check, quali punteggi, quali aggregati, quali prompt se la suite lo ha consentito. È abbastanza per accorgersi che un aggiornamento del modello ha peggiorato tre clienti insieme, e non contiene nulla a cui uno di loro potrebbe obiettare.

## Quando la produzione alimenta la suite

Fin qui i capitoli eseguono la suite su casi scritti da te. Il passo successivo — ed è un passo, non un salto — è eseguire gli stessi check sulle risposte che il sistema dà in produzione, dentro il perimetro del cliente, e trasformare un fallimento lì in un caso della suite.

Così si chiude il ciclo che il capitolo 2 chiedeva di fare a mano: *un fallimento visto, un caso scritto* diventa automatico. Mette anche in pratica tutte insieme le regole di questo capitolo — il verdetto viaggia verso la società di consulenza, la risposta no; il giudice viene eseguito dove stanno i dati; il caso generato ha un id generato e un input riscritto. Se imposti quelle regole adesso, sulla suite che esegui a mano, la versione automatica sono le stesse regole su una sorgente diversa. Se adesso le salti, le scoprirai la prima volta che un caso generato farà finire il CV di un candidato in una pull request.

## Da fare oggi

1. Decidi quale sarà la domanda del cliente e metti per iscritto dove sta la risposta. Se la risposta è «in una dashboard in abbonamento», non hai una risposta.
2. Segna ogni check della tua suite: la sua motivazione cita i dati? Se sì, la motivazione di quel check è payload e non può uscire dal perimetro.
3. Guarda gli id dei tuoi casi. Se qualcuno contiene un nome, un numero d'ordine, un identificatore reale — cambialo adesso, prima che il file finisca da qualche parte.
4. Metti la suite e i riferimenti di ogni cliente nel posto di quel cliente. Se oggi due clienti condividono una directory, separali oggi.
5. Alla prossima accettazione, promuovi. Consegna al cliente il report. Scrivi l'aggregato nel verbale di accettazione. Da quel momento, «è peggiorato da quando l'hai accettato?» ha una risposta che entrambi potete verificare.

---

Questo è il manuale. Se l'hai letto da cima a fondo, sai come tenere sotto controllo una funzionalità basata su LLM più della maggior parte dei team che ne rilasciano una. Lo strumento costruito attorno a questi capitoli è [digline](../../index.md); il progetto da cui viene la maggior parte dei numeri è [pubblico](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f). Nessuno dei due è necessario per iniziare — i venti casi sì.
