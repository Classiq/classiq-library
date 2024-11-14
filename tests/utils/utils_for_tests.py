import os
from functools import lru_cache
from collections.abc import Iterable
from pathlib import Path

ROOT_DIRECTORY = Path(__file__).parents[2]


def iterate_notebooks() -> Iterable[str]:
    if os.environ.get("SHOULD_TEST_ALL_FILES", "") == "true":
        notebooks_to_test = _get_all_notebooks()
    else:
        notebooks_to_test = os.environ.get("LIST_OF_IPYNB_CHANGED", "").split()

    return notebooks_to_test


@lru_cache
def _get_all_notebooks(directory: Path = ROOT_DIRECTORY) -> Iterable[str]:
    return [
        file
        for root, _, files in os.walk(directory)
        for file in files
        if file.endswith(".ipynb")
    ]


def should_skip_notebook(notebook_name: str) -> bool:
    notebook_path = resolve_notebook_path(notebook_name)
    return notebook_path in list(iterate_notebooks())


@lru_cache
def resolve_notebook_path(notebook_name: str) -> str:
    notebook_name_lower = notebook_name.lower()
    if not notebook_name_lower.endswith(".ipynb"):
        notebook_name_lower += ".ipynb"

    for root, _, files in os.walk(ROOT_DIRECTORY):
        for file in files:
            if file.lower() == notebook_name_lower:
                return os.path.join(root, file)
    raise LookupError(f"Notebook not found: {notebook_name}")
