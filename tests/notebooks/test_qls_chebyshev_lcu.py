from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np


@wrap_testbook("qls_chebyshev_lcu", timeout_seconds=1200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_small_pauli"),
        expected_width=15,  # actual 13
        expected_depth=50000,  # actual 20578
    )

    qsols = [
        tb.ref_numpy("qsol_small_pauli"),
        tb.ref_numpy("qsol_008_banded"),
        tb.ref_numpy("qsol_008_banded_approx"),
    ]
    expected_sols = [
        tb.ref_numpy("expected_small"),
        tb.ref_numpy("expected_008"),
        tb.ref_numpy("expected_008"),
    ]
    errs = [0.1, 0.1, 0.2]
    for qsol, clsol, err in zip(qsols, expected_sols, errs):
        assert np.linalg.norm(qsol - clsol) < err
