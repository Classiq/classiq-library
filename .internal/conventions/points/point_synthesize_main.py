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
    title="synthesize_main",
    detail="create_model(main); synthesize(qmod)  ->  synthesize(main)",
    description="Prefer one-step synthesize(main). Trivial cases scripted; the rest "
    "(execution_preferences / constraints) are manual or fall out of the execution migration.",
    static=True,
    detect=detect,
    fix=None,  # trivial cases scripted; remaining ones are context-dependent
)
