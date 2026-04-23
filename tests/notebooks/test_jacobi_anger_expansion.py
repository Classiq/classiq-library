from tests.utils_for_testbook import wrap_testbook
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("jacobi_anger_expansion", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    EPS = tb.ref_numpy("EPS")
    EVOLUTION_TIME = tb.ref_numpy("EVOLUTION_TIME")
    xs = tb.ref_numpy("xs")
    cos_approx = tb.ref_numpy("cos_approx")
    sin_approx = tb.ref_numpy("sin_approx")

    assert np.max(np.abs(np.cos(EVOLUTION_TIME * xs) - cos_approx)) < EPS
    assert np.max(np.abs(np.sin(EVOLUTION_TIME * xs) - sin_approx)) < EPS
