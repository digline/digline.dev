---
title: Warum
template: why.html
seo_title: Warum LLM-Anwendungen eine baseline brauchen
lang: de
translation_of: why.md
description: Ein Prompt ist kein Code, und das Modell verändert sich unter dir. Warum eine Pass/Fail-Schwelle eine Qualitätsregression nicht erkennen kann und was eine freigegebene baseline stattdessen misst.
search:
  exclude: true
source: why.md
source_sha: 5ff0a8d6fc10
source_commit: 6bb2652
model: claude-opus-5
---

# Warum

Wenn du ein Sprachmodell in etwas eingebaut hast, das Menschen benutzen, dann geht es auf dieser Seite um ein Problem, das du schon hast. Vielleicht ist es dir noch nicht aufgefallen. Genau das ist das Problem.

Die Beispiele unten stammen aus einem echten, öffentlichen Projekt: einem kleinen Programm, das jeden Morgen einige KI-Newsletter liest und ein Modell fragt, welche Artikel zwanzig Minuten Lesezeit eines Menschen wert sind. Einfacher wird eine LLM-Anwendung kaum. Alles auf dieser Seite ist in diesem Projekt passiert.

## Ein Prompt ist kein Code

Wenn du eine Zeile Code änderst, erzeugt dieselbe Eingabe jedes Mal dieselbe Ausgabe. Das macht Tests überhaupt möglich: Du schreibst auf, was herauskommen soll, und die Maschine sagt dir, ob es so war.

Ein Prompt funktioniert nicht so. Stell demselben Modell fünfmal dieselbe Frage, gleicher Prompt, gleicher Artikel, und die Antwort fällt nicht immer gleich aus. Jeder run des Newsletter-Judge fragt zu jedem der einundzwanzig Artikel fünfmal. Bei zwei bis sechs davon, je nach run, widersprechen sich die fünf Antworten. Zwischen diesen fünf hat sich nichts geändert: nicht der Code, nicht das Modell, nicht die Eingabe. Das Modell ist eine Wahrscheinlichkeitsverteilung, und du ziehst Stichproben daraus.

Aber es bedeutet: Der übliche Reflex — *einmal ausführen, sieht richtig aus, ausliefern* — ist kein Test. Es ist eine einzige Stichprobe.

## Das Modell verändert sich unter deinen Händen

Selbst wenn du keine Zeile anfasst, bewegt sich die Grundlage, auf der du gebaut hast.

Anbieter aktualisieren Modelle. Sie markieren Versionen als veraltet. Sie ändern, worauf ein Standard-Alias zeigt. Ein Modell, das im März `latest` heißt, ist im Juni nicht dasselbe Modell, und nichts in deinem Repository hält fest, dass es sich geändert hat. Deine Commit-Historie sagt „seit dem Release keine Änderungen“; deine Nutzer sagen „letzte Woche ist es schlechter geworden“; beide haben recht.

Das ist der Fehlerfall, den kein Code-Review finden kann, weil es keinen Diff gibt. Sichtbar wird er nur, wenn es etwas zum Vergleichen gibt — eine Aufzeichnung, wie sich das System auf einer Menge von Eingaben verhalten hat, an einem Datum, unter einer Version — und wenn man dieselben Eingaben erneut laufen lässt und sich den Unterschied ansieht.

## „Es funktioniert“ ist keine Messung

Die meisten Teams haben irgendwo eine Schwelle: ein Score unter 0.7 fällt durch, darüber besteht er. Das ist besser als nichts, und es übersieht genau den Fehlerfall, der am meisten zählt.

So sieht das aus, mit erfundenen Zahlen: Ein check erreicht am Tag der Auslieferung 0.91. Drei Wochen und zwei kleine Prompt-Änderungen später sind es 0.78. Immer noch über 0.7. Immer noch grün. Besteht weiterhin jeden Test, den du hast. Und die Nutzer spüren es schon, denn ein Rückgang um dreizehn Punkte ist für die Person am anderen Ende ein anderes Produkt.

Eine Schwelle erkennt, was *unter dem Schwellenwert* liegt. Sie erkennt nicht, was *schlechter ist als vorher*. Dafür brauchst du eine Referenz — den freigegebenen Zustand, festgehalten — und bei jeder Änderung einen Vergleich damit. Die Referenz ist der Baustein, der fast jedem Team fehlt, und deshalb bleibt die Verschiebung von 0.91 auf 0.78 für diese Teams unsichtbar, bis ein Kunde sie benennt.

## Wer beurteilt den Judge

Für alles, was sich nicht durch exakten Vergleich prüfen lässt — ist diese Antwort höflich, hält sie sich an die Vorgaben, fasst sie treu zusammen —, ist ein weiteres Modell als Judge das praktikable Werkzeug. Das funktioniert. Es erbt aber auch jedes der Probleme von oben: Auch der Judge zieht Stichproben, und er ändert seine Meinung.

Im Newsletter-Projekt stimmt der Judge pro Artikel fünfmal ab, und die Mehrheit entscheidet. Zwei runs im Abstand von vier Tagen, gleicher Prompt: Bei einem von einundzwanzig Artikeln kippte die Mehrheit, von zwei Stimmen von fünf auf fünf von fünf. Und es sind nicht in jedem run dieselben Artikel, bei denen die Stimmen auseinandergehen: Über die sechs veröffentlichten runs hinweg gingen elf der einundzwanzig mindestens einmal auseinander, einer davon in fünf runs, vier davon nur einmal. Zehn nie. Diese elf sind die Grenzfälle, und eine Mehrheit aus fünf Stimmen ist eine dünne Grundlage für eine Entscheidung.

Das ist nicht nur meine Erfahrung. Dan Luu ließ dieselben Senior-SWE-Bench-Ausgaben zehn weitere Male bewerten, und das Geschmacksurteil wich bei identischer Eingabe in 23% der Fälle vom offiziellen ab ([exercise 7](https://danluu.com/exercise-7/)). Ich habe dieselbe Lesart auf meine eigenen Judges angewandt: [Schlechte Evals, meine eigenen](../blog/bad-evals-my-own.md). Der Judge ist ein Messinstrument. Ein Messinstrument wird kalibriert.

Daraus folgen zwei Dinge. Erstens: Du kannst nicht wissen, ob dein *System* schlechter geworden ist, solange du nicht weißt, wie stark dein *Judge* von sich aus schwankt — der noise floor muss vor allem anderen gemessen werden. Zweitens: Ein einzelner Fall ist eine schlechte Entscheidungsgrundlage. Zwischen diesen beiden runs verschob sich der Gesamtwert um einen von einundzwanzig Artikeln, während der Artikel selbst um drei von fünf Stimmen wanderte. Einzelne Fälle dienen der Diagnose. Eine Schwelle kann man auf den Gesamtwert legen.

## Die Frage des Kunden

Wenn du LLM-Funktionen für dein eigenes Produkt baust, ist alles oben ein Qualitätsproblem. Baust du sie für andere — einen Auftraggeber, einen Kunden, ein reguliertes Unternehmen —, ist es auch ein vertragliches, und die Frage kommt in einer bestimmten Form:

*Was hast du getestet, wann, unter welcher Version, und wer hat es freigegeben?*

Ein Dashboard antwortet darauf nicht. Ein Dashboard zeigt heute. Die Frage betrifft ein Datum, einen Commit, ein Artefakt, das jemand ein halbes Jahr später öffnen kann. Die Antwort muss eine Datei sein: diese Suite, diese Referenz, dieser Vergleich, diese Freigabe — im Repository, neben dem Code, den sie beschreibt, mit dem Prompt-Text, der sie erzeugt hat. Liegt sie auf dem Server eines Anbieters, kannst du sie nicht vorzeigen; liegt sie nur in jemandes Erinnerung, existiert sie nicht.

Für den Kunden ist dieselbe Datei der Beleg, dass das, wofür er bezahlt hat, noch das tut, was es am Tag der Abnahme getan hat. Das ist ihm mehr wert als jede Metrik.

## Was „unter Kontrolle“ bedeutet

Setzt man die Teile zusammen, sind „unter Kontrolle“ drei konkrete Dinge, keines davon teuer:

**Eine Referenz.** Ein run deiner Suite, den du angesehen und freigegeben hast — Scores, Prompt-Text, Commit —, als Datei festgehalten und eingecheckt. Nicht der erste grüne run: der Median aus mehreren, denn du weißt jetzt, dass der Judge schwankt.

**Ein Vergleich bei jeder Änderung.** Ändere den Prompt, das Modell, das Retrieval, irgendetwas: Lass die Suite erneut laufen und vergleiche mit der Referenz. Nicht „liegt es unter der Schwelle“, sondern „ist es schlechter als vorher, wo, und um wie viel“ — mit dem Diff des Prompts direkt neben den Scores, die er verändert hat. In CI, damit es passiert, ob du daran denkst oder nicht; nach Zeitplan, damit es auch passiert, wenn der Anbieter etwas geändert hat und du nicht.

**Eine Historie.** Jede Referenz, die du je freigegeben hast, in git, mit den Begründungen. Wenn jemand die Frage des Kunden stellt, ist die Antwort ein `git log`.

Im Newsletter-Projekt kostet ein run etwa sieben Cent: einundzwanzig Artikel, jeder fünfmal bewertet. Das Projekt hat eine Zahl, die es nennen kann, und die runs, die sie belegen: Der Judge stimmt in vier der sechs veröffentlichten runs bei 16 von 21 Artikeln mit dem Leser überein, in den anderen beiden bei 15 und 14.

Genau das macht [digline](../index.md), und mehr macht es nicht. Die Referenz liegt in deinem Repository. Nichts verlässt deinen Rechner. Zum Ausprobieren: `pip install digline`; das Newsletter-Projekt ist [öffentlich](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f), wenn du es erst einmal in der Praxis sehen willst.

Woher diese Zahlen stammen: sechs runs des Newsletter-Judge, eingecheckt als [fixtures](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures), [mit einer Notiz dazu, welche Zahl aus welchem run stammt](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/README.md), und [ein Skript](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/recompute.py), das jede Zahl auf dieser Seite daraus neu berechnet.

---

Wenn du dreißig Minuten statt fünf hast: das [Handbuch](../handbook/01-what-you-are-shipping.md).

Du fragst dich, wie sich das von den Werkzeugen unterscheidet, die du schon kennst? Siehe [digline im Vergleich](../comparison/index.md).
