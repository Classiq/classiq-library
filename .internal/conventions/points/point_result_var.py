"""Execution-outcome variables are named by what they hold: result / job / df."""

import re

from ._model import Notebook, Point

_ASSIGN = re.compile(
    r"(?<![\w.])(\w+)\s*=\s*(?:execute\(|sample\(|get_sample_result\("
    r"|\w+\.result(?:_value)?\()"
)
_OK = re.compile(r"(?:result|job)(?:_\w+)?|dfs?(?:_\w+)?")


def detect(nb: Notebook) -> list[str]:
    return sorted({v for v in _ASSIGN.findall(nb.code) if not _OK.fullmatch(v)})


POINT = Point(
    title="result_var",
    detail="agents/notebook-variable-names.md",
    description="result / result_<suffix> (value), job / job_<suffix> (ExecutionJob), "
    "df / dfs (DataFrame) — by what the variable holds.",
    static=False,
    detect=detect,
    status="outdated",
    exceptions=(("qaoa_in_qaoa", "vqe_result is a keyword-argument name"),),
)
