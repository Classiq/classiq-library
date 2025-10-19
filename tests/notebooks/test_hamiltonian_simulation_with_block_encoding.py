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
        tb.ref_pydantic("qprog_verify_be"),
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
        expected_depth=6500,  # actual depth: 3435
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_cheb_lcu"),
        expected_width=12,  # actual width: 12
        expected_depth=20000,  # actual depth: 12757
    )

    # test notebook content
    renormalized_verify_be = tb.ref_numpy("state_result_verify_be")
    expected_state_be = tb.ref_numpy("expected_state_be")
    overlap = np.abs(
        np.vdot(renormalized_verify_be, expected_state_be)
        / np.linalg.norm(renormalized_verify_be)
        / np.linalg.norm(expected_state_be)
    )
    assert np.abs(1 - overlap) < 1e-5

    expected_state = tb.ref_numpy("expected_state")
    EPS = tb.ref_numpy("EPS")
    renormalized_state_gqsp = tb.ref_numpy("renormalized_state_gqsp")
    renormalized_state_qsvt = tb.ref_numpy("renormalized_state_qsvt")
    renormalized_state_cheb_lcu = tb.ref_numpy("renormalized_state_cheb_lcu")

    renormalized_states = [
        renormalized_state_gqsp,
        renormalized_state_qsvt,
        renormalized_state_cheb_lcu,
    ]
    for state in renormalized_states:
        overlap = np.abs(
            np.vdot(state, expected_state)
            / np.linalg.norm(state)
            / np.linalg.norm(expected_state)
        )
        assert np.abs(1 - overlap) < EPS
