"""The synthesized circuit is named qprog (or qprog_<suffix> when several)."""

import re

from ._model import Notebook, Point

_ASSIGN = re.compile(r"(?<![\w.])(\w+)\s*=\s*synthesize\(")


def detect(nb: Notebook) -> list[str]:
    return sorted(
        {v for v in _ASSIGN.findall(nb.code) if not re.fullmatch(r"qprog(_\w+)?", v)}
    )


POINT = Point(
    title="qprog_var",
    detail="agents/notebook-variable-names.md",
    description="synthesize(...) output is named qprog / qprog_<suffix>, never a prefixed form.",
    static=False,
    detect=detect,
)
