---
seo_title: Was du tatsächlich auslieferst
lang: de
translation_of: handbook/01-what-you-are-shipping.md
description: 'Ein Modellaufruf sieht aus wie eine Funktion und ist keine: derselbe Prompt ergibt bei zweimaligem Sampling zwei Antworten. Was dich das kostet und warum gewöhnliche Tests es nicht sehen können.'
search:
  exclude: true
source: handbook/01-what-you-are-shipping.md
source_sha: 29449261b5b7
source_commit: 356a3c8
model: claude-opus-5
---

# 1. Was du tatsächlich auslieferst

Wenn du aus der gewöhnlichen Softwareentwicklung kommst, musst du als Erstes verlernen, was eine Funktion ist.

## Eine Funktion und das, was wie eine aussieht

Seit dreißig Jahren gilt: Bei gleicher Eingabe erzeugt derselbe Code dieselbe Ausgabe. Alles in der Softwareentwicklung ruht darauf – Tests, Debugging, Code-Review, „bei mir läuft es". Über eine Funktion lässt sich nachdenken, weil sie eine feste Abbildung von Eingaben auf Ausgaben ist.

Ein Aufruf eines Sprachmodells sieht aus wie eine Funktion. Er hat eine Eingabe (den Prompt) und eine Ausgabe (die Completion). Er steht in deinem Code zwischen zwei gewöhnlichen Funktionen. Er ist keine.

Ein Sprachmodell erzeugt eine *Wahrscheinlichkeitsverteilung* über mögliche nächste Token und zieht daraus eine Stichprobe. Genau darin liegt der Sinn: Es ist der Grund, warum dasselbe Modell ein Gedicht und eine SQL-Abfrage schreiben kann. Es bedeutet aber auch, dass derselbe Prompt, zweimal geschickt, mit zwei verschiedenen Antworten zurückkommen kann – und beide sind „richtig" in dem einzigen Sinn, den das Modell kennt: Beide waren wahrscheinlich.

Du kannst die Temperatur auf null setzen und die Streuung verringern. Beseitigen kannst du sie nicht, und bei den meisten nützlichen Aufgaben willst du das auch nicht: Ein Modell bei Temperatur null ist genau in dem schlechter, wofür du es angeschafft hast.

## Was das mit deinen Intuitionen macht

**„Ich habe es ausprobiert, und es funktioniert."** Du hast es einmal ausgeführt. Du hast eine Stichprobe aus der Verteilung gezogen. Die nächste kann anders ausfallen. Im [Newsletter-Richter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f), den dieses Handbuch als durchgehendes Beispiel verwendet, ergaben dieselben einundzwanzig Artikel, zweimal mit identischem Prompt bewertet, zwanzig gleiche Urteile und ein abweichendes. Eins von einundzwanzig ist kein Fehler. So ist die Sache beschaffen.

**„Ich habe den Prompt repariert."** Du hast die Verteilung verändert. Sie liefert jetzt für die Eingabe, die du ausprobiert hast, die gewünschte Antwort. Sie liefert auch für jede andere Eingabe leicht andere Antworten, und die hast du dir nicht angesehen. Prompt-Änderungen wirken global; deine Aufmerksamkeit war lokal.

**„Nichts hat sich geändert, also funktioniert es noch."** Dein Code hat sich nicht geändert. Das Modell hinter der API schon – Anbieter aktualisieren, trainieren neu, markieren Versionen als veraltet und lassen Aliase auf andere Ziele zeigen, ohne ein Changelog, das du lesen würdest. Deine Git-Historie sagt, das System sei unverändert. Deine Nutzer sagen, es sei schlechter geworden. Beide haben recht.

**„Es liegt über dem Schwellenwert."** Ein Schwellenwert fängt ab, was *unter dem Schwellenwert* liegt. Er fängt nicht ab, was *schlechter als letzten Monat* ist. Nimm erfundene Zahlen: Ein Score, der von 0.91 auf 0.78 abdriftet, liegt immer noch über 0.7, ist immer noch grün – und für die Person, die die Antwort bekommt, dreizehn Punkte schlechter.

## Was du also tatsächlich auslieferst

Keine Funktion. Ein System, dessen Verhalten eine Verteilung ist, das von selbst driftet, das sich global ändert, wenn du es lokal bearbeitest, und von dem niemand in deinem Team mehr als eine Handvoll Stichproben gesehen hat.

Das klingt beunruhigend. Es ist beherrschbar – aber nur mit Werkzeugen, die zur Sache passen, und die Werkzeuge gewöhnlicher Software tun das nicht. `assert output == expected` ist gegenüber einer Verteilung bedeutungslos. Ein Code-Review kann eine Änderung nicht sehen, die auf der Seite des Anbieters passiert ist. Eine Demo beweist eine Stichprobe.

Zur Sache passt das, was du bei jeder anderen verrauschten Messung tun würdest: mehrere Stichproben nehmen, mit einer aufgezeichneten Referenz vergleichen und eine Änderung erst dann als echt behandeln, wenn sie größer ist als das Rauschen. Das ist keine neue Idee. So arbeitet ein Labor. Nur haben Softwareteams es nicht so gelernt, weil sich bis vor Kurzem nichts im Stack so verhalten hat.

## Die vier Dinge, die du brauchst

Alles Weitere in diesem Handbuch läuft auf vier Dinge hinaus, und die Reihenfolge ist wichtig:

1. **Fälle** – eine Menge von Eingaben, die dir wichtig sind, zusammen mit dem, was du über die richtigen Antworten weißt. Vom Prompt ferngehalten. Über die Zeit wachsend. Das ist das Kapital, und [Kapitel 2](../../handbook/02-cases.md) handelt davon; [Kapitel 3](../../handbook/03-ground-truth.md) handelt davon, woher die Antworten kommen, wenn dir niemand welche gibt.
2. **Checks** – was du an jeder Ausgabe überprüfst. Die, die kein Modell brauchen, kommen zuerst; die, die einen Richter brauchen, kommen zuletzt, denn ein Richter ist eine weitere Verteilung. [Kapitel 4](../../handbook/04-checks.md), [Kapitel 5](../../handbook/05-the-judge.md).
3. **Eine Referenz** – ein run, den du dir angesehen und freigegeben hast, aufgezeichnet zusammen mit dem Prompt und dem Commit, der ihn erzeugt hat, damit jeder künftige run etwas hat, womit er verglichen werden kann. [Kapitel 6](../../handbook/06-the-reference.md).
4. **Eine Routine** – wann ausgeführt wird, was einen genaueren Blick auslöst, was zu tun ist, wenn der Vergleich rot wird. [Kapitel 7](../../handbook/07-maintenance.md).

Wenn du Software für andere baust, gibt es einen fünften Punkt – was du dem Kunden zeigen kannst und was seinen Perimeter niemals verlassen darf – in [Kapitel 8](../../handbook/08-for-teams-building-for-others.md).

## Eine Gewohnheit, bevor du weiterliest

Öffne das Projekt, in dem du einen LLM-Aufruf hast. Suche die Eingabe, mit der du ihn beim Bauen getestet hast. Schick sie noch einmal, jetzt, fünfmal.

Wenn alle fünf Antworten gleich sind: gut – du hast eine rauscharme Aufgabe, und der Rest dieses Handbuchs wird dir leichtfallen. Wenn sie sich unterscheiden, hast du gerade in einer Minute am eigenen System gesehen, worum es in diesem Kapitel geht. So oder so weißt du jetzt etwas, das du vor dem Ausführen nicht wusstest – und genau darum geht es.
