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

A prompt does not work like that. Send the same article to the same model with the same prompt, and one morning it scores 4, the next morning 3. Nothing changed — not your code, not the model, not the input. The model is a probability distribution, and you are sampling from it.

In our newsletter judge, out of twenty-one articles scored twice with an identical prompt, one changed its verdict. That is not a bug in the judge. It is what a judge is. But it means the ordinary reflex — *run it once, it looks right, ship it* — is not a test. It is one sample.

## The model changes under you

Even if you never touch a line, the thing you built on is moving.

Providers update models. They deprecate versions. They change what a default alias points to. A model named `latest` in March is not the same model in June, and nothing in your repository records that it changed. Your commit history says "no changes since the release"; your users say "it got worse last week"; both are telling the truth.

This is the failure that no code review can catch, because there is no diff. The only way to see it is to have something to compare against — a record of how the system behaved on a set of inputs, on a date, under a version — and to run the same inputs again and look at the difference.

## "It works" is not a measurement

Most teams do have a threshold somewhere: a score below 0.7 fails, above passes. It is better than nothing, and it misses the failure that matters most.

Here is the shape of it. A check scores 0.91 on the day you ship. Three weeks and two prompt tweaks later it scores 0.78. Still above 0.7. Still green. Still passing every test you have. And the users have already started to feel it, because a drop of thirteen points is a different product to the person on the other end.

A threshold catches *below the line*. It does not catch *worse than it was*. For that you need a reference — the approved state, recorded — and a comparison against it on every change. The reference is the piece almost every team is missing, and it is the reason the drift from 0.91 to 0.78 is invisible to them until a customer names it.

## Who judges the judge

For anything that cannot be checked by exact match — is this answer polite, does it stay on policy, does it summarise faithfully — the practical tool is another model acting as a judge. It works. It also inherits every problem above: the judge samples too, and it changes its mind.

In the newsletter project, once the judge was sampled several times per article instead of once, the picture got clearer and more uncomfortable at the same time. Most articles were judged the same way every time. Six out of twenty-one were not: on those, a five-vote judge would split 3–2 one run and 4–1 the next. Those six were exactly the articles a human would also have hesitated over. The judge was not broken; it was honest about the borderline.

Two consequences follow. First, you cannot know whether your *system* got worse until you know how much your *judge* wobbles on its own — the noise floor has to be measured before anything else is. Second, a single case is a bad unit for a decision. Across those same runs, the aggregate — how many articles the judge and the human agreed on — moved by one case out of twenty-one while individual cases swung by three votes. Individual cases are for diagnosis. The aggregate is what you can put a threshold on.

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

In the newsletter project, all of this costs about eight cents per run. Four experiments on the judge's prompt, one calibration, and the project has a number it can state — "agrees with the reader on 62% of borderline articles, stable across runs" — and a file that says which prompt produced it.

That is what [digline](index.md) does, and it is all it does. The reference lives in your repository. Nothing leaves your machine. `pip install digline` to try it; the newsletter project is [public](https://github.com/digline/brief) if you want to see the real thing first.

---

If you have thirty minutes instead of five: the [Handbook](handbook/01-what-you-are-shipping.md).

Wondering how this differs from the tools you already know? See [How digline compares](comparison.md).
