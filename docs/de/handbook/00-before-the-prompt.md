---
seo_title: 'Vor dem Prompt: ein Feature bauen, das sich messen lässt'
lang: de
translation_of: handbook/00-before-the-prompt.md
description: 'Vier Entscheidungen kommen vor dem Prompt und entscheiden, ob ein LLM-Feature überhaupt evaluiert werden kann: die Entscheidung als Struktur ausgeben, die Eingabe deterministisch machen, jeden Aufruf aufzeichnen und einen Fehlschlag als Fehlschlag speichern.'
search:
  exclude: true
source: handbook/00-before-the-prompt.md
source_sha: a25e3595ba15
source_commit: 49fbb1a
model: claude-opus-5
---

# 0. Vor dem Prompt

Der Prompt ist die Mitte der Arbeit, nicht ihr Anfang. Vier Entscheidungen kommen vorher, jede einzelne billig an dem Nachmittag, an dem du sie triffst, und kaum noch zu korrigieren, sobald das Feature in Produktion ist – und zusammen entscheiden sie, ob überhaupt etwas anderes aus diesem Handbuch möglich ist.

## Warum die Reihenfolge verkehrt ausfällt

Die übliche Reihenfolge lautet: Prompt schreiben, ausliefern und sich um den Rest kümmern, wenn sich jemand beschwert. Das sieht aus, als würde man mit dem schwierigen Teil anfangen. Tatsächlich fängt man mit dem einzigen weichen Teil an: Der Prompt bleibt billig zu ändern, alles um ihn herum härtet aus. Die Form der Antwort wird zum Vertrag, gegen den Renderer, Client und gespeicherte Zeilen geschrieben werden, und die schon geschriebenen Zeilen sind die Zeilen, die du hast. Die Aufmerksamkeit richtet sich also auf den Teil, der in einem Jahr noch billig sein wird, und überspringt die vier, die es nicht sein werden.

Was folgt, ist die übliche Form eines LLM-Features in Produktion, abgelesen am Code eines Systems und nicht daran gemessen: Code stellt einen Kontext zusammen, ein Modellaufruf entscheidet, was gesagt wird, zurück kommt Prosa. [Kapitel 3](../../handbook/03-ground-truth.md) nimmt dieses System vom anderen Ende her auseinander und fragt, woher seine Ground Truth kommen könnte. Dies ist die Liste der Entscheidungen, die ihm eine verschafft hätten. Nichts hier ist eine Zahl – nichts wurde ausgeführt.

Diese Lektüre war eben nur eine Lektüre, und es gibt kein Artefakt dahinter: keine datierte Notiz, kein gesichertes Repository, nichts zum Zitieren. Die Form oben ist das, was beim Betrachten eines Systems verstanden und hinterher aus dem Gedächtnis aufgeschrieben wurde, und wer nach dem Dokument sucht, aus dem sie stammt, wird keines finden. Sie wird als wiederkehrende Form angeboten, nicht als Beleg – jede Behauptung in diesem Kapitel steht und fällt damit, ob du sie in deinem eigenen System wiedererkennst, denn sonst trägt sie nichts.

## 1. Gib die Entscheidung aus, nicht nur die Prosa

Wenn das Feature auswählt – welche Einträge es nennt, welche es weglässt, in welcher Reihenfolge –, dann ist diese Auswahl das Verhalten, das du messen willst, und die Prosa ist eine Darstellung davon. Ein System, das die gewählten ids in ihrer Reihenfolge neben dem geschriebenen Satz zurückgibt, lässt sich maschinell prüfen und gibt dem Urteil eines Menschen etwas, worauf es zeigen kann. Eines, das nur den Satz zurückgibt, nicht – egal, was du später anbaust: Jeder check, den du schreibst, liest Prosa, und jede Diskussion darüber, ob die Auswahl richtig war, auch.

Heute ist es ein Feld in der Antwort und ein Parse-Schritt. Später ist es der Vertrag zwischen dem Modell und allem, was danach kommt, und ein Vertrag ist die teure Art von Änderung.

**Wo es hakt:** Nicht jedes Feature wählt aus. Wenn das Produkt die Prosa selbst ist – eine Umformulierung, eine Übersetzung, eine Antwort in einem Gespräch –, gibt es keine Auswahl, die ausgegeben werden könnte, und es bleiben nur die Entscheidungen 3 und 4. Die meisten Features sind das nicht: Sie wählen aus, sortieren, leiten weiter oder extrahieren – und nennen das Ergebnis eine Zusammenfassung.

## 2. Mach die Eingabe deterministisch

Gleiche gespeicherte Daten hinein, gleicher zusammengestellter Kontext heraus. Eine Abfrage, die ohne Sortierung die ersten N Zeilen nimmt, überlässt diese Auswahl der Datenbank, und zwei runs auf unveränderten Daten können sich unterscheiden, ohne dass das Modell seine Meinung geändert hat.

Der offensichtliche Preis: Es gibt nichts einzufrieren, also gibt es keinen Fall. Länger weh tut die Zuordnung: Jeder Unterschied zwischen zwei runs hat zwei mögliche Urheber und keine Möglichkeit, sie auseinanderzuhalten – und ein roter run, den niemand zuordnen kann, ist der Weg, auf dem ein Team lernt, Rot nicht mehr zu lesen.

Heute ist es eine Sortierung in einer Abfrage. Später ist es das, plus jeder run, der vor der Korrektur aufgezeichnet wurde – auf einer Eingabe, die niemand reproduzieren kann.

## 3. Zeichne den Aufruf vom ersten Tag an auf

Die zusammengestellte Eingabe, so wie das Modell sie erhalten hat, die Antwort, so wie sie zurückkam, welches Modell geantwortet hat, und wann. Vier Felder.

Das ist der eine Punkt, der an dem Tag, an dem du ihn schreibst, nichts bringt: Kein Feature liest ihn, kein Bildschirm zeigt ihn, und im Review wird er als Erstes hinterfragt. Er ist auch der einzige, der sich später um keinen Preis nachrüsten lässt. Die anderen sind teuer nachzurüsten; dieser lässt sich gar nicht nachrüsten, weil das, was er festgehalten hätte, weg ist.

**Wo es hakt:** Er ist nicht kostenlos, und ein Kapitel, das etwas anderes behauptete, wäre falsch. Die zusammengestellte Eingabe besteht aus den Daten, die hineingegangen sind; die Aufzeichnung erbt sie also, und mit ihr die Regeln dazu, wo sie liegen darf ([Kapitel 8](../../handbook/08-for-teams-building-for-others.md)): gleicher Perimeter, gleiche Aufbewahrung. Und nimm *welches Modell geantwortet hat* aus der Antwort, nicht aus dem, was du angefordert hast – an dem Tag, an dem ein Anbieter einen Alias umlenkt, sind das zwei verschiedene Tatsachen.

## 4. Lass einen Fehlschlag anders aussehen als eine leere Antwort

Ein Aufruf, der fehlgeschlagen ist, und ein Aufruf, der wirklich nichts zu sagen hatte, sind zwei Tatsachen. Als dieselbe Zeile gespeichert werden sie zu einer, und zwar zur leisen: Ein Ausfall liest sich wie ein ruhiger Morgen.

Diese Entscheidung lässt die Aufzeichnung verrotten, die du gerade aufgebaut hast: Jede Zählung über diese Zeilen liest Schweigen als Zustimmung und bleibt falsch, solange die Zeilen aufbewahrt werden. Nachträglich lassen sie sich auch nicht auseinandersortieren, weder über das Datum noch durch Schlussfolgern – aus dem Grund, den Kapitel 3 zum Neuinterpretieren eines mehrdeutigen Labels nennt. Sie bleiben mehrdeutig.

Heute ist es ein Zustand mehr. Später ist es ein Zustand mehr – und keine Historie.

## Dann der Prompt

Jetzt schreib ihn, und achte darauf, was die vier bewirkt haben: Der Prompt ist der Teil des Features, der am billigsten zu ändern ist – und genau da hätte er von Anfang an sein sollen. Die Struktur ist der Vertrag, der Prompt ist die Art, wie er gefüllt wird, und ein besserer Prompt ist ein Diff in einer Datei, von dem nichts Nachgelagertes wissen muss.

## Die Invarianten kommen vor den Fällen

Eine Invariante ist etwas, das an jedem möglichen Tag für eine korrekte Ausgabe gilt, ganz gleich, welche Daten vorliegen. Kapitel 3 listet die auf, die diese Art von Feature hergibt: Jede gewählte id war in der Eingabe, der verlangte Eintrag erscheint, eine leere Eingabe ergibt eine leere Auswahl.

Hinzuzufügen ist, *wann* du sie schreiben kannst. Eine Invariante braucht keine Ground Truth, kein Label, keinen Fall und keinen Richter – sie ist eine Aussage über das System, nicht über eine Antwort. Sie ist der eine check, der am Tag nach dem Prompt existieren kann, bevor die Arbeit aus [Kapitel 2](../../handbook/02-cases.md) begonnen hat, und das Billigste in diesem Handbuch. Fast niemand schreibt sie.

## Die Geste, dort, wo der Mensch schon ist

Dann eine Geste, auf dem Weg, auf dem der Mensch schon unterwegs ist, mit der er widersprechen kann. Kapitel 3 behandelt, was man fragen soll, warum die naheliegende Frage zwei Dinge auf einmal erfasst und wie weit das für einen Menschen, der nicht du bist, von einer Lösung entfernt ist.

Was davor kommt, ist kleiner: Die Geste braucht ein Objekt. Ohne Entscheidung 1 gibt es nichts, woran man sie hängen kann, und ein Daumen nach unten landet auf einem Absatz – er hält fest, dass ein Morgen schlecht war, und das ist keine Tatsache über irgendeine Entscheidung des Systems. Mit der Struktur landet derselbe Klick auf einem Eintrag, an einer Position, mit einer id. Baue beides in derselben Woche, sonst sammelt die Geste ein Jahr lang das Falsche.

Erst dann die Suite.

## Auf einer Seite

```text
What has to be true before the prompt is worth writing?
├── the decision comes back as data ..... the ids it chose, in order, beside the prose
├── the input cannot move on its own .... same data in, same assembled context out
├── every call is written down .......... the input · the reply · which model · when
└── a failure is not an empty answer .... two outcomes, two rows, never one

                                     ── the prompt ──
                   the only part of this you can still change tomorrow

And then, in this order, what those four have made possible:
├── invariants .......................... true on every possible day, no model needed
├── one judgement gesture ............... where the person already is, attached to the ids
└── a suite ............................. cases, checks, a reference → chapters 1 to 8
```

## Heute umsetzen

Sieben Fragen, eine pro Schritt. Beantworte sie am Whiteboard, bevor eine Zeile des Features geschrieben ist; die rechte Spalte zeigt, wozwischen du wählst.

| Die Frage | Was es kostet, sie zu spät zu beantworten |
|---|---|
| 1. Sagt das Feature, *welche* Dinge es gewählt hat – als Daten und nicht nur in Prosa? | Es gibt nichts, worauf geprüft werden kann, und keine Geste kann auf eine Auswahl zeigen. |
| 2. Erreicht bei gleichen gespeicherten Daten derselbe Kontext das Modell? | Keine Eingabe zum Einfrieren, also kein Fall – und kein roter run, der sich zuordnen lässt. |
| 3. Werden bei jedem Aufruf die zusammengestellte Eingabe, die Antwort, das antwortende Modell und die Zeit aufgeschrieben? | Der einzige Punkt, der sich später um keinen Preis nachrüsten lässt. |
| 4. Kannst du einen fehlgeschlagenen Aufruf von einem echten „nichts zu berichten“ unterscheiden? | Ein Ausfall wird als ruhiger Morgen gespeichert, und jede Zählung über diese Zeilen liest Schweigen als Zustimmung. |
| 5. Ist der Prompt das Einzige, was sich ändern muss, wenn du eine andere Antwort willst? | Der Prompt ist nicht mehr billig: Ihn zu ändern wird zu einer Änderung an allem, was danach kommt. |
| 6. Was gilt an jedem möglichen Tag für eine korrekte Ausgabe, und lässt sich das ohne Modell prüfen? | Du fängst am teuersten Ende an, bei einem Richter, und das auf einem System, dessen Konsistenz niemand gezeigt hat. |
| 7. Wo, in dem, was ein Mensch schon tut, könnte er sagen, dass das falsch war – und woran hängt diese Geste? | Der Widerspruch kommt nie an oder kommt als Label an, das zwei Dinge bedeutet. |

Das nächste Kapitel handelt davon, was du hast, sobald das alles steht, und warum das, was in seinem Zentrum steht, wie eine Funktion aussieht und keine ist.
