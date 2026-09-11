---
title: "Bad evals, my own: five exercises from two LLM judges"
seo_title: >-
  Five exercises on my own LLM judge evals
description: >-
  I applied the reading Dan Luu applies to other people's benchmarks to my own
  two LLM judges. Numbers first, explanations after.
date: 2026-09-11
---

# Bad evals, my own: five exercises from two LLM judges

I run two small LLM judges. One reads ~200 items a day from AI feeds and tells me which five to read (I call it brief). The other reads Reddit threads and tells me which ones are worth a comment from me (scout). Both have a regression suite, both have a promoted baseline, both go through a gate before I change a prompt. I built the gate, so I had every reason to believe the numbers.

Then I reread [Dan Luu's exercise 7](https://danluu.com/exercise-7/), which we cite on the [why page](../why.md). His method is simple: show the benchmark as published, ask "what's wrong with this?", and only then explain. His point is that you don't need domain expertise to find these problems, just the reasoning you'd apply to any experiment. So I applied it to my own judges. Below are five exercises. Every number comes from files in the two repos, with the run id, and at the end there's a section on what this exercise found in the tool itself, which was not the plan.

As in the original, the artifacts come first and the explanations later, in case you want to think before reading mine.

## The exercises

### 1. Three runs, nothing changed

On September 3 I ran the brief suite three times in ten minutes. 21 cases, Haiku 4.5, 5 samples per case, majority vote. The run files record the config hash and the sha256 of both prompt files; all three are identical (`98fc65b1e49e930e`, `05c20df6…`, `3ce6ed3b…`), and git shows no commit touching `prompts/` between the first and the third.

Aggregates: **16/21 → 14/21 → 16/21** accuracy, 10/15 → 9/15 → 10/15 precision.

Here are the seven cases where at least one run was not unanimous. Each string is the five samples of the "agrees with my mark" assertion, 1 = agreed. `(p)`/`(f)` is the majority verdict.

| case | run 06:14 | run 06:18 | run 06:24 |
|---|---|---|---|
| controlling reasoning effort | 10110 (p) | 11111 (p) | 11111 (p) |
| don't classify, hallucinate | 11111 (p) | 11101 (p) | 11110 (p) |
| more than just code review | 11111 (p) | **01010 (f)** | 11111 (p) |
| recent developments in LLM architectures | 11111 (p) | 01110 (p) | 11111 (p) |
| evals skills for coding agents | 11111 (p) | **00011 (f)** | 11111 (p) |
| how we built auto mode | 11110 (p) | 11011 (p) | 11111 (p) |
| "it's hard to eval" is a product smell | 11111 (p) | 11111 (p) | 11110 (p) |

**Which of the three runs is the regression?**

### 2. A reasonable clause

Scout's judge takes a Reddit thread and returns `comment`, `upvote` or `skip`. The rules live in a file called JUDGE.md. On September 9 I tried two edits, one after the other, against a baseline of 17 labelled threads. Both edits looked reasonable to me when I wrote them.

Edit A adds a paragraph:

```diff
 - an open-source maintainer of an adjacent eval/testing project asking for methodological feedback

+Not "comment", however much it looks like one, when the practice my experience
+would recommend is already written in the thread: the author lists it among the
+options they are weighing, or reports it as what they already do. Then the
+thread has no question left for me and the rules below decide it as if it had
+none. It stays "comment" only if I can name the failure that the author's own
+list does not cover.
+
 verdict = "upvote" when the thread is on topic and honest but has no question for me
```

Edit B adds one line:

```diff
 - an open-source maintainer of an adjacent eval/testing project asking for methodological feedback
+- A thread is a comment if any sentence in it asks how to detect that generated logic, prompts or outputs changed from what was previously approved, or how to know whether a fix worked — regardless of the thread's topic or the author's expertise.
```

Results, same judge (Haiku 4.5), same 17 cases, 5 samples each:

| | accuracy | precision | recall |
|---|---|---|---|
| unmodified JUDGE.md (reference) | 10/17 | 9/12 | 9/12 |
| edit A | **8/17** | 6/9 | **6/12** |
| edit B | **9/17** | 8/11 | **8/12** |

Both edits were reverted the same morning.

**Where is the error?**

### 3. A clean precision

Brief scores each item 1 to 5. It shows me everything scored 4 or 5, or the top 5 if fewer, and asks which ones interest me. That answer is the ground truth for the suite. The suite reports precision 10/15 on 21 cases, and the gate has been green for two weeks.

Here is the state of the file that holds the ground truth, 446 items, on September 6:

[![Bar chart of the 446 items in brief's seen.json by judge score. Score 1: 111 items, 8 shown to me, none marked interesting. Score 2: 37 items, 6 shown, none marked. Score 3: 12 items, 2 shown, none marked. Score 4: 14 items, all 14 shown, 7 marked interesting. Score 5: 7 items, all 7 shown, 5 marked. Not judged: 265 items, none shown.](../assets/bad-evals/ex3_censored.svg)](../assets/bad-evals/ex3_censored.svg)

| judge score | items | shown to me | marked interesting |
|---|---|---|---|
| 1 | 111 | 8 | 0 |
| 2 | 37 | 6 | 0 |
| 3 | 12 | 2 | 0 |
| 4 | 14 | 14 | 7 |
| 5 | 7 | 7 | 5 |
| not judged | 265 | 0 | 0 |

**Which metric cannot be computed from this table, no matter how many runs I do?**

### 4. Same judge, same run, two numbers

For two weeks scout's suite had 17 cases. On September 11 I regenerated it from everything I had actually done on Reddit since the judge went live: 144 threads, each labelled with what I did (commented, upvoted, ignored). Same judge (Sonnet 5), same prompt, same config hash, one run over all 144 cases. Then I computed the metrics twice: on the 17 old cases, which are a subset of the 144, and on the full set.

[![Two charts from the same run and the same judge. Top: on the 17-case suite accuracy is 11/17, precision 11/15 and recall 11/12; on the 144-case suite accuracy rises to 123/144 while precision falls to 14/27 and recall to 14/20. Bottom: what I did with the threads in each suite. The 17-case suite is 12 commented, 4 upvoted and 1 ignored; the 144-case suite is 20 commented, 5 upvoted and 119 ignored.](../assets/bad-evals/ex4_17_vs_144.svg)](../assets/bad-evals/ex4_17_vs_144.svg)

| | 17 cases | 144 cases |
|---|---|---|
| accuracy | 11/17 = 0.65 | 123/144 = 0.85 |
| precision | 11/15 = 0.73 | 14/27 = 0.52 |
| recall | 11/12 = 0.92 | 14/20 = 0.70 |

The 17-case numbers are identical to the promoted baseline, so this is not drift between runs. The gate passes on 17 cases and fails on 144. Also: 11 of the 17 old cases came from r/LLMDevs; 73 of the 144 come from r/AI_Agents.

**Which of the two precisions is the true one?**

### 5. My gate has the discontinuity Dan Luu complains about

Scout's gate is three thresholds: accuracy ≥ 0.60, precision ≥ 0.70, recall ≥ 0.85. I set them from the promoted run (11/17, 11/15, 11/12) with a written rule: the threshold sits between the measured value and the value one case lower, so a single case flipping the wrong way fails the gate.

Exercise 7 spends a section on exactly this pattern in Senior SWE-Bench: a continuous score, then a hard cutoff, so that one line of code more turns a "tasteful" solve into a failure. The criticism is that the cutoff is an arbitrary formula that nobody had to write down.

**Is my gate an instance of the same mistake? If not, what is the difference, and when does it stop holding?**

## The explanations

### 1. None of them

Nothing regressed. The second run flipped two cases to fail because 3 out of 5 samples said so, and the third run flipped them back. The prompt, model and config were byte-identical across the three, so the only thing that moved was the judge itself.

This is what I built the 5-sample floor for, and the floor did its job: the gate said "you cannot promote or reject on one run". What the three runs alone don't tell you is *how much* the judge moves. So I pulled every run of the brief suite that has the same config hash. There are sixteen of them, from August 27 to September 10.

[![Bar chart of 16 runs of the brief suite from August 27 to September 10, all with the same judge, prompt and config hash, showing how many of the 21 cases had five samples that did not all agree. The count ranges from 2/21 to 6/21. The three fixture runs of September 3 are highlighted at 2/21, 5/21 and 2/21.](../assets/bad-evals/ex1_nonunanimity.svg)](../assets/bad-evals/ex1_nonunanimity.svg)

The fraction of cases where the five samples disagree goes from 2/21 to 6/21, on runs that are supposed to be replicates. If the noise floor is what you measure once and then trust, this is a problem: the floor itself has a floor.

Dan Luu re-graded Senior SWE-Bench outputs ten times and found the official result flipped 23% of the time. My number is not the same quantity, so I won't put them side by side without saying what mine is. For each non-unanimous case the pattern is 4/1 or 3/2, which means a single sample would have disagreed with the majority with probability 0.2 or 0.4. Weighted over the 21 cases, the chance that a one-sample run gives a different verdict on a given case is between 2% and 8% depending on which of the three runs you pick. The 23% and my 2-8% answer different questions (how often the published single run is wrong, vs. how often one sample would disagree with five), but they come from the same fact: an LLM grading a fixed input is not a deterministic function of the input.

One caveat that matters for the honesty of this section. The run files store, per sample, whether the assertion passed, not the raw score the judge produced. So I know that sample 2 disagreed with my mark; I don't know whether it said 3 instead of 4 or 1 instead of 5. Keeping the raw output per sample became possible only this week, and only if you turn it on. I hadn't.

### 2. In the judge, not in the prompt

I looked for the bug in the two edits for a good half hour. Edit A tells the judge "if the author already lists the practice you'd recommend, don't comment". Edit B tells it "any thread asking how to detect a change from an approved state is a comment". Both are things I believe.

What happened is that Haiku read a sufficient condition as a necessary one. After edit B, threads that clearly matched the earlier rules but didn't contain a sentence about "detecting change" started coming back as `skip`, because the new line read like the definition of a comment rather than one more way to earn one. Recall went from 9/12 to 8/12 on that edit and 6/12 on the other, and the cases that dropped were ones that had been unanimous `comment` for days. The prompt edits were fine as English. They were bad as instructions to this particular model, and no amount of staring at the diff tells you that. Running it does.

Two footnotes. First, the difference between 9/12 and 8/12 is one case, and given exercise 1 you should ask whether that's noise. It's a fair question; the reason I reverted anyway is that the cases that flipped were the stable ones, not the flapping ones, and the 6/12 of edit A is outside anything the noise floor produces. Second, the two diffs above do not exist in git. I reverted with a working-tree checkout, so the repository has exactly one blob of JUDGE.md, ever. The diffs come from the run files, which store the full text of every declared artifact at the moment of the run. September 11 was the first time that design decision paid for itself, and it paid for the whole exercise.

### 3. Recall

`marked` is written only for items the script showed me (lines 359 to 377 of `brief.py`: build the list of items scoring 4 or above, pad to five if shorter, ask, write the answer on those items and only those). An item the judge scored 2 and didn't show me has no label, and never will. So the suite can measure how many of the judge's picks I liked. It cannot measure how many things I would have liked the judge didn't pick, because I never saw them.

There is a second layer I hadn't noticed until I made the table: 265 of the 446 items were never scored at all. The script caps how many items it judges per run, and everything past the cap is stored as skipped. So it isn't "the judge hides the low scores from me"; it's "the judge hides the low scores from me, and something else hides 60% of the feed from the judge".

The 16 low-scoring items I did see (through the pad-to-five rule) I marked as not interesting, all 16. That's mildly reassuring about the judge and says nothing about recall, since 16 of 160 low scores is not a sample of anything.

None of this makes the precision number wrong. It makes it a number about half the pipeline, reported as if it were about the pipeline.

### 4. Neither

The 17-case suite had one negative example. One `ignored` thread against 12 `commented` and 4 `upvoted`. Recall on that suite was recall on things I had already decided to engage with, and precision was computed against 15 predicted positives of which almost all were positives by construction. It's the situation Dan Luu describes for DeepSWE from the other side: I was scoring the judge on the tasks it was already good at, because those were the only tasks I had bothered to label.

The 144-case suite fixes that, then breaks in a different place. The labels come from what I did, and "ignored" turns out to mean two things.

[![Confusion matrix of the 144 cases, my label against the judge's majority verdict over 5 samples; one case had no majority. Threads I commented on: 14 judged comment, 2 upvote, 4 skip. Threads I upvoted: 4 comment, 0 upvote, 1 skip. Threads I ignored: 9 comment, 0 upvote, 109 skip.](../assets/bad-evals/ex4_confusion.svg)](../assets/bad-evals/ex4_confusion.svg)

Nine threads I ignored came back `comment`, five of them unanimously across the 5 samples. With the raw outputs recorded this time, I could read the judge's reasoning on each. On at least five, the judge is right by the letter of JUDGE.md: a thread asking how to tell which of forty diffs between two runs actually matters, one asking what would make you distrust a project-level quality score, one about test-set leakage in prompt optimization. Those are questions for me. I didn't ignore them because the rules say skip. I ignored them because it was the fourth thread that morning, or because I had already commented twice on that subreddit that day. So the ground truth for "not a comment" is polluted with "not today", and the measured precision is lower than the true one by an amount I can't compute from this data.

The honest answer is that the suite measures agreement with my behaviour, and my behaviour is not the rule. To measure the rule I have to change the question the script asks me at the end of each morning: not "did you comment?" but "should this have been a comment?", which is a different, slower and more annoying question. That change is next.

One more thing the recorded outputs showed and no aggregate would have: across the nine false positives the judge's proposed angle is nearly always one of two anecdotes from my own experience, recycled. Precision doesn't care. The person who then writes the comment does.

### 5. It's a different object, until it isn't

The thresholds in Senior SWE-Bench turn a continuous quality score into a ranking of models. A discontinuity there manufactures differences between systems that the data doesn't support. My thresholds do something else: they answer one yes/no question about one system, "may this prompt change be promoted?", and the answer has to be binary because the action is binary. Somebody has to sign, and a signature is a step function.

That's the defence, and I think it holds for a gate, provided the step is placed against a measured floor rather than a round number. The rule "one case worse than measured" is exactly that: the threshold is not 0.7 because 0.7 sounds right, it's 0.7 because 11/15 passed and 10/15 would not, and the 5-sample floor says a single-case move on a stable case is signal.

It stops holding as the suite grows.

[![Curve of how many accuracy points a single case is worth as the suite grows from 5 to 300 cases, falling steeply and then flattening. Marked on it: my old suite at 17 cases, where one case is 5.9 points; DeepSWE, 0.9 points; my new suite at 144 cases, 0.7 points.](../assets/bad-evals/ex5_one_case.svg)](../assets/bad-evals/ex5_one_case.svg)

On 17 cases one case is 5.9 accuracy points, which is more than the noise floor, so "one case worse" is a meaningful event. On 144 cases one case is 0.7 points, and the September 11 run had 13 non-unanimous cases. A threshold one case below the measured value is now inside the noise, and the rule I wrote down for 17 cases is wrong for 144. I don't have the replacement yet. The candidate is a threshold expressed in cases rather than in points, with the count of stable cases that moved as the quantity, which is roughly what the floor already knows.

A smaller confession that belongs here. When I went to write "here is the history of my thresholds", there wasn't one. `promote` overwrote a single file with no log, the baseline file recorded the run's timestamp but not the promotion's, and of the three threshold configurations that appear in run files, one was never committed and is unrecoverable. The history of my own gate lived in commit messages I happened to write. That got fixed this week, after this exercise, not before.

## What the exercise found in the tool

I set out to find flaws in two prompts and found five things in the tool that measures them, one of which turned out to be a flaw in me. In order of how much they bothered me:

1. **Two prompt edits, same config hash.** Edit A's run has the same config hash as runs with the original JUDGE.md. I filed this as a hole and it isn't one: by design the hash is the identity of the suite (assertions, thresholds, samples), a declared artifact travels with its own sha, and a prompt change shows up in the report as a separate fact, artifacts_changed, next to the metrics. That's what let the edit be compared against the baseline at all. What I had actually found was that I'd never read that line of the report.
2. **The gate's central act leaves no trace.** The two rejections of September 9 exist nowhere except a commit message I wrote. `compare` printed its verdict to a terminal and forgot it.
3. **Promote had no history.** See exercise 5.
4. **A case with no majority, and what the run says about it.** One of the 144 cases came back 2/2/1 across the three verdicts. The suite requires 3-of-5 agreement, so I expected a suspended case; the run reports zero. It turned out the agreement rule works on the pass/fail axis, not on the verdict axis: 2 samples agreed with my mark, 3 didn't, that's a 3/5 majority for "fail", and the case fails. Correct by design, and the design wasn't written down anywhere I'd read. It is now.
5. **Per-call cost budget, checked on the mean.** Nine individual judgments exceeded the $0.020 budget, one by 17%, and the budget assertion passed on all 144 cases because it evaluates the mean of five samples. Possibly by design. Not what the name promises.

And one incident that turned into a feature. The first attempt at the 144-case run, 720 calls to Sonnet, was killed at around call 400 by a memory watchdog on my laptop. The tool had measured itself flat under 100 MB; the pressure came from an IDE. But the run file was written only at the end, so about $4 of judgments were gone with nothing on disk. The fix, a per-case journal with `--resume`, shipped the same evening and the second attempt ran through it. $6.18 for 720 calls, against an estimate of $8.06; adaptive thinking is cheaper on the easy skips.

## What I'd take from this

Every one of the five problems is visible in the data I already had. None required knowing anything about LLMs. Exercise 3 is a `for` loop that writes a field on the wrong subset; exercise 4 is a class imbalance you'd catch in an intro stats course; exercise 5 is the observation that 1/n gets small. I had the noise floor, the versioned baseline, the recorded artifacts, all the machinery that's supposed to make this rigorous, and I still measured half a pipeline for two weeks and called it precision.

Dan Luu's line is that evals are more about avoiding mistakes than following a process. I'd add one thing from the other side of the table: the machinery doesn't avoid the mistakes for you, but it does something almost as useful. It keeps the evidence. The diffs in exercise 2 survive only because the run stored the prompt text. The table in exercise 3 exists because every item ever judged is still in the file. When I finally asked the right question, the answer was already on disk.

---

*All numbers in this post come from `.digline/` in the two repos and from `seen.json` in each; run ids are `2026-09-03T06-14-13…`, `06-18-43…`, `06-24-50…` for exercise 1, `2026-09-09T06-34-01…` and `06-51-45…` for exercise 2, `2026-09-11T15-09-23…` for exercise 4. The analysis scripts are in the post's repo. Thread titles in exercise 4 are paraphrased; the threads are public but the point is not who wrote them.*
