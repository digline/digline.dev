---
title: digline and Inspect AI
seo_title: >-
  digline and Inspect AI: an Inspect AI alternative for application regression
description: >-
  What Inspect AI does well — Task, solvers, scorers, sandboxing, epochs and
  reducers, inspect view — and where digline differs: an approved reference
  committed to the repository, and a verdict that gates a pipeline.
---

# digline and Inspect AI

Inspect AI and digline agree about more than any other pair on this list: both are Python, both write their results to local files, both need no account and no server. They disagree about what an evaluation is *for*. Inspect measures a model against a benchmark. digline measures an application against the run someone approved last month.

## What Inspect AI does well

The framework is built by the UK AI Security Institute and is MIT-licensed, and the design is unusually clean. A `Task` is three things and no more: a **dataset** of samples with `input` and `target`, a **solver** that produces an answer, and a **scorer** that judges it. The `@task` decorator registers it so that `inspect eval` can find and run it by name, and `inspect view` opens the logs afterwards — every sample, every message, every tool call, in a viewer that reads an eval log rather than a database.

A solver ranges from `generate()` to a full agent, composed as a chain, and the built-in `react` agent runs a reason-act-observe loop over the tools you supply. The scorers cover the ground a benchmark needs: `includes()`, `match()`, `pattern()`, `answer()`, `exact()`, `f1()`, `choice()`, `math()`, and `model_graded_qa()` and `model_graded_fact()` when a model has to grade the answer.

Two pieces of it are things digline has no equivalent for. **Sandboxing** runs untrusted model-generated code in Docker, Kubernetes, Modal, Proxmox and others — which is what you need the moment an eval lets a model execute what it wrote, and it is a substantial piece of engineering rather than a flag. And **epochs** run each sample repeatedly, folding the repeats with a reducer — `mean_score()`, `median_score()`, `at_least()`, `pass_at()` and others, which `Epochs()` also takes by name as `"mean"`, `"median"`. If your question is a capability question — how often can this model do this at all — that vocabulary is exactly right, and it is the same instinct about sampling that digline's noise floor comes from.

## What digline does differently

**There is an approved reference, and it is a file in the repository.** Inspect writes an eval log per run; comparing this run to one from six weeks ago is something you do by reading two logs. digline's `promote` marks one run as the approved one and writes `.digline/<tenant>/baselines/<suite>.json` — every check on every case with its score, the prompt text that produced it, the commit it ran at, the configuration hash — which you commit. Every later comparison is against that file: reviewed as a diff, reverted with `git revert`, and answering *who approved this, when, under which prompt* without anyone remembering anything. This is the whole of what digline adds, and it is not a feature Inspect is missing so much as a question Inspect is not asking.

**The noise floor is per case and lives in the reference, not in a reducer.** `at_least(2)` and `pass_at(k)` fold repeats into one number by a rule you chose in advance. `Suite.samples` folds too, and then keeps the observed interval for each check *in the baseline*, so the next comparison can read a drop against the band that check actually showed on the approved run. Inside the band, the report says within the noise and does not count it; outside, it counts. Two checks in one suite end up with two different floors because they wobble by different amounts. [ADR 0006](../product/adr/0006-repeated-samples-and-the-noise-floor.md) has the run that forced this: one case going 5/5, then 2/5, then 5/5, with nothing changed.

**The verdict has three states and it is the exit code.** `digline compare` exits `0` when nothing got worse, `1` when something did, and `2` when something could not be judged, and the third state is not folded into the other two. A benchmark reports accuracy; a gate has to answer a question a pipeline can act on, and has to distinguish a real regression from a judge that failed. [ADR 0001](../product/adr/0001-verdict-not-score.md).

**No server and no telemetry** is where the two agree rather than differ. Inspect is a local framework with local logs and a local viewer; so is digline. The only thing worth adding is that digline's report is a self-contained HTML file meant to be sent to someone who will not run anything, which is a different audience from `inspect view`.

**`promote` is absent from every surface an agent can reach.** None of the MCP server's tools writes a baseline; neither does any flag in `pytest-digline` or any input in the GitHub Action. An agent can measure everything and approve nothing — an absence rather than a refusal, because a refusal is a conversation an agent can reopen. [digline for agents](../agents.md).

## When to use which

Use **Inspect AI** when the subject is a model or a capability: benchmarks, comparisons across providers, agentic tasks that need a sandbox, safety and security evaluations, anything where the sample has a `target` and the question is how often the model hits it. Its solver and scorer vocabulary is the right one for that work, and nothing in digline replaces the sandboxing.

Use **digline** when the subject is your application and the question is regression: this prompt, this retrieval, this configuration, against the state a person approved — with the approval in the repository and the answer an exit code in CI.

Together they are complementary rather than overlapping, because they answer at different altitudes: Inspect to decide whether a model is good enough for the job, digline to notice the morning it stopped being.

---

**The other comparisons:** [promptfoo](promptfoo.md) · [DeepEval](deepeval.md) · [Braintrust](braintrust.md) · [LangSmith](langsmith.md) · [Langfuse](langfuse.md) · [Opik](opik.md) — or [the index](index.md), which asks which question each family of tools answers rather than each tool.
