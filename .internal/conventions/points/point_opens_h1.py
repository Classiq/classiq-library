"""A notebook opens with an H1 title (optionally after one logo/banner cell)."""

import re

from ._model import Notebook, Point, src

_H1 = re.compile(r"^\s*#[ \t]+\S")


def _is_h1(cell: dict) -> bool:
    return cell.get("cell_type") == "markdown" and bool(_H1.match(src(cell)))


def _is_logo(cell: dict) -> bool:
    if cell.get("cell_type") != "markdown" or "<img" not in src(cell):
        return False
    return not re.search(r"[A-Za-z0-9]", re.sub(r"<[^>]+>", "", src(cell)))


def detect(nb: Notebook) -> list[str]:
    cells = nb.cells
    ok = bool(cells) and (
        _is_h1(cells[0]) or (_is_logo(cells[0]) and len(cells) > 1 and _is_h1(cells[1]))
    )
    return [] if ok else ["no opening H1 title"]


POINT = Point(
    title="opens_h1",
    detail="first cell is '# Title' (a logo/banner cell may precede it)",
    description="A notebook opens with its H1 title. Not auto-fixable (a title can't be invented).",
    static=True,
    detect=detect,
    fix=None,
    enforced=True,
)
