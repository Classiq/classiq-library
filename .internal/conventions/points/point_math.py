"""Math is written with $...$ (inline) or $$...$$ (display) — nothing else.

Forbid every other LaTeX math delimiter in markdown: \\(...\\), \\[...\\], and
\\begin{equation|align|gather|multline|eqnarray|alignat|flalign} (and their *
variants). Converting them to $/$$ needs judgement, so this is a forbid (no
auto-fix); the agent doc says how to rewrite them.
"""

import re

from ._model import Notebook, Point

_NON_DOLLAR_MATH = re.compile(
    r"\\\("  # \(  inline-math open
    # \[  display-math open — but NOT `\\[6pt]` line-break spacing (preceded by \)
    # nor a `[\[1\]]` citation-link label (preceded by [)
    r"|(?<![\\\[])\\\["
    r"|\\begin\{(?:equation|align|gather|multline|eqnarray|alignat|flalign)\*?\}"
)


def detect(nb: Notebook) -> list[str]:
    return _NON_DOLLAR_MATH.findall(nb.prose)


POINT = Point(
    title="math",
    detail="agents/notebook-math-notation.md",
    description="Math uses $...$ / $$...$$ only — no \\(, \\[, or \\begin{...} math envs. unicode math symbols as LaTeX.",
    static=False,
    detect=detect,
    enforced=True,
)
