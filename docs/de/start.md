---
title: Hier anfangen
template: start.html
lang: de
translation_of: start.md
description: Was eine LLM-Regression ist, warum normale Tests sie nicht erkennen und was digline dagegen tut — in einfachen Worten.
search:
  exclude: true
source: start.md
source_sha: f1b884ed9bca
source_commit: 200f768
model: claude-opus-5
---

# Hier anfangen

Wenn du schon weißt, was eine stille Regression ist, springe direkt zum [Guide](../product/guide.md). Diese Seite ist für alle anderen.

## Das Problem in einer Geschichte

Ich betreibe ein kleines Skript, das jeden Morgen ein paar hundert KI-Artikel liest und ein Sprachmodell die fünf auswählen lässt, die sich zu lesen lohnen. Es funktionierte. Dann ließ es eines Tages die guten aus.

Nichts war abgestürzt. Kein Test war fehlgeschlagen. Der Code war derselbe wie in der Woche davor. Geändert hatte sich das *Verhalten* des Modells — hier eine kleine Änderung am Prompt, dort ein Modell-Update — und Verhalten ist nichts, was ein Unit-Test prüft. Das Skript gab weiterhin fünf Artikel zurück. Nur eben die falschen fünf.

Das ist eine **LLM-Regression**: Dein System läuft noch, antwortet noch, besteht noch seine Tests — und ist unbemerkt schlechter als vorher.

## Warum deine Tests das nicht sehen

Normale Tests vergleichen eine Ausgabe mit einem erwarteten Wert. Ein Sprachmodell liefert keinen erwarteten Wert. Stelle ihm zweimal die gleiche Frage, und du bekommst möglicherweise zwei verschiedene Antworten, die beide in Ordnung sind. Also testen Teams das Verhalten des Modells entweder gar nicht mehr, oder sie schreiben einen Test, der heute besteht und dir über morgen nichts sagen kann.

Die praktischen Fragen lauten dann:

- Verglichen *womit*? Du brauchst eine Referenz — das Verhalten, das du zuletzt akzeptiert hast.
- *Wie viel* schlechter? Ein Wert, der von 0.88 auf 0.86 wandert, kann Rauschen sein. Von 0.88 auf 0.73 ist eine Regression. Ohne zu wissen, wie stark das System von sich aus schwankt, kannst du beides nicht unterscheiden.
- Wer entscheidet, was „richtig“ heißt, und wo ist diese Entscheidung festgehalten?

## Was digline macht

digline ist ein gate, das du vor diese Frage stellst. Du schreibst einmal auf, was du von deinem System erwartest, und zwar als Satz von checks — deterministische (die Antwort ist gültiges JSON, enthält keine Telefonnummern, nennt den Namen des Kunden) und bewertete (ein zweites Modell beurteilt die Antwort anhand einer Rubrik). Du führst sie auf deinem System aus. Wenn dir das Ergebnis gefällt, gibst du es mit **promote** frei: Es wird zur baseline — eine Datei, die neben dem Code in dein Repository eingecheckt wird.

Von da an wird jeder run mit dieser baseline verglichen, und der Bericht beantwortet die einzige Frage, auf die es ankommt. Hier ist ein run, bei dem nichts schlechter geworden ist, obwohl sich drei checks bewegt haben und ein Fall nicht entschieden werden konnte:

<!-- digline: a comparison where nothing got worse -->

und hier einer, bei dem sechs checks schlechter geworden sind:

<!-- digline: a comparison where something did -->

Beides ist die Ausgabe von `digline compare` auf der Beispiel-Suite aus dem ersten Kapitel des [Guide](../product/guide.md), aufgenommen aus dem Release, aus dem diese Dokumentation stammt. Die Zahlen sind die, die diese runs gemessen haben.

Die baseline ist eine Datei in git. Sie hat eine Historie, sie lässt sich diffen, und niemand außer dir gibt sie frei. Es gibt kein Dashboard, in das man sich einloggen muss, und keinen Dienst, der deine Daten erhält — digline läuft dort, wo dein Code läuft.

## Dreißig Sekunden, mit Bildern

<video controls preload="none" poster="/assets/video/ep01-poster.jpg"
       width="1920" height="1080"
       style="width:100%; height:auto; aspect-ratio:16/9; background:#0f1117">
  <source src="/assets/video/ep01.mp4" type="video/mp4">
  Dein Browser unterstützt das video-Tag nicht. <a href="/assets/video/ep01.mp4">Video herunterladen</a>.
</video>

*Folge 1 einer kurzen Reihe über LLM-Regression. Ausgeliefert von dieser Seite — kein Drittanbieter-Player, keine Cookies.*

## Wie es weitergeht

- [Warum](../why.md) — die Überlegungen hinter dem Entwurf, falls du darüber streiten willst.
- [Guide](../product/guide.md) — installieren und in wenigen Minuten zum ersten `compare` kommen.
- [digline im Vergleich](../comparison/index.md) — wenn du schon ein Eval-Tool nutzt und wissen willst, was anders ist.

Zehn Wörter, die dir unterwegs begegnen: **run**, **baseline**, **compare**, **promote**, **check**, **judge**, **Toleranz**, **noise floor**, **Regression**, **gate**. Jedes wird beim ersten Auftreten im Guide erklärt.
