#!/usr/bin/env python3
"""One-stop uniformity report for the classiq-library notebooks.

Run from anywhere inside the repo:

    python3 .internal/notebook_uniformity_report.py

Design
------
Every convention we care about is one `@check`-registered function. Each block is
self-contained: it defines the rule (a `deviates` predicate or a `bucket`), its
documented exceptions, and prints its own report. To drop a point, delete its
function — nothing else references it. To add one, write a function and decorate
it with `@check`.

Exceptions
----------
Known, intentional deviations are listed per-check as `(path_fragment, reason)`
pairs. `report_coverage` subtracts them, so a check that flags 2 notebooks which
are both documented reads as fully covered (e.g. "158/160" + 2 exceptions == 100%).

Two kinds of checks
-------------------
- `report_coverage`  : binary convention (conforms / deviates) -> coverage + to-fix list.
- `report_spread`    : categorical breakdown (no single right answer) -> histogram.
"""

import json
import re
import subprocess
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

MAIN_DIRS = {
    "algorithms",
    "applications",
    "tutorials",
}  # the CI-tested, maintained core
COMMUNITY_DIR = "community"  # not CI-tested; drifts the most
# everything else (benchmarking, functions) falls into the "other" group

# (path fragment, why this deviation is intentional) — a documented, accepted exception
AcceptedDeviation = tuple[str, str]


class Config:
    # max offender paths printed per check (0 == unlimited)
    MAX_LISTED: int = 15
    # print the main/community/other split, not only the ALL total
    SHOW_GROUP_SPLIT: bool = True


# --------------------------------------------------------------------------- #
#  Notebook model + loading
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Notebook:
    rel: str  # path relative to repo root, e.g. "algorithms/shor/shor.ipynb"
    group: str  # "main" | "community" | "other"
    code: str  # all code cells, joined
    markdown: str  # all markdown cells, joined
    first_cell_type: str  # "markdown" | "code" | ""
    first_cell_source: str

    @classmethod
    def from_path(cls, path: Path, root: Path) -> "Notebook":
        cells = json.loads(path.read_text()).get("cells", [])
        first = cells[0] if cells else {}
        rel = path.relative_to(root)
        return cls(
            rel=str(rel),
            group=_group(rel),
            code=_join(cells, "code"),
            markdown=_join(cells, "markdown"),
            first_cell_type=first.get("cell_type", ""),
            first_cell_source="".join(first.get("source", [])),
        )

    @property
    def h1_titles(self) -> list[str]:
        return re.findall(r"(?m)^#\s+(.*\S)", self.markdown)

    @property
    def opens_with_h1_title(self) -> bool:
        return bool(re.match(r"^#\s+\S", self.first_cell_source))


def _join(cells: list[dict], cell_type: str) -> str:
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in cells
        if cell.get("cell_type") == cell_type
    )


def _group(rel: Path) -> str:
    top = rel.parts[0]
    if top in MAIN_DIRS:
        return "main"
    if top == COMMUNITY_DIR:
        return "community"
    return "other"


@lru_cache
def load_notebooks() -> tuple[Notebook, ...]:
    root = Path(subprocess.getoutput("git rev-parse --show-toplevel"))
    paths = sorted(
        p for p in root.rglob("*.ipynb") if ".ipynb_checkpoints" not in p.parts
    )
    return tuple(Notebook.from_path(p, root) for p in paths)


# --------------------------------------------------------------------------- #
#  Shared text helpers (the "intro stuff")
# --------------------------------------------------------------------------- #
def _first_prose(nb: Notebook) -> str:
    """First real sentence of prose — skips headings, html, images, lists, math."""
    for line in nb.markdown.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(
            ("#", "<", "!", "[", ">", "-", "*", "$", "|", "=")
        ):
            return stripped
    return ""


def _title_casing(title: str) -> str | None:
    words = re.findall(r"[A-Za-z]+", title)
    if len(words) < 2:
        return None  # too short to judge
    capitalized = sum(1 for word in words if word[0].isupper())
    if capitalized == len(words):
        return "Title Case"
    if capitalized >= len(words) * 0.6:
        return "Mixed"
    return "Sentence case"


def _normalized_heading(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", "", text.lower())).strip()


# --------------------------------------------------------------------------- #
#  Reporting
# --------------------------------------------------------------------------- #
def _split(nbs: Sequence[Notebook]) -> dict[str, list[Notebook]]:
    groups: dict[str, list[Notebook]] = {"main": [], "community": [], "other": []}
    for nb in nbs:
        groups[nb.group].append(nb)
    return groups


def _is_documented(nb: Notebook, exceptions: Sequence[AcceptedDeviation]) -> bool:
    return any(fragment in nb.rel for fragment, _reason in exceptions)


def report_coverage(
    point: str,
    title: str,
    nbs: Sequence[Notebook],
    *,
    deviates: Callable[[Notebook], bool],
    exceptions: Sequence[AcceptedDeviation] = (),
    details: Sequence[str] = (),
) -> None:
    """Binary convention check. `deviates(nb)` is True when nb breaks the rule."""
    print(f"\n[{point}] {title}")
    for line in details:
        print(f"       {line}")

    groups = _split(nbs)
    if Config.SHOW_GROUP_SPLIT:
        split = "   ".join(
            f"{name} {sum(1 for nb in group if not deviates(nb))}/{len(group)}"
            for name, group in groups.items()
        )
        print(f"       conforming:  {split}")

    offenders = sorted((nb for nb in nbs if deviates(nb)), key=lambda nb: nb.rel)
    todo = [nb for nb in offenders if not _is_documented(nb, exceptions)]
    conforming = len(nbs) - len(offenders)
    documented = len(offenders) - len(todo)
    suffix = (
        f"   (+{documented} documented -> {conforming + documented}/{len(nbs)} effective)"
        if exceptions
        else ""
    )
    print(f"       ALL: {conforming}/{len(nbs)} conforming{suffix}")

    if not todo:
        print("       OK fully covered")
        return
    print(f"       -> to fix: {len(todo)}")
    shown = todo if Config.MAX_LISTED == 0 else todo[: Config.MAX_LISTED]
    for nb in shown:
        print(f"           {nb.rel}")
    if len(shown) < len(todo):
        print(f"           ... (+{len(todo) - len(shown)} more)")


def report_spread(
    point: str,
    title: str,
    nbs: Sequence[Notebook],
    *,
    bucket: Callable[[Notebook], str | None],
    top: int | None = None,
) -> None:
    """Categorical check. `bucket(nb)` returns a label, or None to skip the notebook."""
    print(f"\n[{point}] {title}")
    counts = Counter(label for nb in nbs if (label := bucket(nb)) is not None)
    for label, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]:
        print(f"       {n:4d}  {label}")


# --------------------------------------------------------------------------- #
#  Check registry — each point below is one self-contained, deletable block
# --------------------------------------------------------------------------- #
Check = Callable[[Sequence[Notebook]], None]
_CHECKS: list[Check] = []


def check(fn: Check) -> Check:
    _CHECKS.append(fn)
    return fn


@check
def point_A_show_function(nbs: Sequence[Notebook]) -> None:
    # Present a circuit with `show(qprog)`, never the `qprog.show()` method form.
    exceptions: list[AcceptedDeviation] = []

    def deviates(nb: Notebook) -> bool:
        return bool(
            re.search(r"\b(?:qprog\w*|quantum_program\w*|qp)\.show\(\)", nb.code)
        )

    report_coverage(
        "A",
        "Circuit shown via show(qprog), not `.show()` method",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


@check
def point_B_opens_with_title(nbs: Sequence[Notebook]) -> None:
    # Every notebook opens with a single H1 title cell (covers original points B & 11).
    exceptions: list[AcceptedDeviation] = []

    def deviates(nb: Notebook) -> bool:
        return not nb.opens_with_h1_title

    report_coverage(
        "B/11",
        "Opens with an H1 title (no code-first / non-H1 opener)",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


@check
def point_1_synthesis_flow(nbs: Sequence[Notebook]) -> None:
    # Modern flow is `qprog = synthesize(main)`; avoid the old `create_model(...)` step.
    exceptions: list[AcceptedDeviation] = [
        # ("path/fragment.ipynb", "keeps the model object on purpose because ..."),
    ]

    def deviates(nb: Notebook) -> bool:
        return "create_model(" in nb.code

    report_coverage(
        "1",
        "Synthesis uses synthesize(main), not create_model()+synthesize()",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


@check
def point_2_result_variable(nbs: Sequence[Notebook]) -> None:
    # The execution result is named `result` (or `result_<suffix>` when several);
    # suffix only — `result_1` is fine, but `res`, `job`, or `stage_result` are not.
    exceptions: list[AcceptedDeviation] = []

    def _result_vars(code: str) -> list[str]:
        return re.findall(r"(\w+)\s*=\s*(?:execute\(|\w+\.result(?:_value)?\()", code)

    def deviates(nb: Notebook) -> bool:
        return any(
            not re.fullmatch(r"result(_\w+)?", name) for name in _result_vars(nb.code)
        )

    report_coverage(
        "2",
        "Execution result variable named result / result_<suffix>",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


@check
def point_2b_qprog_variable(nbs: Sequence[Notebook]) -> None:
    # The synthesized circuit is named `qprog` (or `qprog_<suffix>` when several);
    # never `quantum_program`, `qp`, or a prefixed form like `sp_qprog`.
    exceptions: list[AcceptedDeviation] = []

    def _qprog_vars(code: str) -> list[str]:
        return re.findall(r"(\w+)\s*=\s*synthesize\(", code)

    def deviates(nb: Notebook) -> bool:
        return any(
            not re.fullmatch(r"qprog(_\w+)?", name) for name in _qprog_vars(nb.code)
        )

    report_coverage(
        "2b",
        "Synthesis output variable named qprog / qprog_<suffix>",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


@check
def point_3_result_value(nbs: Sequence[Notebook]) -> None:
    # Parse results with `.result_value()`, not the old `.result()[0].value`.
    exceptions: list[AcceptedDeviation] = []

    def deviates(nb: Notebook) -> bool:
        return bool(re.search(r"\.result\(\)\s*\[[^\]]*\]\s*\.value", nb.code))

    report_coverage(
        "3",
        "Results parsed via .result_value(), not .result()[0].value",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


@check
def point_4_title_casing(nbs: Sequence[Notebook]) -> None:
    # Distribution only — fixing needs context (QAOA, Grover...), handled by an agent.
    def bucket(nb: Notebook) -> str | None:
        return _title_casing(nb.h1_titles[0]) if nb.h1_titles else None

    report_spread(
        "4", "Title casing  (distribution -> agent unifies)", nbs, bucket=bucket
    )


@check
def point_5_references_plural(nbs: Sequence[Notebook]) -> None:
    # A references heading must be plural: "References", never "Reference".
    exceptions: list[AcceptedDeviation] = []

    def deviates(nb: Notebook) -> bool:
        return bool(re.search(r"(?mi)^#{1,4}\s+reference\s*$", nb.markdown))

    report_coverage(
        "5",
        'References heading is plural ("References")',
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


@check
def point_6_single_h1(nbs: Sequence[Notebook]) -> None:
    # Exactly one H1 per notebook (the title); sections are H2+.
    exceptions: list[AcceptedDeviation] = []

    def deviates(nb: Notebook) -> bool:
        return len(nb.h1_titles) != 1

    report_coverage(
        "6",
        "Exactly one H1 (the title); sections use H2+",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


@check
def point_7_deep_nesting(nbs: Sequence[Notebook]) -> None:
    # Investigate only — no auto-fix. Show a few with and without H4+ to eyeball.
    def uses_h4plus(nb: Notebook) -> bool:
        return bool(re.search(r"(?m)^#{4,6}\s+\S", nb.markdown))

    with_deep = sorted(nb.rel for nb in nbs if uses_h4plus(nb))
    without = sorted(nb.rel for nb in nbs if not uses_h4plus(nb) and nb.group == "main")
    print(f"\n[ 7] Deep H4+ nesting  (investigate only — no auto-fix)")
    print(f"       uses H4+: {len(with_deep)}/{len(nbs)}")
    print("       examples WITH H4+:")
    for rel in with_deep[:5]:
        print(f"           {rel}")
    print("       examples WITHOUT (main):")
    for rel in without[:5]:
        print(f"           {rel}")


@check
def point_8_intro_opener(nbs: Sequence[Notebook]) -> None:
    # Distribution -> pick the most common phrasing, then an agent rewrites the rest.
    def bucket(nb: Notebook) -> str | None:
        prose = _first_prose(nb)
        return " ".join(prose.lower().split()[:3]).rstrip(".,:") if prose else None

    report_spread(
        "8",
        "Intro opener phrasing  (distribution -> agent unifies)",
        nbs,
        bucket=bucket,
        top=20,
    )


@check
def point_9_section_vocabulary(nbs: Sequence[Notebook]) -> None:
    # Distribution over H2-H4 names — surfaces synonym/singular-plural drift for the agent.
    print("\n[ 9] Section-heading vocabulary  (distribution -> agent unifies)")
    counts: Counter[str] = Counter()
    for nb in nbs:
        for _level, text in re.findall(r"(?m)^(#{2,4})\s+(.*)$", nb.markdown):
            if name := _normalized_heading(text):
                counts[name] += 1
    for name, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:25]:
        print(f"       {n:4d}  {name}")


@check
def point_12_math_delimiters(nbs: Sequence[Notebook]) -> None:
    # Display equations use $$...$$ . Inline $...$ and inner envs (pmatrix, cases,
    # aligned, align) are fine; only \[...\] and bare \begin{equation} are converted.
    exceptions: list[AcceptedDeviation] = [
        # ("path/fragment.ipynb", "renders only under \\[ for reason ..."),
    ]
    styles: dict[str, Callable[[Notebook], bool]] = {
        "$$...$$": lambda nb: "$$" in nb.markdown,
        "\\[...\\]": lambda nb: "\\[" in nb.markdown,
        "\\begin{equation}": lambda nb: bool(
            re.search(r"\\begin\{equation\*?\}", nb.markdown)
        ),
        "\\begin{align}": lambda nb: bool(
            re.search(r"\\begin\{align\*?\}", nb.markdown)
        ),
    }
    groups = _split(nbs)
    details = [
        f"uses {label:18s} "
        + "  ".join(
            f"{name} {sum(1 for nb in g if pred(nb))}" for name, g in groups.items()
        )
        for label, pred in styles.items()
    ]

    def deviates(nb: Notebook) -> bool:
        return styles["\\[...\\]"](nb) or styles["\\begin{equation}"](nb)

    report_coverage(
        "12",
        "Display math uses $$...$$ (not \\[ or \\begin{equation})",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
        details=details,
    )


@check
def point_15_has_main(nbs: Sequence[Notebook]) -> None:
    # A classiq notebook defines `@qfunc def main(...)`. Cross-framework comparison
    # notebooks legitimately do not — those are documented exceptions.
    exceptions: list[AcceptedDeviation] = [
        (
            "classiq_paper/qsvt/qiskit_qsvt",
            "Qiskit comparison notebook, no classiq main",
        ),
        ("classiq_paper/qsvt/tket_qsvt_example", "t|ket> comparison notebook"),
        (
            "classiq_paper/qsvt/pennylane_cat_qsvt_example",
            "PennyLane comparison notebook",
        ),
        (
            "classiq_paper/quantum_walk/qiskit_discrete_quantum_walk",
            "Qiskit comparison notebook",
        ),
        (
            "classiq_paper/quantum_walk/tket_discrete_quantum_walk",
            "t|ket> comparison notebook",
        ),
        (
            "classiq_paper/quantum_walk/pennylane_catalyst_discrete_quantum_walk",
            "PennyLane comparison notebook",
        ),
        ("vlasov_ampere/vlasov_ampere_qiskit", "Qiskit comparison notebook"),
    ]

    def deviates(nb: Notebook) -> bool:
        return not re.search(r"def\s+main\s*\(", nb.code)

    report_coverage(
        "15",
        "Defines @qfunc def main(...) (comparison nbs excepted)",
        nbs,
        deviates=deviates,
        exceptions=exceptions,
    )


# --------------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    nbs = load_notebooks()
    groups = _split(nbs)
    print("=" * 78)
    print("NOTEBOOK UNIFORMITY REPORT")
    print(
        f"  population: {len(nbs)} notebooks "
        f"(main {len(groups['main'])}, community {len(groups['community'])}, other {len(groups['other'])})"
    )
    print(
        "  main = algorithms+applications+tutorials (CI-tested) | "
        "other = benchmarking+functions | community + functions are NOT CI-tested"
    )
    print("=" * 78)
    for run_check in _CHECKS:
        run_check(nbs)


if __name__ == "__main__":
    main()
