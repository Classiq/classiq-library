from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np
import scipy


@wrap_testbook(
    "qsvt_fixed_point_amplitude_amplification",
    timeout_seconds=376,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=13,  # actual width: 11
        expected_depth=18000,  # actual depth: 15432
    )
