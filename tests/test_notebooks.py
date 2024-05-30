import os
from collections.abc import Iterable
from pathlib import Path

from testbook import testbook

TIMEOUT: int = 60 * 3  # 3 minutes

ROOT_DIRECTORY = Path(__file__).parent


def test_notebooks():
    for notebook_path in _get_notebooks():
        with testbook(notebook_path, execute=True, timeout=TIMEOUT) as tb:
            pass  # we simply wish it to run without errors


# TODO: change this function to `from utils_for_tests import iterate_notebooks`, after we merge PR#109
def _get_notebooks() -> Iterable[str]:
    if os.environ.get("SHOULD_TEST_ALL_FILES", "") == "true":
        notebooks_to_test = _get_all_notebooks()
    else:
        if os.environ.get("HAS_ANY_IPYNB_CHANGED", "") == "true":
            notebooks_to_test = os.environ.get("LIST_OF_IPYNB_CHANGED", "").split()
        else:
            notebooks_to_test = []

    return notebooks_to_test


def _get_all_notebooks(directory=ROOT_DIRECTORY):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".ipynb"):
                yield os.path.join(root, file)
