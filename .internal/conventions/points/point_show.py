"""Present a circuit with show(qprog), never the qprog.show() method form."""

import re

from ._model import Notebook, Point, src

_METHOD = re.compile(r"\b(qprog\w*|quantum_program\w*|qp)\.show\(\)")


def detect(nb: Notebook) -> list[str]:
    return [m.group(0) for m in _METHOD.finditer(nb.code)]


def fix(cells: list) -> bool:
    changed = False
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        new = _METHOD.sub(r"show(\1)", src(cell))
        if new != src(cell):
            cell["source"] = new.splitlines(keepends=True)
            changed = True
    return changed


POINT = Point(
    title="show",
    detail="qprog.show()  ->  show(qprog)",
    description="Present a circuit with the show(qprog) function, not the .show() method.",
    static=True,
    detect=detect,
    fix=fix,
    enforced=True,
)
