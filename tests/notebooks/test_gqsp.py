from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np


@wrap_testbook("gqsp", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=10,  # actual 8
        expected_depth=200,  # actual 121
    )

    num_qubits = tb.ref_pydantic("NUM_QUBITS")
    SCALING_CONST = tb.ref_pydantic("SCALING_CONST")
    x, prob = tb.ref_pydantic("x"), tb.ref_pydantic("prob")
    assert (
        np.linalg.norm(
            (1 / 2 ** (num_qubits / 2) * np.cos(2 * np.pi * x) ** 3) ** 2
            - prob / SCALING_CONST**2
        )
        < 0.1
    )
