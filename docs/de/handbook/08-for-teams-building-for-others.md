---
seo_title: Für Teams, die für andere entwickeln
lang: de
translation_of: handbook/08-for-teams-building-for-others.md
description: 'Eine Evaluations-Suite, drei Beteiligte: was Entwickler, Beratungshaus und Kunde jeweils aus denselben runs brauchen, und die Regel, von der es keine Ausnahme gibt.'
search:
  exclude: true
source: handbook/08-for-teams-building-for-others.md
source_sha: e231cf6c9192
source_commit: 356a3c8
model: claude-opus-5
---

# 8. Für Teams, die für andere entwickeln

Alles bis hierher gilt für alle, die ein LLM im Produktivbetrieb haben. Dieses Kapitel richtet sich an eine engere Gruppe: Beratungshäuser, Softwarehäuser, alle, die ein LLM-Feature für einen Kunden bauen und pflegen, der nicht selbst entwickelt und dem die Daten gehören, auf denen das Feature läuft. Wenn das auf dich zutrifft, erfüllt dieselbe Suite zwei weitere Aufgaben — und bei einer davon gibt es eine Regel, von der es keine Ausnahme gibt.

## Drei Personen, eine Suite

In einem Produkt, das du für dich selbst baust, gibt es eine beteiligte Partei. Hier sind es drei, und sie wollen Unterschiedliches aus denselben Zahlen.

**Der Entwickler** will das, was die vorherigen sieben Kapitel beschreiben: Fälle, checks, eine Referenz, einen Vergleich in der CI.

**Das Beratungshaus** — deine Firma — pflegt dieses Feature für mehrere Kunden gleichzeitig. Es muss für jeden von ihnen beantworten: *Hat das Release vom letzten Dienstag den Assistenten von Kunde A verschlechtert?* — und zwar, ohne die Daten von Kunde A zu halten und ohne dass die Zahlen von Kunde A je am selben Ort liegen wie die von Kunde B.

**Der Kunde** besitzt die Daten und liest keinen Code. Er hat zwei Rechte: ein Urteil, das er verstehen kann, über ein System, das er nicht einsehen kann — und dass seine Daten seine Räumlichkeiten nicht verlassen. Und er hat eine Frage, die er früher oder später stellen wird, in einem Meeting oder in einem Audit:

> *Was habt ihr getestet, wann, unter welcher Version, und wer hat es freigegeben?*

Ein Dashboard beantwortet das nicht. Ein Dashboard zeigt den heutigen Stand. Die Frage zielt auf ein Datum, einen Commit, ein Artefakt, das jemand ein halbes Jahr später öffnen kann und das sich seitdem nicht verändert hat. Die Referenzdatei aus Kapitel 6 ist dieses Artefakt — deshalb liegt sie im Repository und nicht auf dem Server eines Anbieters: eine Datei, die du weitergeben kannst, mit Hash und Datum, ist ein Beleg; eine Ansicht, die jemand anders hostet, ist keiner.

## Die Regel: die Nutzdaten bleiben, wo sie entstanden sind, das Urteil wird weitergegeben

Nimm einen erfundenen Fall in einem Recruiting-Tool, Zahlen inklusive: Der Lebenslauf eines Bewerbers geht hinein, ein Ranking kommt heraus, und ein per Richter bewerteter check fragt, ob das Ranking begründet ist. Der run enthält jetzt drei Arten von Dingen:

- **Das Urteil**: Name des checks, bestanden oder nicht, Score 0.81, Schwellenwert 0.70, Toleranz, Kosten. Zahlen darüber, wie sich das System verhalten hat.
- **Die Nutzdaten**: der Lebenslauf, der Ranking-Text und die *Begründung* des Richters — die den Lebenslauf zitiert, um den Score zu erklären.
- **Der Aggregatwert**: Precision 0.75 über den gesamten Satz, 12 richtige Positive, 4 falsche.

Das Beratungshaus braucht das Erste und das Dritte für seine Arbeit. Auf das Zweite hat es kein Recht, und es braucht es auch nicht. Die Regel ist deshalb mechanisch: **ein run, der die Grenze zwischen Kunde und Beratungshaus überschreitet, wird vorher bereinigt** — Begründungen entfernt, Metadaten der Nutzdaten entfernt, die Urteile und die Zahlen bleiben. Nicht als Option, an die jemand beim Export denken muss, sondern als Eigenschaft des runs selbst, geprüft beim Lesen der Datei, sodass ein Dokument, das von sich behauptet, bereinigt zu sein, keine Begründung enthalten kann.

Daraus folgen drei Dinge, und jedes davon ist eine Entwurfsentscheidung, die dir begegnet, egal welches Werkzeug du einsetzt:

**Der Richter läuft innerhalb des Perimeters.** Seine Begründung zitiert die Daten. Sie lässt sich nur dort berechnen, wo die Daten sein dürfen. Was hinausgeht, ist der Score, den er erzeugt hat, nie der Satz.

**Die Fall-ID gehört nicht zu den Nutzdaten — also darf sie auch keine enthalten.** Sie muss die Grenze überqueren, denn über sie findet ein Urteil sein Gegenstück in der Referenz. `order-12345-mario-rossi` als ID trägt den Namen eines Kunden ins Repository des Beratungshauses. Wenn Fälle aus dem Produktivbetrieb erzeugt werden, muss auch die ID erzeugt werden — ein Datum, eine laufende Nummer, ein kurzer Hash — ohne Möglichkeit, einen Bezeichner aus der Anwendung durchzureichen.

**Prompts sind nicht automatisch unbedenklich.** Ein Prompt ist die Arbeit des Beratungshauses, aber er enthält oft die Geschäftsregeln des Kunden, und die gehören dem Kunden. Halte den Prompt standardmäßig innerhalb des Perimeters; lass eine Suite in Code, der durch das Review geht, erklären, dass ihre Prompts weitergegeben werden dürfen.

## Was der Kunde bekommt

Nicht das Repository. Einen **Bericht**: ein in sich geschlossenes Dokument — eine HTML-Datei, druckbar —, das in dieser Reihenfolge beantwortet: *Ist es schlechter geworden?*, *welche checks und um wie viel*, *was wurde getestet und was hat sich daran geändert*, *wann, unter welcher Version, von wem freigegeben*. Geschrieben für jemanden, der keinen Code liest, erzeugt aus demselben Vergleich, den der Entwickler gesehen hat, sodass die beiden nie auseinandergehen können.

Der Bericht wird innerhalb des Kunden-Perimeters erzeugt, wo die Begründungen vorliegen, und er kann sie enthalten: Für den Kunden ist die Erklärung des Richters, warum ein Fall fehlgeschlagen ist, die nützlichste Zeile auf der Seite. Die bereinigte Fassung desselben Berichts — Urteile, keine Begründungen — ist das, was das Beratungshaus behält.

Zwei Gewohnheiten, die den Bericht wertvoll machen:

**Eine Referenz pro Lieferung.** Wenn der Kunde ein Release abnimmt, ist diese Abnahme eine Promotion. Die Referenzdatei hält den Stand fest, den er abgenommen hat; der nächste Bericht vergleicht dagegen. „Seit der Abnahme ist es schlechter geworden“ ist ein Satz, den beide Seiten überprüfen können.

**Der Aggregatwert im Vertrag.** Mit gelabelten Fällen hat eine Suite eine Zahl — Precision 0.75 im erfundenen Fall oben —, die stabil genug ist, um sie festzuschreiben: *Der Klassifikator stimmt bei mindestens 70% der bestätigten Fälle mit euren Prüfern überein.* Setze ihn dorthin, wo das System zum Zeitpunkt der Abnahme messbar steht, nicht dorthin, wo eine der beiden Seiten es gern hätte. Der Schwellenwert ist die Zusage; über den Vergleich behalten beide Seiten sie im Blick.

## Was das Beratungshaus behält

Für jeden Kunden, im Repository dieses Kunden oder in einem kundenspezifischen Verzeichnis, das sich nicht mit dem eines anderen verwechseln lässt: die Suite, die Referenzen, die bereinigten runs. Niemals ein gemeinsamer Speicher, in dem die Urteile von Kunde A neben denen von Kunde B liegen — einen Tippfehler davon entfernt, das eine für das andere zu lesen. Perimeter sind Verzeichnisse, und das Werkzeug sollte sich weigern, über sie hinweg zu vergleichen oder zu promoten, damit der Fehler unmöglich ist und nicht bloß unerwünscht.

Über die Kunden hinweg sieht das Beratungshaus nur das, was weitergegeben wird: welche checks, welche Scores, welche Aggregatwerte, welche Prompts, wenn die Suite es erlaubt hat. Das reicht, um zu bemerken, dass ein Modell-Update drei Kunden auf einmal verschlechtert hat, und es enthält nichts, woran einer von ihnen Anstoß nehmen würde.

## Wenn der Produktivbetrieb die Suite speist

Die bisherigen Kapitel lassen die Suite auf Fällen laufen, die du geschrieben hast. Der nächste Schritt — und es ist ein Schritt, kein Sprung — besteht darin, dieselben checks auf die Antworten anzuwenden, die das System im Produktivbetrieb gibt, innerhalb des Kunden-Perimeters, und einen Fehlschlag dort in einen Fall in der Suite zu überführen.

Damit schließt sich der Kreis, den Kapitel 2 von Hand verlangt hat: *ein gesehener Fehlschlag, ein geschriebener Fall* wird automatisch. Damit treten zugleich alle Regeln dieses Kapitels in Kraft — das Urteil geht an das Beratungshaus, die Antwort nicht; der Richter läuft dort, wo die Daten sind; der erzeugte Fall hat eine erzeugte ID und eine umgeschriebene Eingabe. Wenn du diese Regeln jetzt einrichtest, an der Suite, die du von Hand ausführst, dann ist die automatische Variante dieselben Regeln auf einer anderen Quelle. Lässt du sie jetzt aus, entdeckst du sie beim ersten Mal, wenn ein erzeugter Fall den Lebenslauf eines Bewerbers in einen Pull Request befördert.

## Heute umsetzen

1. Lege fest, wie die Frage des Kunden lauten wird, und schreibe auf, wo die Antwort liegt. Lautet die Antwort „in einem abonnierten Dashboard“, dann hast du keine Antwort.
2. Markiere jeden check in deiner Suite: Zitiert seine Begründung die Daten? Wenn ja, sind die Begründungen dieses checks Nutzdaten und dürfen den Perimeter nicht verlassen.
3. Sieh dir deine Fall-IDs an. Wenn eine davon einen Namen, eine Bestellnummer, einen echten Bezeichner enthält — ändere sie jetzt, bevor die Datei irgendwohin geht.
4. Lege Suite und Referenzen jedes Kunden an den eigenen Ort dieses Kunden. Teilen sich heute zwei Kunden ein Verzeichnis, dann trenne sie heute.
5. Führe bei der nächsten Abnahme ein promote aus. Gib dem Kunden den Bericht. Schreibe den Aggregatwert in das Abnahmeprotokoll. Ab diesem Moment hat „Ist es seit der Abnahme schlechter geworden?“ eine Antwort, die beide Seiten prüfen können.

---

Das ist das Handbuch. Wenn du es von vorn bis hinten gelesen hast, weißt du mehr darüber, ein LLM-Feature unter Kontrolle zu halten, als die meisten Teams, die eines ausliefern. Das Werkzeug, das um diese acht Kapitel herum gebaut ist, ist [digline](../../index.md); das Projekt, aus dem die meisten Zahlen stammen, ist [öffentlich](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f). Keines von beiden brauchst du für den Anfang — die zwanzig Fälle schon.
