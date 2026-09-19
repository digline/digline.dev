---
seo_title: 'Checks: erst deterministisch, der Richter zuletzt'
lang: de
translation_of: handbook/04-checks.md
description: 'Wie du aus einer LLM-Ausgabe ein Urteil machst, und die Regel, die bei der Evaluation am meisten Zeit spart: Lass ein Modell nur das beurteilen, was sich anders nicht beurteilen lässt.'
search:
  exclude: true
source: handbook/04-checks.md
source_sha: bf59e8257331
source_commit: d778c40
model: claude-opus-5
---

# 4. Checks: erst deterministisch, der Richter zuletzt

Ein Testfall gibt an, was hineingeht und was du über die richtige Antwort weißt. Ein check ist die Art, wie du aus einer Ausgabe ein Urteil machst. In diesem Kapitel geht es darum, checks auszuwählen — und um eine Regel, die zu einfach klingt, um wichtig zu sein, und die mehr Zeit spart als alles andere hier: **Lass ein Modell nur das beurteilen, was sich anders nicht beurteilen lässt.**

## Zwei Arten von checks

**Deterministische checks** brauchen kein Modell. Sie sehen sich die Ausgabe an und beantworten eine Frage mechanisch: Enthält sie diese Formulierung, ist sie gültiges JSON, passt sie zu diesem Schema, hat sie weniger als 200 Wörter, kostet sie weniger als einen Cent, enthält sie eine Steuernummer. Gleiche Ausgabe, gleiches Urteil, jedes Mal, sofort, kostenlos.

**Beurteilte checks** lassen ein Modell die Ausgabe bewerten: Ist diese Antwort höflich, beantwortet sie die Frage, wird sie von den abgerufenen Dokumenten gestützt, ist sie besser als die vorige Version. Sie können Dinge ausdrücken, die keine Regex ausdrücken kann. Sie sind zugleich eine zweite Verteilung über der ersten — der Richter zieht ebenfalls Stichproben — und jeder beurteilte check erbt das Rauschen, die Kosten und die Latenz eines Modellaufrufs.

Die meisten Teams greifen zuerst zum Richter, weil das der interessante Teil ist. Dieses Kapitel plädiert für die umgekehrte Reihenfolge.

## Warum zuerst deterministisch

Nimm den [Newsletter-Richter](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/suite.py). Seine Ausgabe ist ein kleines JSON-Objekt: eine Bewertung von 1 bis 5 und eine Begründung in einem Satz. Bevor überhaupt ein Modell gefragt wird, ob die Bewertung *gut* ist, lassen sich drei Dinge ganz ohne Modell prüfen:

- Ist die Ausgabe gültiges JSON mit genau diesen beiden Feldern? (`JsonSchema`)
- Ist die Bewertung eine ganze Zahl zwischen 1 und 5? (dasselbe Schema)
- Hat der Aufruf weniger gekostet als das Budget? (`CostBudget`)

Diese drei fangen die Fehler ab, die in der Produktion tatsächlich auftreten: das Modell verpackt das JSON in Fließtext, das Modell erfindet eine Bewertung von 0, der Prompt wächst, bis jeder Aufruf dreimal so viel kostet wie zuvor. Sie fangen sie kostenlos ab, deterministisch, bei jedem run. Und wenn einer davon fehlschlägt, ist der Fehler eindeutig — über „kein gültiges JSON“ streitet niemand.

Erst danach kommt die Frage, die einen Richter braucht — „stimmt diese Bewertung mit dem überein, was der Leser wollte?“ —, und in diesem Newsletter-Projekt ließ sich sogar diese Frage ohne Modell beantworten, weil die Markierungen des Lesers selbst aufgezeichnet sind. Der check besteht aus vierzehn Zeilen Python: *hat der Richter genau dann ≥4 gesagt, wenn der Leser es markiert hat?* Kein zweites Modell, kein Rauschen aus dem check selbst.

Das allgemeine Muster: **jeder check, den du deterministisch machen kannst, ist eine Rauschquelle weniger zwischen dir und der Antwort.** Eine Suite mit fünf deterministischen checks und einem Richter hat ein verrauschtes Signal zu kalibrieren. Eine Suite mit sechs Richtern hat sechs.

## Was die deterministischen abfangen

Ein kurzer Katalog, geordnet nach dem Fehler, für den es den jeweiligen check gibt:

| Fehler, den du schon erlebt hast | Check |
|---|---|
| Die Antwort hat die Pflichtzeile vergessen (ein Haftungsausschluss, eine Signatur, eine rechtliche Formulierung) | `Contains` |
| Die Antwort hat etwas erwähnt, was sie nie erwähnen darf (einen Wettbewerber, einen internen Namen, „als KI-Modell“) | `NotContains` |
| Die Ausgabe sollte strukturiert sein und kam als Fließtext zurück | `IsJson`, `JsonSchema` |
| Die Antworten werden jede Woche länger oder müssen in einen Kanal passen | `Length` |
| Die Antwort soll einer bekannten *nahekommen*, nicht identisch sein | `Levenshtein`, abgestuft |
| Die Ausgabe erreichte eine Person und enthielt eine IBAN, eine Steuernummer, eine E-Mail-Adresse | `PiiAbsent` |
| Eine Prompt-Änderung hat die Tokens verdoppelt, und aufgefallen ist es erst mit der Rechnung | `CostBudget` |
| Das Feature funktioniert, aber die Nutzer warten vier Sekunden | `LatencyBudget` |

Zu zweien davon ein Hinweis. `PiiAbsent` ist der, den man weglässt und später bereut: Ein LLM, das Kundendaten in seinem Kontext hat, wird früher oder später einen Teil davon in einer Ausgabe wiederholen, in die sie nicht gehören, und kein Richter erkennt eine gültige IBAN so zuverlässig wie eine Prüfsumme. Und die Budgets sind abgestuft, nicht bestanden/durchgefallen: Kosten, die *innerhalb* des Limits steigen, zeigen sich trotzdem als Veränderung gegenüber der Referenz — so merkst du, dass der Prompt wächst, bevor er die Grenze überschreitet.

## Wann ein Richter das richtige Werkzeug ist

Es gibt Fragen, die sich mechanisch nicht beantworten lassen:

- *Ist diese Antwort höflich?* — für Tonfall gibt es keine Regex.
- *Beantwortet sie die gestellte Frage?* — dafür muss man beide verstehen.
- *Wird jede Aussage in dieser Zusammenfassung von der Quelle gestützt?* — die Kernfrage jedes Retrieval-Systems.
- *Ist diese Neufassung besser als das Original?* — eine Präferenz, keine Regel.

Dafür ist ein beurteilter check die einzige Möglichkeit, und davon gibt es zwei Formen. Eine **Rubrik** — du beschreibst das Kriterium in einem Satz, der Richter liefert eine Bewertung in [0, 1] und eine Begründung. Und **Faithfulness** — der Richter zählt die Aussagen in der Ausgabe und wie viele davon der bereitgestellte Kontext stützt; der check dividiert. Die zweite ist die passende für alles, was Dokumente abruft, und sie ist nützlicher als eine Rubrik, weil sie eine Zahl liefert, über die sich streiten lässt, und kein Bauchgefühl.

Welche du auch nimmst: drei Regeln, die alle aus derselben Tatsache folgen — der Richter ist eine Verteilung:

1. **Schwellenwert und Toleranz sind Pflicht**, keine Voreinstellungen. Ein beurteilter check mit einem impliziten „alles über 0 besteht“ ist für immer grün und sagt dir nichts. Setze den Schwellenwert dorthin, wo das System messbar steht; leite die Toleranz aus gemessenem Rauschen ab (Kapitel 5 zeigt, wie).
2. **Zieh Stichproben.** Ein Urteil pro Testfall ist eine Ziehung. Frage drei- oder fünfmal und fasse zusammen — sonst jagst du den nächsten Monat Regressionen hinterher, die nur der Richter sind, der seine Meinung ändert.
3. **Halte den Prompt des Richters genauso fest wie den deines Systems.** Es ist ein Prompt. Er driftet aus denselben Gründen. Er sollte in einer Datei liegen, versioniert sein und bei jedem run mit aufgezeichnet werden, genau wie der Prompt, der getestet wird.

## Der Richter gehört dir

Eines sei klar gesagt, weil sich die Werkzeuge hier unterscheiden: Der Richter ist eine Funktion, die du bereitstellst. Sie ruft das Modell auf, das du wählst, auf die Art, die du wählst, und das Evaluationswerkzeug setzt nur die Frage zusammen und liest die Bewertung aus. Zwei Folgen. In Tests schleust du einen Fake-Richter ein, und jeder beurteilte check wird deterministisch. Und die Begründung des Richters, die die beurteilte Ausgabe zitiert, wird in den run geschrieben, direkt neben die Ausgabe. Der einzige Aufruf, an dem das Werkzeug beteiligt ist, ist der des Richters selbst, an das von dir gewählte Modell; das Werkzeug hat keinen eigenen Server, an den es etwas senden könnte. In Kapitel 8 geht es darum, wann selbst dieser run nicht nach außen gelangen darf.

## Eine Suite zusammenstellen

Für eine erste Suite das Muster, das sich bewährt hat:

- **Ein struktureller check** auf die Form der Ausgabe. Er fängt die peinlichen Fehler ab und kostet nichts.
- **Ein oder zwei inhaltliche checks** — ein `Contains` für die Pflichtformulierung, ein `NotContains` für die verbotene, `PiiAbsent`, wenn die Ausgabe eine Person erreicht.
- **Die Budgets**, immer, abgestuft.
- **Höchstens ein beurteilter check**, mit Stichproben, für das, was wirklich ein Urteil braucht. Wenn du merkst, dass du drei willst, frag dich, ob zwei davon nicht auch Testfälle mit bekannter Antwort sein könnten.

Fünf oder sechs checks auf zwanzig Testfällen. Das läuft in wenigen Minuten, kostet Cent-Beträge und ist schon mehr, als die allermeisten LLM-Features in Produktion haben.

## Heute umsetzen

1. Liste die letzten fünf Fehler auf, die dein Feature produziert hat. Frage bei jedem: *hätte eine Regex, ein Schema oder ein Zähler das abfangen können?* Meistens lautet die Antwort ja.
2. Schreib die zuerst als deterministische checks. Lass sie auf deinen zwanzig Testfällen laufen. Einige werden heute fehlschlagen — genau darum geht es.
3. Schreib erst danach den einen beurteilten check für die Frage, die wirklich ein Modell braucht. Gib ihm einen Schwellenwert und eine Toleranz. Zieh Stichproben.
4. Wenn ein beurteilter check bei einem Testfall fehlschlägt, sieh dir die Begründung an, bevor du dir den Prompt ansiehst. Oft ist der Testfall falsch, nicht das System.

Im nächsten Kapitel geht es um diesen einen beurteilten check: wie stark er schwankt, wie sich die Schwankung messen lässt und wie du verhinderst, dass jeder Dienstag zum Fehlalarm wird.
