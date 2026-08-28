---
seo_title: >-
  Cases: the asset nobody builds
description: >-
  Every team shipping an LLM feature has a prompt and almost none has
  cases. What a case is, and how to have twenty of them by this afternoon.
---

# 2. Cases: the asset nobody builds

Every team that ships an LLM feature has a prompt. Almost none has cases. This chapter is about why that is backwards, and what to do about it — concretely, starting this afternoon.

## What a case is

A case is one input you care about, paired with what you know about the right answer.

That is all. For a support bot: a question a customer actually asked, and whether the reply should have mentioned the refund policy. For a classifier: a job description, and the family a recruiter confirmed it belongs to. For the [newsletter judge](https://github.com/digline/brief) that runs through this handbook: an article title and summary, and whether the reader marked it worth reading.

```json
{
  "id": "2026-08-24-controlling-reasoning-effort-in-llms",
  "vars": {
    "source": "Ahead of AI",
    "title": "Controlling reasoning effort in LLMs",
    "summary": "…the first 400 characters of the article…"
  },
  "expected": { "marked": true }
}
```

Three fields. The `id` names it. The `vars` are what the system receives. The `expected` is what you know. You do not always know the exact right output — for a summary or a free-text answer, nobody does — but you always know *something*: it should mention X, it should not exceed N words, a person you trust rated it acceptable. Whatever you know goes in `expected`. Whatever you do not know, you leave out and check with something weaker.

## Why the prompt gets all the attention and the cases get none

Writing a prompt feels like building. You type, the model answers, you adjust, it answers better. Every iteration is a small reward. Writing cases feels like paperwork: copy an input, decide what the right answer is, save it, repeat. No reward, no visible progress, and the feature already works — you saw it work, you typed the input yourself.

So the prompt gets forty iterations and the cases get zero, and the team ships with a prompt that was tuned against whatever the author happened to type that afternoon. Three months later a user reports something odd. Nobody can say whether it is new, because there is nothing to compare against. The author tries the input, it looks fine, or it doesn't — one sample either way. The prompt gets a forty-first iteration, which fixes this input and quietly breaks two others nobody typed.

That loop is the default. It is not a failure of discipline; it is what happens when the only feedback is the model's next answer.

Cases change the loop. With twenty cases, the forty-first iteration is a number: *nineteen of twenty before, seventeen after*. The fix that broke two things is visible the same minute it was made.

## Where cases come from

Not from your imagination. Cases you invent at your desk test the inputs you already thought of, which are exactly the inputs the prompt already handles. The useful cases come from four places, and none of them requires creativity:

**Corrections.** Every time a person overrides the model — a recruiter changes the job family, an editor rewrites the summary, the reader marks an article the judge scored low — that override is a labelled case, free, and more valuable than anything you could write. In the newsletter project, every morning the reader says which articles were actually worth it; that answer is the `expected` for the day's cases. The program records it as a side effect of normal use. Look for that side effect in your own product: it is almost always there, unrecorded.

**Complaints.** A user says "it got this wrong." Before you touch the prompt, save the input and the right answer as a case. Then fix the prompt. Then run the cases. The complaint becomes permanent protection instead of a one-off patch — and if the fix breaks something else, you find out now.

**Production failures.** Any output that was malformed, empty, off-policy, or embarrassing. You already have these in logs; they are the cases you would least like to see again.

**Edges you noticed.** The empty input. The input in the wrong language. The 4,000-word input. The input that mentions your competitor. You have seen the model handle these strangely at least once; write them down while you remember.

The habit that matters more than any tool: **one failure seen, one case written, the same day.** Not "we should add tests for this later." Later never comes; the failure does.

## How many, and which

Twenty is enough to start. Not two hundred — you will never write two hundred, and twenty already turns a guess into a number. In the newsletter project, twenty-one cases were enough to measure the judge's noise, calibrate its sampling, evaluate four prompt versions and pick one with confidence.

What the twenty need:

**Both answers.** If every case expects a "yes", a model that always says yes scores perfectly. The newsletter suite has ten articles the reader wanted and eleven it did not. Without the eleven, the judge's biggest weakness — promoting things that merely sound relevant — would be invisible.

**The boring middle, not just the edges.** A suite of twenty pathological inputs tells you how the system fails under stress and nothing about how it behaves on Tuesday. Most cases should be ordinary.

**Stable inputs.** A case that fetches today's data is a different case tomorrow. Snapshot the input into the file. The newsletter project stores the article summary in the case, not a URL to re-fetch: the same twenty-one inputs, every run, for months.

**A label, if you can.** For anything that classifies — positive/negative, approve/reject, relevant/not — add the label. With labels, your suite gets an aggregate: *precision 0.62 across the set*, one number stable enough to put a threshold on, where individual cases wobble. Without labels you have twenty verdicts and no summary.

## What cases are not

**Not the prompt's examples.** The few-shot examples inside your prompt are training wheels for the model. Cases are held out; the model never sees them as examples. If you reuse the same inputs for both, you are testing the model's ability to copy, not to generalise.

**Not a one-time deliverable.** A case file that was complete on release day is stale by the second complaint. The set grows at the speed of production — which is why "one failure, one case" is a rule and not a project.

**Not sensitive data, if the file is going anywhere.** A case built from a real customer conversation carries that customer. Keep such cases inside the perimeter they came from, or rewrite the input with the same shape and different facts. For the newsletter project the inputs are public articles, so the file is public too; for a recruiting tool, the job descriptions are fine and the CVs are not.

## The part that accumulates

Everything else in an LLM project depreciates. The prompt you tuned against one model is worse on the next. The threshold you picked drifts. The judge changes its mind. The cases do not depreciate: a correct answer to a real input stays correct when the model changes, when the prompt changes, when you switch providers. Twenty cases in March are twenty cases in September, plus whatever September added.

That is why the boring work is the only work worth doing first. Six months in, the team with the best prompt has a prompt. The team with two hundred real cases has the ability to change anything — model, prompt, provider — and know within an hour whether it got worse. The prompt is an opinion; the cases are the memory.

## Doing it today

1. Find the override in your product — the place where a person corrects the model. If it exists, start recording it. If it does not, that is the first thing to build, before any suite.
2. Open your logs. Take the last ten inputs that produced a complaint or an odd output. Write the right answer for each. That is ten cases.
3. Take ten ordinary inputs from the same logs — ones nobody complained about. Confirm the output was fine. That is twenty.
4. Put them in a file, in the repository, next to the code. Snapshot the inputs. Add labels where they apply.
5. From now on: one failure seen, one case written, the same day.

The next chapter is about what to check on each of them — and why the checks that need no model at all come first.

---

*Previous: [1. What you are actually shipping](01-what-you-are-shipping.md) · Next: [3. Checks: deterministic first, judge last](03-checks.md)*
