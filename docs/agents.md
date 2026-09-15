---
title: digline for agents
seo_title: >-
  digline for agents: measure everything, approve nothing
description: >-
  What a coding agent can do with digline and what it cannot: run and read
  every measurement, and reach no surface that promotes a baseline.
---

# digline for agents

An agent can measure everything and approve nothing. Measurement is work that can be delegated; approving what counts as "acceptable" is not, because a system that can move its own reference optimizes the reference.

## The absence, not the refusal

On the MCP server `promote` does not exist: eight tools read a result or measure a new one, and none of them writes a baseline. A refusal is a conversation an agent can reopen — argue with, retry, work around. An absence is not. The surface is in [digline over MCP](product/mcp.md), the reasoning in [ADR 0011](product/adr/0011-the-mcp-server.md).

## The loop that watches

The operator watches a suite on a cadence, tells a draw from drift from a structural flip — several cases flipping together — and opens an issue in the repository when the answer needs a decision. The remedy stays outside it: fixing the prompt belongs to an engineer or a coding agent, and the alert is the handover. Each cycle proves the wall instead of trusting it: one write that must fail, `promote` called by name, beside one that must succeed, because refusal alone proves nothing. The design is in [the operator loop](product/operator.md), the probe in [its example](product/examples/operator.md).

## Judging what it did, not what it wrote

An agent's sentence is not what moved the money. `ToolsCalled` holds which tools were called and in what order; `ToolCalledWith` holds the arguments one call carried. In the [LangGraph example](product/examples/langgraph.md) a dispatch agent must look an order up before refunding it and refund the figure the lookup returned — an agent that skips the lookup writes a good sentence, and no assertion on the text can see it. Both checks are listed under [the assertions](product/api.md#the-assertions).

## Where the agent meets the gate

[`pytest-digline`](product/pytest.md) puts the comparison in a pytest report, one row per check; the [GitHub Action](https://github.com/digline/digline-action) comments it on the pull request and exits with digline's code. Two more surfaces an agent can drive, and neither can promote: no flag, fixture or marker in the plugin and no input in the Action makes a run the new baseline.

## The rules the agent reads

[`AGENTS.md`](https://github.com/digline/digline/blob/main/AGENTS.md) is the judgment layer the tool does not encode: when to re-run, when to investigate, what to recommend. The same rules ship as a Claude Code skill, [`operating-digline`](https://github.com/digline/digline/tree/main/.claude/skills/operating-digline), and a test fails if the two drift apart. The first rule:

> **Never run `digline promote` on your own initiative.** Assemble the evidence — the `compare` output, the run key, what moved and why you believe it — and recommend. The human runs the command, or tells you to.
