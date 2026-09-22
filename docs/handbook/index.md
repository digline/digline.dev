---
title: Handbook
description: >-
  Nine chapters on evaluating LLM applications in practice: what to build
  first, cases, ground truth, checks, the judge, the baseline, maintenance.
  About the problem, not the tool.
seo_title: >-
  Handbook: keeping an LLM feature under control
---

# Handbook

Nine chapters on keeping an LLM feature under control, for people who have one
in production and have not yet had the bad week. They are about the problem, not
about the tool: nothing here needs digline installed, and most of the numbers
come from one small public project you can go and read. Start at the first chapter
and read them in order — each one leans on the one before it.

- **[0. Before the prompt](00-before-the-prompt.md)** — the four decisions
  that come before the prompt and decide whether the feature can be measured
  at all. The one chapter that asks you to change what you are building
  rather than to measure it.
- **[1. What you are actually shipping](01-what-you-are-shipping.md)** — why a
  model call looks like a function and is not one, and what that costs you.
- **[2. Cases: the asset nobody builds](02-cases.md)** — every team has a
  prompt, almost none has cases. What a case is, and how to have twenty by this
  afternoon.
- **[3. Ground truth: when nobody gives you one](03-ground-truth.md)** — where
  the right answers come from when there is no labelled data, and why that is
  decided when you write the feature.
- **[4. Checks: deterministic first, judge last](04-checks.md)** — how to turn
  an output into a verdict, and the rule that saves the most time: use a model
  to judge only what nothing else can.
- **[5. The judge](05-the-judge.md)** — the two noises, why you have to measure
  the judge's before you can read your system's, and the procedure
  that replaces guessing with a number.
- **[6. The reference](06-the-reference.md)** — a threshold is not a reference.
  The one number you write down and agree to be measured against.
- **[7. Maintenance](07-maintenance.md)** — when the suite runs, what should
  make you look, and what to do the morning it turns red and you changed
  nothing.
- **[8. For teams building for others](08-for-teams-building-for-others.md)** —
  the same suite doing two more jobs when the LLM feature belongs to a customer,
  and the one rule that cannot be bent.
