"""Parse an execution result with .result_value(), not .result()[0].value."""

import re

from ._model import Notebook, Point, src

_OLD = re.compile(r"\.result\(\)\s*\[\s*0\s*\]\s*\.value")


def detect(nb: Notebook) -> list[str]:
    return _OLD.findall(nb.code)


def fix(cells: list) -> bool:
    changed = False
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        new = _OLD.sub(".result_value()", src(cell))
        if new != src(cell):
            cell["source"] = new.splitlines(keepends=True)
            changed = True
    return changed


POINT = Point(
    title="result_value",
    detail="result()[0].value  ->  result_value()",
    description="Read the parsed value with .result_value(), not .result()[0].value.",
    static=True,
    detect=detect,
    fix=fix,
    enforced=True,
)
