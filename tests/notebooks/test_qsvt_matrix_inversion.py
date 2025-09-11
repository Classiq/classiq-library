from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("qsvt_matrix_inversion", timeout_seconds=180)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=5,  # actual width: 4
        expected_depth=3200,  # actual depth: 2150
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
