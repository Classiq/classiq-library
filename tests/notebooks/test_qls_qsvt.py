from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np


@wrap_testbook("qls_qsvt", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_small_pauli"),
        expected_width=11,  # actual 9
        expected_depth=120000,  # actual 65325
    )

    qsols = [tb.ref_numpy("qsol_small_pauli"), tb.ref_numpy("qsol_008_banded")]
    expected_sols = [tb.ref_numpy("expected_small"), tb.ref_numpy("expected_008")]
    errs = [0.1, 0.1]
    for qsol, clsol, err in zip(qsols, expected_sols, errs):
        assert np.linalg.norm(qsol - clsol) < err
