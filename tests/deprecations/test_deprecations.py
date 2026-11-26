import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import nbformat
import pytest
from nbclient.exceptions import CellExecutionError
from testbook import testbook  # type: ignore[import]
from testbook.client import TestbookNotebookClient
from tests.deprecations.mock_classiq_api import INSTALL_MOCK, REPORT
from tests.utils_for_tests import ROOT_DIRECTORY, iterate_notebooks
from tests.utils_for_testbook import (
    DEFAULT_CODE_INJECTIONS,
    NotebookEdit,
    _build_cd_decorator,
)

TIMEOUT: int = 60 * 15  # 15 minutes

# Notebooks that the fakes can't run to their end
SKIPPED_NOTEBOOKS = {
    "fault_tolerance_engine_end_to_end.ipynb": "uses the logical-noise API, which has no fake",
    "projected_based_embedding_tutorial.ipynb": "runs chemistry DFT jobs, which have no fake",
    "adapt_qaoa.ipynb": "loops until the measured gradients are small",
    "adapt_vqe.ipynb": "builds its next model from the measured gradients",
    "bpde.ipynb": "fits a Gaussian to its samples",
    "discrete_log.ipynb": "needs an invertible measured value",
    "fermi_hubbard_1D.ipynb": "expects one-hot states in its state vector",
    "hhl.ipynb": "raises when its result is far from the classical solution",
    "hidden_shift.ipynb": "solves a linear system built from its samples",
    "vehicle_routing_problem.ipynb": "colors a graph by the sampled solution",
}

# Deprecation warnings that the library can't fix, and who fixes them. Remove each one once it's fixed
KNOWN_DEPRECATIONS = {
    "ExecutionSession.minimize is deprecated": "the SDK: CombinatorialProblem.optimize calls it",
}


@pytest.mark.parametrize("notebook_path", iterate_notebooks())
def test_notebook(notebook_path: str) -> None:
    _test_notebook(notebook_path)


def _test_notebook(notebook_path: str) -> None:
    test = _run_without_deprecations
    # NotebookEdit inserts each cell at the top, so the mock is installed right before the notebook's first cell
    with NotebookEdit(
        notebook_path,
        code_injection_at_start=[INSTALL_MOCK] + DEFAULT_CODE_INJECTIONS,
    ):
        for decorator in [
            testbook(notebook_path, timeout=TIMEOUT),
            _build_cd_decorator(notebook_path),
            _build_skip_decorator(notebook_path),
        ]:
            test = decorator(test)
    test()


def _run_without_deprecations(tb: TestbookNotebookClient) -> None:
    error = ""
    try:
        tb.execute()
    except CellExecutionError as exc:
        error = str(exc)

    new_warnings = [w for w in tb.value(REPORT) if not _is_known_deprecation(w)]
    problems = [*map(_format_warning, new_warnings), *filter(bool, [error])]
    assert not problems, "\n".join(problems)


def _is_known_deprecation(warning: dict) -> bool:
    return any(known in warning["message"] for known in KNOWN_DEPRECATIONS)


def _format_warning(warning: dict) -> str:
    return f"cell {warning['cell']}: {warning['category']}: {warning['message']} ({warning['location']})"


def _build_skip_decorator(notebook_path: str) -> Callable:
    def skip_decorator(func: Callable) -> Callable:
        def inner(*args: Any, **kwargs: Any) -> Any:
            if reason := SKIPPED_NOTEBOOKS.get(os.path.basename(notebook_path)):
                pytest.skip(reason)
            return func(*args, **kwargs)

        return inner

    return skip_decorator


def test_readme(tmp_path: Path) -> None:
    _test_notebook(
        _readme_file_to_notebook_file(ROOT_DIRECTORY / "README.md", tmp_path)
    )


def _readme_file_to_notebook_file(readme_path: Path, folder: Path) -> str:
    python_blocks = re.findall("(?s)```python\\s*\\n(.*?)```", readme_path.read_text())
    notebook = nbformat.v4.new_notebook(
        cells=list(map(nbformat.v4.new_code_cell, python_blocks))
    )
    notebook_path = str(folder / f"{readme_path.stem}.ipynb")
    nbformat.write(notebook, notebook_path)
    return notebook_path
