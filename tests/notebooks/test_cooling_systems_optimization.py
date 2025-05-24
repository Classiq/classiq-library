from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
import numpy as np
from testbook.client import TestbookNotebookClient


@wrap_testbook("cooling_systems_optimization", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for the cooling system created by BMW.
    """
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_block_encoding"),
        expected_width=16,  # actual width: 11
        expected_depth=None,  # no transpilation
    )
    validate_quantum_program_size(
        tb.ref_pydantic("matrix_inverse_qprog"),
        expected_width=16,  # actual width: 11
        expected_depth=None,  # no transpilation
    )
    validate_quantum_program_size(
        tb.ref_pydantic("dummy_qprog"),
        expected_width=16,  # actual width: 11
        expected_depth=None,  # no transpilation
    )
    # test notebook content
    assert np.allclose(
        tb.ref_numpy("qsvt_solution"),
        tb.ref_numpy("classical_solution"),
        atol=1e-1,
        rtol=1e-1,
    ), "QSVT solution is not close to the classical solution"
    assert np.allclose(
        np.real(tb.ref_numpy("block_encoded_matrix")),
        np.real(tb.ref_numpy("classical_matrix")),
        atol=1e-2,
    ), "Block encoding matrix is not close to the classical matrix"

    pass  # TODO
