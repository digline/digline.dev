# 3. Checks: deterministic first, judge last

A case says what goes in and what you know about the right answer. A check is how you turn an output into a verdict. This chapter is about choosing checks — and about a rule that sounds too simple to matter and saves more time than anything else here: **use a model to judge only what nothing else can.**

## Two kinds of check

**Deterministic checks** need no model. They look at the output and answer a question mechanically: does it contain this phrase, is it valid JSON, does it match this schema, is it under 200 words, does it cost less than a cent, does it contain a tax code. Same output, same verdict, every time, instantly, for free.

**Judged checks** ask a model to evaluate the output: is this reply polite, does it answer the question, is it supported by the retrieved documents, is it better than the previous version. They can express things no regex can. They are also a second distribution on top of the first — the judge samples too — and every judged check inherits the noise, the cost and the latency of a model call.

Most teams reach for the judge first, because it is the interesting part. This chapter argues for the opposite order.

## Why deterministic first

Take the [newsletter judge](https://github.com/digline/brief). Its output is a small JSON object: a score from 1 to 5 and a one-sentence reason. Before asking any model whether the score is *good*, three things can be checked with no model at all:

- Is the output valid JSON with exactly those two fields? (`JsonSchema`)
- Is the score an integer between 1 and 5? (the same schema)
- Did the call cost less than the budget? (`CostBudget`)

Those three catch the failures that actually happen in production: the model wrapping the JSON in prose, the model inventing a score of 0, the prompt growing until every call costs three times what it did. They catch them for free, deterministically, on every run. And when one of them fails, the error is unambiguous — nobody argues with "not valid JSON".

Only after those comes the question that needs a judge — "does this score agree with what the reader wanted?" — and in the newsletter project even that one turned out to be answerable without a model, because the reader's own marks are recorded. The check is a ten-line comparison: *did the judge say ≥4 exactly when the reader marked it?* No second model, no noise from the check itself.

The general shape: **every check you can make deterministic is one fewer source of noise between you and the answer.** A suite with five deterministic checks and one judge has one noisy signal to calibrate. A suite with six judges has six.

## What the deterministic ones catch

A short catalogue, by the failure each one exists for:

| Failure you have seen | Check |
|---|---|
| The reply forgot the mandatory line (a disclaimer, a signature, a legal phrase) | `Contains` |
| The reply mentioned something it must never mention (a competitor, an internal name, "as an AI model") | `NotContains` |
| The output was supposed to be structured and came back as prose | `IsJson`, `JsonSchema` |
| The answers are getting longer every week, or must fit a channel | `Length` |
| The answer should be *close* to a known one, not identical | `Levenshtein`, graded |
| The output reached a person and contained an IBAN, a tax code, an email | `PiiAbsent` |
| A prompt change doubled the tokens, and nobody noticed until the invoice | `CostBudget` |
| The feature is fine but users wait four seconds | `LatencyBudget` |

Two of these deserve a word. `PiiAbsent` is the one people skip and regret: an LLM that has customer data in its context will, sooner or later, repeat some of it in an output where it does not belong, and no judge is as reliable at spotting a valid IBAN as a checksum. And the budgets are graded, not pass/fail: a cost that creeps up *within* the limit still shows as a change against the reference, which is how you notice the prompt growing before it crosses the line.

## When a judge is the right tool

There are questions nothing mechanical can answer:

- *Is this reply polite?* — no regex for tone.
- *Does it answer the question that was asked?* — requires understanding both.
- *Is every claim in this summary supported by the source?* — the core question of any retrieval system.
- *Is this rewrite better than the original?* — a preference, not a rule.

For those, a judged check is the only option, and there are two shapes. A **rubric** — you describe the criterion in a sentence, the judge returns a score in [0, 1] and a reason. And **faithfulness** — the judge counts the claims in the output and how many the provided context supports; the check divides. The second is the one for anything that retrieves documents, and it is more useful than a rubric because it produces a count you can argue with, not a vibe.

Whichever you use, three rules, all of which come from the same fact — the judge is a distribution:

1. **Threshold and tolerance are mandatory**, not defaults. A judged check with an implicit "anything above 0 passes" is green forever and tells you nothing. Set the threshold where the system measurably is; set the tolerance from measured noise (chapter 4 shows how).
2. **Sample.** One judgement per case is one draw. Ask three or five times and combine — or you will spend the next month chasing regressions that are the judge changing its mind.
3. **Keep the judge's prompt as fixed as your system's.** It is a prompt. It drifts for the same reasons. It should live in a file, be versioned, and be recorded with every run, exactly like the prompt under test.

## The judge is yours

One thing worth stating plainly, because tools differ here: the judge is a function you supply. It calls whatever model you choose, in whatever way you choose, and the evaluation tool only composes the question and reads the score. Two consequences. In tests, you inject a fake judge and every judged check becomes deterministic. And the judge's reasoning — which quotes the output it judged — stays wherever the output was allowed to be; it is never sent anywhere on your behalf.

## Putting a suite together

For a first suite, the pattern that has held up:

- **One structural check** on the output's shape. It catches the embarrassing failures and it costs nothing.
- **One or two content checks** — a `Contains` for the mandatory phrase, a `NotContains` for the forbidden one, `PiiAbsent` if the output reaches a person.
- **The budgets**, always, graded.
- **At most one judged check**, sampled, for the thing that genuinely needs judgement. If you find yourself wanting three, ask whether two of them could be cases with a known answer instead.

Five or six checks on twenty cases. It runs in a minute, costs cents, and it is already more than the vast majority of LLM features in production have.

## Doing it today

1. List the last five failures your feature produced. For each, ask: *could a regex, a schema or a counter have caught this?* Most of the time the answer is yes.
2. Write those as deterministic checks first. Run them on your twenty cases. Some will fail today — that is the point.
3. Only then write the one judged check for the question that genuinely needs a model. Give it a threshold and a tolerance. Sample it.
4. If a judged check fails on a case, look at the reason before you look at the prompt. Half the time the case was mislabelled.

The next chapter is about that one judged check: how much it wobbles, how to measure the wobble, and how to keep it from turning every Tuesday into a false alarm.

---

*Previous: [2. Cases: the asset nobody builds](02-cases.md) · Next: [4. The judge](04-the-judge.md)*
