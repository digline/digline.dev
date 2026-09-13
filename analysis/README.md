# Analysis for "Bad evals, my own"

The scripts behind the numbers in [Bad evals, my own: five exercises from two LLM judges](https://digline.dev/blog/bad-evals-my-own/). One per exercise that has numbers to compute; exercise 2 has none, its diffs and results are read straight off the run files.

They only read: `.digline/` and `seen.json` in [brief](https://github.com/digline/brief) and scout, plus `git log` and `git show` in those two checkouts. Nothing is written, nothing is called over the network. Standard library only, Python 3.10 or later. Every number is printed next to the run id or file it comes from.

The run files are not in either repository: `.digline/*/runs/` is gitignored, as digline generates it, and only the baselines are committed. scout is private. So these scripts reproduce the post on the checkouts it was written from, and show exactly which fields of which run each number is read from; they do not reproduce it from a fresh clone.

By default the scripts look for `brief` and `scout` next to this repository (`../brief`, `../scout`); pass `--brief` or `--scout` to point elsewhere. From the repository root:

| exercise | command | what it prints |
|---|---|---|
| 1 | `python3 analysis/ex1_nonunanimity.py` | the three runs of September 3 (config hash, artifact shas, aggregates, commits touching `prompts/` between them), the seven cases not unanimous in at least one, and for each of the 16 runs with that config hash up to September 10 the non-unanimous cases and the chance that one sample disagrees with the majority |
| 3 | `python3 analysis/ex3_censored.py` | brief's `seen.json` by judge score × shown × marked, when the suite's 21 cases could have been exported from it, and the precision the baseline reports |
| 4 | `python3 analysis/ex4_suite_size.py` | the run of September 11 scored on its 144 cases and on the 17 of `cases-17.json`, against the run's and the baseline's aggregates; labels and subreddits of each set; the confusion matrix from the recorded outputs, the case with no majority, the false positives, the cost per call against the budget |
| 5 | `python3 analysis/ex5_thresholds.py` | the promoted run, each threshold against its measured value and the value one case fewer, every threshold configuration found in a run file and whether `suite.py` ever held it in git, and what one case is worth on 17 and on 144 |

`_runs.py` holds what the four share: the default paths and how to read a run.
