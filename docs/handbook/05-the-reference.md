---
seo_title: >-
  The reference: a threshold is not a baseline
description: >-
  A run that fell from 0.91 to 0.78 passes a 0.7 threshold on both days.
  The one number you write down and agree to be measured against is what
  catches it.
---

# 5. The reference

Everything so far produces numbers. This chapter is about the one number that matters more than the others: the one you write down and agree to be measured against.

## A threshold is not a reference

Most teams that test an LLM feature at all have a threshold: the score must be above 0.7. It answers one question — *is it acceptable?* — and it is blind to the other one — *is it what it was?*

A feature that scored 0.91 on release and 0.78 today passes the threshold on both days. Nothing turns red. And yet something changed by thirteen points, and the person using it felt the change before any test did. To see it you need to have written down the 0.91. That is the reference: a run of your suite that you looked at, judged right, and recorded — scores, the prompt that produced them, the commit, the date — so that every later run can be compared against it instead of against a line.

The threshold says where the floor is. The reference says where you were standing. You need both, and the second is the one almost nobody keeps.

## What a reference contains

A file, in the repository, next to the code. In the [newsletter project](https://github.com/digline/brief) it is `.digline/alessandro/baselines/brief-judge.json`, committed like any other file. Inside:

- **The verdicts** — every check on every case, with its score, threshold and tolerance. Not a summary: the full table, so a later comparison can say *which* case moved.
- **The aggregates**, if the cases are labelled — precision 0.625, accuracy 0.714 — with the counts that produced them.
- **The prompt text** that produced the run, verbatim, with its hash. Not a reference to a file that may have changed since; the text itself, frozen.
- **The commit** the code was at, and whether the working tree was clean.
- **The configuration** of the suite — which checks, which thresholds — as a hash, so that a comparison against a suite with different rules is refused rather than silently meaningless.

Two things follow from the prompt being *inside* the file. First, the reference is reproducible even if you never committed the prompt separately — a common state during a day of experiments. Second, when a later run differs, the comparison can show the diff of the prompt right next to the diff of the scores: *you changed these three lines; these two cases moved.* That pairing is the single most useful thing a comparison can show, and it only exists if the prompt travels with the run.

## Promoting: a deliberate act

A run does not become the reference by being the latest, or by being green. Someone promotes it. That is a decision — *this is what good looks like, I am willing to be measured against it* — and it should feel like one. In the newsletter project it is a command, `digline promote`, and the result is a commit with a file in it that a reviewer can read.

Three things a promotion should refuse, because each one would make the reference a lie:

- A run produced under a **different configuration** than the current suite: its numbers were measured by other rules.
- A run with **any check in error** — a *could not judge* — because a reference is an approved state and an error is not a state.
- A run from a **different tenant** than the one you are promoting for, if your suite has perimeters (chapter 7).

If your tool does not refuse these, refuse them yourself. A reference you cannot trust is worse than none, because it turns every later comparison into an argument.

## Not the first green run

The first run that passes is the most tempting one to promote and the wrong one. You have just read chapter 4: the judge wobbles, and a single run is one draw. Promote it and the reference records the lucky sample; every later run is compared to the lucky one, and looks worse than it is.

In the newsletter project this was found the hard way. The first reference was promoted from the first good run. Three calibration runs later, two cases that the reference recorded at ⅔ agreement were at 1.0 in every subsequent run — the reference had caught them on a bad draw, and would have reported an *improvement* on every future run for no reason.

The procedure that replaces it costs three runs:

1. Run three times on the frozen system.
2. Look at the cases that differ between runs. For each, note which run holds the middle value.
3. Promote the run that is in the middle most often. Break ties on cost.

That run is the reference. It records the typical behaviour, not the best or the worst, and a later comparison against it means what it says.

## What changes the reference, and what does not

**A better prompt.** You changed it, the comparison shows two cases improved and none regressed, you like the diff. Promote. The old reference stays in git history; the new one carries the new prompt text.

**A raised threshold.** You decided the floor should be 0.70, not 0.60. That is a configuration change: the comparison still works — and it tells you the threshold moved, so the flip reads as a rule change and not a model change — but promotion is refused until the configuration matches. Change the rule, run, promote: three steps, all visible in a pull request.

**A new case.** Adding a case does not invalidate the reference: it shows as *new* in the next comparison, with no counterpart to compare against. Once you have looked at it, promote and it becomes part of the record.

**A model change.** The provider updated the model, nothing in your code changed, the comparison shows four cases worse. This is exactly the case the reference exists for. You do not promote the worse run. You investigate, adjust the prompt if needed, and promote when you are back — or you accept the new behaviour deliberately, and the promotion is the record that you did.

**The reference does not change because time passed.** A reference from March is valid in September if nothing was promoted in between. Its age is information, not a defect: it says nobody has approved anything since March, which is either fine or a finding.

## Where the reference lives

In the repository, committed, reviewed. Not on a server, not in a dashboard, not in the memory of the person who ran it. Three reasons that are not about preference:

It can be **diffed**. Two references, two files, `git diff`. Every number that moved, every line of prompt that changed, in one view.

It can be **reviewed**. A promotion is a pull request. Someone other than the author sees the numbers and the prompt before they become the standard.

It can be **shown**. When a customer — or an auditor, or your own team six months from now — asks what was tested and approved and when, the answer is a file with a commit hash and a date, not a screenshot.

## Doing it today

1. Freeze your prompt and your cases. Run the suite three times.
2. Pick the median run by the procedure above. Promote it. Commit the file.
3. Open the file. Confirm the prompt text is inside it, verbatim. If your tool does not put it there, put it there yourself — a copy of the prompt next to the reference, with the same commit.
4. Make one small change to the prompt. Run. Compare. Read the diff of the prompt next to the diff of the scores. That view is the reason for everything in this chapter.

The next chapter is about keeping this alive: when to run, what should make you look, and what to do on the morning the comparison is red and you changed nothing.

---

*Previous: [4. The judge](04-the-judge.md) · Next: [6. Maintenance](06-maintenance.md)*
