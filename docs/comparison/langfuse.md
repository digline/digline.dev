---
title: digline and Langfuse
seo_title: >-
  digline and Langfuse: a Langfuse alternative with no platform to self-host
description: >-
  What Langfuse does well — OpenTelemetry tracing, prompt management,
  experiments, batch evaluation, an MIT self-hosted core — and where
  digline differs: no platform at all, and the reference in your repository.
---

# digline and Langfuse

Langfuse is the tool here whose open-source story is closest to unconditional: the core is MIT, self-hosting is a first-class path rather than an enterprise concession, and the limits you meet are the ones you would expect. The difference from digline is not licence or custody. It is that Langfuse's unit is a platform and digline's is a file.

## What Langfuse does well

Tracing, first. A trace holds every call in a run — model calls and the retrieval, embedding and API calls around them — with sessions for multi-turn conversations, user attribution, and agent runs rendered as a graph. It is built on OpenTelemetry, which is the detail that matters most: instrumentation is not a proprietary shape you would have to unpick later, and there are integrations for well over a hundred libraries and frameworks on top of it.

Prompt management is a product of its own. Prompts are versioned in Langfuse, labels move a version into production without a code change, and the playground lets someone iterate on one in the browser and then run it as an experiment against a dataset.

Evaluation covers both directions from one shape. **Datasets** and **dataset runs** give you the offline side; evaluators receive the input, metadata, output and expected output of each item and return scores. LLM-as-a-judge evaluators run in the UI or the SDK, code evaluators run deterministic checks, and custom evaluators can be numeric, boolean or categorical. The same evaluator shape then runs the other way: **batch evaluation** scores a selected set of historical observations, so a judge you just wrote can be tested against production data you already have. Annotation queues collect the human baseline, and alerts reach Slack, webhooks or GitHub Actions.

The self-hosted deployment is real. All core features and APIs are in the MIT-licensed OSS build without usage limits; a licence key in `LANGFUSE_EE_LICENSE_KEY` unlocks a published list — project-level RBAC roles, protected prompt labels, data retention policies, audit logs, server-side data masking, UI customization, organization creators, the org management API with SCIM, and the instance management API. The list is enumerated rather than described, so what the key buys is a question with an answer.

## What digline does differently

**There is no platform.** Langfuse self-hosted is a backend, a database, a worker and a UI — modest as platforms go, and genuinely yours, but something that has to be deployed, upgraded and backed up by someone. digline's minimum unit is `uv add digline`, or a `docker run`, and there is no server component at all: not Langfuse's, not digline's, not anyone's. No account, no key, no telemetry. For a consultancy that has to run a gate inside a client's CI, that difference is whether the answer is a dependency or a procurement conversation.

**The reference is a committed file, and promoting it is a decision with a name on it.** Langfuse's scores live in Langfuse; a dataset run is a record in the platform. `digline promote` writes `.digline/<tenant>/baselines/<suite>.json` — every check on every case with its score, the prompt text that produced it, the commit it ran at, the configuration hash — and you commit it. It is reviewed as a diff, reverted with `git revert`, and readable in six months by anyone with the repository and nothing else. Langfuse versions your prompts; digline versions the *approval* of the measurement those prompts produced, in the same history as the code.

**The noise floor is measured per case.** Scores in a dashboard move, and reading one against the last is only meaningful if you know how far that score travels on its own. `Suite.samples` runs each case N times and the reference stores each check's observed interval, so `digline compare` reports a drop inside that band as within the noise and does not count it, and one outside it as a regression. Two checks in one suite get two different floors. [ADR 0006](../product/adr/0006-repeated-samples-and-the-noise-floor.md) has the run that forced the decision.

**The verdict has three states, and it is the exit code.** `digline compare` exits `0`, `1` or `2` — nothing got worse, something did, something could not be judged. Langfuse can alert a GitHub Action when a score crosses a line; digline's output *is* the pipeline's answer, and it distinguishes a regression from a judge that failed instead of folding them together. [ADR 0001](../product/adr/0001-verdict-not-score.md).

**`promote` is absent from every surface an agent can reach.** None of the MCP server's tools writes a baseline, nor does any flag in `pytest-digline` or any input in the GitHub Action. Measurement can be delegated; deciding what counts as acceptable cannot, and in digline that is an absence rather than a refusal an agent could argue with. [digline for agents](../agents.md).

## When to use which

Use **Langfuse** when you need to see what the application did: traces of real runs, sessions, cost and latency, an agent's path rendered as a graph, prompts versioned and deployed by label, a judge tested against traffic you already collected. Use it when several people need the same view, and when self-hosting under MIT with a published list of paid features is what the organisation requires.

Use **digline** when the question is narrower and the answer has to be a file: did this change make it worse than the run someone approved, which case, by how much, and is that drop larger than what that check does on its own. Use it when there is to be nothing to deploy.

Using both is the ordinary shape, and the two do not touch: Langfuse watches production and holds the prompt library, digline gates the pull request and keeps the approved reference in the repository next to the code it describes.

---

**The other comparisons:** [promptfoo](promptfoo.md) · [DeepEval](deepeval.md) · [Braintrust](braintrust.md) · [LangSmith](langsmith.md) · [Inspect AI](inspect-ai.md) · [Opik](opik.md) — or [the index](index.md), which asks which question each family of tools answers rather than each tool.
