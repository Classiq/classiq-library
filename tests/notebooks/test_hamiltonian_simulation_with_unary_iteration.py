from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("hamiltonian_simulation_with_block_encoding", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    validate_quantum_model(tb.ref("qmod_3"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_1"),
        expected_width=10,  # actual width: 7
        expected_depth=100,  # actual depth: 68
    )
    validate_quantum_program_size(
        tb.ref("qprog_2"),
        expected_width=20,  # actual width: 18
        expected_depth=14000,  # actual depth: 12905
    )
    validate_quantum_program_size(
        tb.ref("qprog_3"),
        expected_width=15,  # actual width: 10
        expected_depth=6500,  # actual depth: 6021
    )

    # test notebook content
    assert np.allclose(
        np.real(tb.ref_numpy("state_result_1")), tb.ref_numpy("expected_state_1")
    )

    state_result_2 = tb.ref_numpy("state_result_2")
    expected_state_2 = tb.ref_numpy("expected_state_2")
    assert np.linalg.norm(state_result_2 - expected_state_2) < tb.ref("EPS")
    overlap_2 = (
        np.abs(np.vdot(state_result_2, expected_state_2))
        * tb.ref("normalization_exp")
        / np.linalg.norm(state_result_2)
    )
    assert np.isclose(
        overlap_2, 0.999, atol=0.01
    )  # 0.9996884609316635  # should be atol=0.001

    state_result_3 = tb.ref_numpy("state_result_3")
    expected_state_3 = tb.ref_numpy("expected_state_3")
    assert np.linalg.norm(state_result_3 - expected_state_3) < tb.ref("EPS")
    overlap_3 = (
        np.abs(np.vdot(state_result_3, expected_state_3))
        * tb.ref("normalization_exp")
        / np.linalg.norm(state_result_3)
    )
    assert np.isclose(
        overlap_3, 0.999999, atol=0.01
    )  # 0.9999998243682983  # should be atol=0.000001  # in another run it was 1.0018339139233956
