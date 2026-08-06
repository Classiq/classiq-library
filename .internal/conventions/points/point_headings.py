"""Heading hierarchy: no level skips, and shallow nesting (H5+ flagged)."""

import re

from ._model import Notebook, Point

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(\S.*)", re.MULTILINE)


def detect(nb: Notebook) -> list[str]:
    """Detect heading hierarchy issues.

    Checks for:
    1. Level skips - jumping from H1 to H3, or H2 to H4, etc. (the real hierarchy bug)
    2. Excessive depth - H5+ headings are flagged as too deep

    Note on H5+ limit: We allow H4 because many notebooks legitimately use it for
    numbered sub-sub-sections (e.g., "2.1.1 Foo"). H5+ is rare and usually indicates
    over-nesting that should be flattened. If this causes issues in the future,
    consider raising to H6+ or removing the depth check entirely - the level-skip
    check is the more important one.
    """
    issues = []
    prev_level = 0

    for match in _HEADING_RE.finditer(nb.prose):
        hashes, text = match.groups()
        level = len(hashes)

        # Check for level skip (e.g., H1 -> H3 or H2 -> H4)
        if prev_level > 0 and level > prev_level + 1:
            issues.append(f"level skip H{prev_level}→H{level}: {text[:50]}")

        # Flag H5+ as too deep
        if level >= 5:
            issues.append(f"H{level} too deep: {text[:50]}")

        prev_level = level

    return issues


POINT = Point(
    title="headings",
    detail="agents/notebook-heading-hierarchy.md",
    description="No level skips (H1→H3, H2→H4); H5+ flagged as too deep.",
    static=False,
    detect=detect,
)
