"""Section headings read in Title Case (proper nouns / acronyms preserved)."""

import re
from pathlib import Path

from ._model import Notebook, Point

# Minor words that can be lowercase (unless first/last word)
_MINOR_WORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "and",
        "but",
        "or",
        "for",
        "nor",
        "on",
        "at",
        "to",
        "by",
        "of",
        "in",
        "with",
        "into",
        "via",
        "as",
        "from",
        "vs",
        "per",
        "yet",
        "so",
        # Ordinal suffixes — "2nd" becomes "nd" after digit stripping
        "st",
        "nd",
        "rd",
        "th",
    ]
)

# Proper names with unconventional casing, loaded from whitelist file (lazy load)
_PROPER_NAMES_FILE = Path(__file__).parent.parent / "title_case_proper_names.txt"
_PROPER_NAMES: frozenset | None = None


def _get_proper_names() -> frozenset:
    global _PROPER_NAMES
    if _PROPER_NAMES is None:
        if _PROPER_NAMES_FILE.exists():
            _PROPER_NAMES = frozenset(
                line.strip()
                for line in _PROPER_NAMES_FILE.read_text().splitlines()
                if line.strip() and not line.startswith("#")
            )
        else:
            _PROPER_NAMES = frozenset()
    return _PROPER_NAMES


def _is_sentence_case(title: str) -> bool:
    # Strip LaTeX display math
    clean = re.sub(r"\$\$[^$]+\$\$", "", title)
    # Strip LaTeX inline math
    clean = re.sub(r"\$[^$]+\$", "", clean)
    # Strip code spans
    clean = re.sub(r"`[^`]+`", "", clean)
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", "", clean)
    # Strip markdown link URLs, keep link text
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)

    # Split on whitespace, keep tokens that start with a letter, strip trailing punctuation
    tokens = []
    for t in clean.split():
        if t and t[0].isalpha():
            # Strip trailing non-alpha chars (punctuation)
            while t and not t[-1].isalpha():
                t = t[:-1]
            if t:
                tokens.append(t)
    if len(tokens) < 2:
        return False

    # Filter out minor words, single letters (math variables), and proper names with unconventional casing
    proper_names = _get_proper_names()
    principal_words = [
        t
        for t in tokens
        if t.lower() not in _MINOR_WORDS and len(t) > 1 and t not in proper_names
    ]
    if not principal_words:
        return False

    capitalized = sum(1 for w in principal_words if w[0].isupper())
    # Flag as sentence case if any principal word is not capitalized
    return capitalized < len(principal_words)


def detect(nb: Notebook) -> list[str]:
    headings = re.findall(r"(?m)^#+[ \t]+(\S.*\S)", nb.prose)
    return [h for h in headings if _is_sentence_case(h)]


POINT = Point(
    title="title_case",
    detail="agents/notebook-title-case.md",
    description="Headings use Title Case (first letter of each principal word uppercase; QAOA, PyTorch, etc. allowed)",
    static=False,
    detect=detect,
)
