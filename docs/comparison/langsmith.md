---
title: digline and LangSmith
seo_title: >-
  digline and LangSmith: a LangSmith alternative for the pre-deploy gate
description: >-
  What LangSmith does well — tracing, datasets and experiments, evaluate(),
  annotation queues, online evaluation — and where digline differs: one
  question, answered by a committed file and an exit code.
---

# digline and LangSmith

LangSmith is usually described as observability, and the description undersells it: it has a full offline evaluation side too, with datasets, experiments and a comparison view. The difference from digline is not that one watches and the other tests. It is scope, and where the approved answer is kept.

## What LangSmith does well

Tracing is the foundation, and it is the part nothing here competes with. Every call in an agent run becomes a trace you can open — inputs, outputs, latency, cost, tool calls, the tree of it — and for anything built on LangChain or LangGraph it arrives with no instrumentation at all. Around that: dashboards, **rules** and webhooks for automations, **annotation queues** where a human labels runs, and an engine that surfaces recurring issues across traces rather than making you find them.

The evaluation side is a real framework. A **dataset** holds **examples** with inputs and reference outputs; `evaluate()` and `aevaluate()` run a target over it and produce an **experiment**, with `evaluators` per example and `summary_evaluators` across the run, `num_repetitions` to run each example more than once, and `max_concurrency` to control the fan-out. `evaluate_comparative()` does pairwise judging between two experiments. Evaluators can be code, LLM-as-judge, pairwise or human. Online evaluation runs reference-free evaluators over sampled production traffic and feeds the failures back into a dataset — the loop from *this went wrong in production* to *this is now a test case* is one of the things LangSmith does better than anything on this list.

It also meets an existing test suite: `@pytest.mark.langsmith` with `langsmith.testing` gives you `log_inputs()`, `log_outputs()` and `log_reference_outputs()` inside ordinary pytest tests, with the pass/fail rate collected under the `pass` feedback key and any traceable call inside the test traced automatically.

Self-hosting exists on the Enterprise plan, with a licence key: the `langchain/langsmith` Helm chart on Kubernetes, backed by Postgres, Redis and ClickHouse, with Terraform modules and Mission Control for operating it in-cluster.

## What digline does differently

**One question, and the reference for it is a file you committed.** LangSmith's experiments live in LangSmith — cloud or your own cluster, but a deployment either way, with a database behind it. `digline promote` writes `.digline/<tenant>/baselines/<suite>.json`: each check on each case with its score, the prompt text that produced it, the commit, the configuration hash. It goes into the repository, through code review, with a name on the pull request. *Who approved this, when, under which prompt* is `git log`, not an export or a retention policy. digline does no tracing, has no dashboard and sees no production traffic, and does not intend to.

**No server, no account, no telemetry — and digline pins that rather than claiming it.** The minimum installation is `uv add digline` or the Docker image. There is nothing to deploy and no key to hold. digline takes the point seriously enough to guard it in its own repository: `langsmith` is a hard dependency of `langchain-core`, so digline's LangChain and LangGraph examples set all four names the tracing lookup consults — `LANGSMITH_TRACING_V2`, `LANGCHAIN_TRACING_V2`, `LANGSMITH_TRACING`, `LANGCHAIN_TRACING` — in the job environment, and a test asserts all four in both workflows. An earlier release pinned only two, and the release notes say so. This is not a claim about LangSmith, which does exactly what it says; it is what "no telemetry" has to mean to be worth writing down.

**The noise floor is measured per case.** `num_repetitions` runs an example several times; digline's `Suite.samples` does that too, and then keeps the observed interval per check *in the reference*, so the next comparison can read a drop against the band that check actually showed. Inside the band it is reported as within the noise and does not count; outside it, it does. Two checks in one suite carry two different floors. [ADR 0006](../product/adr/0006-repeated-samples-and-the-noise-floor.md) has the run that forced it.

**The verdict has three states, and it is the exit code.** `digline compare` exits `0` when nothing got worse, `1` when something did, `2` when something could not be judged — the third kept separate because a judge that errored is not evidence in either direction. That exit code is the whole gate; there is no dashboard to check afterwards. [ADR 0001](../product/adr/0001-verdict-not-score.md).

**`promote` is absent from every surface an agent can reach.** None of the MCP server's tools writes a baseline, and no flag in `pytest-digline` or input in the GitHub Action does either. An agent can run and read everything and approve nothing, by absence rather than refusal. [digline for agents](../agents.md).

## When to use which

Use **LangSmith** for everything that happens after deploy, and for the loop back from it: traces of real runs, dashboards, annotation queues, online evaluators over live traffic, failures promoted into a dataset. Use it if your application is LangChain or LangGraph, where the instrumentation is free. Use it when several people who are not the developer need to look at the same run.

Use **digline** for the check before the deploy, when the record has to be in the repository rather than in a system: a reference approved by a named person, a comparison that knows each check's own variance, and an exit code that stops the pipeline. Use it when there is no budget or appetite for infrastructure, or when the prompts and outputs cannot leave the perimeter at all.

They stack without overlapping, and this is the ordinary arrangement: digline as the gate on the pull request, LangSmith watching what happens after the deploy and turning what it finds there into the next case in the suite.

---

**The other comparisons:** [promptfoo](promptfoo.md) · [DeepEval](deepeval.md) · [Braintrust](braintrust.md) · [Langfuse](langfuse.md) · [Inspect AI](inspect-ai.md) · [Opik](opik.md) — or [the index](index.md), which asks which question each family of tools answers rather than each tool.
