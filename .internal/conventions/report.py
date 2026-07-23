#!/usr/bin/env python3
"""Notebook-convention status — one small file per point, collected here.

    python3 .internal/conventions/report.py                      # compact status table (default)
    python3 .internal/conventions/report.py --cards              # detailed per-point cards
    python3 .internal/conventions/report.py --full               # per-point summary + legend
    python3 .internal/conventions/report.py --files              # list every offender
    python3 .internal/conventions/report.py --rule math --list   # offender paths only

Every convention lives in its own `points/point_*.py` (see `points/_model.py`):
it carries a title, a before/after example, a description, a `detect()` and
either a static `fix()` or a pointer to its `agent`. This script just loads the
notebooks, runs each point's `detect()`, and renders the status.
"""

import argparse
import os
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import importlib

from points._model import Notebook, Point  # noqa: E402

MAIN = {"algorithms", "applications", "tutorials"}
GROUPS = ("main", "community", "other")

PREVIEW = 5  # offender paths shown per point in the card view
GOOD_PCT = 80  # >= this (but < 100) renders yellow; below, red; 100 is green

# presentation order, top to bottom; points not listed fall to the end (alphabetical)
ORDER = [
    # title & headings
    "opens_h1", "single_h1", "headings", "title_case",
    # prose & notation
    "math", "unicode", "references",
    # code & circuit
    "def_main", "synthesize_main", "qprog_var", "show",
    # parked — superseded by the execution-API refactor
    "execution_interface", "result_value", "result_var",
    # parked — decided against
    "intro_opener",
]  # fmt: skip
# `section_vocab` was intentionally removed (not parked): its detector flagged long /
# sentence-like headings, but most were good, specific titles (e.g. "The Elliptic Curve
# Discrete Logarithm Problem") that a fixed vocabulary would only flatten — a high
# false-positive rate and the same over-correction risk as title_case, but worse (it
# rewrites whole headings, not just casing). Kept this note so it isn't naively re-added.

# short tag -> the sentence `--full` expands it into
TAG_HELP = {
    "static": "detected by a script",
    "agent": "needs an agent's judgement to detect/fix",
    "enforced": "wired into the pre-commit hook",
    "check": "detect-only — no safe automatic fix",
    "auto-fix": "the hook fixes it automatically",
}
# a point's lifecycle status (other than "active") -> its (short, long) label,
# shown dimmed in place of the score
PARKED = {
    "outdated": (
        "old",
        "superseded by the execution-API refactor; kept for the record",
    ),
    "dropped": ("dropped", "decided not to pursue this convention"),
}
APPROX = "(approximate)"
APPROX_FULL = (
    "Detection is approximate — the conforming count is an estimate, not exact."
)


# --- notebooks & points ---------------------------------------------------


def load_points() -> list[Point]:
    mods = sorted((HERE / "points").glob("point_*.py"))
    points = [importlib.import_module(f"points.{m.stem}").POINT for m in mods]
    rank = {title: i for i, title in enumerate(ORDER)}
    return sorted(points, key=lambda p: (rank.get(p.title, len(ORDER)), p.title))


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


def _active(point: Point) -> bool:
    return point.status == "active"


# --- analysis -------------------------------------------------------------


@dataclass
class PointResult:
    point: Point
    offenders: list[Notebook]  # notebooks that violate the point (exceptions excluded)
    counts: dict[str, tuple[int, int]]  # group -> (conforming, total)

    @property
    def ok(self) -> int:
        return sum(ok for ok, _ in self.counts.values())

    @property
    def total(self) -> int:
        return sum(total for _, total in self.counts.values())

    @property
    def pct(self) -> int:
        # floor, never round up: 100% must mean truly complete, not 216/217
        return 100 * self.ok // self.total if self.total else 100

    @property
    def conforms(self) -> bool:
        return not self.offenders


def _offenders(point: Point, nbs: list[Notebook]) -> list[Notebook]:
    return [
        nb
        for nb in nbs
        if point.detect(nb) and not any(frag in nb.rel for frag, _ in point.exceptions)
    ]


def evaluate(point: Point, nbs: list[Notebook]) -> PointResult:
    offenders = _offenders(point, nbs)
    bad = {nb.rel for nb in offenders}
    counts = {}
    for g in GROUPS:
        group = [nb for nb in nbs if _group(nb.rel) == g]
        counts[g] = (sum(nb.rel not in bad for nb in group), len(group))
    return PointResult(point=point, offenders=offenders, counts=counts)


def _is_approx(point: Point) -> bool:
    return point.description.rstrip().endswith(APPROX)


# --- color ----------------------------------------------------------------


class Ansi:
    """Tiny ANSI colorizer; `paint` is a no-op unless `enabled` is set."""

    GREEN, YELLOW, RED, DIM, BOLD = "32", "33", "31", "2", "1"
    enabled = False

    @classmethod
    def paint(cls, text: str, code: str | None) -> str:
        return f"\033[{code}m{text}\033[0m" if cls.enabled and code else text


def _setup_color(choice: bool | None) -> None:
    """`choice` None means auto: color only a real terminal that allows it."""
    if choice is None:
        choice = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    Ansi.enabled = choice


def _pct_color(pct: int) -> str:
    return Ansi.GREEN if pct == 100 else Ansi.YELLOW if pct >= GOOD_PCT else Ansi.RED


# --- formatting helpers ---------------------------------------------------


def _glyph(r: PointResult) -> str:
    return "✓" if r.conforms else "→"


def _mark(r: PointResult) -> str:  # parked = neutral dot; else colored ✓/→ by percent
    if not _active(r.point):
        return Ansi.paint("·", Ansi.DIM)
    return Ansi.paint(_glyph(r), _pct_color(r.pct))


def _frac(counts: tuple[int, int]) -> str:
    return f"{counts[0]}/{counts[1]}"


def _tags(point: Point, full: bool) -> str:
    if not full:
        return " · ".join(point.tags())
    return " · ".join(f"{t} — {TAG_HELP[t]}" for t in point.tags())


def _status_label(point: Point, full: bool) -> str:
    short, long = PARKED[point.status]
    return long if full else short


def _description(point: Point, full: bool) -> str:
    text = point.description.rstrip()
    if full and text.endswith(APPROX):
        return f"{text[: -len(APPROX)].rstrip()} {APPROX_FULL}"
    return text


def _print_paths(offenders: list[Notebook], indent: str, cap: int | None) -> None:
    for nb in offenders[:cap] if cap else offenders:
        print(Ansi.paint(f"{indent}{nb.rel}", Ansi.DIM))
    if cap and len(offenders) > cap:
        print(Ansi.paint(f"{indent}… (+{len(offenders) - cap} more)", Ansi.DIM))


def _print_point_summary(results: list[PointResult]) -> None:
    width = max(len(r.point.title) for r in results)
    print(Ansi.paint("\n  what each point checks", Ansi.BOLD))
    for r in results:
        title = Ansi.paint(f"{r.point.title:{width}}", Ansi.BOLD)
        print(f"    {title}  {_description(r.point, full=False)}")


def _print_legend(results: list[PointResult]) -> None:
    used_tags = {t for r in results for t in r.point.tags()}
    parked = {r.point.status for r in results if not _active(r.point)}
    print(Ansi.paint("\n  legend", Ansi.BOLD))
    for tag, help_text in TAG_HELP.items():  # keep declaration order
        if tag in used_tags:
            print(Ansi.paint(f"    {tag:11} {help_text}", Ansi.DIM))
    for status, (short, long) in PARKED.items():
        if status in parked:
            print(Ansi.paint(f"    {short:11} {long}", Ansi.DIM))
    if any(_is_approx(r.point) for r in results):
        print(Ansi.paint(f"    {'approximate':11} {APPROX_FULL}", Ansi.DIM))


def _print_header(nbs: list[Notebook], points: list[Point]) -> None:
    g = Counter(_group(nb.rel) for nb in nbs)
    n_points = f"{len(points)} point" + ("s" if len(points) != 1 else "")
    print(
        Ansi.paint(
            f"NOTEBOOK CONVENTIONS — {len(nbs)} notebooks "
            f"(main {g['main']} · community {g['community']} · other {g['other']}) "
            f"· {n_points}",
            Ansi.BOLD,
        )
    )
    print(
        Ansi.paint(
            "  main = algorithms + applications + tutorials (the CI-tested core); "
            "community + functions are not",
            Ansi.DIM,
        )
    )


# --- the two human views (--list is a one-liner in main) ------------------


def render_cards(
    results: list[PointResult], full: bool, show_files: bool | None
) -> None:
    for r in results:
        p = r.point
        detail = p.detail if p.static else f"agent: {p.detail}"
        print(f"\n{_mark(r)} {Ansi.paint(p.title, Ansi.BOLD)}   [{_tags(p, full)}]")
        print(Ansi.paint(f"      {detail}", Ansi.DIM))
        print(f"      {_description(p, full)}")
        if not _active(p):  # parked: a dim status line, no score, no offenders
            print(Ansi.paint(f"      {_status_label(p, full)}", Ansi.DIM))
            continue
        split = " · ".join(f"{g} {ok}/{tot}" for g, (ok, tot) in r.counts.items())
        pct = Ansi.paint(f"{r.pct}%", _pct_color(r.pct))
        print(f"      {r.ok}/{r.total} ({pct})    {Ansi.paint(split, Ansi.DIM)}")
        if show_files is not False and r.offenders:  # False hides; None caps; True all
            _print_paths(r.offenders, " " * 9, cap=None if show_files else PREVIEW)


def _table_row(r: PointResult) -> tuple[tuple, list[str | None]]:
    p = r.point
    fracs = tuple(_frac(r.counts[g]) for g in GROUPS) + (_frac((r.ok, r.total)),)
    kind = " · ".join(p.tags())
    if not _active(p):  # a dim row; the score column carries the status label
        cells = ("·", p.title, *fracs, _status_label(p, full=False), kind)
        return cells, [Ansi.DIM] * len(cells)
    cells = (_glyph(r), p.title, *fracs, f"{r.pct}%", kind)
    colors: list[str | None] = [None] * len(cells)
    colors[0] = colors[6] = _pct_color(r.pct)  # the mark and the % column
    return cells, colors


def render_table(results: list[PointResult], show_files: bool | None) -> None:
    head = ("", "point", "main", "community", "other", "all", "%", "kind")
    built = [_table_row(r) for r in results]
    rows = [cells for cells, _ in built]
    widths = [max(map(len, col)) for col in zip(head, *rows)]

    print()
    _emit_row(head, widths, [Ansi.BOLD] * len(head))
    print("  " + Ansi.paint("─" * (sum(widths) + 2 * (len(widths) - 1)), Ansi.DIM))
    for cells, colors in built:
        _emit_row(cells, widths, colors)

    if show_files:  # --files: the full offender list per active point, below the table
        for r in results:
            if _active(r.point) and r.offenders:
                print(f"\n{_mark(r)} {Ansi.paint(r.point.title, Ansi.BOLD)}")
                _print_paths(r.offenders, " " * 4, cap=None)


def _emit_row(cells: tuple, widths: list[int], colors: list[str | None]) -> None:
    parts = [Ansi.paint(c.ljust(w), col) for c, w, col in zip(cells, widths, colors)]
    print("  " + "  ".join(parts).rstrip())


# --- entry point ----------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--cards", action="store_true", help="detailed per-point cards (default: table)"
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="spell it out: a per-point summary plus a legend for tags/statuses",
    )
    ap.add_argument(
        "--files",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="list offending notebooks (default: a short preview in the card view)",
    )
    ap.add_argument(
        "--color",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="colorize output (default: auto when writing to a terminal)",
    )
    ap.add_argument(
        "--rule", metavar="TITLE", help="run only this point (default: all)"
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="print only the offending file paths (to pipe into a fixer)",
    )
    args = ap.parse_args()

    _setup_color(args.color)
    nbs, points = load_notebooks(), load_points()
    if args.rule:
        chosen = [p for p in points if p.title == args.rule]
        if not chosen:
            sys.exit(
                f"unknown rule '{args.rule}'. "
                f"available: {', '.join(sorted(p.title for p in points))}"
            )
        points = chosen

    results = [evaluate(p, nbs) for p in points]

    if args.list:  # bare paths, for `... --list | xargs fixer`; parked points skipped
        src = results if args.rule else [r for r in results if _active(r.point)]
        print("\n".join(sorted({nb.rel for r in src for nb in r.offenders})))
        return

    _print_header(nbs, points)
    if args.cards:
        render_cards(results, full=args.full, show_files=args.files)
    else:
        render_table(results, show_files=args.files)
    if args.full:
        if not args.cards:  # cards already print each description inline
            _print_point_summary(results)
        _print_legend(results)


if __name__ == "__main__":
    main()
