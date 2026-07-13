"""The intro opens with a consistent phrasing (e.g. "This notebook ...")."""

from ._model import Notebook, Point

_PREFERRED = ("this notebook", "in this")
_SKIP = ("#", "<", "!", "[", ">", "-", "*", "$", "|", "=", "_")


def detect(nb: Notebook) -> list[str]:
    for line in nb.prose.splitlines():
        s = line.strip()
        if s and not s.startswith(_SKIP):
            return [] if s.lower().startswith(_PREFERRED) else [s[:60]]
    return []


POINT = Point(
    title="intro_opener",
    detail="agents/notebook-intro-opener.md (to write)",
    description="The first sentence opens with a shared phrasing. (approximate; target TBD)",
    static=False,
    detect=detect,
)
