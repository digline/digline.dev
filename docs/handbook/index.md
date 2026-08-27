---
title: Handbook
description: >-
  Seven chapters on keeping an LLM feature under control, for people who have
  one in production and have not yet had the bad week.
---

# Handbook

Seven chapters on keeping an LLM feature under control, for people who have one
in production and have not yet had the bad week. They are about the problem, not
about the tool: nothing here needs digline installed, and the numbers all come
from one small public project you can go and read. Start at the first chapter
and read them in order — each one leans on the one before it.

- **[1. What you are actually shipping](01-what-you-are-shipping.md)** — why a
  model call looks like a function and is not one, and what that costs you.
- **[2. Cases: the asset nobody builds](02-cases.md)** — every team has a
  prompt, almost none has cases. What a case is, and how to have twenty by this
  afternoon.
- **[3. Checks: deterministic first, judge last](03-checks.md)** — how to turn
  an output into a verdict, and the rule that saves the most time: use a model
  to judge only what nothing else can.
- **[4. The judge](04-the-judge.md)** — the two noises, why you have to measure
  the judge's before you can read your system's, and the forty-minute procedure
  that replaces guessing with a number.
- **[5. The reference](05-the-reference.md)** — a threshold is not a reference.
  The one number you write down and agree to be measured against.
- **[6. Maintenance](06-maintenance.md)** — when the suite runs, what should
  make you look, and what to do the morning it turns red and you changed
  nothing.
- **[7. For teams building for others](07-for-teams-building-for-others.md)** —
  the same suite doing two more jobs when the LLM feature belongs to a customer,
  and the one rule that cannot be bent.
