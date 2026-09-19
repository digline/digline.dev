---
seo_title: 'Wartung: die Suite als Praxis betreiben'
lang: de
translation_of: handbook/07-maintenance.md
description: Wann eine Evaluations-Suite laufen sollte, was dich hinsehen lassen sollte und was zu tun ist an dem Morgen, an dem CI rot wird, obwohl du überhaupt nichts geändert hast.
search:
  exclude: true
source: handbook/07-maintenance.md
source_sha: 0117d185cb00
source_commit: d52f054
model: claude-opus-5
---

# 7. Wartung

Eine Suite, die einmal läuft, ist eine Demo. In diesem Kapitel geht es um den Teil, der daraus eine Praxis macht: wann sie läuft, was dich hinsehen lassen sollte und was zu tun ist an dem Morgen, an dem sie rot wird, obwohl du nichts geändert hast.

## Die fünf Auslöser

Etwas passiert; die Suite läuft; der Vergleich sagt, ob es schlechter geworden ist. Es gibt fünf verschiedene Dinge, die passieren können, und sie verlangen unterschiedliche Reaktionen.

### 1. Du hast etwas geändert

Den Prompt, das Modell, das Retrieval, den Code um den Aufruf herum. Das ist der Auslöser, mit dem du rechnest, und der, den CI abdeckt: Jeder Pull Request lässt die Suite laufen und vergleicht mit der Referenz. Rot blockiert den Merge; die Zeilen unter der Überschrift sagen, welche Fälle sich bewegt haben und um wie viel; daneben steht der Diff des Prompts.

Die Reaktion ist die übliche – sieh dir die Fälle an, die schlechter geworden sind, entscheide, ob die Änderung es wert ist, behebe oder akzeptiere. Die einzige Regel: Ein roter Vergleich wird nie dadurch behoben, dass du die Toleranz erweiterst oder den Schwellenwert senkst. Das sind Regeländerungen, und Regeländerungen gehen durch die Vordertür (Kapitel 6), nicht durch die Korrektur eines fehlschlagenden Builds.

### 2. Der Anbieter hat etwas geändert

In deinem Repository hat sich nichts bewegt. Das Modell hinter der API schon – ein Update, eine Abkündigung, ein umgebogener Alias, ein geändertes Standardverhalten. Deine Commit-Historie sagt „unverändert“. Der Vergleich sagt, sofern er gelaufen ist, vier Fälle schlechter.

*Sofern er gelaufen ist* – darum geht es. CI läuft bei Pushes, und niemand hat gepusht. Dieser Auslöser braucht einen Zeitplan: einen nächtlichen oder wöchentlichen Job, der die Suite gegen die Referenz laufen lässt, ohne dass sich auf deiner Seite etwas geändert hat. Ein rotes Ergebnis bei leerem Diff ist die Signatur des Anbieters – der eine Fehler, den kein Code-Review, kein Test deines eigenen Codes und keine noch so große Sorgfalt abfangen kann, und derjenige, von dem die meisten Teams durch ihre Nutzer erfahren.

Im [Newsletter-Projekt](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) ist das ein wöchentlicher Workflow, der den echten Richter laufen lässt und vergleicht. Er kostet etwa sieben Cent pro Woche. Er ist die billigste Versicherung im Repository.

Die Reaktion unterscheidet sich von der bei Auslöser 1: Du hast das nicht verursacht, also kannst du es auch nicht rückgängig machen. Möglichkeiten, der Reihe nach: die Modellversion festschreiben, falls der Anbieter das zulässt und du auf einem Alias warst; den Prompt an das neue Verhalten anpassen und promoten, wenn du wieder auf dem alten Stand bist; oder das neue Verhalten bewusst als Referenz akzeptieren, wobei die Promotion der Beleg dafür ist, dass du es gesehen und entschieden hast.

### 3. Ein echter Fall ist schiefgegangen

Ein Nutzer meldet es. Ein Log zeigt es. Jemand im Team bemerkt eine Antwort, die nicht hätte vorkommen dürfen. Die Suite hat es nicht abgefangen, weil ihr diese Eingabe fehlte.

Die Reaktion ist die Gewohnheit aus Kapitel 2, und sie ist der wichtigste Satz in diesem Handbuch: **ein gesehener Fehler, ein geschriebener Fall, am selben Tag.** Bevor du den Prompt anfasst, speichere die Eingabe und die richtige Antwort als Fall. Lass die Suite laufen – der neue Fall schlägt fehl, und das ist richtig so; er erscheint als *neu*, ohne Vergleichspunkt. Dann korrigiere den Prompt. Dann lass sie erneut laufen: Der neue Fall besteht, und die anderen zwanzig sagen dir, ob die Korrektur etwas kaputt gemacht hat. Dann promote.

Lässt du den ersten Schritt aus, hast du eine Eingabe geflickt und nichts gelernt. Machst du ihn, wird aus dem Fehler dauerhafter Schutz.

### 4. Die Regeln haben sich verschoben

Jemand hat einen Schwellenwert angehoben, eine Toleranz verschärft, einen check hinzugefügt, einen entfernt. Der Vergleich läuft weiterhin – und er sagt dir, dass sich die Konfiguration von der Referenz unterscheidet, sodass ein Fall, der von bestanden auf fehlgeschlagen gekippt ist, als Regeländerung zu lesen ist und nicht als Modelländerung. Die Promotion wird verweigert, bis die Referenz unter den neuen Regeln neu festgelegt ist.

Die Reaktion ist kurz: unter den neuen Regeln laufen lassen, hinsehen, promoten. Der Sinn der Verweigerung ist, dass eine Regeländerung nie unsichtbar bleibt – sie erzeugt immer eine Promotion, die jemand im Review sehen kann.

### 5. Ein Fall lässt sich nicht mehr beurteilen

Ein check liefert *konnte nicht beurteilen* – die Stichproben des Richters gehen auseinander, die Ausgabe hatte die falsche Form, beim Anbieter lief eine Zeitüberschreitung auf. Das ist weder bestanden noch fehlgeschlagen, und es blockiert die Promotion.

Zwei Reaktionen, und nur zwei. Ist der Fall wirklich mehrdeutig – die Stichproben gehen auseinander, weil ein Mensch sich ebenfalls nicht entscheiden würde –, dann setze ihn aus, mit schriftlicher Begründung, damit er als sichtbare Lücke in der Suite bleibt, statt stillschweigend zu verschwinden. Liegt es am check – falsche Form, falscher Prompt im Richter –, dann behebe den check. Was du nicht tust: die Mindestübereinstimmung so weit senken, bis aus dem geteilten Ergebnis ein Bestehen wird. Das macht aus *unbekannt* ein *in Ordnung*, ohne dass jemand darüber entschieden hat.

## Die zehn Minuten pro Woche

Die Auslöser sind reaktiv. Was eine Suite ehrlich hält, ist eine kleine, langweilige, fest eingeplante Handlung:

1. Öffne den Vergleich aus dem geplanten run. Ob grün oder rot, lies die aggregierten Werte – Precision, Accuracy – gegenüber der Referenz. Zwei Zahlen, dreißig Sekunden.
2. Sieh dir die Liste der Fälle an, die sich bewegt haben, auch innerhalb der Toleranz. Ein Fall, der jede Woche ein wenig driftet, sagt dir etwas, bevor er die Grenze überschreitet.
3. Prüfe die Zahl der Fälle. Ist sie seit letzter Woche nicht gewachsen, frage dich, ob in der Produktion nichts schiefgegangen ist oder ob es niemand aufgeschrieben hat. Meist ist es das Zweite.
4. Prüfe das Alter der Referenz. Eine vier Monate alte Referenz für ein Feature, das sich zweimal geändert hat, ist eine Referenz, die niemand erneut freigegeben hat.
5. Wenn in 1–4 etwas eine Entscheidung verlangt, triff sie jetzt – promoten, aussetzen, einen Fall hinzufügen – und committe.

Zehn Minuten, einmal pro Woche, von der Person, die das Feature verantwortet. Lass es einen Monat lang aus, und die Suite ist immer noch da; lass es ein Quartal lang aus, und sie ist wieder eine Demo.

## Was schlechter wird, ohne dass du es merkst

Drei langsame Fehlentwicklungen, die kein Auslöser abfängt, weil jeder einzelne Schritt zu klein ist, um Alarm auszulösen:

**Schleichende Kosten.** Jede Änderung am Prompt fügt einen Satz hinzu; niemand entfernt einen. Der Budget-check wird genau deshalb abgestuft bewertet, damit Kosten *innerhalb* des Limits trotzdem als Veränderung gegenüber der Referenz sichtbar werden. Achte auf die Zahl, nicht nur auf die Farbe.

**Verrottende Fälle.** Ein Fall, dessen erwartete Antwort im März richtig war, kann im September falsch sein, weil sich das Produkt geändert hat – die Erstattungsfrist wurde verschoben, die Taxonomie hat eine Kategorie dazubekommen. Eine Suite mit verrotteten Fällen schlägt aus den falschen Gründen fehl und gewöhnt die Leute daran, Rot zu ignorieren. Wenn ein Fall fehlschlägt und die Ausgabe richtig aussieht, prüfe den Fall, bevor du den Prompt prüfst.

**Abdriften der Referenz durch Promotions.** Jede Promotion akzeptiert einen kleinen Verlust – „ein Fall schlechter, aber der Diff ist schöner“. Zehn Promotions später liegt die Referenz zehn kleine Verluste unter dem Ausgangspunkt, und jeder einzelne Vergleich war grün. Der Schutz ist der aggregierte Wert in der Datei: Vergleiche die Precision dieses Monats nicht mit der Referenz von letzter Woche, sondern mit der allerersten, die du je freigegeben hast. Git hat sie.

## Heute umsetzen

1. Richte den geplanten run ein – wöchentlich reicht – mit dem echten Richter. Mach ihn zu dem einen Job, der läuft, wenn niemand gepusht hat.
2. Trag die zehnminütige Durchsicht in den Kalender ein, bei der Person, die das Feature verantwortet.
3. Schreib die Regel „ein Fehler, ein Fall“ dorthin, wo das Team sie sieht: in die README der Suite, in die Pull-Request-Vorlage, in das Channel-Topic.
4. Wenn der Vergleich das nächste Mal rot ist und du nichts geändert hast, fass die Toleranz nicht an. Lies den Diff. Er ist leer. Das ist der Anbieter, und jetzt weißt du, wie das aussieht.

Das letzte Kapitel richtet sich an Teams, die LLM-Features für andere bauen – wo dieselbe Suite zur Antwort auf eine Frage wird, die der Kunde stellen wird, und wo ein Teil dessen, was sie enthält, niemals den Perimeter des Kunden verlassen darf.
