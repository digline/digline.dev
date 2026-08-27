# 4. The judge

Chapter 3 ended with a rule: at most one judged check, sampled, with a measured tolerance. This chapter is about the word *measured* — what happens when you skip it, and the forty-minute procedure that replaces guessing with a number. All the figures are from the [newsletter judge](https://github.com/digline/brief), and you can reproduce them.

## Two noises, not one

There are two places a model can change its mind, and they need different remedies.

**The system under test** is a model. Ask it the same thing twice and it may answer differently. In the newsletter project the judge *is* the system: it scores articles. Run the suite twice with nothing changed and one article in twenty-one flips from 4 to 3.

**The judge** — the model you use inside a check to evaluate an output — is also a model, and also flips. If your rubric asks "is this reply polite?", the judge may say 0.8 today and 0.7 tomorrow about the same reply.

The remedy for the first is to ask the *system* several times per case and combine. The remedy for the second is to ask the *judge* several times per output and combine. They look alike and they are not: the first measures how stable your product is, the second how stable your ruler is. Confusing them means fixing the ruler when the product wobbles, or the other way round. Decide which one you are looking at before you touch anything.

## What one sample costs you

Before sampling, the newsletter suite checked each article once. On the first run, twenty-one verdicts. On the second — same prompt, same articles, same model — twenty identical and one different. With a binary check and no tolerance, that one flip is a regression: the comparison turns red, the CI fails, someone investigates, nothing was wrong.

One false alarm in three runs is enough to make a team stop reading the alarms. That is the real cost of a single sample: not the wrong number, but the moment the red stops meaning anything.

## Sampling

The fix is to ask more than once and combine. Three samples per case turned the binary verdict into a fraction — 0, ⅓, ⅔ or 1 — and the check into "the judge agrees with the reader in at least two votes out of three", with a tolerance of one vote for the comparison against the reference.

Three questions come with sampling, and the answers matter more than the number three:

**Combine how?** The score is the mean of the samples. But the interesting quantity is *agreement*: how many samples share the majority verdict. Three scores of 0.80, 0.85, 0.99 disagree loudly and agree completely on the verdict; three of 0.69, 0.71, 0.70 sit within two points of each other and split down the middle on a threshold of 0.70. Agreement sees the second case; the mean does not.

**What if they cannot agree?** Then the judgement was not possible, and the honest answer is *could not judge* — a third state, neither pass nor fail. A case whose samples split evenly is not a regression and not a success; it is a case the judge cannot decide, and a reference built on it would be a reference to a coin flip. Set a minimum agreement (`"3/5"`, say) below which the verdict is an error, and refuse to promote a run that contains one.

**Write fractions as fractions.** "Two out of three" written as `0.67` is a trap: ⅔ is 0.666…, which is *below* 0.67, and every case with one dissenting vote becomes an error. It happened on the first try. `"2/3"` says what you mean and cannot be off by a rounding.

## Measuring the tolerance

The tolerance is the size of change you agree to ignore as noise. Everyone picks it by feel; almost everyone picks it wrong, because the noise of a judge cannot be guessed from the outside. It can be measured in forty minutes:

1. Freeze everything — prompt, model, cases.
2. Run the suite three times.
3. For each case, look at the largest difference between any two runs.
4. The tolerance is that largest difference, plus a little margin.
5. If that number is as large as the differences you want to *catch*, stop: the check is too noisy to be a gate. Sample more, or change the check — do not widen the tolerance until it swallows everything.

Here is what the procedure showed on the newsletter judge at three samples:

| case | run 1 | run 2 | run 3 |
|---|---|---|---|
| how-we-built-claude-code-auto-mode | 1.00 | 0.67 | 0.33 |
| more-than-just-code-review | 0.67 | 1.00 | 0.33 |
| don-t-classify-hallucinate | 0.67 | 0.33 | 0.00 |
| the other eighteen | stable, or within one vote | | |

Three cases swung by two votes out of three on an unchanged system. A tolerance that absorbed that would be ⅔ — wider than any change worth detecting. Step 5 applied: the fix was not the tolerance, it was more samples.

At five samples the same three cases swung by at most two votes out of five in three runs out of four. Not zero — one case still jumps three votes about one run in three — but a gate that fires falsely once every few runs instead of every other run, and a per-case table that tells you exactly which cases the judge is unsure about. Those turned out to be the articles a human would also hesitate over. The judge was not broken; it was honest about the borderline.

## The aggregate is calmer than the cases

The same runs showed something that changes what you put a threshold on. While individual cases jumped by three votes, the number of cases where judge and reader agreed was 14, 14, 15, 15 out of 21 across four runs — moving by one case while the cases beneath it swung.

That is the general pattern, and it is the reason a suite with labelled cases should gate on an aggregate — precision, accuracy, recall — and use the per-case verdicts for diagnosis. A gate on "at least 60% agreement, tolerance one case" would not have fired once across those four runs. A gate on any single case would have fired on most of them.

## The judge's prompt is a prompt

It drifts for the same reasons yours does, and it deserves the same treatment: a file, versioned, recorded with every run. When a judged check starts failing, the first question is not "did the system get worse?" but "did the ruler change?" — and if the judge's prompt is a string inside a function somewhere, you cannot answer it.

Two smaller habits. First, keep the instruction before the output in the judge's prompt, and label the output clearly; a judge that reads an instruction after the text it was asked to judge will sometimes judge the instruction. Second, when you test your suite with a fake judge — and you should — build the fake from one *real* reply, not from what you think the reply looks like. A fake written from the code confirms the code; the newsletter project found a cost under-counted by 384× with every test green, because the fake and the code shared the same wrong assumption about the API's shape.

## Doing it today

1. Decide which noise you are looking at: the system's or the judge's.
2. Sample it — three to start, five if three is not enough — and set a minimum agreement below which the verdict is *could not judge*.
3. Freeze everything and run three times. Read the largest per-case difference. That is your tolerance, or your signal to sample more.
4. If you have labels, put the gate on the aggregate.
5. Move the judge's prompt into a file next to the system's, and record both with every run.

The next chapter is about what to do once the numbers are stable: the run you approve, and why it should be the median of several and not the first green one.

---

*Previous: [3. Checks: deterministic first, judge last](03-checks.md) · Next: [5. The reference](05-the-reference.md)*
