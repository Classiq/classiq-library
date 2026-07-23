"""Prose uses ASCII/LaTeX, not stray unicode (smart quotes, dashes, math italics)."""

from ._model import Notebook, Point

# Kept on purpose: references/author names and emoji are handled by the agent.
_ALLOWED = set("–—")  # (rendered separately) — placeholder for tuning


def detect(nb: Notebook) -> list[str]:
    return sorted({c for c in nb.prose if ord(c) > 0x7F})


POINT = Point(
    title="unicode",
    detail="agents/notebook-unicode-cleanup.md",
    description="Stray unicode (smart quotes, en/em dashes, math-italic letters) -> ASCII/LaTeX; "
    "names in references and emoji are preserved. (approximate)",
    static=False,
    detect=detect,
)
