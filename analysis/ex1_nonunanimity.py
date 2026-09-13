"""Exercise 1: three runs of brief with nothing changed, and the sixteen behind them.

For every run of the brief suite with the fixture runs' config hash, up to and
including September 10, counts the cases whose five samples of
`agrees_with_mark` did not all agree, and the chance that a single sample
would have disagreed with the majority, averaged over the 21 cases.
"""

from __future__ import annotations

import subprocess

from _runs import aggregate, fraction, load, repo_args, run_id, run_path, runs_dir, verdict, votes

SUITE = "brief-judge"
FIXTURES = ["2026-09-03T06-14-13", "2026-09-03T06-18-43", "2026-09-03T06-24-50"]
LAST_DAY = "2026-09-10"

args = repo_args(__doc__.splitlines()[0], "brief")


def split(run: dict) -> tuple[int, float, dict[str, str]]:
    """Non-unanimous cases, P(one sample disagrees with the majority), votes per case."""
    flapping = 0
    p_disagree = 0.0
    per_case = {}
    for result in run["results"]:
        v = verdict(result, "agrees_with_mark")
        s = votes(v)
        agreed = s.count("1")
        if 0 < agreed < len(s):
            flapping += 1
            p_disagree += min(agreed, len(s) - agreed) / len(s)
        per_case[result["case_id"]] = f"{s} ({v['status'][0]})"
    return flapping, p_disagree / len(run["results"]), per_case


# --- The three fixture runs ------------------------------------------------------

fixtures = [(run_path(args.brief, SUITE, rid), None) for rid in FIXTURES]
fixtures = [(path, load(path)) for path, _ in fixtures]

print("fixture runs")
for path, run in fixtures:
    shas = {name: a["sha"][:8] for name, a in sorted(run["artifacts"].items())}
    print(f"  {run_id(path)}")
    print(f"    config {run['config_hash']}  artifacts {shas}  git {run['git_commit'][:8]}")
    print(f"    accuracy {fraction(aggregate(run, 'accuracy')['reason'])}  "
          f"precision {fraction(aggregate(run, 'precision')['reason'])}")

identical = len({(r["config_hash"], tuple((n, a["sha"]) for n, a in sorted(r["artifacts"].items())))
                 for _, r in fixtures}) == 1
print(f"  config hash and artifact shas identical across the three: {identical}")

first, last = fixtures[0][1]["git_commit"], fixtures[-1][1]["git_commit"]
touched = subprocess.run(
    ["git", "-C", str(args.brief), "log", "--format=%h %s", f"{first}..{last}", "--", "prompts/"],
    capture_output=True, text=True, check=True,
).stdout.strip()
print(f"  commits touching prompts/ between {first[:8]} and {last[:8]}: "
      f"{len(touched.splitlines()) if touched else 0}")
print()

splits = [split(run) for _, run in fixtures]
flappers = [case for case in splits[0][2]
            if any(s[2][case][:5] not in ("11111", "00000") for s in splits)]
print(f"cases not unanimous in at least one fixture run: {len(flappers)}")
header = "  ".join(f"{rid[11:16].replace('-', ':'):<9}" for rid in FIXTURES)
print(f"  {'case':<60}  {header}")
for case in flappers:
    cells = "  ".join(f"{s[2][case]:<9}" for s in splits)
    print(f"  {case[:60]:<60}  {cells}")
print()

# --- Every run with the same config hash -----------------------------------------

config = fixtures[0][1]["config_hash"]
print(f"every run with config {config} up to {LAST_DAY}")
print(f"  {'run id':<52} {'not unanimous':>14} {'P(1 sample differs)':>20}")
counts = []
for path in sorted(runs_dir(args.brief, SUITE).glob(f"*-{config}.json")):
    if path.name[:10] > LAST_DAY:
        continue
    run = load(path)
    flapping, p, _ = split(run)
    counts.append(flapping)
    mark = "  <- fixture" if any(path.name.startswith(f) for f in FIXTURES) else ""
    print(f"  {run_id(path):<52} {flapping:>11}/{len(run['results'])} {p:>19.1%}{mark}")
print(f"  runs: {len(counts)}, not unanimous from {min(counts)}/21 to {max(counts)}/21")
print()
print("P(1 sample differs) on the fixture runs: "
      + ", ".join(f"{rid[11:16].replace('-', ':')} {s[1]:.1%}" for rid, s in zip(FIXTURES, splits)))
