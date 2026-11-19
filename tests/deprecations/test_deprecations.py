import os
import re
from pathlib import Path

import nbformat
import pytest
from nbclient.exceptions import CellExecutionError
from testbook import testbook  # type: ignore[import]
from tests.utils_for_tests import ROOT_DIRECTORY, iterate_notebooks
from tests.utils_for_testbook import (
    DEFAULT_CODE_INJECTIONS,
    NotebookEdit,
    _build_cd_decorator,
)

TIMEOUT: int = 60 * 15  # 15 minutes

PYTHON_CODE_PATTERN = r"(?s)```python\s*\n(.*?)```"

INSTALL_MOCK = (
    f"import sys; sys.path.insert(0, {str(Path(__file__).parent)!r})\n"
    "import mock_classiq_api; sys.path.pop(0); mock_classiq_api.install()"
)
# NotebookEdit inserts each cell at the top, so the mock is installed right before the notebook's first cell
INJECTED_CELLS = [INSTALL_MOCK] + DEFAULT_CODE_INJECTIONS
REPORT = "__import__('mock_classiq_api').report()"


# Notebooks that the fakes can't run to their end
SKIPPED_NOTEBOOKS = {
    "fault_tolerance_engine_end_to_end.ipynb": "uses the logical-noise API, which has no fake",
    "projected_based_embedding_tutorial.ipynb": "runs chemistry DFT jobs, which have no fake",
    "adapt_vqe.ipynb": "builds its next model from the measured gradients",
    "bpde.ipynb": "fits a Gaussian to its samples",
    "discrete_log.ipynb": "needs an invertible measured value",
    "fermi_hubbard_1D.ipynb": "expects one-hot states in its state vector",
    "hhl.ipynb": "raises when its result is far from the classical solution",
    "hidden_shift.ipynb": "solves a linear system built from its samples",
    "vehicle_routing_problem.ipynb": "colors a graph by the sampled solution",
}


def _should_test_notebook(notebook_path: str) -> bool:
    return os.path.basename(notebook_path) not in SKIPPED_NOTEBOOKS


@pytest.mark.parametrize(
    "notebook_path", list(filter(_should_test_notebook, iterate_notebooks()))
)
def test_notebook(notebook_path: str) -> None:
    _test_notebook(notebook_path)


def test_readme(tmp_path: Path) -> None:
    readme = (ROOT_DIRECTORY / "README.md").read_text()
    cells = [
        nbformat.v4.new_code_cell(code)
        for code in re.findall(PYTHON_CODE_PATTERN, readme)
    ]
    notebook_path = str(tmp_path / "README.ipynb")
    nbformat.write(nbformat.v4.new_notebook(cells=cells), notebook_path)
    _test_notebook(notebook_path)


def _test_notebook(notebook_path: str) -> None:
    test = _run_without_deprecations
    with NotebookEdit(notebook_path, code_injection_at_start=INJECTED_CELLS):
        test = testbook(notebook_path, timeout=TIMEOUT)(test)
        test = _build_cd_decorator(notebook_path)(test)
    test()


def _run_without_deprecations(tb) -> None:
    error = None
    try:
        tb.execute()
    except CellExecutionError as exc:
        error = exc

    problems = [
        f"cell {warning['cell']}: {warning['category']}: {warning['message']} ({warning['location']})"
        for warning in tb.value(REPORT)
    ]
    if error is not None:
        problems.append(str(error))
    assert not problems, "\n".join(problems)
