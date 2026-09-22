---
title: digline and DeepEval
seo_title: >-
  digline and DeepEval: a DeepEval alternative with the baseline in your repo
description: >-
  What DeepEval does well — its metric library, pytest-native assert_test,
  DeepTeam — and where digline differs: the approved reference is a committed
  file rather than an official run on Confident AI.
---

# digline and DeepEval

DeepEval is the closest neighbour digline has. Both are Python, both live in a `tests/` directory, both hold a score against a number. The one place they part is where the number someone approved is kept.

## What DeepEval does well

DeepEval is a metric library first, and the library is large. RAG has `AnswerRelevancyMetric`, `FaithfulnessMetric`, `ContextualPrecisionMetric`, `ContextualRecallMetric`, `ContextualRelevancyMetric`. Agents have `TaskCompletionMetric`, `ToolCorrectnessMetric`, `ArgumentCorrectnessMetric`, `PlanAdherenceMetric`, `StepEfficiencyMetric`. Multi-turn has `ConversationCompletenessMetric`, `RoleAdherenceMetric`, `KnowledgeRetentionMetric`. Safety has `BiasMetric`, `ToxicityMetric`, `PIILeakageMetric`, `RoleViolationMetric`. Every one of them takes a `threshold`, returns a score between 0 and 1 with a reason attached, and runs concurrently under `async_mode`.

When none of them fits, `GEval` builds one from a criterion written in English, and `DAGMetric` builds one as a decision tree when the criterion has branches rather than a single judgement. That pair covers a lot of ground that a fixed library cannot.

It is pytest-native in a way few eval tools are. `LLMTestCase` holds `input`, `actual_output`, `expected_output` and the retrieval context; `assert_test(test_case, metrics)` is an assertion your existing test file can hold; `deepeval test run` is the CLI your CI already knows how to call, with `-r` and a number to run a test several times, `-c` to skip what has not changed, and `-i` to get through a run. They are short flags with no long form. `EvaluationDataset` and `Golden` give you the dataset side, and `Synthesizer` generates cases when you do not have enough of them. `@observe()` adds tracing and component-level evaluation to an agent without restructuring it.

DeepTeam, from the same team, red-teams the application against a library of vulnerability classes with single-turn and multi-turn attacks, mapped out of the box to OWASP's Top 10 for LLMs and for Agents, NIST AI RMF and MITRE ATLAS among others. And Confident AI is the platform behind all of it: shared reports, production monitoring, human annotation, an MCP server. digline has no equivalent to any of those three.

## What digline does differently

**The approved reference is a file in your repository.** DeepEval has the concept of a known-good run: `deepeval test run --official` marks one, and later runs are compared against it to surface what regressed. That comparison happens on Confident AI and needs a `CONFIDENT_API_KEY`. digline's equivalent is `digline promote`, which writes `.digline/<tenant>/baselines/<suite>.json` — every check on every case with its score, the prompt text that produced it, the commit, the configuration hash — and you commit that file. The approval is then a line in a pull request with a name on it, it reverts with `git revert`, and it is readable six months later by someone who has no account anywhere. Nothing in digline compares anything over a network.

**The threshold and the reference are two different rules.** A `threshold` catches *below the line*: a score of 0.78 against a threshold of 0.70 passes, today and every day. It does not catch *worse than it was* — 0.91 last month, 0.78 now, nothing in the configuration changed, every assertion green. That drift is what a reference is for, and in digline it is the primary rule rather than a second one.

**The noise floor is measured per case.** `Suite.samples` runs each case N times and the reference keeps the observed interval for each check, not only the folded score. `digline compare` then reads a drop against the band that check actually showed: inside it, the report says so and the run is not counted as worse; outside it, it counts. Two checks in one suite get two different floors. An LLM judge disagrees with itself often enough that without this a suite either cries wolf or has its tolerances widened until it sees nothing — the run that forced the decision is in [ADR 0006](../product/adr/0006-repeated-samples-and-the-noise-floor.md).

**The verdict has three states, and it is the exit code.** `digline compare` exits `0` when nothing got worse, `1` when something did, `2` when something could not be judged. A metric that errored is not quietly a failure and not quietly a pass; it is the third state, and it gates differently. [ADR 0001](../product/adr/0001-verdict-not-score.md) has the argument.

**There is no server, no account and no telemetry.** `uv add digline` or the Docker image, and that is the whole installation. No key, no login, no hosted report, and nothing that leaves the machine the run happened on. For a team whose prompts and outputs cannot cross the perimeter, that is the architecture rather than a setting.

**`promote` is absent from every surface an agent can reach.** The MCP server's tools read runs and measure new ones; none writes a baseline. Neither does any flag in `pytest-digline` or any input in the GitHub Action. An agent can measure everything and approve nothing, and not because it is refused: the call does not exist. [digline for agents](../agents.md) explains why an absence and a refusal are not the same thing.

## When to use which

Use **DeepEval** when the work is *measuring*: you need a metric for faithfulness or tool correctness or role adherence and you would rather not write it, you want `GEval` to turn a sentence into a judge, you want `Synthesizer` to give you cases, or you want DeepTeam's red teaming. Use it when a shared platform is what the team needs — reports people outside the repository can open, production monitoring, annotation queues — and Confident AI is a good answer to that.

Use **digline** when the work is *holding a line*: the reference is approved by a person, lives in the repository, and the comparison on every change knows how much each check moves on its own. Use it when the record has to be auditable without an account, or when the approval must not be reachable by an agent.

Together they work, and the seam is the one place the two shapes meet: a DeepEval metric produces a score with a reason, and a digline assertion turns a score into a verdict against a threshold and a tolerance. digline ships an adapter for [`autoevals`](../product/metrics.md#fromautoevals) scorers and none for DeepEval metrics, so combining them today is either two runs in one CI job, or a DeepEval metric wrapped in a custom assertion. The second is a handful of lines, and it is not something digline documents.

---

**The other comparisons:** [promptfoo](promptfoo.md) · [Braintrust](braintrust.md) · [LangSmith](langsmith.md) · [Langfuse](langfuse.md) · [Inspect AI](inspect-ai.md) · [Opik](opik.md) — or [the index](index.md), which asks which question each family of tools answers rather than each tool.
