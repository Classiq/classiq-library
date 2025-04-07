import pytest
import os
from utils_for_tests import get_all_notebooks, ROOT_DIRECTORY, resolve_notebook_path


@pytest.mark.parametrize("notebook_name", map(os.path.basename, get_all_notebooks()))
def test_is_notebook_tested(notebook_name: str):
    if not _should_skip_notebook(notebook_name):
        expected_test_name = f"test_{notebook_name[:-6]}.py"  # [:-6] removes ".ipynb"
        assert list(
            ROOT_DIRECTORY.rglob(expected_test_name)
        ), f"No test was found for '{notebook_name}'. Expecting to find '{expected_test_name}'"


def _should_skip_notebook(notebook_name: str) -> bool:
    notebook_path = resolve_notebook_path(notebook_name)

    return (
        "/functions/" in notebook_path
        or "/community/" in notebook_path
        or "/.ipynb_checkpoints/" in notebook_path
    )
