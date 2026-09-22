---
seo_title: >-
  Before the prompt: building a feature that can be measured
description: >-
  Four decisions come before the prompt and decide whether an LLM feature
  can be evaluated at all: emit the decision as a structure, make the input
  deterministic, record every call, and store a failure as a failure.
---

# 0. Before the prompt

The prompt is the middle of the work, not the start of it. Four decisions come before it, each one cheap on the afternoon you take it and close to unrecoverable once the feature is in production — and together they decide whether anything else in this handbook can be done at all.

## Why the order comes out wrong

The usual order is to write the prompt, ship, and deal with the rest when somebody complains. It looks like starting with the hard part. It is starting with the only soft part: the prompt stays cheap to change, and everything around it sets. The shape of the reply becomes the contract the renderer, the client and the stored rows are written against, and the rows already written are the rows you have. So attention goes to the part that will still be cheap in a year, and skips the four that will not.

What follows is the common shape of an LLM feature in production, read off one system's code rather than measured against it: code assembles a context, one model call decides what to say, prose comes back. [Chapter 3](03-ground-truth.md) takes that system apart from the other end and asks where its ground truth could come from. This is the list of decisions that would have given it one. Nothing here is a number — nothing has been run.

That reading was a reading, and there is no artefact behind it: no dated note, no captured repository, nothing to cite. The shape above is what was understood from looking at a system, written down afterwards from memory, and anyone who goes looking for the document it came from will not find one. It is offered as a shape that recurs, not as evidence — every claim in this chapter has to stand on whether you recognise it in your own system, because there is nothing else holding it up.

## 1. Emit the decision, not only the prose

If the feature chooses — which items to mention, which to leave out, in what order — the choosing is the behaviour you will want to measure, and the prose is a rendering of it. A system that returns the ids it chose, in order, beside the sentence it wrote can be asserted on mechanically, and gives a person's judgement something to point at. One that returns only the sentence cannot, whatever you bolt on later: every check you write reads prose, and so does every argument about whether the choice was right.

Today it is a field in the reply and a parse. Later it is the contract between the model and everything downstream, and a contract is the expensive kind of change.

**Where it resists:** not every feature chooses. If what you sell is the prose itself — a rewrite, a translation, a reply in a conversation — there is no selection to emit, and you carry only decisions 3 and 4. Most features are not that: they pick, rank, route or extract, and call the result a summary.

## 2. Make the input deterministic

Same stored data in, same assembled context out. A query that takes the first N rows with no ordering hands that choice to the database, and two runs on unchanged data can differ without the model having changed its mind.

The obvious cost is that there is nothing to freeze, so there is no case. The one that hurts longer is attribution: every difference between two runs has two possible authors and no way to tell them apart, and a red run nobody can attribute is how a team learns to stop reading red.

Today it is an ordering on a query. Later it is that, plus every run recorded before the fix, taken on an input nobody can reproduce.

## 3. Record the call from the first day

The assembled input as the model received it, the reply as it came back, which model answered, and when. Four fields.

This is the one item that serves nothing on the day you write it: no feature reads it, no screen shows it, and it is the first thing questioned in review. It is also the only one that cannot be added late at any price. The others are expensive to retrofit; this one is not retrofittable, because what it would have held is gone.

**Where it resists:** it is not free, and a chapter that said so would be wrong. The assembled input is the data that went in, so the record inherits it, and the rules about where it may live ([chapter 8](08-for-teams-building-for-others.md)): same perimeter, same retention. And take *which model answered* from the reply, not from what you asked for — on the day a provider re-points an alias those are two different facts.

## 4. Make a failure look different from an empty answer

A call that failed and a call that genuinely had nothing to say are two facts. Stored as the same row they become one, and the one they become is the quiet one: an outage reads as a calm morning.

This is the decision that rots the record you have just built: every count taken over those rows reads silence as agreement, and stays wrong for as long as the rows are kept. Nor can they be sorted out afterwards, by date or by inference, for the reason chapter 3 gives about reinterpreting an ambiguous label. They stay ambiguous.

Today it is one more state. Later it is one more state, and none of the history.

## Then the prompt

Now write it, and notice what the four have done: the prompt is the cheapest part of the feature to change, which is where it should have been all along. The structure is the contract, the prompt is how it gets filled, and a better prompt is a diff in one file that nothing downstream has to know about.

## The invariants come before the cases

An invariant is something true of a correct output on every possible day, whatever the data. Chapter 3 lists the ones this shape of feature gets: every id chosen was in the input, the required item appears, an empty input yields an empty selection.

What is worth adding is *when* you can write them. An invariant needs no ground truth, no label, no case and no judge — it is a statement about the system, not about an answer. It is the one check that can exist the day after the prompt, before the work of [chapter 2](02-cases.md) has begun, and the cheapest thing in this handbook. Almost nobody writes them.

## The gesture, where the person already is

Then one gesture, in the path the person is already on, by which they can disagree. Chapter 3 is about what to ask, why the obvious question records two things at once, and how far short of solved that is for a person who is not you.

What comes first is smaller: the gesture needs an object. Without decision 1 there is nothing to attach it to, and a thumbs-down lands on a paragraph — it records that a morning was bad, which is not a fact about any decision the system made. With the structure, the same click lands on an item, in a position, with an id. Build the two in the same week, or the gesture collects the wrong thing for a year.

Only then the suite.

## On one page

```text
What has to be true before the prompt is worth writing?
├── the decision comes back as data ..... the ids it chose, in order, beside the prose
├── the input cannot move on its own .... same data in, same assembled context out
├── every call is written down .......... the input · the reply · which model · when
└── a failure is not an empty answer .... two outcomes, two rows, never one

                                     ── the prompt ──
                   the only part of this you can still change tomorrow

And then, in this order, what those four have made possible:
├── invariants .......................... true on every possible day, no model needed
├── one judgement gesture ............... where the person already is, attached to the ids
└── a suite ............................. cases, checks, a reference → chapters 1 to 8
```

## Doing it today

Seven questions, one per step. Answer them on a whiteboard before a line of the feature is written; the right-hand column is what you are choosing between.

| The question | What it costs to answer it late |
|---|---|
| 1. Does the feature say *which* things it chose, as data, and not only in prose? | Nothing can be asserted on, and no gesture can point at a choice. |
| 2. Given the same stored data, does the same context reach the model? | No input to freeze, so no case — and no red run that can be attributed. |
| 3. Is the assembled input, the reply, the answering model and the time written on every call? | The only one that cannot be added later at any price. |
| 4. Can you tell a failed call from a genuine "nothing to report"? | An outage is stored as a calm morning, and every count over those rows reads silence as agreement. |
| 5. Is the prompt the only thing that has to change when you want a different answer? | The prompt stops being cheap: changing it becomes a change to everything downstream. |
| 6. What is true of a correct output on every possible day, and can it be checked with no model? | You start at the most expensive end, a judge, on a system nobody has shown to be consistent. |
| 7. Where, in what a person already does, could they say this was wrong — and what is that gesture attached to? | The disagreement never arrives, or arrives as a label that means two things. |

The next chapter is about what you have once these are in place, and why the thing at the centre of it looks like a function and is not one.
