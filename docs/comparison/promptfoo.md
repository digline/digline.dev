---
title: digline and promptfoo
seo_title: >-
  digline and promptfoo: a promptfoo alternative for regression, not selection
description: >-
  What promptfoo does well — the prompt/provider matrix, its assertion library,
  red teaming — and what digline does instead: a committed reference, a noise
  floor measured per case, and a verdict that is an exit code.
---

# digline and promptfoo

promptfoo answers *which of these should I ship?*. digline answers *did it get worse than what I approved?*. Those are different questions, and the tools are shaped by which one they took.

## What promptfoo does well

promptfoo is a matrix. A `promptfooconfig.yaml` declares `prompts`, `providers` (or `targets`) and `tests`; `promptfoo eval` runs every combination; `promptfoo view` opens a local viewer where the outputs sit side by side, one column per variant. When the question is *this prompt or that one, this model or that one*, that layout is the answer, and getting to it costs one file.

The assertion library is wide, and most of it needs no model: `equals`, `contains`, `icontains`, `regex`, `starts-with`, `is-json`, `is-xml`, `is-sql`, `levenshtein`, `rouge-n`, `bleu`, `meteor`, `latency`, `cost`, and `javascript`, `python` or `webhook` for anything the list does not cover. The model-graded ones come after: `llm-rubric`, `g-eval`, `factuality`, `answer-relevance`, `context-faithfulness`, `context-recall`, `classifier`, `moderation`, `select-best`. Each assertion carries a `threshold` and a `weight`, a `metric` name groups several of them into one number, and `derivedMetrics` composes those after the run. For agents there are `trajectory:tool-used`, `trajectory:tool-args-match`, `trajectory:tool-sequence`, `trajectory:step-count`, and a `trace-*` family over spans.

It is built to run locally and to gate a pipeline. `promptfoo eval` exits `100` when at least one test case fails or the pass rate is under the configured threshold, and `PROMPTFOO_FAILED_TEST_EXIT_CODE` changes that code to whatever your CI expects. `--filter-failing`, `--filter-pattern` and `--filter-sample` narrow a re-run to the part you are working on. Output goes to CSV, JSON, YAML, HTML, XML or JUnit.

And `promptfoo redteam` is a second tool inside the first: adversarial test generation by plugin and strategy, a scan report, guardrails. Nothing in digline addresses security testing at all. If red teaming is on your list, that is a reason to run promptfoo regardless of what else you use.

## What digline does differently

Five things, and none of them is a longer assertion list.

**The reference is a run someone approved, committed to the repository.** promptfoo holds a run against the thresholds in the config. digline holds it against a specific earlier run: `digline promote` writes `.digline/<tenant>/baselines/<suite>.json` — every check on every case with the score it got, the prompt text that produced it, the commit it ran at, the configuration hash — and you commit that file. It goes through code review, it rolls back with `git revert`, and six months later it says who approved what. A threshold catches *below the line*. It does not catch *worse than it was*: 0.91 down to 0.78 against a threshold of 0.70 is still green everywhere, and it is the drift that reaches a customer first.

**The noise floor is measured per case, not assumed.** `Suite.samples` runs each case N times and keeps the observed interval rather than only the fold, so `digline compare` knows how far each check moves on its own. A drop that lands inside the reference's band for that check is reported as within the noise and does not count against the run; a drop that leaves it does. Two cases in one suite get two different floors, because they wobble by different amounts — a rubric with a borderline line is not a substring match. The reasoning, and the fixture that forced it, are in [ADR 0006](../product/adr/0006-repeated-samples-and-the-noise-floor.md).

**The verdict has three states and it is the exit code.** `digline compare` exits `0` when nothing got worse, `1` when something did, and `2` when something could not be judged. The third state is not folded into the other two: a judge that errored is neither a pass nor a regression, and a suite that reported it as either would be lying in one direction or the other. [ADR 0001](../product/adr/0001-verdict-not-score.md) is that decision.

**There is no server and no telemetry.** `uv add digline`, or the Docker image; no account, no backend, no hosted viewer, and nothing to deploy. promptfoo is local-first too, so this is a narrow difference rather than a wide one — but it is a real one: promptfoo sends command-level telemetry by default, which `PROMPTFOO_DISABLE_TELEMETRY=1` turns off (its documentation states that prompts, outputs, test cases and API keys are not among it), and `promptfoo share` uploads an eval when you ask it to. digline has neither switch because it has neither feature. For a team whose prompts and outputs cannot leave the perimeter, that is the architecture rather than a setting.

**`promote` is absent from every surface an agent can reach.** The MCP server has tools and none of them writes a baseline; no flag in `pytest-digline` and no input in the GitHub Action does either. An agent can measure everything and approve nothing — not because it is refused, but because the call does not exist. [digline for agents](../agents.md) has the rest.

## When to use which

Use **promptfoo** when you are choosing: comparing prompts, models or configurations against each other, sweeping a matrix, looking for the variant that wins. Use it when you need red teaming. Use it when the team wants one YAML file and a viewer and nothing else.

Use **digline** when the choice is made and the job is to keep it: a reference approved by a named person, in the repository, and a comparison on every change that separates a real drop from the judge's own variance. Use it when the answer has to survive an audit, or when the decision about what "acceptable" means must not be reachable by an agent.

Using both is coherent, and they do not collide: promptfoo reads `promptfooconfig.yaml` and writes its own results, digline reads a `suite.py` and writes `.digline/`. A common arrangement is promptfoo while a change is being explored, digline as the gate on the pull request once it has been chosen.

---

**The other comparisons:** [DeepEval](deepeval.md) · [Braintrust](braintrust.md) · [LangSmith](langsmith.md) · [Langfuse](langfuse.md) · [Inspect AI](inspect-ai.md) · [Opik](opik.md) — or [the index](index.md), which asks which question each family of tools answers rather than each tool.
