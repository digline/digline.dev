---
title: digline and Braintrust
seo_title: >-
  digline and Braintrust: a Braintrust alternative with no platform to run
description: >-
  What Braintrust does well — Eval(), experiments, a persistent baseline,
  Loop, autoevals — and where digline differs: the same comparison with the
  reference as a committed file and no platform anywhere.
---

# digline and Braintrust

Braintrust is the tool on this list whose core idea is closest to digline's. It has experiments, it has a baseline, and it comments regressions on a pull request. The disagreement is not about whether to compare against an approved run. It is about where that run is kept, and what approving it costs.

## What Braintrust does well

The eval itself is a small, well-chosen shape. `Eval()` takes `data` — the cases, with inputs, optional expected outputs and metadata — a `task`, which is the function under test and can be any code rather than only a model call, and `scores`, a list of scorers. `bt eval` discovers and runs the eval files: `--watch` re-runs on save while you work, `--no-input --jsonl` makes the output usable in CI, `--first N` and `--sample N` cut the dataset down for a smoke run on a pull request. Each run becomes an **experiment**: an immutable, comparable record.

The comparison is genuinely good. Select a **baseline** experiment and Braintrust aligns cases across the two runs and puts a score delta on every row, improvements and regressions coloured; a persistent baseline means CI compares against the same reference each time without reselecting it. The GitHub Action creates or updates one comment on the pull request with the improvements and regressions against that baseline, and links back to the full experiment. `BaseExperiment()` in the `data` field supports hill climbing — using a previous experiment's outputs as the expected field when you have no ground truth, which is an honest answer to a real problem.

Around the eval there is a platform: **playgrounds** for iterating on prompts in the browser, **datasets** built from logged traces and human review, **online scoring** that runs scorers over production traces as they arrive, dashboards, and **Loop**, an agent that builds scorers, datasets and dashboards from your data. Self-hosting exists on the Enterprise plan and is a hybrid split: the data plane — API, Postgres, Redis, object storage and the Brainstore query engine — runs in your AWS, GCP or Azure account with official Terraform modules, while the control plane with the web UI, authentication and metadata stays with Braintrust.

**autoevals**, Braintrust's scorer library, is MIT and works standalone with nothing but a model key. digline adapts it directly: [`FromAutoevals`](../product/metrics.md#fromautoevals) puts an autoevals scorer under a digline threshold and tolerance, and `digline.core` does not import `autoevals` to do it — `Score` was given the same shape on purpose.

## What digline does differently

**The reference is a file in the repository, not a record in a platform.** Braintrust's baseline is an experiment, and an experiment lives where the experiments live — selected in a UI, or pinned for CI, in a system you either buy or deploy. digline's `promote` writes `.digline/<tenant>/baselines/<suite>.json`: every check on every case with its score, the prompt text that produced it, the commit it ran at, the configuration hash. You commit it. The approval is a diff in a pull request with a name on it, `git revert` undoes it, and the question *who approved this, when, under which prompt* is answered by `git log` rather than by an export. That is the whole disagreement, and it is a disagreement about custody rather than about features.

**Nothing to deploy, in either direction.** digline's minimum is `uv add digline` or `docker run`. There is no control plane, no data plane, no Terraform, no account, and no telemetry — not a hosted option declined, but no server component in the product at all. Braintrust's hybrid deployment is a serious piece of engineering and it answers the data-residency question well; it also means the smallest possible Braintrust is a running platform, and the smallest possible digline is a dependency.

**The noise floor is measured per case.** A score delta between two runs is only readable if you know how much that score moves on its own. `Suite.samples` runs each case N times and the reference stores the observed interval per check, so `digline compare` reports a drop inside that band as within the noise and does not count it, and a drop outside it as a regression. Two checks in the same suite carry two different floors. The run that forced the decision — one case going 5/5, 2/5, 5/5 with nothing changed — is in [ADR 0006](../product/adr/0006-repeated-samples-and-the-noise-floor.md).

**The verdict has three states, and it is the exit code.** `digline compare` exits `0`, `1` or `2`: nothing got worse, something did, something could not be judged. The third is not folded into the other two, because a scorer that errored is not evidence either way. [ADR 0001](../product/adr/0001-verdict-not-score.md).

**`promote` is absent from every surface an agent can reach.** The MCP server's tools read and measure; none writes a baseline, and neither does any flag in `pytest-digline` or any input in the GitHub Action. Braintrust's own agent, Loop, builds scorers and datasets — useful, and a different question from who is allowed to move the line the build is measured against. In digline that call does not exist rather than being refused. [digline for agents](../agents.md).

## When to use which

Use **Braintrust** when more than one person needs to look at the results: a playground for someone who does not write the eval, datasets grown from production traces, human review, online scoring over live traffic, dashboards over time. Use it when the platform is the point — one system from logging to eval to monitoring — and the hybrid deployment answers your data-residency requirement.

Use **digline** when the answer has to be a file: a client's repository, an audit six months later, a CI job that gates on an exit code, and no infrastructure to run or budget. Use it when the noise floor of an LLM judge is the thing making your comparisons unreadable, or when the approval must be out of an agent's reach.

Together they have a seam the other pairs on this list do not, because autoevals is a shared vocabulary: the same scorer can score a Braintrust experiment and, through `FromAutoevals`, a digline check. Braintrust for exploring and watching, digline for the gate whose record stays in the repository.

---

**The other comparisons:** [promptfoo](promptfoo.md) · [DeepEval](deepeval.md) · [LangSmith](langsmith.md) · [Langfuse](langfuse.md) · [Inspect AI](inspect-ai.md) · [Opik](opik.md) — or [the index](index.md), which asks which question each family of tools answers rather than each tool.
