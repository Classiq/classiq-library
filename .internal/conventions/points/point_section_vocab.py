"""Section headings use a small shared vocabulary, not ad-hoc sentences."""

import re

from ._model import Notebook, Point


def detect(nb: Notebook) -> list[str]:
    # heuristic: a section label is short; full sentences / trailing punctuation
    # are the ad-hoc ones an agent would fold into the shared vocabulary.
    headings = re.findall(r"(?m)^#{2,3}[ \t]+(\S.*\S)", nb.prose)
    return [h for h in headings if len(h.split()) > 6 or h.endswith((".", "!", "?"))]


POINT = Point(
    title="section_vocab",
    detail="agents/notebook-section-vocab.md (to write)",
    description="Section headings drawn from a shared vocabulary (Introduction, Background, "
    "References, ...). (approximate; target TBD)",
    static=False,
    detect=detect,
)
