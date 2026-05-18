from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook(
    "hamiltonian_simulation_guide", timeout_seconds=2000
)  # 2025.03.06 bump from 1000 seconds
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_trotter"),
        expected_width=2,  # actual width: 2
        expected_depth=50,  # actual depth: 40
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_exponentiation"),
        expected_width=2,  # actual width: 2
        expected_depth=30,  # actual depth: 20
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_qdrift"),
        expected_width=2,  # actual width: 2
        expected_depth=150,  # actual depth: 114
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_magnetization_trotter"),
        expected_width=2,  # actual width: 2
        expected_depth=250,  # actual depth: 180
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_magnetization_qdrift"),
        expected_width=2,  # actual width: 2
        expected_depth=600,  # actual depth: 480
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_magnetization_exponentiate"),
        expected_width=2,  # actual width: 2
        expected_depth=20,  # actual depth: 20
    )

    # test notebook content
    time_list = tb.ref("time_list")
    results_ST = tb.ref_numpy("magnetization_ST")
    results_exponentiate = tb.ref_numpy("magnetization_exponentiate")
    results_qdrift = tb.ref_numpy("magnetization_qdrift")

    tolerance = 0.1  # that's a large tolerance. we should lower it.
    np.allclose(results_ST, results_exponentiate, atol=tolerance)
    np.allclose(results_ST, results_qdrift, atol=tolerance)
    np.allclose(results_exponentiate, results_qdrift, atol=tolerance)
