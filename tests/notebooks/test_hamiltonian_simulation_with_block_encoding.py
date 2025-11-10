from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("hamiltonian_simulation_with_block_encoding", timeout_seconds=900)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_be"),
        expected_width=4,  # actual width: 4
        expected_depth=100,  # actual depth: 60
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_gqsp"),
        expected_width=7,  # actual width: 7
        expected_depth=32000,  # actual depth: 17709
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_qsvt"),
        expected_width=8,  # actual width: 8
        expected_depth=6500,  # actual depth: 2458
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_cheb_lcu"),
        expected_width=12,  # actual width: 12
        expected_depth=20000,  # actual depth: 14961
    )

    # test notebook content
    for overlap in [
        tb.ref_numpy("overlap_be"),
        tb.ref_numpy("overlap_gqsp"),
        tb.ref_numpy("overlap_qsvt"),
        tb.ref_numpy("overlap_cheb_lcu"),
    ]:
        EPS = tb.ref_numpy("EPS")
        assert np.abs(1 - overlap) < EPS
