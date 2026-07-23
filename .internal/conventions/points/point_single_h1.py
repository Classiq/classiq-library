"""Exactly one H1 (the title); later H1 headings are demoted to H2."""

import re

from ._model import Notebook, Point, src, strip_fences

_H1 = re.compile(r"^#[ \t]+\S")


def detect(nb: Notebook) -> list[str]:
    h1s = re.findall(r"(?m)^#[ \t]+(\S.*)", nb.prose)
    return h1s[1:]  # every H1 beyond the first is an offender


def fix(cells: list) -> bool:
    seen, changed = False, False
    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue
        lines, in_fence, touched = src(cell).split("\n"), False, False
        for i, line in enumerate(lines):
            if re.match(r"^\s*```", line):
                in_fence = not in_fence
            elif not in_fence and _H1.match(line):
                if seen:
                    lines[i], touched = "#" + line, True
                else:
                    seen = True
        if touched:
            cell["source"] = "\n".join(lines).splitlines(keepends=True)
            changed = True
    return changed


POINT = Point(
    title="single_h1",
    detail="two '# ' headings  ->  one '# ' title + '## ' sections",
    description="A notebook has exactly one H1 (its title); deeper sections use H2+.",
    static=True,
    detect=detect,
    fix=fix,
    enforced=True,  # wired into the pre-commit hook via PR #1642
)
