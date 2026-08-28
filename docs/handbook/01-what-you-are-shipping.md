---
seo_title: >-
  What you are actually shipping
description: >-
  A model call looks like a function and is not one: the same prompt,
  sampled twice, gives two answers. What that costs you, and why ordinary
  tests cannot see it.
---

# 1. What you are actually shipping

If you come from ordinary software, the first thing to unlearn is what a function is.

## A function, and the thing that looks like one

For thirty years, this has been true: given the same input, the same code produces the same output. Everything in software engineering rests on it — tests, debugging, code review, "it works on my machine". You can reason about a function because it is a fixed mapping from inputs to outputs.

A call to a language model looks like a function. It has an input (the prompt) and an output (the completion). It sits in your code between two ordinary functions. It is not one.

A language model produces a *probability distribution* over possible next tokens, and then samples from it. The sampling is the point: it is what lets the same model write a poem and a SQL query. It also means that the same prompt, sent twice, can come back with two different answers — and both are "correct" in the only sense the model knows, which is that both were likely.

You can turn the temperature to zero and reduce the variation. You cannot remove it, and for most useful tasks you do not want to: a model at temperature zero is worse at exactly the things you bought it for.

## What this does to your intuitions

**"I tried it and it works."** You ran it once. You drew one sample from the distribution. The next sample may differ. In the [newsletter judge](https://github.com/digline/brief) this handbook uses as its running example, the same twenty-one articles scored twice with an identical prompt produced twenty identical verdicts and one different one. One in twenty-one is not a bug. It is the shape of the thing.

**"I fixed the prompt."** You changed the distribution. It now produces the answer you wanted for the input you tried. It also produces slightly different answers for every other input, and you have not looked at those. Prompt changes are global; your attention was local.

**"Nothing changed, so it still works."** Your code did not change. The model behind the API did — providers update, retrain, deprecate, and re-point aliases without a changelog you will read. Your git history says the system is unchanged. Your users say it got worse. Both are right.

**"It's above the threshold."** A threshold catches *below the line*. It does not catch *worse than last month*. A score that drifts from 0.91 to 0.78 is still above 0.7, still green, and thirteen points worse to the person receiving the answer.

## What you are actually shipping, then

Not a function. A system whose behaviour is a distribution, that drifts on its own, that changes globally when you edit it locally, and that nobody in your team has seen more than a handful of samples from.

That sounds alarming. It is manageable — but only with tools that match the thing, and the tools of ordinary software do not. `assert output == expected` is meaningless against a distribution. Code review cannot see a change that happened on the provider's side. A demo proves one sample.

What matches the thing is what you would do with any other measurement that has noise in it: take several samples, compare against a recorded reference, and treat a change as real only when it is larger than the noise. That is not a new idea. It is how a laboratory works. It is just not how software teams have been taught to work, because until recently nothing in the stack behaved like this.

## The four things you need

Everything in the rest of this handbook comes down to four things, and the order matters:

1. **Cases** — a set of inputs you care about, with what you know about the right answers. Held out from the prompt. Growing over time. This is the asset, and [chapter 2](02-cases.md) is about it.
2. **Checks** — what you verify on each output. The ones that need no model come first; the ones that need a judge come last, because a judge is another distribution. [Chapter 3](03-checks.md), [chapter 4](04-the-judge.md).
3. **A reference** — a run you looked at and approved, recorded with the prompt and the commit that produced it, so that every future run has something to be compared against. [Chapter 5](05-the-reference.md).
4. **A routine** — when to run, what triggers a look, what to do when the comparison turns red. [Chapter 6](06-maintenance.md).

If you build software for someone else, there is a fifth thing — what you can show the customer, and what must never leave their perimeter — in [chapter 7](07-for-teams-building-for-others.md).

## One habit before you read on

Open the project where you have an LLM call. Find the input you tested it with when you built it. Send it again, now, five times.

If all five answers are the same, good — you have a low-noise task, and you will find the rest of this handbook easy. If they differ, you have just seen the thing this chapter is about, on your own system, in a minute. Either way you now know something you did not know before you ran it, which is the whole idea.

---

*Next: [2. Cases: the asset nobody builds](02-cases.md)*
