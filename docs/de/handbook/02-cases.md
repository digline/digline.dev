---
seo_title: 'Fälle: das Kapital, das niemand aufbaut'
lang: de
translation_of: handbook/02-cases.md
description: Jedes Team, das ein LLM-Feature ausliefert, hat einen Prompt, und fast keines hat Fälle. Was ein Fall ist und wie du bis heute Nachmittag zwanzig davon hast.
search:
  exclude: true
source: handbook/02-cases.md
source_sha: 67838bc398da
source_commit: 48129ea
model: claude-opus-5
---

# 2. Fälle: das Kapital, das niemand aufbaut

Jedes Team, das ein LLM-Feature ausliefert, hat einen Prompt. Fast keines hat Fälle. In diesem Kapitel geht es darum, warum das verkehrt herum ist und was dagegen zu tun ist — konkret, ab heute Nachmittag.

## Was ein Fall ist

Ein Fall ist eine Eingabe, die dir wichtig ist, zusammen mit dem, was du über die richtige Antwort weißt.

Mehr nicht. Bei einem Support-Bot: eine Frage, die ein Kunde tatsächlich gestellt hat, und ob die Antwort die Rückerstattungsregeln hätte erwähnen sollen. Bei einem Klassifikator: eine Stellenbeschreibung und die Berufsgruppe, der sie laut Bestätigung eines Recruiters angehört. Beim [Newsletter-Richter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f), der sich durch dieses Handbuch zieht: Titel und Zusammenfassung eines Artikels und ob der Leser ihn als lesenswert markiert hat.

```json
{
  "id": "2026-08-24-controlling-reasoning-effort-in-llms",
  "vars": {
    "source": "Ahead of AI (Raschka)",
    "title": "Controlling Reasoning Effort in LLMs",
    "summary": "How LLMs Learn Low-, Medium-, and High-Effort Reasoning Modes"
  },
  "expected": {
    "marked": true
  },
  "metadata": {
    "link": "https://magazine.sebastianraschka.com/p/controlling-reasoning-effort-in-llms",
    "original_score": 4
  }
}
```

Drei Felder erledigen die Arbeit. Die `id` benennt ihn. Die `vars` sind das, was das System bekommt. Das `expected` ist das, was du weißt. Die `metadata` sind für den, der den Fall später liest — woher der Artikel stammt und welche Bewertung der Richter ihm an jenem Morgen gegeben hat —, und kein check liest sie. Du kennst nicht immer die genaue richtige Ausgabe — bei einer Zusammenfassung oder einer Freitextantwort kennt sie niemand —, aber du weißt immer *etwas*: Sie sollte X erwähnen, sie sollte N Wörter nicht überschreiten, eine Person, der du vertraust, hat sie als akzeptabel eingestuft. Was du weißt, kommt in `expected`. Was du nicht weißt, lässt du weg und prüfst es mit etwas Schwächerem.

## Warum der Prompt die ganze Aufmerksamkeit bekommt und die Fälle keine

Einen Prompt zu schreiben fühlt sich nach Bauen an. Du tippst, das Modell antwortet, du passt an, es antwortet besser. Jede Iteration ist eine kleine Belohnung. Fälle zu schreiben fühlt sich nach Papierkram an: eine Eingabe kopieren, entscheiden, was die richtige Antwort ist, speichern, von vorn. Keine Belohnung, kein sichtbarer Fortschritt, und das Feature funktioniert ja schon — du hast es funktionieren sehen, du hast die Eingabe selbst getippt.

Also bekommt der Prompt vierzig Iterationen und die Fälle keine, und das Team liefert mit einem Prompt aus, der auf das abgestimmt wurde, was der Autor an jenem Nachmittag zufällig eingetippt hat. Drei Monate später meldet ein Nutzer etwas Merkwürdiges. Niemand kann sagen, ob es neu ist, weil es nichts zum Vergleichen gibt. Der Autor probiert die Eingabe aus, sie sieht gut aus oder eben nicht — so oder so eine einzige Stichprobe. Der Prompt bekommt eine einundvierzigste Iteration, die diese Eingabe repariert und stillschweigend zwei andere kaputt macht, die niemand eingetippt hat.

Diese Schleife ist der Normalfall. Es ist kein Mangel an Disziplin; es ist das, was passiert, wenn die einzige Rückmeldung die nächste Antwort des Modells ist.

Fälle verändern die Schleife. Mit zwanzig Fällen ist die einundvierzigste Iteration eine Zahl: *vorher neunzehn von zwanzig, nachher siebzehn*. Die Korrektur, die zwei Dinge kaputt gemacht hat, wird noch in derselben Minute sichtbar, in der sie entsteht.

## Woher Fälle kommen

Nicht aus deiner Vorstellung. Fälle, die du am Schreibtisch erfindest, prüfen die Eingaben, an die du ohnehin schon gedacht hast — genau die Eingaben, die der Prompt bereits bewältigt. Die nützlichen Fälle stammen aus vier Quellen, und keine davon verlangt Kreativität:

**Korrekturen.** Jedes Mal, wenn ein Mensch das Modell überstimmt — ein Recruiter ändert die Berufsgruppe, ein Redakteur schreibt die Zusammenfassung um, der Leser markiert einen Artikel, den der Richter niedrig bewertet hat —, ist diese Überstimmung ein gelabelter Fall, kostenlos und wertvoller als alles, was du selbst schreiben könntest. In diesem Newsletter-Projekt sagt der Leser jeden Morgen, welche Artikel es wirklich wert waren; diese Antwort ist das `expected` für die Fälle des Tages. Das Programm zeichnet sie als Nebeneffekt der normalen Nutzung auf. Such nach diesem Nebeneffekt in deinem eigenen Produkt: Er ist fast immer da, nur nicht aufgezeichnet.

**Beschwerden.** Ein Nutzer sagt: „Das hat es falsch gemacht.“ Bevor du den Prompt anfasst, speichere die Eingabe und die richtige Antwort als Fall. Dann korrigiere den Prompt. Dann lass die Fälle laufen. Aus der Beschwerde wird dauerhafter Schutz statt eines einmaligen Flickens — und wenn die Korrektur etwas anderes kaputt macht, erfährst du es jetzt.

**Fehler aus der Produktion.** Jede Ausgabe, die fehlerhaft formatiert, leer, regelwidrig oder peinlich war. Diese hast du bereits in den Logs; es sind die Fälle, die du am wenigsten wiedersehen möchtest.

**Randfälle, die dir aufgefallen sind.** Die leere Eingabe. Die Eingabe in der falschen Sprache. Die Eingabe mit 4000 Wörtern. Die Eingabe, die deinen Wettbewerber erwähnt. Du hast mindestens einmal gesehen, wie das Modell damit seltsam umgegangen ist; schreib sie auf, solange du dich erinnerst.

Die Gewohnheit, die mehr zählt als jedes Werkzeug: **ein gesehener Fehler, ein geschriebener Fall, am selben Tag.** Nicht „dafür sollte man später Tests ergänzen“. Später kommt nie; der Fehler schon.

## Wie viele und welche

Zwanzig reichen für den Anfang. Nicht zweihundert — zweihundert wirst du nie schreiben, und zwanzig machen aus einer Vermutung bereits eine Zahl. In diesem Newsletter-Projekt reichten einundzwanzig Fälle, um das Rauschen des Richters über sechs runs hinweg zu messen und um zu zeigen, dass es [nichts verschlechtert hat](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/README.md#reporthtml), den gelesenen Anteil jedes Artikels von 1500 Zeichen auf 400 zu kürzen.

Was die zwanzig brauchen:

**Beide Antworten.** Wenn jeder Fall ein „Ja“ erwartet, erreicht ein Modell, das immer Ja sagt, die volle Punktzahl. Die Newsletter-Suite enthält zehn Artikel, die der Leser wollte, und elf, die er nicht wollte. Ohne die elf wäre die größte Schwäche des Richters unsichtbar — dass er Dinge nach oben bringt, die nur relevant klingen.

**Die langweilige Mitte, nicht nur die Ränder.** Eine Suite aus zwanzig pathologischen Eingaben sagt dir, wie das System unter Stress versagt, und nichts darüber, wie es sich an einem Dienstag verhält. Nimm gewöhnliche Eingaben mit auf — als eigene Gruppe, nicht als Großteil der Menge.

**Stabile Eingaben.** Ein Fall, der die heutigen Daten abruft, ist morgen ein anderer Fall. Halte die Eingabe als Momentaufnahme in der Datei fest. Das Newsletter-Projekt speichert die Zusammenfassung des Artikels im Fall, nicht eine URL zum erneuten Abrufen: dieselben einundzwanzig Eingaben, in jedem run, seit August.

**Ein Label, wenn möglich.** Bei allem, was klassifiziert — positiv/negativ, freigeben/ablehnen, relevant/nicht relevant —, ergänze das Label. Mit Labels bekommt deine Suite einen Gesamtwert: *Precision zwischen 0.60 und 0.67 über sechs runs der Newsletter-Suite hinweg*, eine Zahl, die stabil genug ist, um daran einen Schwellenwert festzumachen, während einzelne Fälle um drei von fünf Stimmen schwankten. Ohne Labels hast du zwanzig Urteile und keine Zusammenfassung.

## Was Fälle nicht sind

**Nicht die Beispiele im Prompt.** Die Few-Shot-Beispiele in deinem Prompt sind Stützräder für das Modell. Fälle werden zurückgehalten; das Modell sieht sie nie als Beispiele. Wenn du dieselben Eingaben für beides verwendest, prüfst du die Fähigkeit des Modells zu kopieren, nicht zu verallgemeinern.

**Kein einmaliges Lieferobjekt.** Eine Falldatei, die am Tag des Release vollständig war, ist bei der zweiten Beschwerde veraltet. Die Menge wächst im Tempo der Produktion — deshalb ist „ein Fehler, ein Fall“ eine Regel und kein Projekt.

**Keine sensiblen Daten, wenn die Datei irgendwohin gelangt.** Ein Fall, der aus einem echten Kundengespräch gebaut ist, trägt diesen Kunden mit sich. Halte solche Fälle innerhalb der Grenzen, aus denen sie stammen, oder schreibe die Eingabe mit derselben Form und anderen Fakten um. Im Newsletter-Projekt sind die Eingaben öffentliche Artikel, also ist die Datei ebenfalls öffentlich; bei einem Recruiting-Werkzeug sind die Stellenbeschreibungen unproblematisch und die Lebensläufe nicht.

## Der Teil, der sich ansammelt

Alles andere in einem LLM-Projekt verliert an Wert. Der Prompt, den du auf ein Modell abgestimmt hast, ist beim nächsten schlechter. Der Schwellenwert, den du gewählt hast, driftet. Der Richter ändert seine Meinung. Die Fälle verlieren nicht an Wert: Eine richtige Antwort auf eine echte Eingabe bleibt richtig, wenn sich das Modell ändert, wenn sich der Prompt ändert, wenn du den Anbieter wechselst. Zwanzig Fälle im März sind zwanzig Fälle im September, plus dem, was im September dazugekommen ist.

Deshalb ist die langweilige Arbeit die einzige, die es sich lohnt, zuerst zu tun. Nach einem halben Jahr hat das Team mit dem besten Prompt einen Prompt. Das Team mit zweihundert echten Fällen kann alles ändern — Modell, Prompt, Anbieter — und weiß innerhalb einer Stunde, ob es schlechter geworden ist. Der Prompt ist eine Meinung; die Fälle sind das Gedächtnis.

## Heute umsetzen

1. Finde die Überstimmung in deinem Produkt — die Stelle, an der ein Mensch das Modell korrigiert. Wenn es sie gibt, fang an, sie aufzuzeichnen. Wenn nicht, ist das das Erste, was zu bauen ist, vor jeder Suite.
2. Öffne deine Logs. Nimm die letzten zehn Eingaben, die zu einer Beschwerde oder einer merkwürdigen Ausgabe geführt haben. Schreibe für jede die richtige Antwort auf. Das sind zehn Fälle.
3. Nimm zehn gewöhnliche Eingaben aus denselben Logs — solche, über die sich niemand beschwert hat. Bestätige, dass die Ausgabe in Ordnung war. Das sind zwanzig.
4. Leg sie in einer Datei ab, im Repository, neben dem Code. Halte die Eingaben als Momentaufnahme fest. Ergänze Labels, wo sie zutreffen.
5. Von jetzt an: ein gesehener Fehler, ein geschriebener Fall, am selben Tag.

Im nächsten Kapitel geht es darum, woher die richtigen Antworten kommen, wenn dir niemand welche gibt — und warum sich das entscheidet, wenn du das Feature schreibst, und nicht danach.
