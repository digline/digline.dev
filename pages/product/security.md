# How digline thinks about its own attack surface

digline is a program you run inside your own repository, with your own
keys, over your own prompts and your own customers' answers. That is
the whole design — [there is no server side](operator.md) — and it
moves the security question somewhere specific: not *what do they do
with my data*, but *what can this program be made to do on my machine*.

This page is the answer, with the record behind it. Everything here is
either shipped and linked, or marked as designed and not yet built.
There is no third category.

## Five surfaces

The threat model is not "digline is attacked". It is: somebody gets to
choose one of the inputs, and the question is what that buys them.

1. **The suite file.** `suite.py` is Python and it executes. Whoever
   can write it can run anything you can run.
2. **The store.** `.digline/<tenant>/` — every run, every baseline, and
   every path that reaches it from outside: a `--run` key, a `?run=`
   query string, an artifact a suite declares.
3. **The provider edge.** The credential, the endpoint, and everything
   digline *says* about them — in an error, on stderr, in a CI log.
4. **The documents that travel.** A run, a comparison, a report. The
   [payload/verdict boundary](adr/0002-three-worlds-and-where-the-data-lives.md)
   decides what crosses, and a field that crosses when it should not is
   a disclosure whatever else it is.
5. **The automation edge.** [The MCP server](mcp.md), where an agent
   rather than a person names the file; and
   [the Action](https://github.com/digline/digline-action), where a
   workflow runs the suite with your provider keys in reach.

Everything found so far has been on one of those five. So has
everything declared out of scope.

## Three boundaries, declared rather than assumed

**A suite inside the root is trusted.** The perimeter decides *which
file* may be named, not what that file may then do. `suite.py` is code;
constraining what code does is a sandbox, and digline is not one. This
is written into
[ADR 0011 §8](adr/0011-the-mcp-server.md) so that the next person to
confirm it reads a decision instead of finding a gap.

A [suite that is **data**](declarative.md) is a different case and gets
a different rule: no code at all, and reads bounded at the perimeter —
your repository, not the suite file's directory, because
`eval/suite.toml` naming `../prompts/system.md` is reading its own
project ([ADR 0007 §6](adr/0007-the-declarative-suite-format.md)).

**The perimeter is the repository.** Not the current directory, not the
suite's directory. Runs, baselines and artifacts resolve inside it or
they are refused — and a path is checked for *where it leads*, not only
for how it is spelled.

**The Action executes code from the checkout.** It loads the suite, and
a suite can be Python, and it wants provider keys. That makes
`pull_request_target` plus a checkout of the pull request's head a
[pwn request with the best possible secrets in reach](https://github.com/digline/digline-action#the-trust-model-and-the-one-way-to-get-it-badly-wrong),
and the README spells out the wrong workflow so nobody has to derive
it.

## What is out of scope, and why

**The behaviour of the models you evaluate.** A jailbreak that works on
your application is a finding about your application. digline generates
no attacks and has no opinion about what an answer should say; the
useful thing to do with one is turn it into a case, so the suite makes
sure it never works again.

**A race between the check and the read.** Every path is checked and
then opened, and between those two calls the filesystem can move. We
reproduced it — swapping a symlink in a loop while runs executed won 4
times in 30 — and are not closing it. The capability it needs, writing
to the repository mid-run, is already the capability to edit `suite.py`,
which is code. A threat model where the attacker can win a millisecond
race but cannot change the file about to execute is not a model of
anything.

Two things make that visible rather than silent: an artifact is recorded
under **the key it actually resolved to**, and artifacts are hashed. A
race that wins still leaves its name in the record.

Both are in [`SECURITY.md`](https://github.com/digline/digline/blob/main/SECURITY.md)
in as many words.

## Six fixes, found and fixed

Two releases in one day, 0.7.1 and 0.7.2. Four came from an audit of
digline's own surfaces; the last two came from going back and trying to
break the first four. Each was reproduced before it was fixed and is
pinned by a test that fails against the old code.

| | What it was | Where |
|---|---|---|
| **High** | `digline-mcp` executed a suite file from anywhere on disk: the `suite` argument was not constrained to `--root` — including on the five tools annotated `read_only_hint` | [GHSA-x56p-g933-6xx6](https://github.com/digline/digline/security/advisories/GHSA-x56p-g933-6xx6) |
| **Medium** | Reads escaping the perimeter, three ways: an unvalidated run key, an unbounded declarative-suite read, and a symlink followed out of the result store | [GHSA-j878-2v6m-m4vx](https://github.com/digline/digline/security/advisories/GHSA-j878-2v6m-m4vx) |
| **Low** | A credential embedded in a target URL reaching stderr and a CI build log | [GHSA-xrvr-5x82-w7g7](https://github.com/digline/digline/security/advisories/GHSA-xrvr-5x82-w7g7) |

Two are worth reading for the shape of the mistake rather than the
severity. `endpoint_host` reduced what *digline* said about a URL and
not what *urllib* said, so a URL with userinfo and no explicit port
raised an unhandled traceback carrying the key — through an exception
class the existing handler did not catch. And a run key was proved to be
a safe *segment* without ever being asked where it *led*, so a symlink
under a perfectly legal key was served by the viewer with a 200.

Both fixes are in the
[changelog](changelog.md) at full length, including what was ruled out.

## What held

The adversarial pass that found those last two also ran **38 attempts
that did not work**, and that half is the part worth publishing: the
MCP spec's own edge cases, suites as data, encodings, prefix traps,
normalisation. Case folding fails closed in both directions on a
case-insensitive filesystem.

Since then the rule is standing: **a release that adds surface gets an
adversarial delta-pass over that surface before the announcement
round** — not before the tag, before anyone is told to upgrade. Three
questions per new field: where does it cross a boundary, who wrote the
value, and what does a hostile value do there.

It has run twice.

- **Over 0.8.0.** Found `resolved_model` travelling in clear out of a
  redacted run, next to a `base_url` that redaction had withheld —
  a boundary decided that morning and wrong by lunchtime. 0.8.1 shipped
  before the announcements.
- **Over 0.9.0**, on the Action and the pytest plugin. No
  vulnerability, and nothing on PyPI needed a fix. It found the Action's
  trust model undocumented, which is now the README section linked
  above, and a comment marker that reached a `jq` program by string
  interpolation. It also confirmed what the design claimed: no `${{ }}`
  reaches any script body, and hostile input carrying quotes, `$()`,
  backticks and an appended `--privileged` each landed as one inert
  argument.

## When a finding becomes an advisory

The line is **exposure**, and it is the same line every time.

A **published advisory** for a vulnerability that shipped: a released
version, on an index somebody could install from. Three exist, and they
are the three in the table above.

A **`Security` entry in the changelog and no advisory** for a finding
the process caught before it could reach anybody. There is no version to
warn somebody off, and an advisory against a defect nobody could reach
is noise in the one channel that must not become noise. It is not the
lighter category — it is where the finding that never reached anybody
goes, described in full.

Report one through
[GitHub's private vulnerability reporting](https://github.com/digline/digline/security/advisories/new).
There is no bounty. There is a fast reply and a name in the record.

## Signs you can check yourself

None of the above is worth more than the evidence under it.

- **Every package on PyPI carries publish attestations.** PEP 740,
  signed by the workflow that built it — not by a person, and not
  after the fact. The publisher recorded against digline 0.9.0 is
  `digline/digline`, workflow `publish.yml`, environment `pypi`:
  [read the provenance](https://pypi.org/integrity/digline/0.9.0/digline-0.9.0-py3-none-any.whl/provenance).
- **The image carries SLSA provenance**, produced by the build rather
  than described by it: `docker buildx imagetools inspect
  ghcr.io/digline/digline:0.9.0 --format '{{json .Provenance}}'`.
- **The publishing workflow waits for a person.** The one irreversible
  step in a release — the upload — sits behind a required reviewer,
  because a version number is spent the moment it goes up.
- **Every action the build runs is pinned by commit SHA**, and the
  image's base by digest, with Dependabot keeping both current. A pin
  nothing watches is a freeze.
- **[OpenSSF Scorecard](https://scorecard.dev/viewer/?uri=github.com/digline/digline)**
  runs weekly and publishes, so the supply-chain checks can be read off
  the source rather than off a badge we render. **CodeQL** runs on every
  push and pull request.

  Read the zeros too. Two of them are structural: this is a
  single-maintainer project, and a mandatory-review checkmark earned by
  approving one's own pull requests would be theater. The checks that
  can be real here are real; the ones that would be performance are left
  at zero and said out loud.

Two of those are about digline's dependencies and its build, not about
its code. That is the honest shape of it: most of what a security page
can prove is about the chain around the software, and the part about the
software itself is the record above — reproduced, fixed, tested, and
written down whether or not anybody was watching.
