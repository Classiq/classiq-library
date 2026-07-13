"""The two shared types every convention point is built from.

A `Point` is one convention (e.g. "result_value"). It carries its own docs and
its own logic, so the whole rule lives in a single small file:

    detect(nb) -> list[str]   the offending snippets in a notebook ([] == conforms)
    fix(cells) -> bool        edit the raw cells in place; True if it changed anything
                              (None when the convention needs human/agent judgement)
    agent                     path to the agent mission doc, for judgement-heavy points

The collector (`report.py`) uses `detect`; the pre-commit hook uses `fix`.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass(frozen=True)
class Notebook:
    rel: str  # path relative to repo root
    code: str  # all code cells, joined
    prose: str  # markdown cells, ``` fences stripped per cell, joined
    cells: tuple  # raw cell dicts, for structural checks

    @classmethod
    def load(cls, path: Path, root: Path) -> "Notebook":
        cells = json.loads(path.read_text()).get("cells", [])
        md = [src(c) for c in cells if c.get("cell_type") == "markdown"]
        code = [src(c) for c in cells if c.get("cell_type") == "code"]
        return cls(
            rel=str(path.relative_to(root)),
            code="\n".join(code),
            prose="\n".join(strip_fences(m) for m in md),
            cells=tuple(cells),
        )


def src(cell: dict) -> str:
    return "".join(cell.get("source", []))


def strip_fences(markdown: str) -> str:
    """Drop ``` fenced code blocks so their `#` lines aren't read as headings."""
    out, in_fence = [], False
    for line in markdown.splitlines():
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
        elif not in_fence:
            out.append(line)
    return "\n".join(out)


@dataclass
class Point:
    key: str  # short id, e.g. "result_value"
    example: str  # short before/after, e.g. "result[0].value -> result_value"
    description: str  # one or two plain sentences
    detect: Callable[[Notebook], list[str]]  # offenders; [] means it conforms
    fix: Optional[Callable[[list], bool]] = None  # static in-place fix, or None
    agent: Optional[str] = None  # agent mission doc (relative to conventions/)
    enforced: bool = False  # wired into the pre-commit hook?
    exceptions: tuple = field(default_factory=tuple)  # (path_fragment, reason)

    def solution(self) -> str:
        if self.fix:
            return "auto-fix (pre-commit)" if self.enforced else "static fix"
        if self.agent:
            return f"agent: {self.agent}"
        return "manual"
