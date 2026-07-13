"""Synthesize functionally: synthesize(main), not create_model() + synthesize()."""

import re

from ._model import Notebook, Point

_CREATE_MODEL = re.compile(r"(?<![\w.])create_model\(")


def detect(nb: Notebook) -> list[str]:
    # `create_model(...)` is the old two-step flow. The trivial cases were collapsed
    # by a script; the rest carry execution_preferences / constraints and need a
    # human (or the ongoing new-execution-interface migration) to unwind.
    return _CREATE_MODEL.findall(nb.code)


POINT = Point(
    key="synthesize_main",
    example="create_model(main); synthesize(qmod)  ->  synthesize(main)",
    description="Prefer the one-step synthesize(main) over create_model() + synthesize().",
    detect=detect,
    fix=None,  # trivial cases scripted; remaining ones are context-dependent
    agent="one_off_fixes/collapse_synthesize.py (safe subset); manual for the rest",
)
