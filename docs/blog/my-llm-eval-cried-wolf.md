---
title: "My LLM eval cried wolf. Here's what I measured."
seo_title: >-
  Measuring the noise floor of an LLM-judged eval
description: >-
  A case went from 5/5 to 2/5 with nothing changed. How I measured the noise
  floor of an LLM-judged eval, what it caught the week after, and where it
  still can't see.
date: 2026-09-09
---

# My LLM eval cried wolf. Here's what I measured.

Disclosure first: I write digline, a small Python library for regression testing LLM applications. This post is not about the library. It is about a bug in how I was measuring my own pipeline, and about what happened once I started measuring the measurement. Skip the tool if you like; the problem is yours too.

## The wolf

I have a pipeline that reads for me in the morning. A few dozen RSS feeds from the AI world, a filter, and a Claude call that picks the five items worth my time. I call it the brief. Around it I had an eval suite: 21 cases, each a fixed input with a rubric, scored by an LLM judge against a mark I had given by hand. It ran on every change and it had been green for weeks. Long enough that I had stopped treating it as something that might be wrong and started treating it as the thing that told me when I was.

One afternoon a case went from 5/5 to 2/5. Nothing else in the report moved. I did what you do. I diffed the prompt against the approved version: identical. The model alias, the config, the retrieval step, the trace of the call itself: identical, byte for byte. I reran the case fifteen minutes later. 5/5.

I had spent an hour investigating a regression that did not exist. What had regressed was my measurement, and the measurement had no way to tell me that, because I had never asked it what "unchanged" looks like. I had one reference score per case and a threshold, and a threshold assumes the number under it is a number. It was a sample.

Here is the part that matters more than the lost hour. A gate that cries wolf gets muted. Not out of negligence, out of arithmetic: if it fires once a week on nothing, by the end of the month someone (me) has learned to click through. Then the real regression arrives, the gate fires, and it gets clicked through with all the others. The failure mode of a noisy eval is not the false alarms. It is that it trains you to ignore the true one.

So I stopped and asked the question I should have asked on day one: how much does this score move when I change nothing?

## The measurement

What I had was one run, one score per case, stored as the reference, and a comparison rule that flagged any drop larger than a declared tolerance. The tolerance was global. It treated a case whose judge is effectively deterministic and a case whose judge flips a coin on a borderline rubric line with the same seriousness, because it knew nothing about either.

What I changed, now written down as an ADR:

- **When a version is approved, each case is asked K times, not once.** In my setup K is 5. The score stays the mean of the samples; on a binary check, a mean over five votes is just the majority vote with a threshold at one half.
- **The reference stores, for each check, the min and max of those K samples** alongside the score. That range is the check's own noise floor, measured on the version I said was good.
- **On comparison, a drop counts as a regression only if the new score leaves the reference's band.** A drop that lands inside it is reported, but as "within the noise", and it is not counted. The report separates the two in the headline.
- **The band is the reference's, never the current run's.** The reference is the reviewed measurement. Letting a noisy new run widen its own excuse is how a regression hides inside a model that got less stable.
- **A flip through the threshold is never within noise.** Pass to fail is reported whatever the samples did. The band explains a movement; it does not excuse a result.

Why min/max per check, rather than a tighter tolerance or a standard deviation:

- **Per check, because noise is a property of the check, not the suite.** One global number is a guess about all of them at once, and it is wrong for most of them in one direction or the other.
- **Min/max, because with five samples a standard deviation is a model I have not earned.** The min and the max are what was seen. They are a fact rather than a distribution, and a reader can verify them against the raw samples printed beside them.
- **Because a band is measured, and a tolerance is declared.** I kept both. A tolerance says how much movement a reviewer decided is acceptable; the band says how much the system moves on its own. The report says which one spoke. Collapsing them would have deleted the ability to say "this moved more than you allowed, and less than it moves by itself".
- **Because a zero-width band is not a noise floor.** A check whose reference samples were unanimous has no interval, so every later change of mind is reported. That is right: a case decided five times out of five and now decided twice out of five has moved, and one case is a diagnosis. The floor earns its keep where the dispersion actually was.

Two sentences I now keep next to the suite. Provenance in traces is observability; provenance in the reference is a contract. The trace tells you what happened. The reference tells you what you agreed counts as the same. And: the gate is a veto, not an approval. Passing means I found nothing beyond the noise. It does not mean the change is good.

## The proof

The fixture is public, in the brief's repository, pinned to a commit. Three consecutive runs within eleven minutes, same suite, same prompt files, same `config_hash`, five samples per case. Nothing changed between them, and the report checked that for itself before comparing. Two cases, `evals-skills-for-coding-agents` and `more-than-just-code-review`, go 5/5, then 2/5, then 5/5 within the same triple. That is the wolf, reproduced on demand, twice in one morning.

Then the middle run compared against the reference. Both aggregates fell. Precision comes in at 0.600000 against a reference band of 0.615385–0.666667: below the floor, reported as beyond the noise. Accuracy fell by more, 0.095238 against precision's 0.066667, and lands at 0.666667 against a band of 0.666667–0.761905: exactly on the lower edge, within the noise, not counted. The reference had already produced that accuracy once in its own five samples. It had never produced that precision.

On the declared tolerance alone, 0.047619, one case out of twenty-one, both would have tripped. The same run is noisy enough to explain the larger movement and not the smaller one, and only the reference's own history can tell them apart. The two per-case flips are still reported, because a flip is never noise; the difference is that the headline now says one check moved within noise, and I know which aggregate to trust before I open a trace.

![The `digline compare` report for the middle run. The headline counts three checks worse and one moved within noise; the two per-case flips are listed as passing to failing, then precision is marked beyond the noise of its check and accuracy within it, each with the reference band it is being read against printed beside the scores.](../assets/digline-noise-floor-post.png)

## The week after

I have a second pipeline, scout, that reads Reddit feeds and asks a judge which threads are worth a comment. Seventeen cases, each with a human verdict, mine. Same suite machinery, reference approved with bands, same rule. Over the following week I made three changes to it, and the comparison handled all three differently.

The first was a change to the judge's prompt. The judge kept flagging threads where the practice under discussion was one the author plainly already followed, so I added a clause: it is not a comment if the practice is already in the post. Reasonable, explained, reviewed. Recall went from 0.80 to 0.50, beyond the noise, and the like-for-like count went from 9/15 to 7/15. The per-case reasons showed what had happened. The judge had applied the clause to the author's perceived competence, "this person clearly knows this already", rather than to what the post actually said. Rejected.

The second was also a prompt change. I added a sufficient condition to the list of what makes a thread worth commenting on. The judge read it as a necessary one. Accuracy went from 0.588 to 0.529 and recall from 0.75 to 0.667. Adding a sufficient condition to the comment list narrowed it. Rejected.

The conclusion I drew from the two together: with Haiku 4.5 as the judge, rules with more than one clause do not compose. Each clause gets applied, but not in relation to the others, and a reasonable edit to one line changes the meaning of the ones around it in ways I could not see from the prompt.

The third change was the judge itself. Same prompt, Sonnet 5 with thinking on. Recall went from 0.75 to 0.917 and precision from 0.75 to 0.733. The two comments the previous judge had missed came back, with reasoning that matched why I had labelled them in the first place. One case showed up as broken, and reading the judge's text it was the judge applying a rule I had written more faithfully than I had applied it when labelling; the label was the bug. The comparison promoted this one.

The cost per judgement went up 7.5×, and that is the thinking tokens, not the price per token: roughly $10 a month instead of roughly $1.35 for this pipeline. I paid it.

What I want to draw attention to is not the numbers but that the same rule produced three different verdicts, each with reasons per case. Two edits I would have defended in review turned out to break the judge in ways only the cases could show. One expensive change I would have hesitated over turned out to be worth it, and the comparison said so before I had to argue it with myself. That is what a gate with a measured floor buys: not fewer alarms, but alarms I can read.

## Limits, and what readers taught me

The limits, declared:

- **The band is min/max over K=5. It is not a confidence interval.** It is optimistic: at small K the observed range is narrower than the true one, so the floor will miss some noise. It will not invent any, which is the direction I care about, but a drop that lands just below the band on a check that was already wobbling deserves a look, not a rollback.
- **It needs a reference before it is useful.** Day one is run, look, approve. There is no floor until something has been approved with samples.
- **LLM-as-judge is still LLM-as-judge.** The band measures how much the judge moves, not whether it is right. Scout's third change is the cheerful version of that; the two rejected edits are the other one.

After I posted the fixture on Reddit, three readers pointed at holes I had not seen. I am citing them as theirs.

- **A canary case.** A fixed input with one unambiguous answer, not scored for quality, only watched inside its band. If the canary moves, the model behind the alias has changed, and the right move is to re-baseline everything rather than chase whichever case happened to trip first.
- **Store the provider fingerprint next to the scores**, where the provider exposes one. The alias is not the model; the fingerprint is closer to it.
- **A stable score with changing reasoning is a judge that is right by accident**, and a band on the score cannot see it. Keep the judge's text, not just its number. Scout's three verdicts were readable only because scout keeps its own log of the judge's text; the suite runs did not, and that is the next thing to change.

## Where this lives

The decision is written up as [ADR 0006](../product/adr/0006-repeated-samples-and-the-noise-floor.md) on digline.dev, and the three runs, the reference and the comparison are in the [fixtures of the brief repository](https://github.com/digline/brief/blob/c9d86ff22d68d3df458fa0da81348ec962d16aa7/fixtures/README.md), pinned to the commit. If you measure your own floor and it looks different from mine, I would like to know.
