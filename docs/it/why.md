---
title: Perché
template: why.html
seo_title: Perché le applicazioni LLM hanno bisogno di una baseline
lang: it
translation_of: why.md
description: Un prompt non è codice, e il modello si muove sotto i tuoi piedi. Perché una soglia passa/non passa non può vedere una regressione di qualità, e che cosa misura invece una baseline approvata.
search:
  exclude: true
source: why.md
source_sha: d1952e7f33ac
source_commit: 3f60b0d
model: claude-opus-5
---

# Perché

Se hai inserito un modello linguistico in qualcosa che le persone usano, questa pagina parla di un problema che hai già. Forse non te ne sei ancora accorto. Questo è il problema.

Gli esempi che seguono vengono da un progetto reale e pubblico: un piccolo programma che ogni mattina legge alcune newsletter sull'IA e chiede a un modello quali articoli meritino venti minuti del tempo di una persona. È semplice quanto può esserlo un'applicazione LLM. Tutto quello che c'è in questa pagina è capitato a quel progetto.

## Un prompt non è codice

Quando modifichi una riga di codice, lo stesso input produce lo stesso output, ogni volta. È questo che rende possibili i test: scrivi quale risultato deve uscire e la macchina ti dice se è uscito.

Un prompt non funziona così. Fai la stessa domanda allo stesso modello cinque volte, stesso prompt, stesso articolo, e non risponde sempre nello stesso modo. Ogni run del giudice delle newsletter interroga ciascuno dei ventuno articoli cinque volte. Da due a sei di essi, a seconda del run, ricevono cinque risposte che non concordano tra loro. Tra quelle cinque non è cambiato niente: né il codice, né il modello, né l'input. Il modello è una distribuzione di probabilità e tu stai estraendo dei campioni.

Ma significa che il riflesso abituale — *eseguilo una volta, sembra giusto, rilascia* — non è un test. È un solo campione.

## Il modello cambia sotto i tuoi piedi

Anche se non tocchi una riga, ciò su cui hai costruito si muove.

I fornitori aggiornano i modelli. Dichiarano deprecate alcune versioni. Cambiano ciò a cui punta un alias predefinito. Un modello chiamato `latest` a marzo non è lo stesso modello a giugno, e niente nel tuo repository registra che è cambiato. La cronologia dei commit dice «nessuna modifica dal rilascio»; gli utenti dicono «la settimana scorsa è peggiorato»; entrambi dicono la verità.

È il guasto che nessuna revisione del codice può rilevare, perché non c'è nessun diff. Il solo modo di vederlo è avere un termine di confronto — la registrazione di come il sistema si è comportato su un insieme di input, in una data, con una certa versione — e rieseguire gli stessi input per guardare la differenza.

## «Funziona» non è una misura

La maggior parte dei team ha una soglia da qualche parte: un punteggio sotto 0.7 non passa, sopra passa. È meglio di niente, e non rileva il problema che conta di più.

Ecco come si presenta, con numeri inventati. Un check ottiene 0.91 il giorno del rilascio. Tre settimane e due ritocchi al prompt dopo, ottiene 0.78. Sempre sopra 0.7. Sempre verde. Supera ancora tutti i test che hai. E gli utenti hanno già iniziato a percepirlo, perché un calo di tredici punti, per chi sta dall'altra parte, è un prodotto diverso.

Una soglia rileva *ciò che è sotto soglia*. Non rileva *ciò che è peggiore di prima*. Per questo serve un riferimento — lo stato approvato, registrato — e un confronto con quello a ogni modifica. Il riferimento è il pezzo che manca a quasi tutti i team, ed è la ragione per cui lo slittamento da 0.91 a 0.78 resta per loro invisibile finché non lo segnala un cliente.

## Chi giudica il giudice

Per tutto ciò che non si può verificare con una corrispondenza esatta — questa risposta è cortese, rispetta le policy, riassume in modo fedele — lo strumento pratico è un altro modello nel ruolo di giudice. Funziona. Ed eredita tutti i problemi visti sopra: anche il giudice estrae campioni, e cambia idea.

Nel progetto delle newsletter il giudice vota cinque volte per articolo e decide la maggioranza. Due run a quindici minuti di distanza, stesso prompt: su un articolo su ventuno la maggioranza si è ribaltata, da due voti su cinque a cinque su cinque. E gli articoli su cui i voti si dividono non sono gli stessi in ogni run: nei sei run pubblicati, undici dei ventuno si sono divisi almeno una volta, uno di essi in cinque run, quattro di essi una sola volta. Dieci non si sono divisi mai. Quegli undici sono i casi limite, e una maggioranza di cinque voti è una base fragile su cui appoggiare una decisione.

Non è un'esperienza solo mia. Dan Luu ha fatto rivalutare dieci volte in più gli stessi output di Senior SWE-Bench e il verdetto sul buon gusto ha discordato da quello ufficiale nel 23% dei casi, a input identico ([exercise 7](https://danluu.com/exercise-7/)). Ho applicato la stessa lettura ai miei giudici: [Valutazioni sbagliate, le mie](../blog/bad-evals-my-own.md). Il giudice è uno strumento. Uno strumento si calibra.

Ne seguono due conseguenze. Primo: non puoi sapere se il tuo *sistema* è peggiorato finché non sai quanto oscilla da solo il tuo *giudice* — il noise floor va misurato prima di ogni altra cosa. Secondo: un singolo caso è una cattiva unità su cui decidere. Tra quei due run il dato aggregato si è spostato di un articolo su ventuno, mentre l'articolo stesso si è spostato di tre voti su cinque. I singoli casi servono per la diagnosi. È sul dato aggregato che puoi mettere una soglia.

## La domanda del cliente

Se sviluppi funzionalità LLM per un prodotto tuo, tutto quanto sopra è un problema di qualità. Se le sviluppi per qualcun altro — un committente, un cliente, un'azienda soggetta a regolamentazione — è anche un problema contrattuale, e la domanda arriva in una forma precisa:

*Che cosa hai testato, quando, con quale versione, e chi l'ha approvato?*

Una dashboard non risponde. Una dashboard mostra il presente. La domanda riguarda una data, un commit, un artefatto che qualcuno possa aprire sei mesi dopo. La risposta deve essere un file: questa suite, questo riferimento, questo confronto, questa approvazione — nel repository, accanto al codice che descrive, con il testo del prompt che l'ha prodotta. Se sta sul server di un fornitore, non puoi mostrarlo tu; se sta solo nella memoria di qualcuno, non esiste.

Per il cliente, quello stesso file è la prova che ciò che ha pagato fa ancora quello che faceva il giorno in cui l'ha accettato. Per lui vale più di qualsiasi metrica.

## Che cosa significa «sotto controllo»

Mettendo insieme i pezzi, «sotto controllo» si riduce a tre cose concrete, nessuna delle quali costosa:

**Un riferimento.** Un run della tua suite che hai guardato e approvato — punteggi, testo del prompt, commit — registrato come file e committato. Non il primo run verde: la mediana di alcuni, perché ormai sai che il giudice oscilla.

**Un confronto a ogni modifica.** Cambia il prompt, il modello, il recupero dei documenti, qualsiasi cosa: esegui di nuovo la suite e confronta con il riferimento. Non «è sotto la soglia» ma «è peggiore di prima, dove, di quanto» — con il diff del prompt accanto ai punteggi che ha spostato. In CI, così avviene indipendentemente dal fatto che te ne ricordi; a intervalli programmati, così avviene quando è il fornitore a cambiare qualcosa e non tu.

**Uno storico.** Tutti i riferimenti che hai approvato, in git, con le motivazioni. Quando qualcuno fa la domanda del cliente, la risposta è un `git log`.

Nel progetto delle newsletter un run costa circa sette centesimi: ventuno articoli, giudicati cinque volte ciascuno. Il progetto ha un numero da dichiarare, con i run a sostenerlo: il giudice concorda con il lettore su 16 articoli su 21 in quattro dei sei run pubblicati, e su 15 e 14 negli altri due.

È questo che fa [digline](../index.md), ed è tutto ciò che fa. Il riferimento sta nel tuo repository. L'unica chiamata che esce è quella che la tua suite fa al tuo modello — digline non ha server, né account, né telemetria. `pip install digline` per provarlo; il progetto delle newsletter è [pubblico](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) se prima vuoi vedere un caso reale.

Da dove vengono questi numeri: sei run del giudice delle newsletter, committati come [fixtures](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures), [con una nota su quale numero viene da quale run](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/README.md), e [uno script](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/recompute.py) che da essi ricalcola ogni numero di questa pagina.

---

Se hai trenta minuti invece di cinque: il [Manuale](../handbook/01-what-you-are-shipping.md).

Ti chiedi in cosa si distingue dagli strumenti che già conosci? Vedi [Come si colloca digline](../comparison/index.md).
