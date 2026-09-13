"""Exercise 3: brief's ground truth, by judge score, shown and marked.

`marked` is written only on the items brief.py showed me, so the table says
which part of the pipeline the suite can see at all.
"""

from __future__ import annotations

from collections import Counter

from _runs import aggregate, fraction, load, repo_args

args = repo_args(__doc__.splitlines()[0], "brief")
seen_path = args.brief / "seen.json"
seen = load(seen_path)

items: Counter = Counter()
shown: Counter = Counter()
marked: Counter = Counter()
for record in seen.values():
    score = record.get("score", "not judged")
    items[score] += 1
    shown[score] += bool(record.get("shown"))
    marked[score] += bool(record.get("marked"))

print(f"source: {seen_path} ({len(seen)} items)")
print()
print(f"{'judge score':<12} {'items':>6} {'shown':>6} {'marked':>7}")
for score in [1, 2, 3, 4, 5, "not judged"]:
    print(f"{score!s:<12} {items[score]:>6} {shown[score]:>6} {marked[score]:>7}")
print()

never_scored = items["not judged"]
print(f"never scored: {never_scored}/{len(seen)} = {never_scored / len(seen):.0%}")
low = [1, 2, 3]
low_shown = sum(shown[s] for s in low)
low_marked = sum(marked[s] for s in low)
low_items = sum(items[s] for s in low)
print(f"scored below 4 and shown (pad to five): {low_shown}, marked interesting: {low_marked}")
print(f"scored below 4 in all: {low_items}")
unshown_scored = sum(items[s] - shown[s] for s in [1, 2, 3, 4, 5])
print(f"scored but never shown, so never labelled: {unshown_scored}")
print()

# When the suite's cases were taken from this file: make_cases.py keeps every
# record that was shown, has a summary and has a mark, so count those by day.
cases_path = args.brief / "cases" / "brief.json"
cases = load(cases_path)
links = {c["metadata"]["link"] for c in cases}
eligible = [r for r in seen.values() if r.get("shown") and "summary" in r and "marked" in r]
print(f"cases: {cases_path.name}, {len(cases)} cases, "
      f"{sum(c['expected']['marked'] for c in cases)} marked; all in seen.json: "
      f"{links <= {r.get('link') for r in eligible}}")
print("  records make_cases.py would export, by the day they were judged:")
for day in sorted({r["judged_at"][:10] for r in eligible}):
    upto = [r for r in eligible if r["judged_at"][:10] <= day]
    print(f"    up to {day}: {len(upto)}")
print()

# The number the suite reports, which only the shown items can produce.
baseline_path = args.brief / ".digline" / "alessandro" / "baselines" / "brief-judge.json"
baseline = load(baseline_path)
print(f"baseline: {baseline_path.name}, created_at {baseline['created_at']}")
print(f"  precision {fraction(aggregate(baseline, 'precision')['reason'])} "
      f"on {len(baseline['results'])} cases")
