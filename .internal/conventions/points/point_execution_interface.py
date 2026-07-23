"""Use the new execution interface, not the old execute() call.

The SDK is moving from `execute(qprog).result_value()` to the ExecutionSession
API (`es.sample()` / `.run()` / `.estimate()`) and `calculate_state_vector()`.
This point tracks that migration; it supersedes `result_value` over time.
"""

import re

from ._model import Notebook, Point

_OLD_EXECUTE = re.compile(r"(?<![\w.])execute\(")


def detect(nb: Notebook) -> list[str]:
    return _OLD_EXECUTE.findall(nb.code)


POINT = Point(
    title="execution_interface",
    detail="execute(qprog).result_value()  ->  ExecutionSession / calculate_state_vector",
    description="Use the new execution interface (ExecutionSession, calculate_state_vector), "
    "not execute(). Tracks the ongoing SDK migration.",
    static=True,
    detect=detect,
    fix=None,  # migration reshapes cells; done by the team's migration, not a regex
    status="outdated",
)
