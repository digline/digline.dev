---
title: "The more samples I took, the less my noise floor could see"
description: "A noise floor built from the range of K single samples, compared against a mean: why it widens as K grows while the measurement behind it gets better, what it adds on two real suites, and what should replace it."
seo_title: >-
  The more samples I took, the less my noise floor could see
date: 2026-10-16
---

# The more samples I took, the less my noise floor could see

On 21 September I noted a problem in a commit message, in a private repository. The note said that the samples of one check are binary, so for any case whose samples disagree the recorded minimum is 0.0 and the maximum is 1.0.

I pushed the commit and kept shipping the feature. Three weeks later I measured it properly. The defect was worse than the one I had written down.

## What the band is

digline runs each case K times against the approved version. It records the minimum and the maximum of the K scores next to the baseline. This post calls that recorded range the band.

A later run is compared with the baseline in four steps:

1. A case whose pass/fail outcome flipped is reported as changed. It never reaches the band.
2. The denominator check refuses to compare two aggregate scores computed over different numbers of items. It does not act on the score of a single case.
3. The **declared tolerance** absorbs small drops.
4. The band absorbs any remaining drop that falls inside the recorded range.

A drop therefore counts as a regression only if it falls outside the tolerance **and** outside the band. Because the band is the last step, the tolerance can make it redundant.

The idea behind the band is sound: a tool should not alert on movement that the system already shows when nothing has changed. The implementation is wrong, for one reason.

**The band is the range of single samples, but it is compared against a mean.** As K grows, the range of the samples widens toward the full spread of the distribution. The extremes of a sample always behave this way. As K grows, the mean also becomes more precise. A wider band hides larger drops. So the more samples the band uses, the less it can detect, while the measurement behind it improves.

This holds for every check, binary or not. The rest of this post measures how much it matters.

## Measured

The first suite comes from the repository's own examples. I ran it 21 times with one unchanged prompt. In this post a band is one pair of case and assertion, and each band has 63 samples.

I discarded an earlier pass against the committed baseline, for a reason that had nothing to do with its numbers. The prompt differed in all 21 comparisons, so that baseline had been recorded under a different prompt. The pass therefore measured a deliberate change plus noise, and reported the sum as noise.

The suite has two assertions and six cases, which make eleven bands. `levenshtein` runs on five of the cases. `llm_rubric` runs on all six. The case `calibration-half-right` has `llm_rubric` only.

**The width grows with K.** Median band width at K equal to 2, 5 and 31:

| Assertion | K=2 | K=5 | K=31 |
|---|---|---|---|
| rubric | 0.1167 | 0.3000 | 0.4833 |
| Levenshtein | 0.0136 | 0.0339 | 0.0738 |

The table comes from resampling. For each band I took its 63 samples, drew K of them without replacement 5000 times with seed 20261014, and kept the median width. I then took the median across the five non-calibration cases. I never ran the suite at K equal to 31. No cell in the table is a band: each cell is a median of per-case medians, and it matches a real band only by accident.

Across the three values of K shown, the width only increases. From K=2 to K=31 it grows by a factor of 4.1 on the rubric and 5.4 on Levenshtein. Over the same range, the dispersion of the mean falls.

**The width also depends on which run you approved.** For this result I set K to 3 and used each of the 21 runs in turn as the baseline. Nine bands have a finite ratio between their widest and narrowest width. That ratio ranges from about 5, on `order-a-book` with `levenshtein`, to about 150, on `price-check` with `levenshtein`. Only the choice of baseline run changes. The system, the cases and the day are the same.

The other two bands have no finite ratio, because some baseline runs give them zero width. This happens for `calibration-half-right` in 6 of the 21 baselines, and for `gift-wrap` with `llm_rubric` in 1. This is the stronger result: on these two bands, the choice of baseline can shrink the band to a single point. The widest band in the whole set is 0.6500, on `opening-hours` with `llm_rubric`.

**The variance model fits where I can check it.** Across the 21 runs, on the two scored assertions, the observed variance of the mean is 0.000027 against 0.000031 predicted from internal noise alone, and 0.00132 against 0.00107. One value is below the prediction and one is above.

## What the band actually adds

The declared rules are as follows. `levenshtein` has a pass threshold of 0.75 and a tolerance of 0.05. `llm_rubric` has a threshold of 0.7 and a tolerance of 0.1. Each comparison uses three samples.

A delta counts as unchanged if it falls inside the tolerance **or** inside the band. The band can therefore only add unchanged verdicts. It can never remove one. The quantity to measure is how much it adds.

The largest margin the band adds beyond the tolerance is **0.3167 of the scale**, on `price-check` with `llm_rubric`, whose widest band is 0.5833. This is not the widest band in the set. On `opening-hours` with `llm_rubric`, whose widest band is 0.65, the largest added margin is 0.3000. On `price-check` with `levenshtein` the band adds **0.046**.

Two different tools produced the numbers in this section. A measurement script computed the added margin and counted the baselines on which the band extends beyond the tolerance. It counts only on the side of the threshold where the baseline sits. digline's own comparison function produced the counts out of 420 and the table below. It reports the outcome of every comparison, and the verdict "within noise" when the band decided it.

The two frequencies below answer different questions. **Both refer to the five rubric bands.** On the Levenshtein assertion the first frequency is 0 or 1, and on the calibration case it is 0.

The first frequency is how often the band extends beyond the tolerance at all. With K equal to 3 and each of the 21 runs used in turn as the baseline, this happens in 7, 13, 13, 11 and 12 of the 21 baselines. The second frequency is how often the band decided a comparison. The band declared a delta unchanged in 18, 39, 48, 21 and 35 of **420 run pairs**, which is **4.3 to 11.4 percent of comparisons**. The pairs are not independent, as the limits section explains.

These suppressed comparisons are not missed regressions. All 21 runs use one configuration with one unchanged prompt, so every delta between two of them is noise. There is no regression in this set for the band to hide. Every comparison the band declared unchanged was a false alarm, and the band suppressed it correctly. The mechanism still only enlarges what the gate cannot see. On these runs, enlarging it was correct.

The table shows the three stages for the five rubric bands, over the 420 pairs:

| Band | outside the tolerance, before the band, flips excluded | after the band | flips | after, plus flips |
|---|---|---|---|---|
| `gift-wrap` | 142 (33.8%) | 124 (29.5%) | 0 | 124 (29.5%) |
| `opening-hours` | 122 (29.0%) | 83 (19.8%) | 0 | 83 (19.8%) |
| `order-a-book` | 126 (30.0%) | 78 (18.6%) | 76 | 154 (36.7%) |
| `price-check` | 90 (21.4%) | 69 (16.4%) | 0 | 69 (16.4%) |
| `signed-copies` | 148 (35.2%) | 113 (26.9%) | 40 | 153 (36.4%) |

The difference between the first two columns is 18, 39, 48, 21 and 35. These are the counts from the paragraph above, measured at two stages.

Flips never reach the band, and the gate reports them anyway. With an unchanged prompt, they are also noise. The last column is therefore the share of comparisons the gate flagged on these runs: 16.4 to 36.7 percent.

So the band suppresses 4 to 11 comparisons in a hundred, in a gate that flagged up to 37 in a hundred. On these runs every flag was a false alarm. Removing the band without changing the tolerance would make the gate noisier. The case against the band rests on how it behaves as K grows and on what it does to binary checks. These frequencies are not part of that case.

On this suite, then, the band does some work. It decides a few comparisons in a hundred, on some assertions only, depending on which run was approved. On this data it decides them correctly.

## The second number nobody measured

I did not expect this result. It is the reason the title of this post is about K.

Whether the band decides anything depends on the tolerance. It also depends on **`min_agreement`**, the setting that says how many of the K samples must agree for a case to count. The setting has no default. A suite that samples must declare it, or digline refuses to run.

Take a binary check with K equal to 5 and a pass threshold of 0.5. The largest movement that can occur without crossing the threshold is:

| `min_agreement` | largest movement that exists |
|---|---|
| 2/5 and below | 0.5 |
| 3/5 | 0.4 |
| 4/5 | 0.2 |
| unanimity | none |

Two things must be kept apart here. Each row of the table is a setting, chosen once for the whole suite. Agreement is a property of a single comparison. At any setting below unanimity, a suite contains both unanimous and split comparisons.

When the baseline samples of a comparison disagree, the minimum is 0 and the maximum is 1. The band then covers the entire scale and excuses every movement allowed in that row. When the baseline samples are unanimous, the band is a single point and excuses nothing.

So the setting fixes the largest movement that can occur. The band then decides, case by case, whether that movement is reported. On split cases it is never reported.

## What is binary and what is not

The table above applies to binary checks, and the difference matters.

Unanimity is a property of states, not scores. A split binary baseline always contains 0 and 1, so its band is the whole interval. A split rubric baseline contains only the scores it actually produced, so its band is narrower. In one rubric assertion I measured, the samples ranged from 0.45 to 0.6. That band does not excuse a movement of 0.33.

The claim that "the band swallows everything" therefore applies only to binary checks. For every check, binary or not, the main result still holds: a range of single samples is compared against a mean, and the range widens with K while the mean becomes more precise.

Hiroki Tamba's paper on temperature control and reproducibility in LLM-as-judge evaluations shows that a judge can return different verdicts on the same input, even at temperature 0. The paper shows that this disagreement can persist. It states explicitly that it does not estimate how often it happens. Its test items were built to sit at the decision boundary, which is where split baselines come from.

## The measurement I threw away and then did again

The second suite is the judge for a pipeline I run every day. It has 145 cases and 5 assertions per case, so 725 comparisons. Each case uses five samples, and the suite sets `min_agreement` to 3/5.

I measured the band on this suite and wrote the numbers down. Later I could not reproduce them, because the script and the table had been in a working directory that no longer existed. I applied to myself the rule this post is about: a figure you cannot regenerate is not a measurement, whatever you remember about it. I withdrew the numbers.

Then I measured again and kept the artefacts. Every probe went through the real comparison function. The script and its output were saved. I ran the script three times from two different directories, and all three outputs matched the saved one. A positive control showed that the detector works.

**The band adds nothing to any of the 725 comparisons.** This holds for every comparison, not only on average. For all five assertions, the probe searched from both sides of the baseline score, not of the threshold. It looked for a value inside the band, outside the tolerance, and on the same side of the threshold as the baseline. It found none. 551 of the bands have zero width, and 29 cover the entire scale.

Five of the comparisons belong to one case that is in the suite because the judge is unstable on it. That case acts as a sentinel for the noise this post is about. The band adds nothing on those five comparisons either.

The positive control is what makes the zero meaningful. With the tolerance set to 0, the same probes find 174 comparisons where the band decides the outcome. That is the expected number: 145 from the cost check, one per case, plus the 29 full-scale bands. So the zero is a zero, not a broken test.

There are two reasons for the zero. Only the first holds for any baseline.

**The reason that holds for any baseline.** Agreement is always computed over five samples, so the guarantee follows from the number of samples that were judged. With five judged, the means are multiples of 0.2, and the largest movement that stays on one side of the threshold is 0.4. With four judged, only 4-0 and 3-1 reach 3/5, so the possible means are 0, 0.25, 0.75 and 1, and the largest movement is 0.25. With three judged, only 3-0 reaches 3/5, and the largest movement is 0. With two judged, every case errors. The largest movement in any of these is 0.4, and the declared tolerance is 0.41. So the guarantee comes from `min_agreement`, and "every sample was judged" adds nothing to it.

This argument covers two of the five assertions: the two that score agreement with a threshold of 0.5 and a tolerance of 0.41. A third assertion is covered by construction. Its threshold is 0.0 and its tolerance is 1.0, which is the whole scale.

**The reason that holds only for this baseline.** The schema check has a threshold of 1.0 and a tolerance of 0.0, so nothing in its configuration protects it. Its zero comes from all 145 of its bands having zero width on this baseline. The cost check has a threshold of 0.5 and a tolerance of 0.15, and its bands are up to 0.224054 wide. Its zero is a measurement and nothing more.

This limit is wider than I first stated. On this baseline, three of the five assertions pass in all 145 cases, so the probe only ever saw their passing side: the schema check, the assertion with threshold 0.0, and the cost check. For the assertion with threshold 0.0 this does not matter, because a tolerance of 1.0 covers the whole scale. For the cost check it does matter. The two assertions that have both sides have 18 and 16 failing comparisons. If the schema check failed on a case whose samples disagreed, the band would again affect the decision.

## Why the two quantities move in opposite directions

Evan Miller's paper on error bars in evals explained this, though not in the way I first assumed.

Miller splits the variance of an eval score into two parts: the variance of the conditional mean across questions, and the mean conditional variance within a question. Resampling reduces the second part and never the first, because the first is, in his words, "a property of the super-population and therefore immutable" (section 3, page 5). I first concluded that the gain from more samples hits a ceiling, and I wrote that down.

That conclusion is correct when you compare two different models on a benchmark. digline compares a system against its own earlier state, on the same fixed set of cases. Miller's formula for the two-model case shows the difference. The term that carries the between-question variance is

> omega squared = Var(x_A) + Var(x_B) - 2 Cov(x_A, x_B)

(section 5, page 9). When both sides use the same cases and the difficulty of each case has not changed, the covariance cancels the two variances and the term is zero. The remaining term is the within-case variance divided by K, and it keeps falling as K grows.

This cancellation follows from the design, because the cases are identical on both sides. I have one weak estimate of the term, and the limits section describes its problems.

None of this is Miller's view of bands. His paper never discusses the extremes, ranges, minima or maxima of samples. Its intervals are confidence intervals, for a mean and for a difference. Nobody told me to build a min-max band. I built it because it looked like a measurement.

## What it should be instead

The replacement is paired differences, per case.

This is recommendation four in Miller's paper, on page 2: when comparing, do the inference on the question-level paired differences rather than the population-level summary statistics. The standard error of those differences is equation 7, section 4.2, page 7.

My case is favourable for this technique, because both sides use the same suite and the per-case difficulty cancels. I measured the gain instead of citing it. The paired standard error is 0.37 of the unpaired one on one assertion and 0.50 on the other. The per-case correlations are 0.91 and 0.77. These are ratios of standard errors. Squared into variance, the reduction is 86 percent and 75 percent.

## The number to put at the end of a run

I wanted to report a minimum detectable effect. It does not exist as a single number, because the between-case term depends on the change you are trying to detect, not on the suite.

What does exist is a detection floor. It must state its assumptions, or it promises more than it can deliver. The sentence to print is "this suite has less than an 80 percent chance of detecting a change smaller than X". This is weaker than "this suite cannot detect a change smaller than X". The assumptions are omega squared equal to zero, five cases, a t distribution with 4 degrees of freedom, K equal to 3 per side, alpha 0.05 two-sided, and power 0.80. The floor can be computed from the baseline alone, before any change. On the example suite the detection floors are 0.029 and 0.172 for the two scored assertions.

These floors apply to the mean across the suite's cases. For a single case the floor is wider.

The assumption that omega squared is zero is the favourable one: it holds only when the change affects every case in the same way. Any real change makes the term positive. That is why the number is a floor: an estimate would need that term.

The principle is not mine. Tamba's paper recommends reporting grader disagreement as a first-class health metric of the harness, because a harness that reports single-run verdicts without their variance can present noise as a safety property. This section applies the same argument to a gate. My band did the opposite: it used the disagreement to excuse movement, so the disagreement was never reported to anyone.

A tool that prints that number next to the outcome is telling the truth about what it can see. A tool that prints a band is telling you it measured something.

## The objection I expect

A likely objection is that five samples are not enough to assume a distribution.

That is true, but it is not a reason to keep the band. The range of five samples is also an assumption, and a worse one, because it widens with K. The choice is between two assumptions. One is declared and has its width printed next to it. The other is silent and points the wrong way.

## What this does not support

The 21 runs cover 27 minutes. They say nothing about drift over days or across model versions.

I tested for drift within that window with a permutation test on two statistics. The first is F: three times the variance of the per-run means, divided by the mean of the within-run variances. The second is the absolute Spearman rho between the creation order of the runs and the run mean. The test covered 11 bands and 2 statistics, with 2000 permutations and seed 7. For each band, the 63 samples were reshuffled into 21 runs of 3. Two of the 22 results were below 0.05: `gift-wrap` with `llm_rubric` on F, at p equal to 0.017, and `signed-copies` with `llm_rubric` on the Spearman rho, at p equal to 0.039. By chance alone you would expect 1.1, which is 22 times 0.05. That figure is arithmetic and not a measurement, and it assumes 22 independent tests. The tests are not independent, because the two statistics for a band use the same samples. So the result cannot be distinguished from chance, and this comparison is only approximate.

The 420 run pairs are ordered pairs. They are not independent either, because every run appears in many of them. The percentages above describe this set of runs. I would not read them as a rate.

Miller's appendix C, on page 14, says the mean conditional variance and the variance of conditional means should be estimated from earlier data with K much greater than 1. I estimated mine at K equal to 3, which is nowhere near that. The floors above therefore inherit that noise.

I have one weak estimate of the between-case term, and it has several problems. I split the runs into two halves by creation order: runs 1 to 10 and runs 11 to 21. On the rubric, the observed omega squared is 0.001944, against 0.001024 expected if omega squared were zero. That is a ratio of 1.898, at p equal to 0.108. On Levenshtein it is 0.000017 against 0.000029, a ratio of 0.567, at p equal to 0.687. The p-values come from a chi-squared distribution with 4 degrees of freedom.

The problems with this estimate are these. It assumes that the per-case means are normal. It treats the noise term as known, although it is estimated from the same samples. It treats the noise as equal for every case, although it is an average across cases. There are only five cases. And the two halves are one configuration split in time, so they estimate the omega squared of no change at all. The term for a real change has still not been measured. Measuring it needs two genuinely different configurations.

There is also a separate defect at the run level, where the value being compared is not even a mean. It is a different problem with a different fix, and I have left it out of this post.

## What changes

The decision is public in [ADR 0050](../product/adr/0050-the-noise-floor-compares-a-range-with-means.md), *The noise floor compares a range of single samples with a movement of means*, status *proposed*, in digline's documentation. It says the floor must compare a movement of means against the dispersion of the mean of the judged samples, and not against the range of single samples. It also says the floor applies only where an assertion declares it.

This is a breaking change, and mostly it makes digline report more. A check with a tolerance of 0 and a non-unanimous baseline will start reporting movements it used to call unchanged.

The opt-in is the larger break. Today every sampling assertion gets a floor, whether it asks for one or not. After the change, a check that does not declare a floor has none, and only the tolerance decides it. This is the change most likely to surprise users, so it goes in the first line of the announcement.

"Reporting more" is not true at every K. A window a fixed number of standard errors wide narrows as 1 over the square root of K, while the range of single samples widens. The two can therefore cross at small K. Below the crossing, the new floor would be the wider of the two. Whether a crossing exists, and where, depends on how many standard errors the window declares. The ADR leaves that number to be declared, so this post cannot give it.

What bothers me is that I had written down a defect of this feature, in my own repository, three weeks before I measured it, and I kept shipping. The defect I wrote down was smaller than the one this post describes, which does not help. A finding that stays in a commit message is not a finding. Neither is a measurement whose working directory is gone. That second half of the lesson cost more, and it arrived the day after the measurement.

## Where the numbers came from

The scripts and the outputs behind these figures are in a private repository, so readers cannot re-run them. This list says where each number came from.

**The median band widths as K varies.** A resampling of each band's 63 samples, 5000 draws of K without replacement, seed 20261014.

**The ratios between widths, 4.808650 at the low end and 146.550201 at the high end, the two bands with no ratio, the widest band at 0.6500 and the 0.5833.** Widths at K equal to 3, with each of the 21 runs used in turn as the baseline, computed from the recorded samples. No resampling. The body rounds the two ratios to about 5 and about 150. These are the exact values.

**How much the band adds, 0.3167, 0.3000 and 0.046, and the 7, 13, 13, 11 and 12 baselines out of 21.** The measurement script over the 21 runs, counting only on the side of the threshold where the baseline sits.

**The detection floors 0.029 and 0.172, the two pairs for the variance of the mean, the ratios 0.37 and 0.50 and the correlations 0.91 and 0.77.** The variance decomposition over the 21 runs.

**The omega squared of the two halves, 0.001944 against 0.001024 at a ratio of 1.898 and p 0.108, and 0.000017 against 0.000029 at a ratio of 0.567 and p 0.687.** The same variance decomposition, run again so that the test could be attached to it.

**The frequencies 18, 39, 48, 21 and 35 out of 420 pairs, and the raw counts in the three-stage table.** digline's own comparison function, through its outcome for every comparison and its verdict of "within noise" for the ones the band decided.

**The first and last columns of that table, and all of its percentages.** Arithmetic over those counts, as with the 1.1. No script prints them.

**The zero over the 725 comparisons, the 551 zero-width bands, the 29 full-scale ones, the positive control at 174 and the cost widths up to 0.224054.** The measurement script with every probe passed through the comparison function, run three times from two different directories, all three identical to the saved output.

**The 2 out of 22, at p equal to 0.017 and p equal to 0.039.** A permutation test, 2000 permutations, seed 7.

**The 1.1.** Arithmetic, and the body says so where it uses it.

**The citations of Tamba.** arXiv 2606.26185v1, the only version. The repeated-grading design is at section 4.1, page 3. The recommendation to surface grader disagreement as a first-class harness health metric is M4, section 6, page 6. The paper's own limit, that it demonstrates non-determinism can persist rather than estimating a rate, is section 5.4, page 6. No figure from the paper is quoted here.

**The five citations of Miller.** Verified against the rendered pages of the PDF, which is arXiv 2411.00640v1. The omega squared formula is at section 5, page 9, verbatim. The super-population quote is at section 3, page 5. Recommendation four is on page 2. Equation 7 is at section 4.2, page 7. The sentence about K much greater than 1 is in appendix C, page 14, which this post paraphrases rather than quotes.
