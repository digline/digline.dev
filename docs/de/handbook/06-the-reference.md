---
seo_title: 'Die Referenz: Ein Schwellenwert ist keine Referenz'
lang: de
translation_of: handbook/06-the-reference.md
description: Ein Score kann weit fallen und liegt an beiden Tagen trotzdem über seinem Schwellenwert. Bemerkt wird das nur durch die eine Zahl, die du aufschreibst und an der du dich messen lässt.
search:
  exclude: true
source: handbook/06-the-reference.md
source_sha: c46f6b87214f
source_commit: 356a3c8
model: claude-opus-5
---

# 6. Die Referenz

Alles bisher Beschriebene liefert Zahlen. In diesem Kapitel geht es um die eine Zahl, die mehr zählt als die anderen: die, die du aufschreibst und an der du dich messen lässt.

## Ein Schwellenwert ist keine Referenz

Die meisten Teams, die ein LLM-Feature überhaupt testen, haben einen Schwellenwert: Der Score muss über 0.7 liegen. Er beantwortet eine Frage — *ist das akzeptabel?* — und ist blind für die andere — *ist es noch das, was es war?*

Hier mit erfundenen Zahlen. Ein Feature, das beim Release 0.91 erreichte und heute 0.78 erreicht, liegt an beiden Tagen über dem Schwellenwert. Nichts wird rot. Trotzdem hat sich etwas um dreizehn Punkte verändert, und wer das Feature benutzt, hat die Veränderung vor jedem Test bemerkt. Um das zu sehen, musst du die 0.91 aufgeschrieben haben. Das ist die Referenz: ein run deiner Suite, den du dir angesehen, für richtig befunden und festgehalten hast — Scores, der Prompt, der sie erzeugt hat, der Commit, das Datum —, damit jeder spätere run damit verglichen werden kann statt mit einer Linie.

Der Schwellenwert sagt, wo der Boden ist. Die Referenz sagt, wo du gestanden hast. Du brauchst beides, und das Zweite führt fast niemand.

## Was eine Referenz enthält

Eine Datei, im Repository, neben dem Code. Im [Newsletter-Projekt](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) ist das [`.digline/alessandro/baselines/brief-judge.json`](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/.digline/alessandro/baselines/brief-judge.json), committet wie jede andere Datei. Darin:

- **Die Urteile** — jeder check zu jedem Fall, mit Score, Schwellenwert und Toleranz. Keine Zusammenfassung: die vollständige Tabelle, damit ein späterer Vergleich sagen kann, *welcher* Fall sich bewegt hat.
- **Die Aggregate**, wenn die Fälle gelabelt sind — Precision 0.667 und Accuracy 0.762, zehn von fünfzehn und sechzehn von einundzwanzig — mit den zugrunde liegenden Anzahlen.
- **Der Prompttext**, der den run erzeugt hat, wörtlich, mit seinem Hash. Kein Verweis auf eine Datei, die sich seitdem geändert haben kann; der Text selbst, eingefroren.
- **Der Commit**, auf dem der Code stand, und ob der Working Tree sauber war.
- **Die Konfiguration** der Suite — welche checks, welche Schwellenwerte — als Hash, damit ein Vergleich mit einer Suite mit anderen Regeln abgelehnt wird, statt still und leise bedeutungslos zu sein.

Daraus, dass der Prompt *in* der Datei steht, folgen zwei Dinge. Erstens ist die Referenz reproduzierbar, auch wenn du den Prompt nie separat committet hast — ein üblicher Zustand an einem Tag voller Experimente. Zweitens kann der Vergleich, wenn ein späterer run abweicht, das Diff des Prompts direkt neben das Diff der Scores stellen: *du hast diese drei Zeilen geändert; diese zwei Fälle haben sich bewegt.* Diese Gegenüberstellung ist das Nützlichste, was ein Vergleich zeigen kann, und es gibt sie nur, wenn der Prompt zusammen mit dem run gespeichert wird.

## Promoten: eine bewusste Handlung

Ein run wird nicht dadurch zur Referenz, dass er der neueste ist oder dass er grün ist. Jemand promotet ihn. Das ist eine Entscheidung — *so sieht gut aus, daran lasse ich mich messen* — und sie sollte sich auch so anfühlen. Im Newsletter-Projekt ist es ein Befehl, `digline promote`, und das Ergebnis ist ein Commit mit einer Datei darin, die ein Reviewer lesen kann.

Drei Dinge sollte eine Promotion verweigern, weil jedes davon die Referenz zur Lüge machen würde:

- Einen run, der unter einer **anderen Konfiguration** als der aktuellen Suite entstanden ist: Seine Zahlen wurden nach anderen Regeln gemessen.
- Einen run, in dem **irgendein check auf Fehler steht** — ein *konnte nicht beurteilen* —, denn eine Referenz ist ein freigegebener Zustand, und ein Fehler ist kein Zustand.
- Einen run aus einem **anderen Mandanten** als dem, für den du promotest, wenn deine Suite Perimeter hat (Kapitel 8).

Wenn dein Werkzeug das nicht verweigert, verweigere es selbst. Eine Referenz, der du nicht trauen kannst, ist schlechter als gar keine, weil sie jeden späteren Vergleich in eine Diskussion verwandelt.

## Nicht der erste grüne run

Der erste run, der durchgeht, ist der verlockendste zum Promoten — und der falsche. Du hast gerade Kapitel 5 gelesen: Der Richter schwankt, und ein einzelner run ist eine Ziehung. Promotest du ihn, hält die Referenz die glückliche Stichprobe fest; jeder spätere run wird mit der glücklichen verglichen und sieht schlechter aus, als er ist.

Eine Ziehung kann nach beiden Seiten ausschlagen. Drei runs der Newsletter-Suite am 3. September, elf Minuten auseinander und ohne jede Änderung, stimmten bei 16, 14 und 16 von 21 Artikeln mit dem Leser überein. Eine Referenz aus dem zweiten der drei würde die anderen beiden als zwei Artikel besser ausweisen — eine *Verbesserung*, die niemand gemacht hat.

Das Verfahren, das an seine Stelle tritt, kostet drei runs:

1. Lass die Suite dreimal auf dem eingefrorenen System laufen.
2. Sieh dir die Fälle an, die sich zwischen den runs unterscheiden. Notiere für jeden, welcher run den mittleren Wert hält.
3. Promote den run, der am häufigsten in der Mitte liegt. Bei Gleichstand entscheiden die Kosten.

Dieser run ist die Referenz. Er hält das typische Verhalten fest, nicht das beste und nicht das schlechteste, und ein späterer Vergleich damit bedeutet, was er sagt.

## Was die Referenz ändert und was nicht

**Ein besserer Prompt.** Du hast ihn geändert, der Vergleich zeigt zwei verbesserte Fälle und keine Verschlechterung, das Diff gefällt dir. Promoten. Die alte Referenz bleibt in der Git-Historie; die neue trägt den neuen Prompttext.

**Ein angehobener Schwellenwert.** Du hast entschieden, dass der Boden bei 0.70 liegen soll, nicht bei 0.60. Das ist eine Konfigurationsänderung: Der Vergleich funktioniert weiterhin — und er sagt dir, dass sich der Schwellenwert verschoben hat, sodass der Umschlag als Regeländerung und nicht als Modelländerung lesbar ist —, aber die Promotion wird verweigert, bis die Konfiguration übereinstimmt. Regel ändern, laufen lassen, promoten: drei Schritte, alle in einem Pull Request sichtbar.

**Ein neuer Fall.** Einen Fall hinzuzufügen macht die Referenz nicht ungültig: Er erscheint im nächsten Vergleich als *neu*, ohne Gegenstück zum Vergleichen. Wenn du ihn dir angesehen hast, promote, und er wird Teil der Aufzeichnung.

**Eine Modelländerung.** Der Anbieter hat das Modell aktualisiert, an deinem Code hat sich nichts geändert, der Vergleich zeigt vier schlechtere Fälle. Genau dafür gibt es die Referenz. Du promotest den schlechteren run nicht. Du untersuchst, passt bei Bedarf den Prompt an und promotest, wenn du wieder auf dem alten Stand bist — oder du akzeptierst das neue Verhalten bewusst, und die Promotion ist der Beleg dafür.

**Die Referenz ändert sich nicht, weil Zeit vergangen ist.** Eine Referenz vom März gilt im September, wenn dazwischen nichts promotet wurde. Ihr Alter ist eine Information, kein Mangel: Es sagt, dass seit März niemand etwas freigegeben hat — was entweder in Ordnung ist oder ein Befund.

## Wo die Referenz liegt

Im Repository, committet, reviewt. Nicht auf einem Server, nicht in einem Dashboard, nicht im Gedächtnis der Person, die den run ausgeführt hat. Drei Gründe, die nichts mit Vorlieben zu tun haben:

Sie lässt sich **diffen**. Zwei Referenzen, zwei Dateien, `git diff`. Jede Zahl, die sich bewegt hat, jede Prompt-Zeile, die sich geändert hat, in einer Ansicht.

Sie lässt sich **reviewen**. Eine Promotion ist ein Pull Request. Jemand anderes als der Autor sieht die Zahlen und den Prompt, bevor sie zum Maßstab werden.

Sie lässt sich **vorzeigen**. Wenn ein Kunde — oder ein Prüfer, oder dein eigenes Team in sechs Monaten — fragt, was wann getestet und freigegeben wurde, ist die Antwort eine Datei mit Commit-Hash und Datum, kein Screenshot.

## Heute umsetzen

1. Friere deinen Prompt und deine Fälle ein. Lass die Suite dreimal laufen.
2. Wähle nach dem obigen Verfahren den mittleren run aus. Promote ihn. Committe die Datei.
3. Öffne die Datei. Vergewissere dich, dass der Prompttext wörtlich darin steht. Wenn dein Werkzeug ihn nicht dort ablegt, lege ihn selbst dort ab — eine Kopie des Prompts neben der Referenz, im selben Commit.
4. Nimm eine kleine Änderung am Prompt vor. Lass laufen. Vergleiche. Lies das Diff des Prompts neben dem Diff der Scores. Diese Ansicht ist der Grund für alles in diesem Kapitel.

Im nächsten Kapitel geht es darum, das am Leben zu halten: wann laufen gelassen wird, was dich hinsehen lassen sollte, und was an dem Morgen zu tun ist, an dem der Vergleich rot ist und du nichts geändert hast.
