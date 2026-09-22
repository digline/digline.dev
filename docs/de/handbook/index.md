---
title: Handbuch
seo_title: 'Handbuch: ein LLM-Feature unter Kontrolle behalten'
lang: de
translation_of: handbook/index.md
description: 'Neun Kapitel zur Bewertung von LLM-Anwendungen in der Praxis: was zuerst zu bauen ist, Fälle, Ground Truth, checks, der Richter, die Referenz, Wartung. Über das Problem, nicht über das Werkzeug.'
search:
  exclude: true
source: handbook/index.md
source_sha: 102161a61926
source_commit: c51c251
model: claude-opus-5
---

# Handbuch

Neun Kapitel darüber, wie du ein LLM-Feature unter Kontrolle behältst — für
alle, die eines in Produktion haben und die schlimme Woche noch nicht hinter
sich haben. Es geht um das Problem, nicht um das Werkzeug: nichts davon setzt
eine Installation von digline voraus, und die meisten Zahlen stammen aus einem
kleinen öffentlichen Projekt, das du nachlesen kannst. Fang beim ersten Kapitel
an und lies sie der Reihe nach — jedes baut auf dem vorherigen auf.

- **[0. Vor dem Prompt](../../handbook/00-before-the-prompt.md)** — die vier
  Entscheidungen, die vor dem Prompt kommen und darüber entscheiden, ob das
  Feature überhaupt messbar ist. Das eine Kapitel, das dich bittet, zu ändern,
  was du baust, statt es zu messen.
- **[1. Was du tatsächlich auslieferst](../../handbook/01-what-you-are-shipping.md)** — warum
  ein Modellaufruf wie eine Funktion aussieht und keine ist, und was dich das
  kostet.
- **[2. Fälle: das Kapital, das niemand aufbaut](../../handbook/02-cases.md)** — jedes Team hat
  einen Prompt, fast keines hat Fälle. Was ein Fall ist und wie du bis heute
  Nachmittag zwanzig davon hast.
- **[3. Ground Truth: wenn dir niemand eine gibt](../../handbook/03-ground-truth.md)** —
  woher die richtigen Antworten kommen, wenn es keine gelabelten Daten gibt, und
  warum sich das entscheidet, während du das Feature schreibst.
- **[4. Checks: erst deterministisch, der Richter zuletzt](../../handbook/04-checks.md)** — wie
  aus einer Ausgabe ein Urteil wird, und die Regel, die am meisten Zeit spart:
  lass ein Modell nur das beurteilen, was sonst nichts beurteilen kann.
- **[5. Der Richter](../../handbook/05-the-judge.md)** — die zwei Arten von Rauschen, warum du
  das des Richters messen musst, bevor du das deines Systems lesen kannst, und
  das Verfahren, das Raten durch eine Zahl ersetzt.
- **[6. Die Referenz](../../handbook/06-the-reference.md)** — ein Schwellenwert ist keine
  Referenz. Die eine Zahl, die du festhältst und an der du dich messen lässt.
- **[7. Wartung](../../handbook/07-maintenance.md)** — wann die Suite läuft, was dich hinsehen
  lassen sollte, und was an dem Morgen zu tun ist, an dem sie rot wird und du
  nichts geändert hast.
- **[8. Für Teams, die für andere entwickeln](../../handbook/08-for-teams-building-for-others.md)**
  — dieselbe Suite mit zwei weiteren Aufgaben, wenn das LLM-Feature einem Kunden
  gehört, und die eine Regel, von der nicht abgewichen werden darf.
