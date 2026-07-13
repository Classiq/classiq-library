"""A references section heading reads "References" (plural), never "Reference"."""

import re

from ._model import Notebook, Point, src

_SINGULAR = re.compile(r"^(#{1,6}[ \t]+)([Rr])eference([ \t]*)$", re.MULTILINE)


def detect(nb: Notebook) -> list[str]:
    return [m.group(0).strip() for m in _SINGULAR.finditer(nb.prose)]


def fix(cells: list) -> bool:
    changed = False
    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue
        new = _SINGULAR.sub(r"\1\2eferences\3", src(cell))
        if new != src(cell):
            cell["source"] = new.splitlines(keepends=True)
            changed = True
    return changed


POINT = Point(
    title="references",
    detail="## Reference  ->  ## References",
    description="The references section heading is plural.",
    static=True,
    detect=detect,
    fix=fix,
    enforced=True,
)
