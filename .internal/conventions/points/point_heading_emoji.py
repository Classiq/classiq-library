"""Headings carry no emoji — section titles stay plain text.

`## Results 🎉` -> `## Results`. Auto-fixed: the emoji is removed together with
its own surrounding whitespace, collapsing to a single space only when it sat
between two words (so intentional multi-spaces elsewhere in the heading survive).
"""

import re

from ._model import Notebook, Point, src

_HEADING = re.compile(r"(?m)^#+[ \t]+.*$")
_HEADING_LINE = re.compile(r"^#+[ \t]+")
_FENCE = re.compile(r"^\s*```")
# Emoji unicode blocks. Built into a character class at runtime (not written as a
# literal range) so static analysers don't misread the astral \U0001xxxx escapes.
_EMOJI_BLOCKS = (
    (0x1F300, 0x1FAFF),  # pictographs, emoticons, transport, supplemental symbols
    (0x1F000, 0x1F0FF),  # tiles (mahjong, dominoes, cards)
    (0x2600, 0x26FF),  # miscellaneous symbols (weather, zodiac, ...)
    (0x2700, 0x27BF),  # dingbats (sparkles, check-mark button, ...)
    (0x2B00, 0x2BFF),  # stars and misc symbols
    (0x1F1E6, 0x1F1FF),  # regional-indicator flags
    (0xFE0F, 0xFE0F),  # emoji variation selector
)
_EMOJI_CLASS = "[" + "".join(f"{chr(lo)}-{chr(hi)}" for lo, hi in _EMOJI_BLOCKS) + "]"
_EMOJI = re.compile(_EMOJI_CLASS)
_EMOJI_RUN = re.compile(rf"\s*{_EMOJI_CLASS}+\s*")


def _strip_emoji(line: str) -> str:
    """Drop emoji + their own whitespace; keep one space only between two words."""

    def collapse(match: re.Match) -> str:
        before, after = line[: match.start()], line[match.end() :]
        between_words = (before and not before[-1].isspace()) and (
            after and not after[0].isspace()
        )
        return " " if between_words else ""

    return _EMOJI_RUN.sub(collapse, line)


def detect(nb: Notebook) -> list[str]:
    return [h for h in _HEADING.findall(nb.prose) if _EMOJI.search(h)]


def fix(cells: list) -> bool:
    changed = False
    for cell in cells:
        if cell.get("cell_type") != "markdown":
            continue
        lines, in_fence, touched = src(cell).split("\n"), False, False
        for i, line in enumerate(lines):
            if _FENCE.match(line):
                in_fence = not in_fence
            elif not in_fence and _HEADING_LINE.match(line) and _EMOJI.search(line):
                if (stripped := _strip_emoji(line)) != line:
                    lines[i], touched = stripped, True
        if touched:
            cell["source"] = "\n".join(lines).splitlines(keepends=True)
            changed = True
    return changed


POINT = Point(
    title="heading_emoji",
    detail="## Results 🎉  ->  ## Results",
    description="A markdown heading contains no emoji.",
    static=True,
    detect=detect,
    fix=fix,
    enforced=True,
)
