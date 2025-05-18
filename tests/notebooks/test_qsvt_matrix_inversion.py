from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
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
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=5,  # actual width: 4
        expected_depth=1500,  # actual depth: 1328
    )
