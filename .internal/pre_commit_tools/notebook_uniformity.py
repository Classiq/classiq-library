#!/usr/bin/env python3
"""Pre-commit hook: enforce the auto-fixable convention points.

Single source of truth: every convention lives in `.internal/conventions/points/`
as a `Point` (see `points/_model.py`). This hook applies the `fix()` of each point
marked `enforced`, then reports any enforced point that still fails (e.g. opens_h1,
which has no auto-fix). The points are reached through the `points` symlink to
`../conventions/points` — no sys.path juggling.

To add or change an enforced rule, edit its point file; nothing here changes.
"""

import importlib
from functools import partial
from pathlib import Path

from _common import PROJECT_ROOT, load_notebook, report, run_precommit, save_notebook
from points._model import Notebook

_POINTS_DIR = Path(__file__).resolve().parent / "points"


class Config:
    # if True, the hook does nothing (safety switch)
    IS_DISABLED: bool = False
    # if True, fix notebooks in place; if False, only report violations
    SHOULD_AUTO_FIX: bool = True


def enforced_points() -> list:
    points = []
    for module_path in sorted(_POINTS_DIR.glob("point_*.py")):
        point = importlib.import_module(f"points.{module_path.stem}").POINT
        if point.enforced:
            points.append(point)
    return points


def _is_documented(nb: Notebook, point) -> bool:
    return any(fragment in nb.rel for fragment, _reason in point.exceptions)


def check_notebook(notebook_path: str, points: list, auto_fix: bool) -> bool:
    abs_path = PROJECT_ROOT / notebook_path
    nb = load_notebook(str(abs_path))

    fixed = [p.title for p in points if p.fix and auto_fix and p.fix(nb.cells)]
    if fixed:
        save_notebook(str(abs_path), nb)

    model = Notebook.load(abs_path, PROJECT_ROOT)
    unfixed = [
        p.title for p in points if p.detect(model) and not _is_documented(model, p)
    ]

    for title in fixed:
        report(notebook_path, f"{title}: auto-fixed — please `git add`", fixed=True)
    for title in unfixed:
        report(notebook_path, f"{title}: needs a manual fix")
    return not (fixed or unfixed)


if __name__ == "__main__":
    if not Config.IS_DISABLED:
        points = enforced_points()
        run_precommit(
            partial(check_notebook, points=points, auto_fix=Config.SHOULD_AUTO_FIX)
        )
