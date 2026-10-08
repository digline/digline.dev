# The GitHub Action

[`digline/digline-action`](https://github.com/digline/digline-action) runs the gate on a pull request. It compares the branch against the baseline committed in the repository, comments the comparison on the pull request, and exits with digline's code. This page covers what each exit code means, which of them are digline's and which are not, and what the action does not do.

## The smallest workflow

The step, in a job triggered by `pull_request`, after `actions/checkout`:

```yaml
- uses: digline/digline-action@v1
  with:
    suite: eval/suite.py
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

In an explicit `permissions:` block the job needs two entries: `contents: read`, without which the checkout fails, and `pull-requests: write` for the comment. Without the second the gate still works: the comment step warns, and the job's result is still digline's code.

## Since which version

**What this page describes holds from `v1.2.0`, released on 2026-10-08.** `@v1` points there. A workflow pinned to `v1.0.0` or `v1.1.0` gets the older behaviour, which differs in three ways:

- a `digline run` that fails makes the action exit `1`, *something got worse*, whatever digline returned, and leaves every output empty;
- every code other than `0`, `1` and `2` is annotated as *digline refused the request*, an internal error (`70`) and docker's `125` included;
- the comment is not posted when the report contains no backtick, which is the ordinary report.

The record is in issues [#4](https://github.com/digline/digline-action/issues/4) and [#6](https://github.com/digline/digline-action/issues/6). To pin, use `@v1.2.0` or its commit, not an older `v1.x`.

## Exit codes, in three kinds

The exit code is the action's contract, and the kind a code belongs to decides every word the action says about it: in the annotation, in the comment and in the outputs.

| Kind | Code | Means |
|---|---|---|
| **The verdict** | `0` | nothing got worse: the job passes |
| | `1` | something got worse: the job fails, and it comments |
| **digline's, not a verdict** | `2` | the run could not be judged. Nothing downstream of it is meaningful |
| | `64` | digline refused the request: a suite that could not be loaded, a tenant that does not match |
| | `70` | digline failed in a way nobody anticipated, and printed the traceback to the job log |
| **Not digline's** | `125`–`127`, or another | docker could not pull or start the image, or the container was stopped. The action exits with that code |
| | `255` | the action failed, and the code of what failed is one of the five above, or there is none |

What digline itself means by the first five is on the [API page](api.md#the-exit-code-exit_code-and-run_exit_code).

The action does not turn any of digline's codes into a pass or a fail of its own. It exits with digline's code, whether `digline run` or `digline compare` gave it, and never puts a `1` where digline gave another code.

A code digline does not have is not digline's, and the action does not report it as one. The annotation says *digline-action failed; not a digline exit code*, and the `exit-code` output is empty. When the code of what failed would read as one of digline's, a shell stopping on its own `1` for example, the action exits `255` instead. An exit code must never be readable as a verdict when nothing was judged.

## Inputs

| Input | Default | |
|---|---|---|
| `suite` | required | `path/to/suite.py[:attribute]` or `path/to/suite.toml`, from the repository root |
| `root` | `.` | the directory holding the store, the CLI's `--root` |
| `tenant` | empty | verifies the suite's tenant, never overrides it |
| `env` | empty | verifies the suite's environment, never overrides it |
| `image` | a digline release, see [the image](#the-image) | the image to run, or a derivation of it with the suite's dependencies |
| `run` | `true` | produce a run before comparing. **This calls the provider and spends money.** `false` compares the run an earlier step produced |
| `comment` | `true` | post the comparison on the pull request |
| `comment-on-success` | `false` | comment when nothing got worse, too |
| `forward-env` | the variables of the three first-party plugins | environment variables passed into the container, by name, when set on the step |
| `github-token` | `${{ github.token }}` | the token the comment is posted with |

`suite`, `root`, `tenant` and `env` are the CLI's own flags and mean exactly what they mean there.

## Outputs

All four are written on every path, whether the gate passes or fails and whether or not digline ran. An empty value is never a missing one: it says something.

| Output | Holds | When it is empty |
|---|---|---|
| `exit-code` | digline's code, unchanged | only when the action failed and digline gave no code |
| `headline` | the comparison's first line, the sentence the report shows | never. When nothing was compared it is a sentence from the action naming the code. It never carries digline's stderr, which can quote the suite; that stays in the job log |
| `run-key` | the key of the run that was compared, or `latest` with `run: false` | when there is no run: `digline run` failed, or the action failed before it |
| `report` | the path to the comparison, verbatim | never as a path. The file always exists, and it is empty when nothing was compared |

## Telling 1 from 2

Without `continue-on-error` the job stops at the action, with digline's code, which is the right default. To act on the difference, let the job continue and read the output:

```yaml
- uses: digline/digline-action@v1
  id: gate
  continue-on-error: true
  with:
    suite: eval/suite.py

- if: always()
  env:
    CODE: ${{ steps.gate.outputs.exit-code }}
    HEADLINE: ${{ steps.gate.outputs.headline }}
  run: |
    echo "$HEADLINE"
    case "$CODE" in
      0)  echo "proceed" ;;
      1)  echo "something got worse"; exit 1 ;;
      2)  echo "could not be judged: nothing downstream is meaningful"; exit 1 ;;
      "") echo "the action failed before digline gave an answer"; exit 1 ;;
      *)  echo "digline exited $CODE, which is not a verdict"; exit 1 ;;
    esac
```

The values go through `env:`, never as `${{ }}` inside `run:`. Interpolating them into the script is how a workflow gets a shell injection.

The empty branch is not optional. With `continue-on-error`, a recipe that reads only `0`, `1` and `2` passes a job in which the image was never pulled.

## The comment

One comment per suite, edited in place on every push rather than added to, so a branch pushed eleven times carries one comment that says what is true now. By default it is posted only when the code is not `0`: something got worse, the run could not be judged, or there is no verdict at all.

**On a pull request from a fork** the action still tries. It looks for its earlier comment and then edits or posts one, the read-only token refuses the write, and the step logs a warning, *the comment was not posted*, and exits `0`. The job's result is still digline's code. No comment on a fork's pull request is correct: that run has no access to the repository's secrets, which is what makes running a contributor's suite safe at all. The [action's README](https://github.com/digline/digline-action#the-trust-model-and-the-one-way-to-get-it-badly-wrong) has the one configuration that breaks this, and why not to use it.

### Two limits, both true today

**The comment is identified by the suite, and by nothing else.** Its marker holds the `suite` value, normalised: `root`, `tenant` and `env` do not enter it. Two invocations on one pull request with the same suite and a different `root`, `tenant` or `env` overwrite each other's comment, across jobs and workflows. The normalisation also makes distinct paths collide: `eval/suite.py:smoke` and `eval/suite.py-smoke` get one comment. This is [issue #5](https://github.com/digline/digline-action/issues/5), open, with no fix planned.

**With `comment-on-success: false`, a comment is never brought back to green.** A suite that gets worse comments. When a later push fixes it, nothing got worse, so the comment step does not run, and the old *something got worse* comment stays on the pull request as it was. The check mark is right and the comment is stale. `comment-on-success: true` avoids it, at the cost of a comment on every green pull request.

### One comment for N suites

A gate over several suites or agents, with a single comment naming the ones that got worse, is not something the action does. It is built downstream:

1. each invocation with `comment: false` and `continue-on-error: true`;
2. each one's `exit-code` and `headline` saved where a later job can read them. Across a matrix that means an artifact per leg, because a matrix job's outputs keep only one leg. In one job with several steps, copy the `report` file after each step if you need it, because its path is the same for every invocation and the next one overwrites it;
3. one job, `needs:` on the others, that writes the comment and fails if any code is not `0`. An empty `exit-code` and a `2` are red, not green.

There is no official example of this today.

## The image

The default image names a **digline** release, not the action's version. `@v1` is the action's line and digline is on its own, so `@v1` alone does not say which digline runs. The `image` default in the action's `action.yml` says it, and that line is the one place it is written.

As of 2026-10-08 the default is `ghcr.io/digline/digline:0.30.0`, from `v1.1.0` onwards.

Two checks keep it from falling behind:

- the action's own CI compares the default with the newest digline on PyPI, and the job fails when they differ. It runs every Monday on a schedule, on every push to the action's `main` and on every pull request to it;
- digline's `release-followup` workflow, which runs after every release and on every push to digline's `main`, reads the default on the action's `main` **and on `v1`**, and fails its run and opens an issue unless both name the released version. Both refs, because a bump on `main` that `v1` does not point at reaches nobody: until 2026-10-08, `@v1` still resolved to 0.9.0, after `main` had been bumped twice, to 0.19.0 and then 0.29.0.

For a suite whose `suite.py` imports an application, derive the image from the release the default names, add the suite's dependencies, and point `image` at the derivation. [The Docker image](docker.md) page has the how.
