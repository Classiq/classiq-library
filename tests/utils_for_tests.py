import os
from functools import lru_cache
from pathlib import Path

ROOT_DIRECTORY = Path(__file__).parents[1]


def iterate_notebooks() -> list[str]:
    if os.environ.get("SHOULD_TEST_ALL_FILES", "") == "true":
        notebooks_to_test = get_all_notebooks()
    else:
        notebooks_to_test = os.environ.get("LIST_OF_IPYNB_CHANGED", "").split()

    return notebooks_to_test


@lru_cache
def iterate_notebook_names() -> list[str]:
    return list(map(os.path.basename, iterate_notebooks()))


# do not use `get_all_notebooks` unless you're sure it's the right one.
# 95% of the tests would use `iterate_notebooks_names`
@lru_cache
def get_all_notebooks(
    directory: Path = ROOT_DIRECTORY, suffix: str = ".ipynb"
) -> list[str]:
    return [
        f"{root}/{file}"
        for root, _, files in os.walk(directory)
        for file in files
        if file.endswith(suffix)
    ]


def should_run_notebook(notebook_name: str) -> bool:
    return notebook_name in iterate_notebook_names()


def should_skip_notebook(notebook_name: str) -> bool:
    return not should_run_notebook(notebook_name)


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
