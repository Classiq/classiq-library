import os
from collections.abc import Iterable
from pathlib import Path

ROOT_DIRECTORY = Path(__file__).parents[1]


def iterate_notebooks() -> Iterable[str]:
    if os.environ.get("SHOULD_TEST_ALL_FILES", "") == "true":
        notebooks_to_test = _get_all_notebooks()
    else:
        #if os.environ.get("HAS_ANY_IPYNB_CHANGED", "") == "true":
            notebooks_to_test = os.environ.get("LIST_OF_IPYNB_CHANGED", "").split()
        #else:
        #    notebooks_to_test = []

    return notebooks_to_test


def _get_all_notebooks(directory: Path = ROOT_DIRECTORY) -> Iterable[str]:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".ipynb"):
                yield os.path.join(root, file)
