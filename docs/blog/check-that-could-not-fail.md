---
title: "The check was written well, and it could not fail"
description: "A faithfulness check on an LLM call scored 1.000 because the prompt already forbade what it measured. What a green check says, how to make one red on purpose, what that costs, and what it cannot find."
seo_title: >-
  The check was written well, and it could not fail
date: 2026-09-29
---

# The check was written well, and it could not fail

A green check does not say the thing works. It says the check looked and
found nothing. Those are two different facts, and on the screen they look
the same. The only way to tell them apart is to try to make the check red.

This post is one case. It is small, and nothing in it was broken. That is
why it is worth telling in full.

## A check that measured the prompt

[brief][brief] is my morning digest. Six RSS feeds go in. One model call
scores each item against my taste. A second call writes one sentence
about each item it shows me: what the item is about, and nothing more.
That second call is the describer. Why it is a second call, and not a
field in the first, is the story of [an earlier post][added].

The describer's prompt [says this][describer]:

> You have not read the article. Say only what the title and summary
> state: the subject, and the form if they give it away. Add no detail
> they do not contain.

That is a constraint. It stops the describer from inventing.

The suite checked the describer with digline's `Faithfulness`. A judge
reads the item and the sentence, and says how much of the sentence the
item supports. A sentence that adds a detail scores lower. For a call
that describes something, this is the right check. It is the one most
people would write first. It was set up correctly, and the judge did its
job.

It scored a median of 1.000 over the cases it could score. The lowest
was 0.833.

Now put the two side by side. The prompt forbids invented detail. The
check looks for invented detail. The prompt runs first, when the
sentence is written. The check runs second, on what the prompt let
through. So the check was measuring the prompt. There was nothing left
for it to find. A sentence that may only say what the item says is
almost a copy of the item, and a copy is always faithful.

The record that retired the check, [decision 0003][d3], puts it in two
lines: *"The instrument is not broken. It has nothing left to find."*

## Why it did not look wrong

This is not a bug. There is no line to fix. The check is correct. The
judge is correct. The prompt is correct too: it was the right repair, and
it was made in the right place. Two correct things, placed one after the
other, made one of them useless. Review each part, and each part passes.

And the result looked like success. A faithfulness score of 1.000 is what
you hope to see. Nothing about it asks for a second look.

It did not last long. The check was built on 22 September, on another
sentence the judge wrote. On 23 September it moved to the describer, and
it was retired [the same day][retire]. But the question that retired it
had not been asked before, through two earlier decisions, twelve runs
and $1.36. The check moved with the system, and nobody asked what it
could still catch.

0003 turns that into one question you can ask of any check:

> **Can you state a failure the check would catch that the constraint
> permits?**

If you cannot, the check is measuring the constraint. This is not only
about judges. A schema check after a serializer that cannot emit the
wrong shape. A range assertion after a clamp. A null check after a
constructor that refuses null. Each one is green, and green is what it is
supposed to look like.

0003 retired the check. If anything watches the describer, it says, it
should watch the constraint holding, not the outcome the constraint
guarantees: is the describer still only describing, or has it started to
judge? That check would need no model. It would fail when the thing it
watches fails.

The shape is not rare. In the five days after 0003 it turned up five more
times in digline itself: in tests, in a CI gate, and in a function that
gave the same empty answer for two different facts.

## Make it red on purpose

A check that has never been red has a sensitivity nobody has measured.
0003 says this about its own check: *"I know it is green. I do not know
it would go red, because nothing has ever made it."*

So make it. Break the thing the check is for, and run it. For a
faithfulness check, take a real output and add a detail the input does
not contain. For a test of a refusal, delete the refusal. For a guard,
remove what it guards. If the check stays green, it was not checking
what you thought.

For brief's check, that answers half. The mutation shows the check can
fail. The question above asks whether anything in your system can make
it fail. You need both. The first is an experiment. The second is a
minute of reading.

The experiment has a cost, and it is easy to miss. You are making a
failing test on purpose. The failure is yours, but other people can see
it. Push it to a branch with an open pull request, and it is a CI
failure. Write "this test fails" in a chat, and it is a claim about the
code. Nobody who reads it knows you meant it. So:

- Make the change in your own copy of the tree, not in a checkout
  somebody else is using.
- Restore it from a copy of the file, not from git. `git checkout --
  <file>` also throws away any work in that file you had not committed.
- When you report a red that other people can see, say in the same
  sentence that you made it.

digline's [contributing guide][contrib] has these as a rule.

## What it cannot find

Mutation finds a check that stopped working, or one that never worked. It
does not find a property that was never true.

The method is: remove the thing that makes the property true, and see
the check notice. If the property was never true, there is nothing to
remove. Say a test is named for a refusal, and its body only checks that
a message was printed. Nothing in the code refuses. There is no line to
delete. The test is green before your mutation and green after it, and
you learn nothing.

This is a real limit, not a detail. Mutation tells you the check reacts.
It cannot tell you the thing you believe is there. For that the only
tool is reading: read a test's name as its first assertion. If the name
says *never*, *no longer* or *refuses*, one line of the body must say it
too.

## What to look at in your own code

Three checks, about fifteen minutes.

**Name the failure.** For each check in your suite, write down one
failure it would catch. Then look upstream. Is there a prompt rule, a
schema, a clamp or a validator that already forbids that failure? If
yes, the check is measuring that rule.

**Find one that has never been red.** Pick a check that has only ever
passed. Break what it is for, in your own copy, and run it. Restore from
a copy. If it stays green, you have found a check that works on nothing.

**Read one name against its body.** Pick a test whose name makes a
promise. Find the line in the body that keeps it. If there is no such
line, no mutation would have told you.

A green check is a report about what the check saw. Before you trust
it as a report about your system, make it red once.

[brief]: https://github.com/digline/brief/blob/d4bb22b2906d67caaadcaaa8a31ae4e605f767fe/README.md
[added]: added-field.md
[describer]: https://github.com/digline/brief/blob/d4bb22b2906d67caaadcaaa8a31ae4e605f767fe/prompts/describer.txt
[d3]: https://github.com/digline/brief/blob/d4bb22b2906d67caaadcaaa8a31ae4e605f767fe/decisions/0003-a-check-that-cannot-fail.md
[retire]: https://github.com/digline/brief/commit/d013037da850e799ef26548e0d1ee39f887a5d81
[contrib]: https://github.com/digline/digline/blob/76d901050e7faae82fb70b5c2459e104ff0da2cd/CONTRIBUTING.md
