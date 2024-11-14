import os
from collections.abc import Iterable
from pathlib import Path

ROOT_DIRECTORY = Path(__file__).parents[1]


def iterate_notebooks() -> Iterable[str]:
    if os.environ.get("SHOULD_TEST_ALL_FILES", "") == "true":
        notebooks_to_test = _get_all_notebooks()
    else:
        notebooks_to_test = os.environ.get("LIST_OF_IPYNB_CHANGED", "").split()

    return notebooks_to_test


def _get_all_notebooks(directory: Path = ROOT_DIRECTORY) -> Iterable[str]:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".ipynb"):
                yield os.path.join(root, file)


def should_test_notebook(notebook_path: str) -> bool:
    return notebook_path in list(iterate_notebooks())


def resolve_notebook_path(notebook_name: str) -> str:
    notebook_name_lower = notebook_name.lower()
    if not notebook_name_lower.endswith(".ipynb"):
        notebook_name_lower += ".ipynb"

    for root, _, files in os.walk(ROOT_DIRECTORY):
        for file in files:
            if file.lower() == notebook_name_lower:
                return os.path.join(root, file)
