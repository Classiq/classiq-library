from pathlib import Path
import pytest
from tests_helpers.run_notebook import run_notebook

# pytest rootdir is .../tests, so this points to the repo root
TESTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TESTS_DIR.parent

@pytest.mark.timeout(600)
def test_qGAN_challenge():
    nb_path = REPO_ROOT / "tutorials" / "basic_tutorials" / "qGAN-state-prep" / "qGAN_challenge.ipynb"
    assert nb_path.exists(), f"Notebook not found: {nb_path}"
    run_notebook(nb_path)
