---
seo_title: >-
  The judge, and how to measure its noise
description: >-
  An LLM judge samples too. Why you must measure the judge's noise before
  you can read your system's, and the procedure that replaces guessing
  with a number.
---

# 5. The judge

Chapter 4 ended with a rule: at most one judged check, sampled, with a measured tolerance. This chapter is about the word *measured* — what happens when you skip it, and the procedure that replaces guessing with a number. The measurements are from the six runs the [newsletter judge](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/README.md) publishes, and you can recompute them.

## Two noises, not one

There are two places a model can change its mind, and they need different remedies.

**The system under test** is a model. Ask it the same thing twice and it may answer differently. In the newsletter project the judge *is* the system: it scores articles. Run the suite twice, fifteen minutes apart, with nothing changed, and one article in twenty-one changes verdict.

**The judge** — the model you use inside a check to evaluate an output — is also a model, and also flips. If your rubric asks "is this reply polite?", the judge may say 0.8 today and 0.7 tomorrow about the same reply.

The remedy for the first is to ask the *system* several times per case and combine. The remedy for the second is to ask the *judge* several times per output and combine. They look alike and they are not: the first measures how stable your product is, the second how stable your ruler is. Confusing them means fixing the ruler when the product wobbles, or the other way round. Decide which one you are looking at before you touch anything.

## What one sample costs you

A verdict from one sample is one draw. On a case the judge finds easy, the draw almost always lands the same way; on a borderline one it is a coin toss, and any real set of cases has a few borderline ones. With a binary check and no tolerance, every toss that lands the other way is a regression: the comparison turns red, the CI fails, someone investigates, nothing was wrong.

A few of those are enough to make a team stop reading the alarms. That is the real cost of a single sample: not the wrong number, but the moment the red stops meaning anything.

## Sampling

The fix is to ask more than once and combine. The newsletter suite asks five times per case, which turns the binary verdict into a fraction — 0, 0.2, 0.4, 0.6, 0.8 or 1 — and the check into "the judge agrees with the reader in at least three votes out of five".

Three questions come with sampling, and the answers matter more than the number five:

**Combine how?** The score is the mean of the samples. But the interesting quantity is *agreement*: how many samples share the majority verdict. Take made-up scores: three samples of 0.80, 0.85, 0.99 disagree loudly and agree completely on the verdict; three of 0.69, 0.71, 0.70 sit within two points of each other and split two to one on a threshold of 0.70. Agreement sees the second case; the mean does not.

**What if they cannot agree?** Then the judgement was not possible, and the honest answer is *could not judge* — a third state, neither pass nor fail. A case whose samples split three to two is not a regression and not a success; it is a case the judge cannot decide, and a reference built on it would be a reference to a coin flip. Set a minimum agreement below which the verdict is an error, and refuse to promote a run that contains one — but set it where it can fire. With five samples the majority is always at least three, so `"3/5"` never refuses a vote in which every sample was judged; the floor that catches a three-to-two split is `"4/5"`.

**Write fractions as fractions.** "Two out of three" written as `0.67` is a trap: ⅔ is 0.666…, which is *below* 0.67, and every case with one dissenting vote out of three becomes an error. `"2/3"` says what you mean and cannot be off by a rounding; the newsletter suite writes `"3/5"`.

## Measuring the tolerance

The tolerance is the size of change you agree to ignore as noise. Everyone picks it by feel; almost everyone picks it wrong, because the noise of a judge cannot be guessed from the outside. It can be measured, in three runs:

1. Freeze everything — prompt, model, cases.
2. Run the suite three times.
3. For each case, look at the largest difference between any two runs.
4. The tolerance is that largest difference, plus a little margin.
5. If that number is as large as the differences you want to *catch*, stop: the check is too noisy to be a gate. Sample more, or change the check — do not widen the tolerance until it swallows everything.

Here is what it shows on the newsletter judge: six runs, five samples per case, with the same prompts, the same cases and the same configuration. Each cell is how many of the five samples agreed with the reader; the times are UTC.

| case | 1 Sep 12:29 | 1 Sep 12:44 | 3 Sep 06:14 | 3 Sep 06:18 | 3 Sep 06:24 | 3 Sep 06:30 |
|---|---|---|---|---|---|---|
| evals-skills-for-coding-agents | 2 | 5 | 5 | 2 | 5 | 5 |
| more-than-just-code-review | 4 | 5 | 5 | 2 | 5 | 5 |
| controlling-reasoning-effort-in-llms | 5 | 4 | 3 | 5 | 5 | 4 |
| recent-developments-in-llm-architectures | 5 | 4 | 5 | 3 | 5 | 4 |
| the other seventeen | within two votes, and the majority never changes | | | | | |

Two cases swung by three votes out of five on an unchanged system, and in any one run between two and six of the twenty-one cases were split. On a single case, then, step 5 applies: a tolerance that absorbed three votes would be as wide as any change on that case worth catching. The suite declares two votes per case, and lets a three-vote swing show. The per-case table is still worth having: it tells you exactly which cases the judge is unsure about.

## The aggregate is calmer than the cases

The same runs showed something that changes what you put a threshold on. While single cases jumped by three votes out of five, the number of articles on which judge and reader agreed was 15, 16, 16, 14, 16 and 16 out of 21 across the six runs — never more than two apart.

That is the general pattern, and it is the reason a suite with labelled cases should gate on an aggregate — precision, accuracy, recall — and use the per-case verdicts for diagnosis. A threshold of 60% agreement would not have fired on any of the six. Against the reference the project keeps, the per-case check, with its two votes of tolerance, went red on two of the other five.

## The judge's prompt is a prompt

It drifts for the same reasons yours does, and it deserves the same treatment: a file, versioned, recorded with every run. When a judged check starts failing, the first question is not "did the system get worse?" but "did the ruler change?" — and if the judge's prompt is a string inside a function somewhere, you cannot answer it.

Two smaller habits. First, keep the instruction before the output in the judge's prompt, and label the output clearly; a judge that reads an instruction after the text it was asked to judge will sometimes judge the instruction. Second, when you test your suite with a fake judge — and you should — build the fake from one *real* reply, not from what you think the reply looks like. A fake written from the code confirms the code; the newsletter project [found a cost under-counted by 384×](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/README.md#the-fake-judge-and-ci) with every test green, because the fake and the code shared the same wrong assumption about the API's shape.

## Doing it today

1. Decide which noise you are looking at: the system's or the judge's.
2. Sample it — the newsletter suite asks five times — and set a minimum agreement below which the verdict is *could not judge*.
3. Freeze everything and run three times. Read the largest per-case difference. That is your tolerance, or your signal to sample more.
4. If you have labels, put the gate on the aggregate.
5. Move the judge's prompt into a file next to the system's, and record both with every run.

The next chapter is about what to do once the numbers are stable: the run you approve, and why it should be the median of several and not the first green one.
