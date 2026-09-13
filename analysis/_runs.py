"""What the four scripts share: where the two repos are, and how to read a run.

Everything here opens files for reading and nothing else. The run files are
digline's own JSON (schema 10); the few fields read are named where they are
read, so a schema change breaks loudly rather than quietly.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The site repo, brief and scout are checked out side by side.
DEFAULT_ROOT = HERE.parent.parent


def repo_args(description: str, *names: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    for name in names:
        parser.add_argument(
            f"--{name}",
            type=Path,
            default=DEFAULT_ROOT / name,
            help=f"checkout of {name} (default: %(default)s)",
        )
    return parser.parse_args()


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def runs_dir(repo: Path, suite: str) -> Path:
    return repo / ".digline" / "alessandro" / "runs" / suite


def run_path(repo: Path, suite: str, run_id: str) -> Path:
    """The run file whose name starts with `run_id`, which must be exactly one."""
    matches = sorted(runs_dir(repo, suite).glob(f"{run_id}*.json"))
    if len(matches) != 1:
        raise SystemExit(f"{run_id}: expected one run file, found {len(matches)}")
    return matches[0]


def run_id(path: Path) -> str:
    return path.stem


def verdict(result: dict, assertion: str) -> dict:
    (found,) = [v for v in result["verdicts"] if v["assertion"] == assertion]
    return found


def aggregate(run: dict, assertion: str) -> dict:
    (found,) = [a for a in run["aggregate"] if a["assertion"] == assertion]
    return found


def fraction(reason: str) -> str:
    """'precision 0.600000 = 9/15 (21 counted, ...)' -> '9/15'."""
    return reason.split(" = ", 1)[1].split(" ", 1)[0]


def votes(v: dict) -> str:
    """The five samples of a binary assertion as a string, 1 = passed."""
    return "".join("1" if s >= 0.5 else "0" for s in v["samples"])


def ratio(num: int, den: int) -> str:
    return f"{num}/{den} = {num / den:.2f}" if den else f"{num}/0"
