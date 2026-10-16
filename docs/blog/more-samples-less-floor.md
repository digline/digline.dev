---
title: "The more samples I took, the less my noise floor could see"
description: "A noise floor built from the range of K single samples, compared against a mean: why it widens as K grows while the measurement behind it gets better, what it adds on two real suites, and what should replace it."
seo_title: >-
  The more samples I took, the less my noise floor could see
date: 2026-10-16
---

# The more samples I took, the less my noise floor could see

On 21 September I wrote the problem down in a commit message, in a private repository, which is about the least read place there is. The samples of that check are binary, the note said, so the recorded minimum and maximum come out 0.0 and 1.0 for any case whose samples don't all agree.

I pushed the commit and went on shipping the thing it described. Three weeks later I measured it properly, and the defect turned out worse than the one I'd written down.

## What the band is

digline runs each case K times against the approved version and records the minimum and the maximum of those K scores next to the reference.

On a later run the comparison goes in order. A case whose outcome flipped is never unchanged, so it never reaches the band at all. Next comes the denominator check, which refuses to compare two scores computed over a different number of things. It acts on the aggregates of a run and leaves the score of a single case alone. Then the **declared tolerance**. Only what survives all of that meets the band, so a drop counts as a regression when it falls outside the tolerance **and** outside the recorded range.

That ordering matters for everything below: the band is the last step in the chain, so the step just before it can make it redundant.

The idea behind it is that a tool should not page you for movement it has already seen the system make on its own. I still think that idea is right. The implementation isn't, and the reason fits in one sentence.

**The band is the range of single draws, compared against a mean.** Raise K and the range widens toward the support of the distribution, because that's what the extremes of a sample do. Raise K and the mean it's being compared against stabilises. The two move in opposite directions, so the comparison sees less just as the measurement behind it becomes more trustworthy.

That holds for every check, binary or not. The rest of this piece measures how much it matters.

## Measured

A suite from the repository's own examples, run 21 times, 63 samples per band, that is per case and assertion pair, one unchanged prompt throughout. I threw away an earlier pass against the committed baseline, for a reason that had nothing to do with its numbers. The prompt came out different in all 21 comparisons, which meant the baseline had been recorded under another prompt, so the pass was adding a deliberate change to the noise and calling the sum noise.

First the populations, so the numbers below add up. Two assertions and six cases make eleven bands: `levenshtein` runs on five of the cases, `llm_rubric` on all six, and `calibration-half-right` carries `llm_rubric` only.

**The width grows with K.** Median band width, at K equal to 2, 5 and 31:

| Assertion | K=2 | K=5 | K=31 |
|---|---|---|---|
| rubric | 0.1167 | 0.3000 | 0.4833 |
| Levenshtein | 0.0136 | 0.0339 | 0.0738 |

Declaring things is the point of this piece, so here is how K varies in that table. For each band I take its 63 samples and draw K of them without replacement, 5000 times, seed 20261014, and keep the median of the widths. Then the median of that across the five non-calibration cases. So the table resamples the samples I already have. I never ran anything at K equal to 31. And no cell in it is a band: each one is a median of per-case medians, and it matches a real band only by accident.

Monotone at the three K shown, and wider by a factor of 4.1 on the rubric and 5.4 on the Levenshtein from K=2 to K=31. Over the same range the dispersion of the mean falls.

**The width also depends on which run you happened to approve.** These are widths at K equal to 3, with each of the 21 runs taken in turn as the reference. On the nine bands that have a finite ratio, the width varies by a factor of about 5 at the low end, on `order-a-book` with `levenshtein`, up to about 150 at the high end, on `price-check` with `levenshtein`, depending only on which run was promoted as the baseline. Levenshtein sits at both ends of that. Same system, same cases, same day.

The other two bands have no ratio at all, because some reference run gives them a width of zero: `calibration-half-right` in 6 of the 21 references, and `gift-wrap` with `llm_rubric` in 1. That's the stronger result: on two bands out of eleven, depending on which run was promoted, the band shrinks to a single point, in six promotions out of twenty-one on one of them and in one on the other. The widest band in the whole set is 0.6500, on `opening-hours` with `llm_rubric`.

**The model holds where I can check it.** Across the 21 runs, on the two scored assertions, the variance of the mean is 0.000027 against 0.000031 predicted by internal noise alone, and 0.00132 against 0.00107. One below the prediction, one above.

## What the band actually adds

First the declared rules, since this whole section compares the band against them. `levenshtein` has a pass threshold of 0.75 and a tolerance of 0.05. `llm_rubric` has a threshold of 0.7 and a tolerance of 0.1. Three samples per comparison.

A delta is called unchanged if it sits inside the declared tolerance **or** inside the band. It's a disjunction, so the band can only widen the invisible zone. That leaves exactly one quantity to measure: by how much.

The most it adds on any band is **0.3167 of the scale** beyond what the tolerance already covered, and that's `price-check` with `llm_rubric`, whose widest band is 0.5833. That isn't the widest band in the set. On `opening-hours` with `llm_rubric`, at 0.65, the most it adds is 0.3000. On `price-check` with `levenshtein` it adds **0.046**.

The numbers in this section come from two different instruments. The measurement script computes how much the band adds, counted only on the side of the threshold where the reference sits, and also the count of references on which it has a region of its own at all. The product's own comparison function produces the counts out of 420 and the table further down, through its outcome for every comparison and through its verdict of "within noise" for the ones the band decided.

The two frequencies below answer different questions, so each comes with its denominator and its scope. **Both of the figures quoted here are the ones from the five rubric bands.** On the Levenshtein assertion the first is 0 or 1, and on the calibration case it's 0.

Across those five rubric bands, the band sticks out past the tolerance window in 7, 13, 13, 11 and 12 of the 21 runs, each run taken in turn as the reference at K equal to 3. That's how often it has a region of its own at all. Separately, it's the thing that declared a delta unchanged in 18, 39, 48, 21 and 35 cases out of **420 run pairs**, which is **4.3 to 11.4 percent of comparisons**. Those pairs aren't independent, which is in the limits below.

Read the sign of those numbers carefully, because "invisible zone" sounds like "missed regressions", and on this data that's the wrong reading. The 21 runs are one configuration with one unchanged prompt, so every delta between two of them is noise by construction. There's no regression in that set for the band to hide. The comparisons it declared unchanged are false alarms that it suppressed correctly. The mechanism stays what it is, a disjunction that can only widen what the gate is unable to see, but on these runs widening it was the right thing to do.

The whole picture has three stages. On the 420 pairs, for the five rubric bands:

| Band | outside the window, before the band, flips excluded | after the band | flips | after, plus flips |
|---|---|---|---|---|
| `gift-wrap` | 142 (33.8%) | 124 (29.5%) | 0 | 124 (29.5%) |
| `opening-hours` | 122 (29.0%) | 83 (19.8%) | 0 | 83 (19.8%) |
| `order-a-book` | 126 (30.0%) | 78 (18.6%) | 76 | 154 (36.7%) |
| `price-check` | 90 (21.4%) | 69 (16.4%) | 0 | 69 (16.4%) |
| `signed-copies` | 148 (35.2%) | 113 (26.9%) | 40 | 153 (36.4%) |

The difference between the first two columns is 18, 39, 48, 21 and 35, which are the five numbers in the paragraph above. The two counts are the same quantity measured at two stages.

The flips never reach the band and get reported anyway, and on an unchanged prompt they are noise as well. So the last column is the share of comparisons the gate flagged on these runs, 16.4 to 36.7 percent.

That gives the thesis of this piece its number. The band suppresses 4 to 11 comparisons in a hundred, inside a gate that flagged as many as 37 in a hundred, every one of them a false alarm on these runs. Taking it out without touching the tolerance makes an already noisy gate noisier. The case against the band rests on how it behaves in K and on what it does to binary checks, and these frequencies aren't part of it.

So on this suite the band does something. It decides a few comparisons in a hundred, on some assertions only, depending on which run was approved, and on these data it decides them well.

## The second number nobody measured

This is the part I didn't expect, and it's why the title of this piece is about K.

Whether the band gets to decide anything isn't only a question of the tolerance. It's also a question of **`min_agreement`**, the setting that says how many of the K samples must agree for a case to count at all. It has no default: a suite that samples must declare it or digline refuses to run.

For a binary check at K equals 5 with a pass threshold of 0.5, the largest same-side movement that can exist is:

| `min_agreement` | largest movement that exists |
|---|---|
| 2/5 and below | 0.5 |
| 3/5 | 0.4 |
| 4/5 | 0.2 |
| unanimity | none |

Now put that next to the shape of a binary band, keeping two things apart. The rows of that table are settings, chosen once for the suite. Agreement is a property of one comparison, and at any setting below unanimity the suite will hold both kinds.

Take a comparison whose baseline samples disagreed. The minimum is 0 and the maximum is 1, so the band is the entire scale and excuses all the movement available in that row. Take one whose samples were unanimous and the band collapses to a point and excuses nothing.

So the setting fixes how large a movement can exist, and then the band decides case by case whether that movement is visible, with the split cases giving it away for free.

## What is binary and what is not

The table above is for a binary check, and the distinction matters more than it looks.

Unanimity is a property of states, not scores. A split binary baseline necessarily holds 0 and 1, so its band is the whole interval. A split rubric baseline holds the scores it actually saw, which is narrower: I measured a rubric assertion whose samples ran between 0.45 and 0.6, and it doesn't excuse a movement of 0.33.

So "the band swallows everything" is a statement about binary checks. What is true of every check, binary or not, is the one sentence at the top: a range of single draws against a mean, widening with K while the mean settles.

## The measurement I threw away and then did again

There's a second suite behind this work, the judge for a pipeline I run every day: 145 cases, 5 assertions each, 725 comparisons. Five samples per case, and the suite declares `min_agreement` at 3/5.

I measured the band on it, wrote the numbers down, and then found I could not reproduce them. The script and the table had lived in a working directory that no longer existed. So I applied to myself the rule this whole piece is about, which is that a figure you can't regenerate isn't a measurement whatever you remember about it, and I withdrew them.

Then I measured it again, with the artefact kept this time: every probe passed through the real comparison function, the script and its output saved, three executions run from two different directories and all three identical to that saved output, and a positive control to show the detector actually fires.

**The band adds nothing to any of the 725 comparisons.** Not on average, not mostly. All five assertions, and on each of them the probe went looking from both sides of the reference score, not of the threshold, for a value that would land inside the band, outside the tolerance window, and on the side of the threshold where the reference sits. 551 of the bands have zero width and 29 cover the entire scale.

Five of those comparisons are one case that sits in the suite because the judge's answer on it is unstable, one comparison per assertion. It's a sentinel for exactly the noise this piece is about, and the band adds nothing on those five either.

The positive control is what makes that zero readable. Run the same probes with the tolerance set to 0 and the detector finds 174 comparisons where the band is doing the deciding. That's the number that should appear, and it decomposes: 145 from the cost check, one per case, plus the 29 full-scale bands. So the zero is a zero, not a broken test.

The reason has two halves, and only one of them holds whatever happens.

**The half that holds whichever run is promoted.** Agreement is always computed over five samples, so the guarantee can be read off the number of samples that were judged. With five judged, the means sit on fifths and the largest same-side movement that can exist is 0.4. With four judged, only 4-0 and 3-1 clear 3/5, so the means are 0, 0.25, 0.75 and 1, and the largest is 0.25. With three judged, only 3-0 clears it and the largest is 0. With two, everything errors. The largest movement available anywhere in that list is 0.4, against a declared tolerance of 0.41. So the guarantee comes from `min_agreement`, and "every sample was judged" adds nothing to it.

That argument covers two of the five assertions, the two that score agreement at a threshold of 0.5 with a tolerance of 0.41. A third is covered by construction: its threshold is 0.0 and its tolerance is 1.0, which is the whole scale.

**The half that's only true of this baseline.** The schema check has a threshold of 1.0 and a tolerance of 0.0, so nothing structural protects it: its zero comes from all 145 of its bands having zero width here. The cost check has a threshold of 0.5 and a tolerance of 0.15, against bands as wide as 0.224054, so its zero is measured and nothing more.

The limit is wider than the one sentence I first gave it. Three of the five assertions have only one side on this baseline, 145 of 145 passing: the schema check, the one at threshold 0.0, and the cost check. For the one at threshold 0.0 that's harmless, because a tolerance of 1.0 covers the scale either way. For the cost check it isn't harmless. The two assertions that do have both sides have 18 and 16 comparisons that fail. If a schema check failed with samples that disagreed, the band would be back in the decision.

## Why the two quantities move in opposite directions

Evan Miller's paper on error bars in evals is what straightened this out, though not in the way I first assumed.

Miller decomposes the variance of an eval score into the variance of the conditional mean across questions and the mean conditional variance within a question. Resampling shrinks the second and never the first, because the first is, in his words, "a property of the super-population and therefore immutable" (section 3, page 5). I took that to mean the gain from more samples hits a ceiling, and I wrote as much.

That's true when you compare two different models on a benchmark. digline does something else: it compares a system against its own earlier state, on the same fixed set of cases. Miller's own formula for the two-model case says why. The term that carries the between-question variance is

> omega squared = Var(x_A) + Var(x_B) - 2 Cov(x_A, x_B)

(section 5, page 9). When both sides are the same cases and the difficulty hasn't moved, the covariance eats the two variances and the term goes to zero. What is left is the within-case term divided by K, and that falls without a floor.

That cancellation is an argument from construction: the cases are identical on both sides. A weak estimate of that term does exist, and it's in the limits below with everything that's wrong with it.

And none of this is Miller's view of bands. His paper never discusses extremes, ranges, minima or maxima of samples at all. Its intervals are confidence intervals, for a mean and for a difference. Nobody told me to build a min-max band. I built it because it looked like a measurement.

## What it should be instead

Paired differences, per case.

This is recommendation four in Miller's paper, on page 2: when comparing, do the inference on the question-level paired differences rather than the population-level summary statistics. The standard error of those differences is equation 7, section 4.2, page 7.

My case is the favourable one for this technique, because both sides are literally the same suite and the per-case difficulty cancels. I measured the gain instead of citing it. The paired standard error comes out at 0.37 of the unpaired one on one assertion and 0.50 on the other, with per-case correlations of 0.91 and 0.77. Those are ratios of standard errors, so squared into variance the reduction is 86 percent and 75 percent.

## The number to put at the end of a run

I wanted it to be a minimum detectable effect, but that doesn't exist as a single number, because the between-case term depends on the change you are trying to detect, not on the suite.

What does exist is a floor, and it has to carry its assumptions or it promises more than it holds. The sentence to print is "this suite has less than an 80 percent chance of seeing a change smaller than X", which is weaker than "this suite can't see a change smaller than X", and the assumptions behind it are omega squared equal to zero, five cases, a t distribution with 4 degrees of freedom, K equal to 3 per side, alpha 0.05 two-sided, and power 0.80. It's computable from the baseline alone, before you change anything. On the example suite those detection floors are 0.029 and 0.172 for the two scored assertions.

One thing about their scale. Those floors apply to the mean across the suite's cases. For a single case the floor is wider.

The favourable case is omega squared equal to zero, which holds only when the change touches no case differently from any other. Any real change makes that term positive. That's why the number is a floor: an estimate would need that term.

A tool that prints that number next to the outcome is telling the truth about what it can see. A tool that prints a band is telling you it measured something.

## The objection I expect

Five samples aren't enough to assume a distribution.

That's true, but it's no argument for keeping what I have. The range of five draws is an assumption too, and a worse one, because it widens with K. So the choice is between two assumptions: one declared, with a width written next to it, and one that's silent and points the wrong way.

## What this does not support

The 21 runs span 27 minutes, so they say nothing about drift over days or model versions. I tested for drift inside that window with a permutation test on two statistics. One is F, three times the variance of the per-run means divided by the mean of the within-run variances. The other is the absolute Spearman rho between the creation order of the runs and the run mean. 11 bands by 2 statistics, 2000 permutations, seed 7, the 63 samples of each band reshuffled into 21 runs of 3. Two results out of 22 came out below 0.05, `gift-wrap` with `llm_rubric` on F at p equal to 0.017 and `signed-copies` with `llm_rubric` on the Spearman rho at p equal to 0.039. The 1.1 I compare them against is 22 times 0.05, which is arithmetic and not a measurement, and it assumes 22 independent tests. They aren't independent, because the two statistics of a band are computed from the same samples. So the result can't be told apart from chance, and the comparison that says so is a rough one.

The 420 run pairs are ordered pairs and they aren't independent either, since every run appears in many of them. The percentages above describe this set of runs, and I wouldn't read them as a rate.

Miller's appendix C, page 14, says the mean conditional variance and the variance of conditional means should be estimated from previous data having K much greater than 1. I estimated mine at K equal to 3, which is nowhere near that, so the floors above inherit the noise.

The between-case term has one weak estimate, and it's worth writing down with its faults. Splitting the runs in two halves by creation order, runs 1 to 10 and runs 11 to 21, the observed omega squared on the rubric is 0.001944 against 0.001024 expected if omega squared were zero, a ratio of 1.898 at p equal to 0.108. On the Levenshtein it's 0.000017 against 0.000029, a ratio of 0.567 at p equal to 0.687. The p comes from a chi squared with 4 degrees of freedom.

What is wrong with it: normality is assumed on the per-case means. The noise term is treated as known when it's estimated from the same samples, and as equal for every case when it's an average across cases. There are five cases. And the two halves are one configuration split in time, so what they estimate is the omega squared of no change at all. For the term of a real change there is still no measurement, and getting one takes two genuinely different configurations.

There's also a separate defect at the run level, where the value being compared isn't even a mean. It's a different problem with a different fix, and I've left it out to keep this one clear.

## What changes

The decision is public. [ADR 0050](../product/adr/0050-the-noise-floor-compares-a-range-with-means.md), *The noise floor compares a range of single samples with a movement of means*, status *proposed*, in digline's documentation. It says the floor has to compare a movement of means against the dispersion of the mean of the judged samples, and not against the range of the single samples, and that it applies only where an assertion declares it.

That's a break, and mostly it breaks in the direction of noticing more. A check with a tolerance of 0 and a baseline that wasn't unanimous will start reporting movements it used to call unchanged.

The bigger break is the opt-in. Today every sampling assertion gets a floor whether it asked for one or not. Afterwards a check that doesn't declare one has no floor at all and is decided by the tolerance alone. That's the change most likely to surprise somebody, so it goes in the first line of the announcement.

And "noticing more" isn't true at every K. A window a fixed number of standard errors wide narrows as 1 over the square root of K, while the range of single draws widens. So the two can cross at small K, and below such a crossing the new floor would be the wider of the two. Whether there is a crossing at all, and where, depends on how many standard errors the window declares, and that's exactly what the ADR leaves to be declared, so there is no number for it here.

What bothers me is that I had written down a defect of this feature, in my own repository, three weeks before I measured it, and I kept shipping. The one I wrote down was smaller than the one this piece is about, which doesn't help. A finding that stays in a commit message is not a finding. Neither is a measurement whose working directory is gone. That second half of the lesson cost more, and it arrived the day after the measurement.

## Where the numbers came from

One thing before the list. The scripts and the outputs behind these figures live in a private repository, so nobody reading this can re-run them. The list says where each number came from, and that's all it can do.

**The median band widths as K varies.** A resampling of each band's 63 samples, 5000 draws of K without replacement, seed 20261014.

**The ratios between widths, 4.808650 at the low end and 146.550201 at the high end, the two bands with no ratio, the widest band at 0.6500 and the 0.5833.** Widths at K equal to 3, with each of the 21 runs taken in turn as the reference, computed from the recorded samples. No resampling. The body rounds those two ratios to about 5 and about 150, and these are the exact values.

**How much the band adds, 0.3167, 0.3000 and 0.046, and the 7, 13, 13, 11 and 12 references out of 21.** The measurement script over the 21 runs, counted only on the side of the threshold where the reference sits.

**The detection floors 0.029 and 0.172, the two pairs for the variance of the mean, the ratios 0.37 and 0.50 and the correlations 0.91 and 0.77.** The variance decomposition over the 21 runs.

**The omega squared of the two halves, 0.001944 against 0.001024 at a ratio of 1.898 and p 0.108, and 0.000017 against 0.000029 at a ratio of 0.567 and p 0.687.** The same variance decomposition, measured again so that the test could be attached to it.

**The frequencies 18, 39, 48, 21 and 35 out of 420 pairs, and the raw counts in the three-stage table.** The product's own comparison function, through its outcome for every comparison and through its verdict of "within noise" for the ones the band decided.

**The first and last columns of that table, and all of its percentages.** Arithmetic over those counts, as with the 1.1. No script prints them.

**The zero over the 725 comparisons, the 551 zero-width bands, the 29 full-scale ones, the positive control at 174 and the cost widths up to 0.224054.** The measurement script with every probe passed through the comparison function, three executions run from two different directories, all three identical to the saved output.

**The 2 out of 22, at p equal to 0.017 and p equal to 0.039.** A permutation test, 2000 permutations, seed 7.

**The 1.1.** Arithmetic, and the body says so where it uses it.

**The five citations of Miller.** Verified against the rendered pages of the PDF, which is arXiv 2411.00640v1. The omega squared formula at section 5 page 9, verbatim. The super-population quote at section 3 page 5. Recommendation four on page 2. Equation 7 at section 4.2 page 7. And the sentence about K much greater than 1 in appendix C page 14, which this piece paraphrases rather than quotes, as it should.
