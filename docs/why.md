---
title: Why
template: why.html
seo_title: >-
  Why LLM applications need a baseline
description: >-
  A prompt is not code, and the model moves under you. Why a pass/fail
  threshold cannot see a quality regression, and what an approved baseline
  measures instead.
---

# Why

If you have put a language model into something people use, this page is about a problem you already have. You may not have noticed it yet. That is the problem.

The examples below come from a real, public project: a small program that reads a few AI newsletters every morning and asks a model which articles deserve twenty minutes of a person's time. It is about as simple as an LLM application gets. Everything on this page happened to it.

## A prompt is not code

When you change a line of code, the same input produces the same output, every time. That is what makes tests possible: you write down what should come out, and the machine tells you whether it did.

A prompt does not work like that. Ask the same model the same question five times, same prompt, same article, and it does not always answer the same way. Every run of the newsletter judge asks each of twenty-one articles five times. In two to six of them, depending on the run, the five answers disagree with each other. Nothing changed between those five: not the code, not the model, not the input. The model is a probability distribution, and you are sampling from it.

But it means the ordinary reflex — *run it once, it looks right, ship it* — is not a test. It is one sample.

## The model changes under you

Even if you never touch a line, the thing you built on is moving.

Providers update models. They deprecate versions. They change what a default alias points to. A model named `latest` in March is not the same model in June, and nothing in your repository records that it changed. Your commit history says "no changes since the release"; your users say "it got worse last week"; both are telling the truth.

This is the failure that no code review can catch, because there is no diff. The only way to see it is to have something to compare against — a record of how the system behaved on a set of inputs, on a date, under a version — and to run the same inputs again and look at the difference.

## "It works" is not a measurement

Most teams do have a threshold somewhere: a score below 0.7 fails, above passes. It is better than nothing, and it misses the failure that matters most.

Here is the shape of it, with made-up numbers. A check scores 0.91 on the day you ship. Three weeks and two prompt tweaks later it scores 0.78. Still above 0.7. Still green. Still passing every test you have. And the users have already started to feel it, because a drop of thirteen points is a different product to the person on the other end.

A threshold catches *below the line*. It does not catch *worse than it was*. For that you need a reference — the approved state, recorded — and a comparison against it on every change. The reference is the piece almost every team is missing, and it is the reason the drift from 0.91 to 0.78 is invisible to them until a customer names it.

## Who judges the judge

For anything that cannot be checked by exact match — is this answer polite, does it stay on policy, does it summarise faithfully — the practical tool is another model acting as a judge. It works. It also inherits every problem above: the judge samples too, and it changes its mind.

In the newsletter project the judge votes five times per article and the majority decides. Two runs fifteen minutes apart, same prompt: on one article out of twenty-one the majority flipped, from two votes out of five to five out of five. And the articles that split are not the same ones each run: across the six published runs, eleven of the twenty-one split at least once, one of them in five runs, four of them only once. Ten never split at all. Those eleven are the borderline ones, and a five-vote majority is a thin thing to hang a decision on.

It isn't only my experience. Dan Luu had the same Senior SWE-Bench outputs graded ten more times and the tastefulness verdict disagreed with the official one 23% of the time, on identical input ([exercise 7](https://danluu.com/exercise-7/)). I applied the same reading to my own judges: [Bad evals, my own](blog/bad-evals-my-own.md). The judge is an instrument. An instrument gets calibrated.

Two consequences follow. First, you cannot know whether your *system* got worse until you know how much your *judge* wobbles on its own — the noise floor has to be measured before anything else is. Second, a single case is a bad unit for a decision. Across that pair of runs the aggregate moved by one article out of twenty-one, while the article itself moved by three votes out of five. Individual cases are for diagnosis. The aggregate is what you can put a threshold on.

## The customer's question

If you build LLM features for your own product, everything above is a quality problem. If you build them for someone else — a client, a customer, a regulated business — it is also a contractual one, and the question arrives in a specific form:

*What did you test, when, under which version, and who approved it?*

A dashboard does not answer that. A dashboard shows today. The question is about a date, a commit, an artefact someone can open six months later. The answer has to be a file: this suite, this reference, this comparison, this approval — in the repository, next to the code it describes, with the prompt text that produced it. If it lives on a vendor's server, it is not yours to show; if it lives only in someone's memory, it does not exist.

For the customer, the same file is the proof that the thing they paid for still does what it did on the day they accepted it. That is worth more to them than any metric.

## What "under control" means

Put the pieces together and "under control" turns out to be three concrete things, none of them expensive:

**A reference.** A run of your suite that you looked at and approved — scores, prompt text, commit — recorded as a file and committed. Not the first green run: the median of a few, because you now know the judge wobbles.

**A comparison on every change.** Change the prompt, the model, the retrieval, anything: run the suite again and compare with the reference. Not "is it below the threshold" but "is it worse than it was, where, by how much" — with the diff of the prompt right next to the scores it moved. In CI, so it happens whether you remember or not; on a schedule, so it happens when the provider changes something and you did not.

**A history.** Every reference you ever approved, in git, with the reasons. When someone asks the customer's question, the answer is a `git log`.

In the newsletter project a run costs about seven cents: twenty-one articles, judged five times each. The project has a number it can state, with the runs to back it: the judge agrees with the reader on 16 of 21 articles in four of the six published runs, and on 15 and 14 in the other two.

That is what [digline](index.md) does, and it is all it does. The reference lives in your repository. Nothing leaves your machine. `pip install digline` to try it; the newsletter project is [public](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) if you want to see the real thing first.

Where these numbers come from: six runs of the newsletter judge, committed as [fixtures](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures), [with a note on which number comes from which run](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/README.md), and [a script](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/recompute.py) that recomputes every number in this page from them.

---

If you have thirty minutes instead of five: the [Handbook](handbook/01-what-you-are-shipping.md).

Wondering how this differs from the tools you already know? See [How digline compares](comparison/index.md).
