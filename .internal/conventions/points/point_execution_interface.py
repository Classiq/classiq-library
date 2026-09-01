"""Use the new execution interface, not the old one.

This is not a single rule but a *family* of signals — the SDK moved from
`execute(qprog).result_value()` and nested `ExecutionPreferences` to free
`sample()` / `observe()` (and a flat `ExecutionSession` only for deliberate
multi-call reuse), plus a DataFrame-shaped result. The individual signals live
in `_exec_signals.py`; this point unions them and the report shows a per-family
breakdown underneath it.
"""

from . import _exec_signals
from ._model import Notebook, Point


def detect(nb: Notebook) -> list[str]:
    return _exec_signals.detect(nb)


POINT = Point(
    title="execution_interface",
    detail="execute() / ExecutionPreferences / .estimate / batch_*  ->  sample() / observe() / variational_minimize",
    description="Use the new execution interface: free sample()/observe(), no nested "
    "ExecutionPreferences, observe not .estimate, variational_minimize not .minimize, "
    "no batch_*, and a DataFrame-shaped result (no .parsed_counts / .dataframe).",
    static=True,
    detect=detect,
    fix=None,  # migration reshapes cells; handled per-family (script or agent), not one regex
    subsignals=_exec_signals.SIGNALS,
)
