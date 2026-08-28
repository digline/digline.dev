---
seo_title: >-
  Maintenance: running the suite as a practice
description: >-
  When an evaluation suite should run, what should make you look, and what
  to do the morning CI turns red and you changed nothing at all.
---

# 6. Maintenance

A suite that runs once is a demo. This chapter is about the part that makes it a practice: when it runs, what should make you look, and what to do on the morning it turns red and you changed nothing.

## The five triggers

Something happens; the suite runs; the comparison says whether it got worse. There are five different somethings, and they need different responses.

### 1. You changed something

The prompt, the model, the retrieval, the code around the call. This is the trigger you expect, and the one CI handles: every pull request runs the suite and compares with the reference. Red blocks the merge; the lines under the headline say which cases moved and by how much; the diff of the prompt sits next to them.

The response is the ordinary one — look at the cases that regressed, decide whether the change is worth it, fix or accept. The only rule: a red comparison is never fixed by widening the tolerance or lowering the threshold. Those are rule changes, and rule changes go through the front door (chapter 5), not through the fix for a failing build.

### 2. The provider changed something

Nothing in your repository moved. The model behind the API did — an update, a deprecation, a re-pointed alias, a change in default behaviour. Your commit history says "unchanged". The comparison, if it ran, says four cases worse.

*If it ran* is the point. CI runs on pushes, and nobody pushed. This trigger needs a schedule: a nightly or weekly job that runs the suite against the reference with no change on your side. A red result with a clean diff is the signature of the provider — the one failure that no code review, no test of your own code, and no amount of care can catch, and the one most teams discover from users.

In the [newsletter project](https://github.com/digline/brief) this is a weekly workflow that runs the real judge and compares. It costs eight cents a week. It is the cheapest insurance in the repository.

The response is different from trigger 1: you did not do this, so you cannot undo it. Options, in order: pin the model version if the provider allows it and you were on an alias; adjust the prompt to the new behaviour and promote when back; or accept the new behaviour as the reference, deliberately, with the promotion as the record that you saw it and decided.

### 3. A real case went wrong

A user reports it. A log shows it. Someone on the team notices an answer that should not have happened. The suite did not catch it because the suite did not have that input.

The response is the habit from chapter 2, and it is the most important sentence in this handbook: **one failure seen, one case written, the same day.** Before you touch the prompt, save the input and the right answer as a case. Run the suite — the new case fails, which is correct; it shows as *new*, with nothing to compare against. Then fix the prompt. Then run again: the new case passes, and the other twenty tell you whether the fix broke anything. Then promote.

Skip the first step and you have patched one input and learned nothing. Do it and the failure is permanent protection.

### 4. The rules moved

Someone raised a threshold, tightened a tolerance, added a check, removed one. The comparison still runs — and it tells you the configuration differs from the reference, so a case that flipped from pass to fail reads as a rule change, not a model change. Promotion is refused until the reference is re-established under the new rules.

The response is short: run under the new rules, look, promote. The point of the refusal is that a rule change is never invisible — it always produces a promotion someone can see in review.

### 5. A case stopped being judgeable

A check returns *could not judge* — the judge's samples split, the output was the wrong shape, the provider timed out. It is neither pass nor fail, and it blocks promotion.

Two responses, and only two. If the case is genuinely ambiguous — the samples split because a human would split too — suspend it, with a written reason, so it stays in the suite as a visible gap rather than silently disappearing. If the check is at fault — wrong shape, wrong prompt in the judge — fix the check. What you do not do is lower the minimum agreement until the split becomes a pass: that converts *unknown* into *fine* without anyone deciding it.

## The weekly ten minutes

The triggers are reactive. The practice that keeps a suite honest is one small, boring, scheduled act:

1. Open the comparison from the scheduled run. Green or red, read the aggregates — precision, accuracy — against the reference. Two numbers, thirty seconds.
2. Look at the list of cases that moved, even within tolerance. A case that drifts a little every week is telling you something before it crosses the line.
3. Check the case count. If it has not grown since last week, ask whether nothing went wrong in production or whether nobody wrote it down. It is usually the second.
4. Check the reference's age. A reference from four months ago on a feature that changed twice is a reference nobody re-approved.
5. If anything in 1–4 needs a decision, make it now — promote, suspend, add a case — and commit.

Ten minutes, once a week, by whoever owns the feature. Skip it for a month and the suite is still there; skip it for a quarter and it is a demo again.

## What gets worse without you noticing

Three slow failures that no trigger catches, because each step is too small to alarm:

**Cost creep.** Every prompt edit adds a sentence; nobody removes one. The budget check is graded precisely so that cost *within* the limit still shows as a change against the reference. Watch the number, not just the colour.

**Case rot.** A case whose expected answer was right in March may be wrong in September because the product changed — the refund window moved, the taxonomy gained a category. A suite with rotten cases fails for the wrong reasons and teaches people to ignore red. When a case fails and the output looks right, check the case before the prompt.

**Reference drift by promotion.** Each promotion accepts a small loss — "one case worse, but the diff is nicer". Ten promotions later the reference is ten small losses below where you started, and every single comparison was green. The defence is the aggregate in the file: compare this month's precision not to last week's reference but to the first one you ever approved. Git has it.

## Doing it today

1. Add the scheduled run — weekly is enough — with the real judge. Make it the one job that runs when nobody pushed.
2. Put the ten-minute review in the calendar, on the person who owns the feature.
3. Write the "one failure, one case" rule where the team will see it: the README of the suite, the pull request template, the channel topic.
4. The next time the comparison is red and you did not change anything, do not touch the tolerance. Read the diff. It is empty. That is the provider, and now you know what that looks like.

The last chapter is for teams that build LLM features for someone else — where the same suite becomes the answer to a question the customer will ask, and where some of what it contains must never leave their perimeter.

---

*Previous: [5. The reference](05-the-reference.md) · Next: [7. For teams building for others](07-for-teams-building-for-others.md)*
