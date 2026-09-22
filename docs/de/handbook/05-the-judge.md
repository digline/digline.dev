---
seo_title: Der Richter und wie du sein Rauschen misst
lang: de
translation_of: handbook/05-the-judge.md
description: Auch ein LLM-Richter zieht Stichproben. Warum du das Rauschen des Richters messen musst, bevor du das deines Systems ablesen kannst, und das Verfahren, das Raten durch eine Zahl ersetzt.
search:
  exclude: true
source: handbook/05-the-judge.md
source_sha: ba60264b1a69
source_commit: 340f1dd
model: claude-opus-5
---

# 5. Der Richter

Kapitel 4 endete mit einer Regel: höchstens ein durch einen Richter bewerteter check, mit Stichproben und einer gemessenen Toleranz. In diesem Kapitel geht es um das Wort *gemessen* — darum, was passiert, wenn du es überspringst, und um das Verfahren, das Raten durch eine Zahl ersetzt. Die Messwerte stammen aus den sechs runs, die der [Newsletter-Richter](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/README.md) veröffentlicht, und du kannst sie nachrechnen.

## Zwei Arten von Rauschen, nicht eine

Es gibt zwei Stellen, an denen ein Modell seine Meinung ändern kann, und sie erfordern unterschiedliche Gegenmittel.

**Das getestete System** ist ein Modell. Frag es zweimal dasselbe, und es kann unterschiedlich antworten. Im Newsletter-Projekt *ist* der Richter das System: Er bewertet Artikel. Lass die Suite zweimal laufen, im Abstand von fünfzehn Minuten, ohne dass sich etwas geändert hat, und bei einem von einundzwanzig Artikeln ändert sich das Urteil.

**Der Richter** — das Modell, das du innerhalb eines check verwendest, um eine Ausgabe zu bewerten — ist ebenfalls ein Modell und kippt ebenfalls. Wenn deine Rubrik fragt „Ist diese Antwort höflich?“, sagt der Richter zur selben Antwort heute vielleicht 0.8 und morgen 0.7.

Das Gegenmittel für das Erste ist, das *System* pro Fall mehrfach zu fragen und die Antworten zusammenzufassen. Das Gegenmittel für das Zweite ist, den *Richter* pro Ausgabe mehrfach zu fragen und zusammenzufassen. Sie sehen gleich aus und sind es nicht: Das Erste misst, wie stabil dein Produkt ist, das Zweite, wie stabil dein Maßstab ist. Sie zu verwechseln heißt, den Maßstab zu reparieren, wenn das Produkt schwankt, oder umgekehrt. Entscheide, welches von beiden du vor dir hast, bevor du irgendetwas anfasst.

## Was dich eine einzelne Stichprobe kostet

Ein Urteil aus einer Stichprobe ist eine einzelne Ziehung. Bei einem Fall, den der Richter leicht findet, fällt die Ziehung fast immer gleich aus; bei einem Grenzfall ist sie ein Münzwurf, und jede reale Fallsammlung enthält ein paar Grenzfälle. Bei einem binären check ohne Toleranz ist jeder Wurf, der anders ausfällt, eine Regression: Der Vergleich wird rot, die CI schlägt fehl, jemand geht der Sache nach, und es war nichts.

Ein paar davon genügen, damit ein Team die Alarme nicht mehr liest. Das sind die wahren Kosten einer einzelnen Stichprobe: nicht die falsche Zahl, sondern der Moment, in dem das Rot nichts mehr bedeutet.

## Stichproben

Die Abhilfe besteht darin, mehr als einmal zu fragen und zusammenzufassen. Die Newsletter-Suite fragt fünfmal pro Fall; damit wird aus dem binären Urteil ein Bruchteil — 0, 0.2, 0.4, 0.6, 0.8 oder 1 — und aus dem check die Aussage „Der Richter stimmt in mindestens drei von fünf Stimmen mit dem Leser überein“.

Mit Stichproben kommen drei Fragen, und die Antworten sind wichtiger als die Zahl fünf:

**Wie zusammenfassen?** Der Score ist der Mittelwert der Stichproben. Die interessante Größe ist aber die *Übereinstimmung*: wie viele Stichproben das Mehrheitsurteil teilen. Nimm erfundene Scores: Drei Stichproben mit 0.80, 0.85, 0.99 weichen deutlich voneinander ab und stimmen im Urteil vollständig überein; drei mit 0.69, 0.71, 0.70 liegen nicht mehr als zwei Hundertstel auseinander und teilen sich bei einem Schwellenwert von 0.70 im Verhältnis zwei zu eins. Die Übereinstimmung sieht den zweiten Fall; der Mittelwert nicht.

**Was, wenn sie sich nicht einig werden?** Dann war das Urteil nicht möglich, und die ehrliche Antwort lautet *konnte nicht beurteilt werden* — ein dritter Zustand, weder bestanden noch durchgefallen. Ein Fall, dessen Stichproben sich drei zu zwei aufteilen, ist keine Regression und kein Erfolg; er ist ein Fall, den der Richter nicht entscheiden kann, und eine Referenz, die darauf aufbaut, wäre eine Referenz auf einen Münzwurf. Lege eine Mindestübereinstimmung fest, unterhalb derer das Urteil ein Fehler ist, und weigere dich, einen run zu promoten, der einen solchen Fall enthält — aber lege sie so fest, dass sie auch auslösen kann. Bei fünf Stichproben beträgt die Mehrheit immer mindestens drei, also lehnt `"3/5"` nie eine Abstimmung ab, in der jede Stichprobe beurteilt wurde; die Untergrenze, die eine Aufteilung von drei zu zwei erfasst, ist `"4/5"`.

**Schreibe Brüche als Brüche.** „Zwei von drei“ als `0.67` geschrieben ist eine Falle: ⅔ ist 0.666…, also *kleiner* als 0.67, und jeder Fall mit einer Gegenstimme von dreien wird zum Fehler. `"2/3"` sagt, was du meinst, und kann nicht an einer Rundung scheitern; die Newsletter-Suite schreibt `"3/5"`.

## Die Toleranz messen

Die Toleranz ist die Größe der Änderung, die du als Rauschen zu ignorieren bereit bist. Alle wählen sie nach Gefühl; fast alle wählen sie falsch, denn das Rauschen eines Richters lässt sich von außen nicht erraten. Messen lässt es sich, in drei runs:

1. Friere alles ein — Prompt, Modell, Fälle.
2. Lass die Suite dreimal laufen.
3. Sieh dir für jeden Fall die größte Differenz zwischen zwei beliebigen runs an.
4. Die Toleranz ist diese größte Differenz plus ein wenig Spielraum.
5. Ist diese Zahl so groß wie die Unterschiede, die du *erkennen* willst, dann halte an: Der check ist zu verrauscht für ein gate. Nimm mehr Stichproben oder ändere den check — weite die Toleranz nicht aus, bis sie alles verschluckt.

So sieht das beim Newsletter-Richter aus: sechs runs, fünf Stichproben pro Fall, mit denselben Prompts, denselben Fällen und derselben Konfiguration. Jede Zelle gibt an, wie viele der fünf Stichproben mit dem Leser übereinstimmten; die Zeiten sind UTC.

| Fall | 1. Sep. 12:29 | 1. Sep. 12:44 | 3. Sep. 06:14 | 3. Sep. 06:18 | 3. Sep. 06:24 | 3. Sep. 06:30 |
|---|---|---|---|---|---|---|
| evals-skills-for-coding-agents | 2 | 5 | 5 | 2 | 5 | 5 |
| more-than-just-code-review | 4 | 5 | 5 | 2 | 5 | 5 |
| controlling-reasoning-effort-in-llms | 5 | 4 | 3 | 5 | 5 | 4 |
| recent-developments-in-llm-architectures | 5 | 4 | 5 | 3 | 5 | 4 |
| die anderen siebzehn | höchstens zwei Stimmen Unterschied, und die Mehrheit ändert sich nie | | | | | |

Zwei Fälle schwankten bei unverändertem System um drei von fünf Stimmen, und in jedem einzelnen run waren zwischen zwei und sechs der einundzwanzig Fälle gespalten. Für einen einzelnen Fall gilt damit Schritt 5: Eine Toleranz, die drei Stimmen aufnimmt, wäre so breit wie jede Änderung an diesem Fall, deren Erkennung sich lohnt. Die Suite legt zwei Stimmen pro Fall fest und lässt einen Ausschlag von drei Stimmen sichtbar werden. Die Tabelle pro Fall ist trotzdem nützlich: Sie sagt dir genau, bei welchen Fällen sich der Richter unsicher ist.

## Der Aggregatwert ist ruhiger als die Einzelfälle

Dieselben runs zeigten etwas, das ändert, worauf du einen Schwellenwert legst. Während einzelne Fälle um drei von fünf Stimmen sprangen, lag die Zahl der Artikel, bei denen Richter und Leser übereinstimmten, über die sechs runs hinweg bei 15, 16, 16, 14, 16 und 16 von 21 — nie mehr als zwei auseinander.

Das ist das allgemeine Muster, und es ist der Grund, warum eine Suite mit gelabelten Fällen das gate auf einen Aggregatwert legen sollte — Precision, Accuracy, Recall — und die Urteile pro Fall zur Diagnose nutzen sollte. Ein Schwellenwert von 60 % Übereinstimmung hätte bei keinem der sechs ausgelöst. Gegenüber der Referenz, die das Projekt führt, wurde der check pro Fall mit seinen zwei Stimmen Toleranz bei zwei der anderen fünf rot.

## Der Prompt des Richters ist ein Prompt

Er driftet aus denselben Gründen wie deiner und verdient dieselbe Behandlung: eine Datei, versioniert, bei jedem run mitgeschrieben. Wenn ein durch einen Richter bewerteter check zu scheitern beginnt, lautet die erste Frage nicht „Ist das System schlechter geworden?“, sondern „Hat sich der Maßstab geändert?“ — und wenn der Prompt des Richters ein String irgendwo in einer Funktion ist, kannst du sie nicht beantworten.

Zwei kleinere Gewohnheiten. Erstens: Stelle im Prompt des Richters die Anweisung vor die Ausgabe und kennzeichne die Ausgabe deutlich; ein Richter, der eine Anweisung nach dem Text liest, den er beurteilen soll, beurteilt manchmal die Anweisung. Zweitens: Wenn du deine Suite mit einem Fake-Richter testest — und das solltest du —, baue den Fake aus einer *echten* Antwort, nicht aus dem, was du für die Antwort hältst. Ein Fake, der aus dem Code heraus geschrieben ist, bestätigt den Code; im Newsletter-Projekt [wurden Kosten um den Faktor 384 zu niedrig gezählt](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/README.md#the-fake-judge-and-ci), bei durchweg grünen Tests, weil Fake und Code dieselbe falsche Annahme über die Form der API teilten.

## Heute umsetzen

1. Entscheide, welches Rauschen du vor dir hast: das des Systems oder das des Richters.
2. Zieh Stichproben daraus — die Newsletter-Suite fragt fünfmal — und lege eine Mindestübereinstimmung fest, unterhalb derer das Urteil *konnte nicht beurteilt werden* lautet.
3. Friere alles ein und lass es dreimal laufen. Lies die größte Differenz pro Fall ab. Das ist deine Toleranz — oder dein Signal, mehr Stichproben zu ziehen.
4. Wenn du Labels hast, setze das gate auf den Aggregatwert.
5. Verschiebe den Prompt des Richters in eine Datei neben die des Systems und schreibe bei jedem run beide mit.

Im nächsten Kapitel geht es darum, was zu tun ist, sobald die Zahlen stabil sind: der run, den du freigibst, und warum er der Median aus mehreren sein sollte und nicht der erste grüne.
