---
seo_title: >-
  For teams building for others
description: >-
  One evaluation suite, three interested parties: what the developer, the
  consultancy and the customer each need from the same runs, and the rule
  that cannot bend.
---

# 7. For teams building for others

Everything up to here applies to anyone with an LLM in production. This chapter is for a narrower group: consultancies, software houses, anyone who builds and maintains an LLM feature for a customer who does not develop, and who owns the data the feature runs on. If that is you, the same suite does two more jobs — and one of them has a rule that cannot be bent.

## Three people, one suite

In a product you build for yourself there is one interested party. Here there are three, and they want different things from the same numbers.

**The developer** wants what the previous six chapters describe: cases, checks, a reference, a comparison in CI.

**The consultancy** — your company — maintains this feature for several customers at once. It needs to answer, for each of them, *did last Tuesday's release make customer A's assistant worse?* — and it needs to answer it without holding customer A's data, and without customer A's numbers ever sitting in the same place as customer B's.

**The customer** owns the data and does not read code. It has two rights: to a verdict it can understand about a system it cannot inspect, and to its data not leaving its premises. And it has a question, which it will ask sooner or later, in a meeting or in an audit:

> *What did you test, when, under which version, and who approved it?*

A dashboard does not answer that. A dashboard shows today. The question is about a date, a commit, an artefact that someone can open six months later and that has not changed since. The reference file from chapter 5 is that artefact — which is why it lives in the repository and not on a vendor's server: a file you can hand over, with a hash and a date, is evidence; a screen someone else hosts is not.

## The rule: the payload stays where it was born, the verdict travels

Take one case in a recruiting tool: a candidate's CV goes in, a ranking comes out, and a judged check asks whether the ranking is justified. The run now contains three kinds of thing:

- **The verdict**: check name, pass or fail, score 0.81, threshold 0.70, tolerance, cost. Numbers about how the system behaved.
- **The payload**: the CV, the ranking text, and the judge's *reason* — which quotes the CV to explain the score.
- **The aggregate**: precision 0.74 across the set, 12 true positives, 4 false.

The consultancy needs the first and the third to do its job. It has no right to the second, and no need for it. So the rule is mechanical: **a run that crosses the boundary between the customer and the consultancy is redacted first** — reasons removed, payload metadata removed, the verdicts and the numbers kept. Not as an option someone remembers to set on the export; as a property of the run itself, verified when the file is read, so that a document claiming to be redacted cannot contain a reason.

Three things follow, and each is a design decision you will face whatever tool you use:

**The judge runs inside the perimeter.** Its reason quotes the data. It can be computed only where the data may be. What leaves is the score it produced, never the sentence.

**The case identifier is not payload — so it must never contain any.** It has to cross the boundary, because it is how a verdict finds its counterpart in the reference. `order-12345-mario-rossi` as an id carries a customer's name into the consultancy's repository. When cases are generated from production, the id must be generated too — a date, a sequence, a short hash — with no way to pass an application identifier through.

**Prompts are not automatically safe.** A prompt is the consultancy's work, but it often contains the customer's business rules, and those are the customer's. Default to keeping the prompt inside the perimeter; let a suite declare, in code that goes through review, that its prompts may travel.

## What the customer receives

Not the repository. A **report**: a self-contained document — one HTML file, printable — that answers, in this order, *did it get worse?*, *which checks and by how much*, *what was under test and what changed in it*, *when, under which version, approved by whom*. Written for someone who does not read code, generated from the same comparison the developer saw, so that the two can never disagree.

The report is generated inside the customer's perimeter, where the reasons are available, and it can include them: for the customer, the judge's explanation of why a case failed is the most useful line on the page. The redacted version of the same report — verdicts, no reasons — is what the consultancy keeps.

Two habits that make the report worth something:

**One reference per delivery.** When the customer accepts a release, that acceptance is a promotion. The reference file records the state they accepted; the next report compares against it. "It got worse since you accepted it" is a sentence both sides can verify.

**The aggregate in the contract.** With labelled cases, a suite has a number — precision 0.74 — stable enough to write down: *the classifier agrees with your reviewers on at least 70% of confirmed cases.* Set it where the system measurably is at acceptance, not where either side wishes it were. The threshold is the commitment; the comparison is how both sides watch it.

## What the consultancy keeps

For each customer, in that customer's own repository or in a per-customer directory that cannot be confused with another's: the suite, the references, the redacted runs. Never a single store where customer A's verdicts sit next to customer B's — a typo away from reading one as the other. Perimeters are directories, and the tool should refuse to compare or promote across them, so that the mistake is impossible rather than merely discouraged.

Across customers, the consultancy sees only what travels: which checks, which scores, which aggregates, which prompts if the suite allowed it. That is enough to notice that a model update degraded three customers at once, and it contains nothing any of them would object to.

## When production feeds the suite

The chapters so far run the suite on cases you wrote. The next step — and it is a step, not a leap — is to run the same checks on the responses the system gives in production, inside the customer's perimeter, and to turn a failure there into a case in the suite.

That closes the loop that chapter 2 asked for by hand: *one failure seen, one case written* becomes automatic. It also brings every rule in this chapter into force at once — the verdict travels to the consultancy, the response does not; the judge runs where the data is; the generated case has a generated id and a rewritten input. If you set those rules up now, on the suite you run by hand, the automatic version is the same rules on a different source. If you skip them now, you will discover them the first time a generated case lands a candidate's CV in a pull request.

## Doing it today

1. Decide what the customer's question will be, and write down where the answer lives. If the answer is "in a dashboard we subscribe to", you do not have an answer.
2. Mark every check in your suite: does its reason quote the data? If yes, that check's reason is payload and cannot leave the perimeter.
3. Look at your case ids. If any contain a name, an order number, a real identifier — change them now, before the file goes anywhere.
4. Put each customer's suite and references in that customer's own place. If two customers share a directory today, separate them today.
5. At the next acceptance, promote. Give the customer the report. Write the aggregate into the acceptance note. From that moment, "did it get worse since you accepted it?" has an answer you both can check.

---

That is the handbook. If you have read it end to end, you know more about keeping an LLM feature under control than most teams shipping one. The tool built around these seven chapters is [digline](../index.md); the project all the numbers came from is [public](https://github.com/digline/brief). Neither is required to start — the twenty cases are.

---

*Previous: [6. Maintenance](06-maintenance.md)*
