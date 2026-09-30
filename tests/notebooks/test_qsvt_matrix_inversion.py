from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("qsvt_matrix_inversion", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    QSVT matrix inversion via a by-hand QSVT inverse built on BlockEncoding,
    verified against the classical solution.
    """
    # `qprog` is the by-hand QSVT inverse driven by BlockEncoding.from_matrix.
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=10,  # data + block-encoding ancillas + QSVT auxiliary
        expected_depth=43000,  # by-hand QSVT (kappa_eff~12.9, eps=1e-4); actual ~41049
    )

    computed_x = tb.ref_pydantic("computed_x")
    expected_x = tb.ref_pydantic("expected_x")
    assert (
        min(
            np.linalg.norm(computed_x - expected_x),
            np.linalg.norm(-computed_x - expected_x),
        )
        < 0.05
    )
