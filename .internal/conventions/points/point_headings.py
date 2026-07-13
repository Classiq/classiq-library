"""Heading hierarchy stays shallow and well-nested (H2/H3; avoid H4+)."""

import re

from ._model import Notebook, Point


def detect(nb: Notebook) -> list[str]:
    return re.findall(r"(?m)^#{4,}[ \t]+\S.*", nb.prose)


POINT = Point(
    title="headings",
    detail="agents/notebook-heading-hierarchy.md",
    description="Sections nest cleanly under the H1; deep H4+ levels are flattened. (approximate)",
    static=False,
    detect=detect,
)
