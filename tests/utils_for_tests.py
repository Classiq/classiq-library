import os
import re
from functools import lru_cache
from pathlib import Path

ROOT_DIRECTORY = Path(__file__).parents[1]


def iterate_notebooks() -> list[str]:
    if os.environ.get("SHOULD_TEST_ALL_FILES", "") == "true":
        notebooks_to_test = get_all_notebooks()
    else:
        notebooks_to_test = get_changed_notebooks()

    return notebooks_to_test


def get_changed_notebooks() -> list[str]:
    changed_notebooks = os.environ.get("LIST_OF_IPYNB_CHANGED", "").split()

    changed_tests = os.environ.get("LIST_OF_IPYNB_TESTS_CHANGED", "").split()
    changed_notebooks_from_tests = list(
        filter(
            bool,
            map(
                get_notebook_of_test,
                changed_tests,
            ),
        )
    )

    return list(set(changed_notebooks + changed_notebooks_from_tests))


def get_notebook_of_test(test_path: str) -> str | None:
    if os.path.basename(test_path) == "test__community_and_functions.py":
        # this is a special test. It tests a whole folder of notebooks, rather than a single one
        return None

    with open(ROOT_DIRECTORY / test_path) as f:
        test_data = f.read()

    find_results = re.findall('@wrap_testbook\\([\n\\s]*"(\\S*?)"', test_data)
    if len(find_results) == 1:
        # Previously, we simply had `return resolve...`
        # however, we got a case where `LIST_OF_IPYNB_TESTS_CHANGED` had a test to which
        #   it's corresponding notebook did not exist.
        # this is indeed a bug. BUT, it's a bug *for that test only*.
        # What actually happened is that pytest failed collecting all the tests.
        # Now, aside from us not wanting to fail the collection process,
        # it was also "scary" to see so many failures.
        # Thus, this solution, albeit a hack, solves this problem.
        # It makes it so that tests with missing notebooks gets "resolved"
        #   in a minimal way - only the `notebook_name` is returned
        #   and that's fine, since `should_skip_notebook`, which is the
        #   function that failed in the collection process, only uses
        #   `iterate_notebook_names`
        # this way, every other test will successfully get skipped (or not skipped)
        # and the test with the missing notebook will fail in `wrap_testbook`
        #   when it calls `resolve_notebook_path`
        # thus the collection process will now fail (as it failed before this fix)
        #   only now it fails collecting only 1 test - the one with the missing notebook
        #   rather than failing to collect all the tests.
        try:
            return resolve_notebook_path(find_results[0])
        except LookupError:
            return find_results[0]
    else:
        print(f"Failed extracting notebook name from test file")
        return None


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
