from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook(
    "swap_test",
    timeout_seconds=40,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=10,  # actual width: 7
        expected_depth=150,  # actual depth: 122
    )

    # test notebook content
    RTOL = 0.05
    assert np.isclose(
        tb.ref("overlap_from_swap_test"), tb.ref("exact_overlap"), RTOL
    ), f"The quantum result is too far than classical one, by a relative tolerance of {RTOL}. Please verify your parameters"
