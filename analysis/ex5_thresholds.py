"""Exercise 5: scout's gate thresholds, against the promoted run they came from.

Checks the written rule (each threshold sits between the measured value and
the value one case fewer), lists every threshold configuration that appears in
a run file and whether git ever held it, and how many points one case is worth.
"""

from __future__ import annotations

import re
import subprocess

from _runs import aggregate, fraction, load, repo_args, run_id, run_path, runs_dir, verdict, votes

SUITE = "scout-judge"
BIG_RUN = "2026-09-11T15-09-23"
METRICS = ["accuracy", "precision", "recall"]

args = repo_args(__doc__.splitlines()[0], "scout")


def git(*argv: str) -> str:
    return subprocess.run(["git", "-C", str(args.scout), *argv],
                          capture_output=True, text=True, check=True).stdout


def thresholds(run: dict) -> tuple[float, ...]:
    return tuple(aggregate(run, m)["threshold"] for m in METRICS)


# --- The promoted run and the rule ----------------------------------------------------

baseline_path = args.scout / ".digline" / "alessandro" / "baselines" / f"{SUITE}.json"
baseline = load(baseline_path)
promoted = [p for p in sorted(runs_dir(args.scout, SUITE).glob("*.json"))
            if load(p)["created_at"] == baseline["created_at"]]
print(f"baseline {baseline_path.name}: run created_at {baseline['created_at']}"
      f" = {', '.join(run_id(p) for p in promoted)}")
print(f"  records when it was promoted: {'promoted_at' in baseline}")
print()

print(f"{'metric':<10} {'measured':<16} {'one case fewer':<16} {'threshold':<10} rule holds")
for m in METRICS:
    num, den = map(int, fraction(aggregate(baseline, m)["reason"]).split("/"))
    t = aggregate(baseline, m)["threshold"]
    measured, lower = num / den, (num - 1) / den
    print(f"{m:<10} {f'{num}/{den} = {measured:.3f}':<16} {f'{num - 1}/{den} = {lower:.3f}':<16} "
          f"{t:<10} {lower < t <= measured}")
# "One case fewer" keeps the denominator. A case moving across it can also move
# the denominator of precision; say what that does rather than leave it implied.
counts = aggregate(baseline, "precision")["metadata"]
tp, fp = counts["true_positive"], counts["false_positive"]
print(f"  precision if a positive stops being predicted: {tp - 1}/{tp + fp - 1} = "
      f"{(tp - 1) / (tp + fp - 1):.3f}; if a negative starts: {tp}/{tp + fp + 1} = "
      f"{tp / (tp + fp + 1):.3f}")
print()

# --- Every threshold configuration in a run file, and whether git had it ------------------

committed: dict[tuple[float, ...], list[str]] = {}
for commit in git("log", "--format=%h", "--", "suite.py").split():
    source = git("show", f"{commit}:suite.py")
    found = dict(re.findall(r"(Accuracy|Precision|Recall)\(over=\"\w+\", threshold=([0-9.]+)", source))
    if len(found) == 3:
        key = tuple(float(found[k]) for k in ["Accuracy", "Precision", "Recall"])
        committed.setdefault(key, []).append(commit)

seen: dict[tuple[float, ...], list[str]] = {}
for path in sorted(runs_dir(args.scout, SUITE).glob("*.json")):
    seen.setdefault(thresholds(load(path)), []).append(run_id(path))

print("threshold configurations (accuracy, precision, recall) in run files")
for key, ids in seen.items():
    in_git = ", ".join(committed.get(key, [])) or "never committed"
    print(f"  {key}: {len(ids)} runs, {ids[0][:19]} .. {ids[-1][:19]}; git: {in_git}")
print()

# --- What one case is worth ------------------------------------------------------------------

big_path = run_path(args.scout, SUITE, BIG_RUN)
big = load(big_path)
flapping = sum(0 < votes(verdict(r, "agrees_with_mark")).count("1") < 5 for r in big["results"])
for n in [len(baseline["results"]), len(big["results"])]:
    print(f"one case in {n}: {100 / n:.1f} accuracy points")
print(f"not unanimous in {run_id(big_path)}: {flapping}/{len(big['results'])}")
