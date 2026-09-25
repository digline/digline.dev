---
title: "You blocked the word, not the act"
description: "A guard that keys on a name is defeated by a different spelling of the same act. Three of them, measured in one day: a second route, a different launcher, an abbreviated flag."
seo_title: >-
  You blocked the word, not the act
date: 2026-09-25
---

# You blocked the word, not the act

If you've built a control over what an agent may do — a hook that asks
before a dangerous command, a permission filter, a tool allowlist — you
built it by matching a string against a command line. Something in it
says `promote`, or `deploy`, or `terraform apply`; if the string is
there you stop and ask a person, and if it isn't you stay out of the
way.

That is the only thing available at that layer, and it is the right
thing to build. But what you have caught is a **word**, and what you
meant to catch is an **act**. Those come apart quietly, because nothing
fails when they do.

Here are three that came apart in my own code, all measured on the same
day, 2026-09-24.

## One: the act arrives under a fourth word

The decision I care about is that a person, not an agent, approves a
new baseline. Three surfaces defend it, and every one of them keys on
the same word:

| surface | what it matches |
| --- | --- |
| the MCP server | there is no tool called `promote` — the absence is asserted by a test |
| the plugin hook | the first word after `digline` is `promote` or `register` |
| the skill | *"Never run `digline promote` on your own initiative"* |

Each is correct about what it matches. And `digline view`, which opens
a small local web page for browsing runs, served `POST /promote`.

That was not an oversight in the small: the route was designed and
documented, under a heading in its own docs called *The one route that
writes*. Every part of it was decided. What was never decided is what
it meant sitting next to a guarantee, written three times, that this
thing cannot promote.

Read from the source it looks like it needs a browser and a click. It
does not. The origin check returns "allowed" when there is no `Origin`
header at all, with a comment saying why: that's a curl or an old
browser, neither of which is the cross-site attack it was written for.
Against a caller with a shell it is the whole door. Measured, not read
off the code: two runs in a store, the first one promoted, the server
started, one POST with no `Origin` and no credential of any kind. 200,
and the baseline moved to the other run. No `promote` command ran. No
MCP tool was called; none exists to call. The hook never fired, because
it reads the first word after `digline` and that word was `view`.

Two details make this worse than a gap. The skill doesn't merely fail
to mention `view` — two sections below the rule, it **points the agent
at it**: *"`digline view` is the table you pick from."* Good advice,
aimed at the one surface none of the three defences watch. And the
hook's silence on `view` was a **tested invariant**: `digline view
--suite s.py` sat in the list of commands asserted silent, next to
`grep -rn promote src/`. That test's reasoning is sound — a hook that
interrupts reading is a hook people learn to dismiss — and it was
written when `view` belonged in that company. It was pinning the hole
open.

## Two: the same command, spelled differently

The hook keys on the word `digline`. So I fed it payloads instead of
reading it:

| spelling | hook asks? |
| --- | --- |
| `digline promote --run x` | yes |
| `uvx digline promote --run x` | yes |
| `python -m digline.cli promote --run x` | yes |
| `uv tool run digline promote --run x` | **no** |
| `python -m digline.cli.main promote --run x` | **no** |

`uv tool run` is the long form of `uvx`, which the matcher handles; it
checks that the word after `uv` is `run`, and `uv tool run` isn't.
`python -m digline.cli.main` is a working entry point — verified, it
runs, exit 0 — that the module set doesn't list. In the same line the
entry `"digline"` is dead: there is no `__main__.py`, so `python -m
digline` refuses. The list holds a spelling that cannot run and misses
one that can.

## Three: the flag that the fix introduced

The first instance was fixed: the view refuses to promote by default
now, the route 404s, and a `--allow-promote` flag brings the old server
back for a person who wants it. The hook learned to watch that flag,
since a flag that enables promotion for every run in the store until
you kill the server is a bigger decision than one promotion, not a
smaller one.

argparse accepts any unambiguous prefix of an option, and nothing
turned that off. `digline view --a`, `--al`, `--allow`, `--allow-p`,
`--allow-prom` all start the promoting server. The hook matches the
flag as a whole word, so **all of them are silent**; only the full
spelling asks. Run end to end: `digline view --a`, then a POST with no
`Origin`, 200, the baseline moved, nobody asked. The guard added to
close the first hole was walked past by an abbreviation of the flag it
was added to watch, in the release that shipped it.

The docstring of the matching code said the opposite, in a sentence I
wrote: *"`--allow-promote=` is not a spelling argparse accepts for a
`store_true`, so a prefix match would only ever widen this."* True
about suffixes, and argparse abbreviates prefixes. A confident sentence
about what the parser accepts, never once run against the parser.

## Nobody read their way to any of this

This is the uncomfortable half. **None of the three was visible by
reading the code.**

The first was found by somebody else. **kantorcodes1** was writing a
digline profile for [HOL Guard][hol], an external tool, which meant
classifying each command by what it does to the world. That reading asks a question no
review here had asked: *is this command a read or a write?* Every one
of these surfaces had been reviewed by someone asking whether it was
correct, and `POST /promote` **is** correct: it does what its
documentation says, with an origin check, through the same call as the
CLI, with the same refusals. Correct and contradictory are independent
properties, and only the second is visible from a table of
what-writes-what — which nothing in a per-surface review ever builds.

The other two were found by running the hook with a payload. Not by
reading it; I had read it many times.

The people who write these controls verify them by reading them, and
reading cannot find this class, because the defect is never in the
guard's logic. Each of these guards does exactly what its code says.
The gap is between the strings the guard matches and the strings the
*other side* accepts — the parser, the launcher, the router — and that
set is written down nowhere its author is looking.

## Two ways to finish a name-based guard

Two, and they are not equivalent.

**Make the name the only spelling.** Turn abbreviation off on that
parser, so the full word is the one thing that parses. Then a
whole-word match is complete by construction — not because the guard
got smarter, but because the set of accepted spellings shrank to the
one it matches. This is the one that cannot drift.

**Or derive the spellings from the side that accepts them.** The parser
knows every prefix it will take; the packaging knows every entry point
that starts the program. A guard that asks them, instead of listing
what its author remembered, keeps up when they move. A listed guard is
already stale: what counts as an unambiguous prefix of
`--allow-promote` depends on every other option on that command, so
adding an unrelated flag silently changes which spellings the guard
should have been matching.

What does not work is the third option, which is the one I had taken:
write the list once, then verify it by reading it.

## What to look at in your own code

Three checks, about ten minutes, on whatever guard you have in front of
you.

**An abbreviation.** Take the exact string your guard matches, shorten
it, and run it. Does the thing that actually parses the command accept
spellings your guard doesn't? Option prefixes, `--flag=value` against
`--flag value`, clustered short flags, a trailing slash on a path. Run
it rather than reasoning about it, and check the guard, not the
program.

**A different launcher.** Your guard knows the program by one name. The
program answers to several: `uvx`, `uv tool run`, `pipx run`, `npx`,
`python -m`, an absolute path, a wrapper script, a container. Write
down the ones that work on your machine and feed each to the guard.

**A second route to the same operation.** Your guard names a command.
Now ignore commands and ask: what else performs this act? Enumerate
every call site that reaches the write — the web route, the API
endpoint, the library function a script can import, the editor with the
file open. Then check each against the guard. This is the one that
found the worst of the three, and it is the only one of the three
checks that isn't about strings at all.

## The part I should say plainly

Two of the three above are defects in a hook **we ship** — in digline's
Claude Code plugin, on machines that are not mine. The first instance
is fixed and released; the hook fixes ride the plugin's next release,
with the dead entry in the module list. Somebody will work this out
from the diffs, and it is better said here.

What the hook has always said about itself is what stays true: *a
preference, not a wall — the wall is the reviewed diff.* Why no hook
can be the wall is the same shape as everything above. A hook sees a
string a model proposed to a shell. `bash -c`, a variable, an alias, an
`ssh`, a Python one-liner, an entry point nobody enumerated — each is a
spelling, and there is no complete set of spellings. The hook lives on
the side of the act where the act has a *name*; a guarantee has to live
on the side where it has an *effect* — the write, the route, the
commit. There, there is exactly one thing to enumerate, and it is not a
vocabulary.

So the fix for the first instance was not a better pattern in the hook.
It was removing the route. And the rule the three of them produced is
not "the view must not promote" — it is that the set of code paths
reaching the write is written down, and a path that is not on the list
fails the build. That is what would catch the next one, which nobody
has thought of yet. It is ruled and not yet written, which is the
honest state of it.

The uncomfortable part is the last sentence of instance three. The
guard that was added to close the first hole was defeated, on the day
it shipped, by an abbreviation of the flag it was written to watch. A
name-keyed guard doesn't fail once and get fixed. It fails the same way
again, in the fix.

[hol]: https://github.com/hashgraph-online/hol-guard
