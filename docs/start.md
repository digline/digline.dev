---
title: Start here
description: >-
  What an LLM regression is, why ordinary tests don't catch it, and what
  digline does about it — in plain language.
---

# Start here

If you already know what a silent regression is, skip to the [Guide](product/guide.md). This page is for everyone else.

## The problem, in one story

I run a small script that reads a few hundred AI articles every morning and asks a language model to pick the five worth reading. It worked. Then one day it started skipping the good ones.

Nothing had crashed. No test had failed. The code was the same as the week before. What had changed was the *behaviour* of the model — a prompt tweak here, a model update there — and behaviour is not something a unit test checks. The script still returned five articles. They were just the wrong five.

That is an **LLM regression**: your system still runs, still answers, still passes its tests, and is quietly worse than it was.

## Why your tests don't see it

Ordinary tests compare an output with an expected value. A language model doesn't give you an expected value. Ask it the same question twice and you may get two different answers, both acceptable. So teams either stop testing the model's behaviour, or they write a test that passes today and can't tell you anything about tomorrow.

The practical questions turn out to be:

- Compared to *what*? You need a reference — the behaviour you last accepted.
- Worse by *how much*? A score that moves from 0.88 to 0.86 may be noise. From 0.88 to 0.73 is a regression. Without knowing how much the system wobbles on its own, you can't tell the two apart.
- Who decides what "right" means, and where is that decision written down?

## What digline does

digline is a gate you put in front of that question. You write down, once, what you expect from your system as a set of checks — deterministic ones (the answer is valid JSON, contains no phone numbers, mentions the customer's name) and judged ones (a second model rates the answer against a rubric). You run them against your system. When you're happy with the result, you **promote** it: it becomes the baseline, a file committed in your repository next to the code.

From then on, every run is compared with that baseline, and the report answers the only question that matters:

> Nothing got worse compared with the reference. 2 checks moved within noise. Every case could be judged. 1 case is suspended. The suite is unchanged from the reference. 1 file under test changed since the reference.

or

> 14 checks got worse compared with the reference. 7 cases could not be judged. No case is suspended. The suite is unchanged from the reference. The files under test are the same as the reference.

The baseline is a file in git. It has history, it can be diffed, and nobody promotes it but you. There is no dashboard to log into and no service that receives your data — digline runs where your code runs.

## Thirty seconds, with pictures

<video controls preload="none" poster="assets/video/ep01-poster.jpg"
       width="1920" height="1080"
       style="width:100%; height:auto; aspect-ratio:16/9; background:#0f1117">
  <source src="assets/video/ep01.mp4" type="video/mp4">
  Your browser does not support the video tag. <a href="assets/video/ep01.mp4">Download the video</a>.
</video>

*Episode 1 of a short series on LLM regression. Served from this site — no third-party player, no cookies.*

## Where to go next

- [Why](why.md) — the reasoning behind the design, if you want to argue with it.
- [Guide](product/guide.md) — install it and get your first `compare` in a few minutes.
- [How digline compares](comparison.md) — if you're already using an eval tool and want to know what's different.

Ten words you'll meet along the way: **run**, **baseline**, **compare**, **promote**, **check**, **judge**, **tolerance**, **noise floor**, **regression**, **gate**. Each is explained the first time it appears in the Guide.
