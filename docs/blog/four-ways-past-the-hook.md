---
title: "Four ways an agent walked past my command hook"
description: "Four times in two days, a guard of mine named the act it guarded, and the act arrived under another name. In the order it happened, with three checks to run."
seo_title: >-
  Four ways an agent walked past my command hook
date: 2026-09-25
---

# Four ways an agent walked past my command hook

You have built a control over what an agent may do. A hook that asks
before a dangerous command. A permission filter. An allowlist. It
matches a string against a command line. The string says `promote`, or
`deploy`, or `terraform apply`. If it is there, you stop and ask a
person. If it is not, you stay out of the way.

That is the only thing you can do at that layer, and it is the right
thing to build. Here is what happened to mine.

## Three defences, all correct

A person approves a new baseline, not an agent. The baseline is the
stored reference every later run is compared against. If an agent
promotes on its own, nobody decided anything.

Three surfaces defend that:

| surface | what it matches |
| --- | --- |
| the MCP server | no tool called `promote` — a test calls it and expects *unknown tool* |
| the plugin hook | the first word after `digline` is `promote` or `register` |
| the skill an agent loads | *"Never run `digline promote` on your own initiative"* |

Each is correct about what it matches. Two have tests. The plugin ships
this line, and an agent reads it at install time: *an MCP server that
measures, reads and explains, and cannot promote a baseline, because
approval is a person's commit.*

## The reader who was not using it

On 2026-09-24 somebody outside the project read the code. They were
writing a digline profile for [HOL Guard][hol], which meant going
through the commands one by one and writing down what each one does to
the world. They were not using digline. They were reading it for a
different question: is this command a read or a write?

`digline view` opens a small local web page for browsing runs. It served
`POST /promote`.

This was not an oversight. The route was designed and documented, under
a heading of its own: *The one route that writes*. Nobody decided what
it meant sitting next to a guarantee that this thing cannot promote. A
guarantee written three times.

From the source it looks like it needs a browser and a click. It does
not. The origin check allows a request with no `Origin` header, and a
comment says why: that is a curl or an old browser, and neither is the
attack it was written for. Against a caller with a shell, it is the
door.

Measured, not read. Two runs in a store, the first promoted. The server
started. One POST with no `Origin` and no credential of any kind. 200,
and the baseline moved to the other run. No `promote` command ran. No
MCP tool was called; none exists to call. The hook stayed quiet, because
it reads the first word after `digline`, and that word was `view`.

Two things found afterwards are worse. First, the skill does not just
fail to mention `view`. Two sections below the rule it sends the agent
there: *"`digline view` is the table you pick from."* Good advice,
pointing at the one surface none of the three defences watch. Second,
the hook's silence on `view` was a tested invariant. `digline view
--suite s.py` sat in a list of commands asserted silent, next to `grep
-rn promote src/`. That test was written when `view` belonged in the
list. By now it held the hole open.

## The fix, and the day it shipped

The repair was not a better pattern. The route now refuses by default.
There is no button, and a POST to `/promote` gets the same 404 as any
unknown path: on that server there is no promote. A `--allow-promote`
flag brings the old server back for a person who wants it, and the hook
learned to watch the flag. That flag allows promotion for every run in
the store until the server is killed — a bigger decision than one
promotion, not a smaller one.

That shipped in 0.20.0, on the afternoon of 2026-09-24. Going over the
release that evening, I checked something I had never run: the flag,
against the code that parses it.

argparse accepts any unambiguous prefix of an option, and nothing had
turned that off. `digline view --a`, `--al`, `--allow`, `--allow-p` and
`--allow-prom` all start the promoting server. Measured: the form is on
the page for each one. The hook matches the flag as a whole word, so all
of them are silent. Only the full spelling asks.

Then the chain, end to end. `digline view --a`, then a POST with no
`Origin`. 200. The baseline moved. Nobody was asked.

So 0.20.0 was public with that hole in it, for about fourteen hours.
0.20.1 closed it the next morning.

The docstring had ruled this out, in a sentence I wrote:
*"`--allow-promote=` is not a spelling argparse accepts for a
`store_true`, so a prefix match would only ever widen this."* That is
true about suffixes. argparse abbreviates prefixes. A confident sentence
about what the parser accepts, never run against the parser.

## What closing it found

The same sweep had found two more, by feeding the hook payloads rather
than reading it:

| spelling | hook asks? |
| --- | --- |
| `digline promote --run x` | yes |
| `uvx digline promote --run x` | yes |
| `python -m digline.cli promote --run x` | yes |
| `uv tool run digline promote --run x` | **no** |
| `python -m digline.cli.main promote --run x` | **no** |

`uv tool run` is the long form of `uvx`. The matcher handles `uvx`, and
checks that the word after `uv` is `run`. `python -m digline.cli.main`
is a working entry point: it runs, exit 0. The module list does not name
it, and the one name it does have cannot run at all.

Closing those two turned up a third that nobody had looked for: `uv run
python -m digline.cli promote`. Silent as well. It appeared because the
fix had to stop listing launchers and work out, in general, what `uv`
runs. The general answer named a spelling the hand-written list had
missed. All of them ask in 0.20.1, where `view` also refuses
abbreviations, so the full word is the only spelling that parses.

## Nobody read their way to any of it

Four times, and not once from reading the code that holds the guard.

The first came from somebody classifying commands for another tool. The
other three came from running the hook with a payload. Not from reading
it. I had read it many times, and once wrote a wrong conclusion about it
into a docstring.

Reading cannot find this kind of defect, and not because the reader is
careless. The defect is never in the guard's logic. Every surface here
had been reviewed for correctness, and `POST /promote` is correct: it
does what its documentation says, through the same call as the CLI, with
the same refusals. Correct and contradictory are two different things,
and only the second shows up in a table of what writes what. No
per-surface review builds that table. The gap is between the strings the
guard matches and the strings the other side accepts: the parser, the
launcher, the router. That set is not written down anywhere the guard's
author is looking.

There are two ways to finish a guard that keys on a name. They are not
equivalent.

**Make the name the only spelling.** Turn abbreviation off on that
parser. The full word is then the only thing that parses, and a
whole-word match is complete by construction. The guard did not get
smarter. The set of accepted spellings got smaller. This one cannot
drift.

**Or derive the spellings from the side that accepts them.** The parser
knows every prefix it will take. The packaging knows every entry point
that starts the program. A guard that asks them keeps up when they
change. A written list is stale already. What counts as an unambiguous
prefix of `--allow-promote` depends on every other option on that
command. One new flag quietly changes what the guard should match.

The third option does not work, and it is the one I had taken: write the
list once, then check it by reading it.

## What to look at in your own code

Three checks, about ten minutes, on whatever guard you have.

**An abbreviation.** Take the exact string your guard matches. Shorten
it. Run it. Does the code that parses the command accept spellings your
guard does not? Option prefixes. `--flag=value` against `--flag value`.
Clustered short flags. A trailing slash on a path. Run it instead of
reasoning about it, and watch the guard, not the program.

**A different launcher.** Your guard knows the program by one name. The
program answers to several: `uvx`, `uv tool run`, `pipx run`, `npx`,
`python -m`, an absolute path, a wrapper script, a container. Write down
the ones that work on your machine and feed each to the guard.

**A second route to the same operation.** Your guard names a command.
Now ignore commands, and ask what else performs the act. The web route.
The API endpoint. The library function a script can import. The editor
with the file open. List the call sites that reach the write, and check
each one against the guard. This check found the worst of the four, and
it is the only one of the three that is not about strings.

## The part I should say plainly

Three of the four were defects in a hook we ship, in digline's Claude
Code plugin, on machines that are not mine. All are closed in 0.20.1,
the release this post waited for. Somebody would work it out from the
diffs; better said here.

The hook has always described itself the same way, and that stays true:
a preference, not a wall. The wall is the reviewed diff. No hook can be
the wall, and the reason is the same shape as everything above. A hook
sees a string that a model proposed to a shell. `bash -c`. A variable.
An alias. An `ssh`. An entry point nobody listed. Each is a spelling,
and there is no complete set of spellings. The hook sits on the side
where the act has a name. A guarantee has to sit on the side where the
act has an effect: the write, the route, the commit. There, there is one
thing to list, and it is not a vocabulary.

That is also why these four did not produce the rule "the view must not
promote". The rule they produced is that the set of code paths reaching
the write is written down, and a path not on the list fails the build.
That would catch the fifth. It is ruled and not yet written, which is
the honest state of it.

All four are side by side in [ADR 0032 §8][adr]: what each guard
matched, which spelling walked past, and what closed it.

Three spellings were invisible to reading the guard. The fourth was
invisible to fixing the other three. It only appeared when the fix had
to answer in general what the guard had been answering from a list. A
guard that keys on a name does not fail once and get closed. It fails
the same way in the fix, and again in the fix of the fix.

[hol]: https://github.com/hashgraph-online/hol-guard
[adr]: ../product/adr/0032-the-second-path-to-an-absent-tool.md#8-a-guard-that-keys-on-a-name-is-defeated-by-another-spelling-of-the-same-act
