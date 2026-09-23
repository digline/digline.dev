---
title: "The field you added changed the answer you already had"
description: "Asking an LLM call for one more field changed how it scored everything else, and moving the field after the score didn't undo it. Measured on one judge, eight runs, $0.88."
seo_title: >-
  The field you added changed the answer you already had
date: 2026-09-23
---

# The field you added changed the answer you already had

If you've ever added a field to a structured reply, a reason next to
a label, a confidence next to a score, a summary next to a
classification, you probably checked that the new field came back
right. You probably didn't check what it did to the fields that were
already there. Almost nobody does, because it looks additive. The old
fields are still there, still in the schema, still parsed the same
way. One more key in the JSON shouldn't change the others.

It does. Here's the one I measured.

I had a judging prompt that worked. It returned a score, and it was
about as stable as an LLM judge gets. I ran it twenty-one times. In
eighteen of those runs it agreed with my labels on 16 of the 21 cases.
Very nearly deterministic.

The sentence it returned alongside the score had a problem, though.
It mixed description with judgement, something like "the reply
lists three causes and misses the obvious one", and only the first
half was checkable. So I asked the same call for one more thing: the
description on its own, as its own field. A good reason, a small change.

Agreement didn't collapse. It got slightly worse, a median of 15 of
21 against the old 16, and much more variable, 13 to 17 against 14 to
16. The variance is the bigger half of the story, and it's the part
you miss. A one-point drop in the median is the kind of thing you
shrug at. What changed is that the judge got **loose**. Each
case is sampled more than once, and the number to watch is how many
cases come back with samples that disagree with each other:

|                              | one field           | new field first | new field after the score |
| ---------------------------- | ------------------- | --------------- | ------------------------- |
| runs                         | 21                  | 4               | 4                         |
| cases whose samples disagree | median 4, range 2–6 | 7, 7, 7, 8      | 7, 7, 7, 8                |

The old prompt's worst run is below the new prompt's best. No overlap
at all.

## The fix everyone reaches for

The obvious diagnosis was position, and I liked it. A reply is
generated in the order the JSON declares it. I had put the description
first, so the score got written after the description, and
conditioned on it, and the model had just made that description up.
Put the new field after the score and the score is written before the
description exists. It can't be influenced by something that hasn't
been generated yet.

That's the answer you want to be true, because it's free. Reorder two
keys and carry on.

So I moved it. The disagreement counts came back 7, 7, 7, 8. Not
better, not halfway back. Identical, run for run, to the field first.

In case the model had moved under me, I ran the old prompt the same
day: 6 cases of 21, inside its usual band. The judge hadn't changed.
The prompt had, and putting the field last didn't give back what
adding it took away.

**Putting the new field last doesn't make it safe.** The score was
never only reading what came before it in the reply. It was reading
the whole request, and the request now asked for something else as
well.

## What I don't know

This is one judging prompt, on one model, over twenty-one cases. I
measured an effect, not a mechanism. I have two guesses. Maybe asking
for a description changes what the model thinks the job is, no matter
where the answer sits. Maybe it's just a longer prompt, so a different
one. I tested neither. It may not reproduce on your model, or on a
prompt that isn't a judge. What I can say is that the one explanation I was sure
of, position, is the one the numbers ruled out.

## What to look at in your own code

Three questions, about ten minutes.

**When you last added a field, did you re-measure the old ones?** Not
whether the new field is right. Whether the fields that were already
there behave the way they did the day before. If the answer is "the
tests still passed", that's a check on the parser, not on the answer.

**Would you have seen it?** My headline number dropped by one case,
so nothing looked broken. The change was in the spread: cases that used
to come back unanimous now split between their own samples. If each case is
asked once, and you only look at the aggregate, a judge can go loose
and you'd never know.

**Does the new field have to be in that call?** This is what's left
standing, and it's narrower than the fix I wanted. If the existing
behaviour has to be preserved, the new field doesn't belong in that
reply at all, first or last. It belongs in a second call, with the
first one left exactly as it was. That costs you a request per case.
I haven't measured the second call yet. It's what's left because it's
the only option that doesn't touch the call I did measure.

## What it cost

Two prompt versions, eight runs, $0.88. The runs were taken with
digline, but nothing above needs it. A handful of repeated runs
before and after the change, and a count of the cases that stopped
agreeing with themselves, is enough.

The uncomfortable part is how reasonable the change was. I wasn't
making the judge do more. I was making its output easier to check. The
change that made the judge harder to trust was the one I made to trust
it more.

## Addendum, 2026-09-23: the control a reader proposed

The post says I measured an effect and not a mechanism. A few hours
after it went up, **u/aofu_dev** on r/LLMDevs proposed the control that
tests one mechanism. Add a dummy field that always returns "ok", and see
whether the disagreement still goes up on the same cases without asking
for a description. Same reply shape, no work in it. The control is
theirs. I ran exactly that arm, and nothing else.

I wrote the predictions down before the run, including what the result
could and couldn't tell apart. If the field itself was the cost, every
run would come back at 7 or more. If the describing was the cost, every
run would come back at 6 or fewer.

Four runs, same suite, same 21 cases, five samples each:

|                              | one field | description field | `"ok"` field |
| ---------------------------- | --------- | ----------------- | ------------ |
| cases whose samples disagree | 2–6       | 7–8, eight runs   | 5, 3, 5, 4   |

Every run is back inside the old prompt's band. The case the description
had made unstable split in one run of four, not seven of eight. All 420
replies returned "ok". The old prompt, run once more that afternoon, gave
4, so the model hadn't moved.

**It isn't the field.** One more key that asks for nothing cost nothing
on this judge. What loosened it was asking for *that* field, one the model
has to work to fill.

That narrows the advice above. "The new field doesn't belong in that
reply" is about a field with content. A constant key is harmless here.

It doesn't settle my two guesses, and I said so before the run. The "ok"
field added 6 tokens to the prompt. The description came with about 160
tokens of instructions. So the cost is either the describing or the
length of what asked for it, and this control can't tell those apart. The
next arm can: the old prompt padded with about 160 tokens of neutral text,
and no field.

It cost $0.45, including one run I took by mistake and left out of the
count. The predictions, the numbers and the mistake are in
[decision 0004](https://github.com/digline/brief/blob/3635b44ce72a47738660fc1e816417716d3160b4/decisions/0004-the-constant-field.md),
pinned to the commit.
