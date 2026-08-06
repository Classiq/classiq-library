"""Prose uses ASCII/LaTeX, not stray unicode (smart quotes, dashes, math italics)."""

from functools import lru_cache
from pathlib import Path

from ._model import Notebook, Point

_WHITELIST_PATH = Path(__file__).parent.parent / "unicode_allowed_names.txt"


@lru_cache(maxsize=1)
def _load_allowed_names() -> frozenset[str]:
    if not _WHITELIST_PATH.exists():
        return frozenset()
    names = []
    for line in _WHITELIST_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.append(line)
    return frozenset(names)


def _line_has_violation(line: str, allowed_names: frozenset[str]) -> list[str]:
    if not any(ord(c) > 0x7F for c in line):
        return []
    cleaned = line
    for name in allowed_names:
        cleaned = cleaned.replace(name, "")
    return [c for c in cleaned if ord(c) > 0x7F]


def detect(nb: Notebook) -> list[str]:
    allowed = _load_allowed_names()
    violations = []
    for line in nb.prose.splitlines():
        violations.extend(_line_has_violation(line, allowed))
    return sorted(set(violations))


POINT = Point(
    title="unicode",
    detail="agents/notebook-unicode-cleanup.md",
    description="Stray unicode (smart quotes, en/em dashes, math-italic letters) -> ASCII/LaTeX; "
    "whitelisted names (Gilyén, Schrödinger, etc.) are preserved.",
    static=False,
    detect=detect,
)
