---
title: "The case that errors is usually the case that was failing"
description: "A case that errors drops out of the denominator, so precision and recall get measured over a smaller suite than the run you are comparing against. The score goes up."
seo_title: >-
  The case that errors is usually the case that was failing
date: 2026-09-18
---

# The case that errors is usually the case that was failing

If your suite gates on a run level number, precision, recall, accuracy,
F1 over all your cases, then you've made a decision you probably never
wrote down: what happens to a case that couldn't be judged at all.

The usual answer is to drop it. The model timed out, the endpoint
returned something the parser didn't expect, the judge came back with no
score. You can't score that case, so it leaves the calculation. Sounds
reasonable, and it's what my own tool did from the first commit.

Here's what it costs. Four cases, one of them actually regressed. Two
runs that differ only in whether one case errored:

|                          | the case was judged  | the case errored    |
| ------------------------ | -------------------- | ------------------- |
| that case's check        | fail 0.0             | error               |
| run level recall         | fail 0.75 (3 of 4)   | pass 1.0 (3 of 3)   |
| compared to the baseline | regressed 1.0 → 0.75 | unchanged 1.0 → 1.0 |

The regression is the same in both columns. Nothing about the system
under test is different. But three out of four is 0.75 and three out of
three is 1.0, so the score went **up**, because the case that left the
calculation was the one that was failing.

That's the trap in one sentence: **the case most likely to error is
often the same case that was going to fail.** A malformed reply, a weird
input, a path the model handles badly. The thing that breaks your parser
and the thing that breaks your quality are usually the same thing. So
the exclusion isn't random with respect to what you're measuring, and
dropping it flatters you in exactly the situation you built the gate for.

Then the second half, which is the part that actually bit me. The two
numbers get compared. 1.0 against 1.0 reads as *unchanged*, and my tool
printed the headline you can guess.

Except they're not two measurements of the same thing. One is over four
cases, the other over three. Comparing them isn't a comparison at all,
and calling the result "unchanged" is a claim about something that was
never valid to begin with.

## What to look at in your own code

Three questions, about ten minutes.

**Does your aggregate drop anything?** Not just errors. Suspended cases,
cases with no label, any case you skip for any reason, they all do this.
A rule that only watches errors leaves the other doors open, which is the
mistake I made first.

**Does your comparison know the two denominators differ?** If it puts this
run's number next to the reference's number, and the two came from
different sets of cases, it shouldn't be allowed to say "unchanged".
"Unchanged" is a claim, and it isn't available here.

**Does your reader ever see the count?** Mine did disclose it. The
excluded count was right there in the verdict's metadata, and in the HTML
report. It just wasn't on the two surfaces people actually read. A
disclosure nobody runs into isn't a disclosure.

## What I did about it

I stopped letting a moved denominator produce a comparison of run-level
scores. When the two sides counted different cases, the gap between them
isn't a regression and isn't an improvement, the two numbers just aren't
comparable. So since 0.15.3 digline compare and digline explain say that
in their own words, refuse "unchanged" as an answer, and leave the
reader to judge. That covers the case where the gate held, and the case
where it went up, which is the direction the trap flatters you in.
There, the exit code doesn't move because of it. The reading does.

The other direction I left alone on purpose. A gate that drops below its
threshold stays red, even when it was the denominator that pushed it
there. A passing case that errors takes its pass out of the count, and
two of three can fail a bar that three of four cleared. That's a false
alarm, and I'd rather have a false alarm than a quiet pass. And digline
diff, which puts two runs side by side without judging either, still
calls 1.0 against 1.0 the same. It hasn't learned this one yet.

There's a fuller account, including why it affects every version before
0.15.3 and how it can be triggered by whoever runs the endpoint you're
testing, in [GHSA-8c38-f965-cgww][advisory].

The uncomfortable part is that it was in the first commit of the project,
and I only found it because a later change made it quieter instead of
louder. A silent wrong answer lives a lot longer than a loud one.

[advisory]: https://github.com/digline/digline/security/advisories/GHSA-8c38-f965-cgww
