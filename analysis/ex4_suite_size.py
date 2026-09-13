"""Exercise 4: scout's judge, one run, scored on the 17 old cases and on all 144.

Recomputes accuracy, precision and recall from the per-case verdicts of the
September 11 run, on the full set and on the subset of the 17 cases in
cases-17.json, checks them against the run's and the baseline's aggregates,
and builds the confusion matrix from the recorded outputs.
"""

from __future__ import annotations

import json
from collections import Counter

from _runs import aggregate, fraction, load, ratio, repo_args, run_id, run_path, verdict, votes

SUITE = "scout-judge"
RUN = "2026-09-11T15-09-23"
BUDGET_USD = 0.020
MARKS = ["commented", "upvoted", "ignored"]
VERDICTS = ["comment", "upvote", "skip"]

args = repo_args(__doc__.splitlines()[0], "scout")
path = run_path(args.scout, SUITE, RUN)
run = load(path)
cases = {c["id"]: c for c in load(args.scout / "cases.json")}
old = {c["id"] for c in load(args.scout / "cases-17.json")}
baseline = load(args.scout / ".digline" / "alessandro" / "baselines" / "scout-judge.json")

print(f"run {run_id(path)}")
print(f"  config {run['config_hash']}  model {run['target_config']['values']['model']}  "
      f"cases {len(run['results'])}  JUDGE.md {run['artifacts']['JUDGE.md']['sha'][:8]}")
print(f"  the 17 old cases are all in the run: {old <= {r['case_id'] for r in run['results']}}")
print()


def metrics(results: list[dict]) -> dict[str, tuple[int, int]]:
    """Accuracy on the full verdict; precision and recall on 'comment' vs the rest.

    A case is predicted `comment` when its majority on agrees_on_comment says
    so: it passes and the label is positive, or it fails and the label is negative.
    """
    correct = sum(verdict(r, "agrees_with_mark")["status"] == "pass" for r in results)
    tp = fp = fn = 0
    for r in results:
        positive = cases[r["case_id"]]["label"] == "positive"
        predicted = positive == (verdict(r, "agrees_on_comment")["status"] == "pass")
        tp += positive and predicted
        fp += (not positive) and predicted
        fn += positive and not predicted
    return {"accuracy": (correct, len(results)), "precision": (tp, tp + fp), "recall": (tp, tp + fn)}


subset = [r for r in run["results"] if r["case_id"] in old]
full = metrics(run["results"])
small = metrics(subset)

print(f"{'':<10} {'17 cases':<18} {'144 cases':<18} {'run aggregate':<14} {'baseline':<9}")
for name in ["accuracy", "precision", "recall"]:
    print(f"{name:<10} {ratio(*small[name]):<18} {ratio(*full[name]):<18} "
          f"{fraction(aggregate(run, name)['reason']):<14} "
          f"{fraction(aggregate(baseline, name)['reason']):<9}")
print(f"  baseline is run {baseline['created_at']}, on {len(baseline['results'])} cases")
print()

for label, group in [("17 cases", subset), ("144 cases", run["results"])]:
    ids = [r["case_id"] for r in group]
    marks = Counter(cases[i]["expected"]["mark"] for i in ids)
    subs = Counter(cases[i]["metadata"]["subreddit"] for i in ids)
    print(f"{label}: " + ", ".join(f"{marks[m]} {m}" for m in MARKS)
          + "; top subreddits " + ", ".join(f"r/{s} {n}" for s, n in subs.most_common(3)))
print()

# --- The confusion matrix, from the outputs the run recorded ----------------------

matrix: Counter = Counter()
no_majority = []
flapping = 0
unanimous_fp = 0
for r in run["results"]:
    mark = cases[r["case_id"]]["expected"]["mark"]
    said = Counter(json.loads(resp["output"])["verdict"] for resp in r["responses"])
    top, n = said.most_common(1)[0]
    s = votes(verdict(r, "agrees_with_mark"))
    flapping += 0 < s.count("1") < len(s)
    if n * 2 <= len(r["responses"]):
        no_majority.append((r["case_id"], mark, dict(said), verdict(r, "agrees_with_mark")))
        continue
    matrix[mark, top] += 1
    unanimous_fp += mark == "ignored" and top == "comment" and n == len(r["responses"])

print("my label x judge's majority verdict over 5 samples")
print(f"  {'':<10}" + "".join(f"{v:>9}" for v in VERDICTS))
for m in MARKS:
    print(f"  {m:<10}" + "".join(f"{matrix[m, v]:>9}" for v in VERDICTS))
print(f"  cases with no majority verdict: {len(no_majority)}")
for case_id, mark, said, v in no_majority:
    print(f"    {case_id}: marked {mark}, samples {said}, "
          f"agrees_with_mark {votes(v)} -> {v['status']}")
print(f"  suspended cases in the run: {sum(r['suspended'] for r in run['results'])}")
print(f"  ignored but judged comment: {matrix['ignored', 'comment']}, "
      f"of which unanimous: {unanimous_fp}")
print(f"  cases whose five samples of agrees_with_mark are not unanimous: {flapping}")
print()

# --- Cost ---------------------------------------------------------------------------

costs = [resp["cost_usd"] for r in run["results"] for resp in r["responses"]]
over = sorted((c for c in costs if c > BUDGET_USD), reverse=True)
budget_pass = sum(verdict(r, "cost_budget")["status"] == "pass" for r in run["results"])
print(f"calls {len(costs)}, total ${sum(costs):.2f}")
print(f"single calls above ${BUDGET_USD:.3f}: {len(over)}, worst ${over[0]:.6f} "
      f"(+{over[0] / BUDGET_USD - 1:.0%})")
print(f"cost_budget passed on {budget_pass}/{len(run['results'])} cases (it checks the mean of five)")
