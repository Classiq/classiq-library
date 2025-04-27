from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
import numpy as np
from testbook.client import TestbookNotebookClient


@wrap_testbook("cooling_systems_optimization", timeout_seconds=2200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for the cooling system created by BMW.
    """
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_block_encoding")
    )
    validate_quantum_program_size(
        tb.ref("matrix_inverse_qprog")
    )
    validate_quantum_program_size(
        tb.ref("dummy_qprog")
    )
    # test notebook content
    assert np.allclose(
        tb.ref_numpy("qsvt_solution"), tb.ref_numpy("classical_solution"), atol=1e-1, rtol=1e-1
    )

    pass  # TODO