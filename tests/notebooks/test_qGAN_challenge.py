import sys
import importlib
from pathlib import Path
import pytest

# Compute repo root from this file (tests/notebooks/ -> tests -> repo root)
TESTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(REPO_ROOT))  # allow importing helpers from repo root

# Be flexible about helper location
run_notebook = None
try:
    from tests_helpers.run_notebook import run_notebook  # common layout
except ModuleNotFoundError:
    try:
        run_notebook = importlib.import_module("classiq_library.tests_helpers.run_notebook").run_notebook
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Could not import run_notebook from either 'tests_helpers' or "
            "'classiq_library.tests_helpers'. Ensure the helper exists in the repo and "
            "that the test is executed from the repository root or with REPO_ROOT on sys.path."
        ) from e

@pytest.mark.timeout(600)
def test_qGAN_challenge():
    nb_path = REPO_ROOT / "tutorials" / "basic_tutorials" / "qGAN-state-prep" / "qGAN_challenge.ipynb"
    assert nb_path.exists(), f"Notebook not found: {nb_path}"
    run_notebook(nb_path)
