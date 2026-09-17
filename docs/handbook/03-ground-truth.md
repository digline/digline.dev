---
seo_title: >-
  Ground truth when nobody gives you one
description: >-
  Where the expected answer comes from when there is no labelled data: freeze
  the input, cover forms, capture disagreement, and design the feature so a
  judgment has something to attach to.
---

# 3. Ground truth: when nobody gives you one

Chapter 2 said to find the place where a person corrects the model. This chapter is for when that place does not exist — or exists and records something other than what you think. It is written from three systems: the [newsletter judge](https://github.com/digline/brief), a second judge by the same author that picks Reddit threads worth answering (private, described in [Bad evals, my own](../blog/bad-evals-my-own.md)), and a product feature described in shape only. Each of them failed to produce ground truth in a different way.

## Freeze the input, not the world

A case is a photograph of a situation. That tomorrow's data will differ is irrelevant: you are testing what the system does facing that situation, not the data.

So the input goes into the case whole, as the model saw it that day. Re-fetching an article today would put a different input under an old label. The newsletter project stores the summary it judged — but only for the items it showed its reader, so 144 items it judged and never showed have a score and no input. Even labelled, they could not be replayed.

## Cover forms, don't sample

The obvious way to get cases is to export every labelled record. The Reddit judge did that on 2026-09-11 and got 144 cases. 109 of them were threads the reader ignored and the judge skipped: the same ordinary morning, over and over. Accuracy on that set was 0.85. Precision on the one verdict that mattered was 0.52. The volume flattered the easy days and said nothing about the hard ones.

Choose cases for their shape instead: the crowded input, the empty one, the urgent item buried under noise, the missing field, two priorities that conflict. That list is not a result. The ordinary day is one of the shapes, and chapter 2 is right that it must be there — as a form, not as the sediment of every morning.

## A label is not a judgment

The Reddit judge asked its reader, each morning, what they did: `c` commented, `u` upvoted, Enter ignored. `ignored` became `skip` in the suite. Then the reader looked at nine threads they had ignored and the judge had marked `comment`, and found that on at least five the judge was right by its own rules. They had been ignored because it was the fourth thread that morning, or because the reader had already commented twice in that forum that day.

So `ignored` meant *the judge was wrong* and *no time*, and every case built on it was a reading of an answer that never said which. **Do not reinterpret it afterwards** — by date, by the judge's confidence, by what you must have meant. That is inventing an expected value on your own behalf. The old records stay ambiguous, and no new case is minted from them.

The fix was made at the keyboard on 2026-09-16: `n` for *declined*, Enter for *deferred*. The key that empties a list of forty had to mean the value that claims nothing, or the ambiguous label would have been rebuilt under a new name in one morning. Enter wrote `ignored` from September 7 to 16. Those negatives cannot be recovered, and every later morning would have gone the same way.

That split did not remove the ambiguity, because `declined` still asks what you *did*. A thread left because the reader had already commented twice in that forum is still a `declined`, still a negative. Removing it takes a question about the rule — not *did you comment?* but *should this have been a comment?* — and neither judge asks one. The only place in these systems that asks about the rule is the same author's monitoring loop, *would you have wanted to be woken?*, and nobody has answered it yet.

## Disagreement is the event

Rereading good outputs teaches you nothing and convinces you of a lot. The only moment worth capturing is when a person would have answered differently from the model. Neither judge follows that yet: both export every explicit label, agreements included.

**The newsletter project is the counter-example**, and it is more useful than a success. Its reader is shown the items the judge scored 4 or 5, padded to five, and asked *which ones interest you? (enter = none)*. The only explicit answer is *yes*, and it can only be given to items the judge already chose. Unshown items have no label; 265 of 446 were never even scored. Enter is ambiguous. The one route to a disagreement — marking a padded low-scoring item — had been open sixteen times by September 6, and taken zero. The method yields **no capturable disagreement at all**, not because the reader never disagreed, but because it never asked where they could.

The ground truth has to be a by-product of work the person already does. Both judges ask at the end of a morning the reader was having anyway. The monitoring loop's question is a separate command to run later, and its empty record is too young to explain — but that is the shape of a chore. In a product the person is not you, which is the hard case, and nothing here has solved it.

## When the selection was never a datum

The third system has the commonest shape of LLM feature in production, and what follows was read from its code, not run against it. A product writes each user a morning briefing. Code assembles a context and hands it to one model call. The model decides which items to mention, in what order, with what reasoning, and whether to say anything at all.

The reply is prose with links in it. Nothing parses or validates it. An item is identifiable only if the model happened to wrap it in a link carrying an id, and nothing checks that the id exists in the input.

In the two judges the labels were ambiguous. Here **the selection exists only inside the prose**. There is nothing to assert on, and nothing a user's judgment could attach to: a feedback button would have no object to point at. Two ordinary things make it worse. A failed model call and a genuine "nothing to report" store the same row — an absence disguised as an answer. And some of the queries that build the context take N rows with no ordering, so which items reach the model is up to the database: two runs on the same data can differ without the model changing its mind, and there is no input to freeze.

The feature works, and none of this shows in review. It just cannot be evaluated. **Whether your ground truth will be collectable is decided when you write the feature**, not afterwards. A system that emits its decision as a structure — the chosen items, in order, with their ids — can be checked deterministically and can carry a person's judgment. One that emits only prose cannot, whatever you bolt on later.

The fix is a shape: emit the selection first; validate its ids against the input; store a failure as a failure; let the prose be a rendering of the selection.

## What you can then assert

With the selection as data, most of what matters is stable across every possible day and needs no model: every id is in the input, so nothing is invented and nothing comes from another user's data; the item that must appear appears; an empty input yields an empty selection. Only the ordering — is the urgent thing first? — needs a judge. None of these has been run on that system yet; they are what the structure makes possible.

## Growth, and the honest limit

Start from a few chosen forms. Let every failure in production become a case, and never delete one: a case that found a defect is a wall that holds, and removing it is the one way to learn what it was holding. The Reddit judge's exporter was changed on 2026-09-16 to append and never remove; the newsletter's still regenerates its file wholesale.

Twenty cases do not tell you the system is correct. They tell you it has not got worse on twenty situations somebody judged representative. A regression gate, not a proof.

## Doing it today

1. Find where your feature's decision lives. If it is only in prose, change the output before you write a single case. If you cannot change it yet, you cannot evaluate the feature — and that is already a finding: start by recording the assembled input and the reply, because they exist only if you write them down today.
2. Check your inputs are deterministic. A query that truncates without an order is the first bug.
3. Look at the answer your users give by doing nothing. Make sure it claims nothing.
4. Ask about the rule, not the behaviour, and only where the person would have answered differently.
5. Pick five forms. Write one case for each.

The next chapter is about what to check on those cases — and why the checks that need no model at all come first.
