"""Section headings read in Title Case (proper nouns / acronyms preserved)."""

import re

from ._model import Notebook, Point


def _is_sentence_case(title: str) -> bool:
    words = re.findall(r"[A-Za-z]+", title)
    if len(words) < 2:
        return False
    capitalized = sum(1 for w in words if w[0].isupper())
    return capitalized < len(words) * 0.6  # mostly-lowercase -> sentence case


def detect(nb: Notebook) -> list[str]:
    headings = re.findall(r"(?m)^#+[ \t]+(\S.*\S)", nb.prose)
    return [h for h in headings if _is_sentence_case(h)]


POINT = Point(
    title="title_case",
    detail="agents/notebook-title-case.md",
    description="Headings use Title Case; acronyms (QAOA, HHL) and math stay intact. (approximate)",
    static=False,
    detect=detect,
)
