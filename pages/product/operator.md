# The operator loop

digline answers one question: *did the system get worse than what
somebody approved?* This page is about who asks that question when
nobody is looking.

An **operator** is an agent that runs the checks on a schedule,
absorbs the measurement's own noise, and wakes a human only for drift
that deserves a decision. How it does that is
[the reference assembly](examples/operator.md)'s to say, and that is
where it changes. This page is about why you would want one, and what
it is not allowed to become. Everything here is either shipped — and
linked — or marked as being designed with pilots. There is no third
category.

## Two questions, two sources

The loop watches one thing — the measurement — fed by two sources.
They are equal in the design and staggered in implementation.

**The committed suite, re-run on a schedule**, answers: *is the system
I approved still that system?* This is digline's thesis pointed at
production: the same suite that gates your CI, run against the real
endpoint with the real model under the real keys ([`HttpTarget`](api.md)
exists for exactly this), compared against the baseline somebody
signed. Synthetic monitoring, in the oldest sense: known probes, on a
cadence, against the live system. **Every brick of this runs today.**

**Production traffic, turned into cases**, answers a different
question: *is the world still the one I approved for?* A suite covers
what you knew to ask. Your users ask things its author never foresaw —
and drift hides best exactly there. Turning traffic into cases means
capture, correlation, redaction at birth, and a harvest that
*proposes* candidates the way an agent proposes anything in digline:
a human approves them, or they are nothing. **This source is
designed, not shipped.** The landing format already exists — a
harvested case is a [TOML suite](declarative.md) plus its cases,
diffable and reviewable like any other — but the harvest itself is
being designed with people who have real traffic. Bring your history;
the last section says how.

## What it is not allowed to become

The operator automates the judgment [`AGENTS.md`](https://github.com/digline/digline/blob/main/AGENTS.md)
writes down — and nothing beyond it. Three boundaries, and none of
them is a setting.

**It cannot approve.** `promote` is not on the operator's surface —
not refused, absent. A refusal is a conversation an agent can reopen;
an absence is not. A baseline to re-approve needs a person, and that
is not a policy a future release could relax.

**It cannot repair.** The operator watches the measurement; it does
not fix the system. A prompt belongs to your engineer or your coding
agent, and the alert is the handover between the two.

**It cannot spend without saying so.** Every action it takes carries
a declared cost, and what bounds the total is declared in
configuration before anything runs — not chosen in the moment. With a
stochastic judge, enough re-runs always produce a green one, and a
limit picked afterwards measures your patience rather than the
system.

What it decides on its own, how it classifies, and when it wakes
somebody are [the reference assembly](examples/operator.md)'s to
state, beside the code that does it.

## Where it lives, and what travels

**In your perimeter, with your keys.** A container beside your
application — the [official image](docker.md) with a different
entrypoint — a scheduler you already have, and the operator's model
called with your credentials. It is the same trust model as the
judge: the reasoning about a report happens where the report is born.

An alert keeps apart what the wire said and what a model thought
about it, and says which is which: the measurement is digline's, the
opinion is the operator's, and the document never lets the second
wear the first's clothes.

Delivery is deliberately boring: a webhook, an email, an issue opened
in your own repository. An alert is a document, not a platform. There
is no inbox to host, and no state of ours to keep.

## Why the loop is not a service

The first question this design gets asked is whether we could run it
for you. No — and the reason is yours, not ours.

The reports the loop reasons about carry verdict reasons,
configurations, case names: fragments of your system and of your end
clients' data. Hosted by us, your compliance perimeter would suddenly
include us — our servers, our keys, our subprocessor agreement, our
audit. digline exists so that none of that is needed. What leaves
your perimeter is the redacted alert your own suite
[declared could travel](api.md) — and nothing else.

(The one hosted thing this project may ever grow is a fleet console
that receives *only* those already-travel-safe alerts and verdicts,
for teams maintaining AI features across many end clients. That is a
different page, for a later day.)

The README has said it since before this page existed: **if digline
ever grows paid features, they will run inside your perimeter too.**

## Run it today

[`examples/operator/`](examples/operator.md) is the reference
assembly: a suite, an operator configuration — cadence, stopping
rule, budget, in a file, not in someone's head — an operator prompt
written against this document, the interactive path, and a scheduled
workflow whose escalation opens an issue in your own repository. Real
alerts the loop produced ship beside it, and they are what this page
describes in the abstract. The deterministic parts run without any
key; the judgment is an explicit opt-in, the same convention every
example in the repository follows.

Fork it, point it at your endpoint, change the cadence.

## Designed with pilots

The second source — traffic into cases — is being designed with
people who run LLM systems in production. What a capture looks like.
How a request correlates to a run boundary. What makes one sample a
candidate golden and another one noise. What redaction can do at
birth, and what it cannot: a case you commit lives in your
repository, so the question is not whether the payload is written
down but whose perimeter the repository is in — and what a capture
should do when that repository is not yours is one of the open
questions, not a thing already settled. These are questions your
history answers better than our whiteboard.

If that is you, [open an issue](https://github.com/digline/digline/issues)
— that is the fastest way to move this.
