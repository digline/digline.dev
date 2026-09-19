---
seo_title: Ground Truth, wenn dir niemand eine gibt
lang: de
translation_of: handbook/03-ground-truth.md
description: 'Woher die erwartete Antwort kommt, wenn es keine gelabelten Daten gibt: den Input einfrieren, Formen abdecken, Widerspruch erfassen und das Feature so entwerfen, dass sich ein Urteil daran festmachen lässt.'
search:
  exclude: true
source: handbook/03-ground-truth.md
source_sha: 74e7f304be5e
source_commit: d778c40
model: claude-opus-5
---

# 3. Ground Truth: wenn dir niemand eine gibt

In Kapitel 2 hieß es, die Stelle zu finden, an der ein Mensch das Modell korrigiert. Dieses Kapitel ist für den Fall, dass es diese Stelle nicht gibt — oder dass es sie gibt und sie etwas anderes aufzeichnet, als du denkst. Es beruht auf drei Systemen: dem [Newsletter-Richter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f), dessen Code und Fälle öffentlich sind, dessen Aufzeichnung jedes bewerteten Eintrags aber nicht — die Zahlen unten stammen aus dieser Aufzeichnung, so wie [Bad evals, my own](../../blog/bad-evals-my-own.md) sie zeigt; einem zweiten Richter desselben Autors, der Reddit-Threads auswählt, auf die sich eine Antwort lohnt (nicht öffentlich, im selben Beitrag beschrieben); und einem Produkt-Feature, das nur seiner Form nach beschrieben wird. Jedes davon hat auf andere Weise keine Ground Truth hervorgebracht.

## Den Input einfrieren, nicht die Welt

Ein Fall ist eine Momentaufnahme einer Situation. Dass die Daten morgen anders aussehen, spielt keine Rolle: Du testest, was das System in dieser Situation tut, nicht die Daten.

Der Input kommt deshalb vollständig in den Fall, so wie das Modell ihn an diesem Tag gesehen hat. Einen Artikel heute erneut abzurufen hieße, unter ein altes Label einen anderen Input zu legen. Das Newsletter-Projekt speichert die Zusammenfassung, die es bewertet hat — aber nur für die Einträge, die es seinem Leser gezeigt hat; 144 bewertete und nie gezeigte Einträge haben also eine Punktzahl und keinen Input. Selbst mit Label ließen sie sich nicht nachspielen.

## Formen abdecken, nicht Stichproben ziehen

Der naheliegende Weg zu Fällen ist, jeden gelabelten Datensatz zu exportieren. Der Reddit-Richter hat das am 2026-09-11 getan und 144 Fälle erhalten. 109 davon waren Threads, die der Leser ignoriert und der Richter übersprungen hat: immer wieder derselbe gewöhnliche Morgen. Accuracy auf dieser Menge lag bei 0.85. Precision für das eine Urteil, auf das es ankam, lag bei 0.52. Die Menge ließ die leichten Tage gut aussehen und sagte nichts über die schweren.

Wähle Fälle stattdessen nach ihrer Form: den überfüllten Input, den leeren, den dringenden Eintrag, der im Rauschen untergeht, das fehlende Feld, zwei Prioritäten, die sich widersprechen. Diese Liste ist kein Ergebnis. Der gewöhnliche Tag ist eine dieser Formen, und Kapitel 2 hat recht damit, dass er vorkommen muss — als Form, nicht als Bodensatz jedes einzelnen Morgens.

## Ein Label ist kein Urteil

Der Reddit-Richter hat seinen Leser jeden Morgen gefragt, was er mit jedem Thread gemacht hat: kommentiert, hochgevotet oder ignoriert. Aus `ignored` wurde in der Suite `skip`. Dann sah sich der Leser neun Threads an, die er ignoriert und der Richter mit `comment` markiert hatte, und stellte fest, dass der Richter bei mindestens fünf nach seinen eigenen Regeln recht hatte. Ignoriert worden waren sie, weil es der vierte Thread an diesem Morgen war oder weil der Leser an diesem Tag in diesem Forum schon zweimal kommentiert hatte.

`ignored` bedeutete also *der Richter lag falsch* und *keine Zeit*, und jeder darauf aufgebaute Fall war die Deutung einer Antwort, die nie sagte, was von beidem. **Deute es nicht nachträglich um** — nicht nach Datum, nicht nach der Confidence des Richters, nicht danach, was du wohl gemeint haben musst. Das heißt, sich selbst einen Erwartungswert zu erfinden. Die alten Datensätze bleiben mehrdeutig, und aus ihnen entsteht kein neuer Fall.

Die Lösung setzt bei der Eingabe an. Welche Taste auch immer die Morgenliste abräumt, sie muss *deferred* schreiben, den Wert, der nichts behauptet, nicht *declined*. Sonst ist das mehrdeutige Label binnen eines Morgens unter neuem Namen zurück. Die negativen Labels, die vor der Korrektur geschrieben wurden, sind nicht mehr zu retten.

Diese Aufteilung beseitigt die Mehrdeutigkeit nicht, denn `declined` fragt weiterhin danach, was du *getan* hast. Ein Thread, den der Leser liegen ließ, weil er in diesem Forum schon zweimal kommentiert hatte, ist weiterhin ein `declined`, weiterhin ein negatives Label. Um das zu beseitigen, braucht es eine Frage nach der Regel — nicht *hast du kommentiert?*, sondern *hätte das ein Kommentar sein sollen?* — und keiner der beiden Richter stellt eine solche Frage.

## Der Widerspruch ist das Ereignis

Gute Ausgaben noch einmal zu lesen, lehrt dich nichts und überzeugt dich von vielem. Der einzige Moment, den zu erfassen sich lohnt, ist der, in dem ein Mensch anders geantwortet hätte als das Modell. Keiner der beiden Richter tut das bisher: Beide exportieren jedes explizite Label, Übereinstimmungen eingeschlossen.

**Das Newsletter-Projekt ist das Gegenbeispiel**, und es ist nützlicher als ein Erfolg. Seinem Leser werden die Einträge gezeigt, die der Richter mit 4 oder 5 bewertet hat, aufgefüllt auf fünf, und er wird gefragt: *welche interessieren dich? (Enter = keine)*. Die einzige explizite Antwort ist *ja*, und sie lässt sich nur zu Einträgen geben, die der Richter ohnehin ausgewählt hat. Nicht gezeigte Einträge haben kein Label; 265 von 446 wurden nicht einmal bewertet. Enter ist mehrdeutig. Der eine Weg zu einem Widerspruch — einen aufgefüllten, niedrig bewerteten Eintrag zu markieren — stand bis zum 6. September sechzehnmal offen und wurde kein einziges Mal genommen. Die Methode liefert **überhaupt keinen erfassbaren Widerspruch**, nicht weil der Leser nie widersprochen hätte, sondern weil sie nie dort gefragt hat, wo er es hätte tun können.

Die Ground Truth muss ein Nebenprodukt der Arbeit sein, die die Person ohnehin tut. Beide Richter fragen am Ende eines Morgens, den der Leser ohnehin hatte; eine Frage, die ein eigener, später auszuführender Befehl ist, wird zur lästigen Pflicht. In einem Produkt ist die Person nicht du selbst, und das ist der schwierige Fall; hier ist er nicht gelöst.

## Wenn die Auswahl nie ein Datenpunkt war

Das dritte System hat die häufigste Form eines LLM-Features im Produktivbetrieb; was folgt, ist aus seinem Code gelesen, nicht gegen das System ausgeführt worden. Ein Produkt schreibt jedem Nutzer ein morgendliches Briefing. Code stellt einen Kontext zusammen und übergibt ihn an einen einzigen Modellaufruf. Das Modell entscheidet, welche Einträge es erwähnt, in welcher Reihenfolge, mit welcher Begründung und ob es überhaupt etwas sagt.

Die Antwort ist Fließtext mit Links darin. Nichts parst oder validiert sie. Ein Eintrag ist nur dann identifizierbar, wenn das Modell ihn zufällig in einen Link mit einer id gepackt hat, und nichts prüft, ob es die id im Input überhaupt gibt.

Bei den beiden Richtern waren die Labels mehrdeutig. Hier **existiert die Auswahl nur innerhalb des Fließtexts**. Es gibt nichts, worauf sich eine Zusicherung beziehen könnte, und nichts, woran sich das Urteil eines Nutzers festmachen ließe: Ein Feedback-Button hätte kein Objekt, auf das er zeigen könnte. Zwei ganz gewöhnliche Dinge verschlimmern das. Ein fehlgeschlagener Modellaufruf und ein echtes „nichts zu berichten“ speichern dieselbe Zeile — ein Fehlen, als Antwort verkleidet. Und einige der Abfragen, die den Kontext aufbauen, nehmen N Zeilen ohne Sortierung; welche Einträge beim Modell ankommen, entscheidet damit die Datenbank: Ein run auf denselben Daten kann anders ausfallen als der nächste, ohne dass das Modell seine Meinung ändert, und es gibt keinen Input zum Einfrieren.

Das Feature funktioniert, und nichts davon fällt im Review auf. Es lässt sich nur eben nicht evaluieren. **Ob sich deine Ground Truth erheben lässt, entscheidet sich, wenn du das Feature schreibst**, nicht danach. Ein System, das seine Entscheidung als Struktur ausgibt — die gewählten Einträge, in ihrer Reihenfolge, mit ihren ids — lässt sich deterministisch prüfen und kann das Urteil eines Menschen tragen. Eines, das nur Fließtext ausgibt, kann das nicht, egal was du später noch anbaust.

Die Lösung ist eine Form: erst die Auswahl ausgeben; ihre ids gegen den Input validieren; einen Fehlschlag als Fehlschlag speichern; den Fließtext zu einer Darstellung der Auswahl machen.

## Was sich dann zusichern lässt

Liegt die Auswahl als Daten vor, ist das meiste, worauf es ankommt, über jeden denkbaren Tag hinweg stabil und braucht kein Modell: Jede id steht im Input, also ist nichts erfunden und nichts stammt aus den Daten eines anderen Nutzers; der Eintrag, der erscheinen muss, erscheint; ein leerer Input ergibt eine leere Auswahl. Nur die Reihenfolge — steht das Dringende an erster Stelle? — braucht einen Richter. Nichts davon ist bisher gegen dieses System ausgeführt worden; es ist das, was die Struktur möglich macht.

## Wachstum und die ehrliche Grenze

Beginne mit einigen wenigen ausgewählten Formen. Lass jeden Fehler im Produktivbetrieb zu einem Fall werden und lösche nie einen: Ein Fall, der einen Defekt aufgedeckt hat, ist eine tragende Wand, und sie zu entfernen ist der einzige Weg herauszufinden, was sie gehalten hat. Der Exporter des Newsletter-Projekts macht das Gegenteil: Er erzeugt seine Datei jedes Mal komplett neu.

Zwanzig Fälle sagen dir nicht, dass das System korrekt ist. Sie sagen dir, dass es sich bei zwanzig Situationen, die jemand für repräsentativ hielt, nicht verschlechtert hat. Ein gate gegen Regressionen, kein Beweis.

## Heute umsetzen

1. Finde heraus, wo die Entscheidung deines Features steckt. Steckt sie nur im Fließtext, ändere die Ausgabe, bevor du einen einzigen Fall schreibst. Kannst du sie noch nicht ändern, kannst du das Feature nicht evaluieren. Das ist für sich genommen ein Befund, und was heute zu tun ist: den zusammengestellten Input und die Antwort aufzeichnen, denn morgen sind sie weg.
2. Prüfe, ob deine Inputs deterministisch sind. Eine Abfrage, die ohne Sortierung abschneidet, ist der erste Bug.
3. Sieh dir die Antwort an, die deine Nutzer geben, indem sie nichts tun. Sorge dafür, dass sie nichts behauptet.
4. Frage nach der Regel, nicht nach dem Verhalten, und nur dort, wo die Person anders geantwortet hätte.
5. Wähle fünf Formen. Schreibe für jede einen Fall.

Im nächsten Kapitel geht es darum, was an diesen Fällen zu prüfen ist — und warum jeder check, der gar kein Modell braucht, zuerst kommt.
