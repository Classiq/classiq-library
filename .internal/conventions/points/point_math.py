"""Display math uses $$...$$, not \\[...\\] or \\begin{equation}/{align}."""

import re

from ._model import Notebook, Point

_OLD_DISPLAY = re.compile(r"\\\[|\\begin\{equation\}|\\begin\{align\}")


def detect(nb: Notebook) -> list[str]:
    return _OLD_DISPLAY.findall(nb.prose)


POINT = Point(
    title="math",
    detail="agents/notebook-math-notation.md",
    description="Display math in $$...$$; inline in $...$; unicode math symbols as LaTeX.",
    static=False,
    detect=detect,
)
