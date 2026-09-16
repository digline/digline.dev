---
title: digline and Opik
seo_title: >-
  digline and Opik: an Opik alternative with no backend to deploy
description: >-
  What Opik does well — Apache-2.0 tracing, experiments, LLM-as-judge metrics,
  the Agent Optimizer, guardrails, a fully self-hostable platform — and where
  digline differs: no platform, and the approved reference in your repository.
---

# digline and Opik

Opik is Comet's open-source platform for the whole LLM lifecycle, and its self-hosted story is one of the least qualified in the category. Where it and digline diverge is where the truth is kept: Opik's unit of record is an experiment in a platform, digline's is a file in your repository.

## What Opik does well

Tracing is the base and it is thorough: `@track` on a function logs it, and an agent run arrives as a full trace tree — every call, every step, cost and latency attached. Around it: datasets, experiments, and a metric library of LLM-as-judge and heuristic scorers — `Hallucination`, `AnswerRelevance`, `ContextPrecision`, `Moderation` among them — plus prompt management and a playground.

The production side is more than a dashboard. Online evaluation rules score live traffic as it arrives, **Opik Guardrails** checks outputs against safety rules in the path rather than after it, and a pytest integration runs evaluations in CI on every commit. **Opik Agent Optimizer** is a separate SDK that improves prompts and agents against a dataset rather than only reporting on them — an answer to a question digline does not address at all.

And the licence is the part worth stating plainly: Apache-2.0, with the server backend, web application, tracing, datasets, experiments, prompt management, online evaluation and the optimizer all in the repository. `./opik.sh` brings the whole platform up under Docker Compose; there is a Helm chart for Kubernetes. Self-hosting the full product needs no commercial licence. If you want to see what your application is doing, call by call, that is a short path to it.

## What digline does differently

**The unit of record.** Opik's is the experiment, and an experiment lives in a platform: you deploy a backend, a database and a UI, and the results live there. digline's is a file. `digline promote` writes `.digline/<tenant>/baselines/<suite>.json` — every check on every case with its score, the prompt text that produced it, the commit it ran at, the configuration hash — and you commit it. It goes through code review, it rolls back with `git revert`, and it carries who approved it and under which commit. One answers *what is happening?*; the other answers *did it get worse than what was approved, and who approved it?*.

**The operational floor.** Opik's minimum is a running platform, self-hosted or Comet's. digline's is `uv add digline` or a `docker run`, and there is no server anywhere — not Comet's, not yours. No account, no key, no telemetry. For a team that has to put a gate inside someone else's CI, that is the difference between a dependency and a deployment.

**The noise floor is measured per case.** Scores on a dashboard move on their own, and a drop is only readable against how far that particular check travels. `Suite.samples` runs each case N times and the reference keeps each check's observed interval, so `digline compare` reports a drop inside that band as within the noise and does not count it, and one outside it as a regression. Two checks in the same suite carry two different floors. [ADR 0006](../product/adr/0006-repeated-samples-and-the-noise-floor.md) has the run that forced the decision.

**The verdict has three states, and it is the exit code.** `digline compare` exits `0`, `1` or `2`: nothing got worse, something did, something could not be judged. Scores over time on a dashboard answer a different shape of question than a three-state verdict that gates a pipeline, and the third state exists because a judge that errored is not evidence either way. [ADR 0001](../product/adr/0001-verdict-not-score.md).

**`promote` is absent from every surface an agent can reach.** None of the MCP server's tools writes a baseline, and neither does any flag in `pytest-digline` or any input in the GitHub Action. Opik's optimizer changes prompts against a dataset; nothing in digline changes anything, and nothing in it lets an agent move the line the build is measured against. An absence rather than a refusal. [digline for agents](../agents.md).

## When to use which

Use **Opik** when you need tracing and want one platform across the lifecycle: traces of real runs, datasets grown out of them, experiments, guardrails in the path, online rules over production traffic, and an optimizer that proposes better prompts. Use it when Apache-2.0 self-hosting of the whole platform is the requirement.

Use **digline** when the question is regression against an approved reference, and the answer has to live in the client's repository, survive an audit and gate a CI job — with nothing to deploy.

Using both is coherent: they answer different questions, and neither reads the other's storage. Opik watching what the application does, digline holding the line on what it is allowed to become.

---

**The other comparisons:** [promptfoo](promptfoo.md) · [DeepEval](deepeval.md) · [Braintrust](braintrust.md) · [LangSmith](langsmith.md) · [Langfuse](langfuse.md) · [Inspect AI](inspect-ai.md) — or [the index](index.md), which asks which question each family of tools answers rather than each tool.
