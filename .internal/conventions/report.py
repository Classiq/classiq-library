#!/usr/bin/env python3
"""Notebook-convention status — one small file per point, collected here.

    python3 .internal/conventions/report.py            # long view (default)
    python3 .internal/conventions/report.py --short     # one line per point

Every convention lives in its own `points/point_*.py` (see `points/_model.py`):
it carries a title, a before/after example, a description, a `detect()` and
either a static `fix()` or a pointer to its `agent`. This script just loads the
notebooks, runs each point's `detect()`, and renders the status.
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import importlib

from points._model import Notebook, Point  # noqa: E402

MAIN = {"algorithms", "applications", "tutorials"}


def load_points() -> list[Point]:
    mods = sorted((HERE / "points").glob("point_*.py"))
    return [importlib.import_module(f"points.{m.stem}").POINT for m in mods]


def load_notebooks() -> list[Notebook]:
    root = Path(subprocess.getoutput("git rev-parse --show-toplevel"))
    return [
        Notebook.load(p, root)
        for p in sorted(root.rglob("*.ipynb"))
        if ".ipynb_checkpoints" not in p.parts
    ]


def _group(rel: str) -> str:
    top = rel.split("/")[0]
    return "main" if top in MAIN else ("community" if top == "community" else "other")


def _offenders(point: Point, nbs: list[Notebook]) -> list[Notebook]:
    return [
        nb
        for nb in nbs
        if point.detect(nb) and not any(frag in nb.rel for frag, _ in point.exceptions)
    ]


def _split(nbs: list[Notebook], offenders: list[Notebook]) -> str:
    bad = {nb.rel for nb in offenders}
    parts = []
    for g in ("main", "community", "other"):
        grp = [nb for nb in nbs if _group(nb.rel) == g]
        ok = sum(1 for nb in grp if nb.rel not in bad)
        parts.append(f"{g} {ok}/{len(grp)}")
    return "   ".join(parts)


def render(point: Point, nbs: list[Notebook], short: bool) -> None:
    offenders = _offenders(point, nbs)
    ok, total = len(nbs) - len(offenders), len(nbs)
    tick = "OK " if not offenders else "-> "
    tags = (["enforced"] if point.enforced else []) + [point.solution()]
    if short:
        print(f"  {tick}{point.key:18} {ok:>3}/{total}   [{' · '.join(tags)}]")
        return
    print(f"\n{tick}{point.key}   [{' · '.join(tags)}]")
    print(f"      {point.example}")
    print(f"      {point.description}")
    print(f"      {ok}/{total} conforming    ({_split(nbs, offenders)})")
    for nb in offenders[:5]:
        print(f"         {nb.rel}")
    if len(offenders) > 5:
        print(f"         ... (+{len(offenders) - 5} more)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--short", action="store_true", help="one line per point")
    short = ap.parse_args().short
    nbs, points = load_notebooks(), load_points()
    print(f"NOTEBOOK CONVENTIONS  —  {len(nbs)} notebooks, {len(points)} points")
    for point in points:
        render(point, nbs, short)


if __name__ == "__main__":
    main()
