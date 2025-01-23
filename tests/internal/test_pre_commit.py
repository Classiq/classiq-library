import pytest
from pre_commit_tools import (
    clean_timeouts,
    notebook_pre_commit_collection,
    qmod_pre_commit_collection,
)

PROJECT_ROOT = clean_timeouts.PROJECT_ROOT


#
# tests from `clean_timeouts`
#
def test_timeouts_unique_keys():
    assert clean_timeouts.validate_unique_keys()


def test_timeouts_missing_files():
    missing_files = clean_timeouts.find_missing_files()
    assert not missing_files


#
# tests from `notebook_pre_commit_collection`
#
@pytest.mark.parametrize("notebook_path", map(str, PROJECT_ROOT.rglob("*.ipynb")))
def test_notebooks(notebook_path: str):
    assert notebook_pre_commit_collection.validate_notebook(
        notebook_path, automatically_add_timeout=False
    )


def test_notebooks_unique_names():
    assert notebook_pre_commit_collection.validate_unique_names()


#
# tests from `qmod_pre_commit_collection`
#
@pytest.mark.parametrize("qmod_path", map(str, PROJECT_ROOT.rglob("*.qmod")))
def test_notebooks(qmod_path: str):
    if "functions/function_declarations" in qmod_path:
        return  # skipped
    if "functions/open_library_definitions" in qmod_path:
        return  # skipped

    assert qmod_pre_commit_collection.validate_qmod(
        qmod_path, automatically_add_timeout=False
    )


def test_notebooks_unique_names():
    assert qmod_pre_commit_collection.validate_unique_names()
