import os
import pytest
from pathlib import Path
from classiq_library.tests_helpers.run_notebook import run_notebook

ROOT = Path(__file__).resolve().parents[3]  # repo root

@pytest.mark.timeout(600)
def test_qGAN_challenge_solution():
    nb_path = ROOT / "tutorials" / "basic_tutorials" / "qGAN-state-prep" / "Solution/qGAN_challenge_solution.ipynb"
    assert nb_path.exists(), f"Notebook not found: {nb_path}"
    run_notebook(nb_path)
