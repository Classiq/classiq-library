from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook(
    "vqls_with_lcu",
    timeout_seconds=1200,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    validate_quantum_model(tb.ref("qmod_3"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_1"),
        expected_width=5,  # actual width: 3
        expected_depth=15,  # actual depth: 9
    )
    validate_quantum_program_size(
        tb.ref("qprog_2"),
        expected_width=7,  # actual width: 5
        expected_depth=50,  # actual depth: 35
    )
    validate_quantum_program_size(
        tb.ref("qprog_1"),
        expected_width=5,  # actual width: 3
        expected_depth=20,  # actual depth: 10
    )

    # test notebook content
    assert tb.ref(
        "bool(optimizer._out.success)"
    )  # convert `np.bool_` to `bool` to help serialize

    assert tb.ref("optimizer.my_cost(optimal_params)") < 0.5  # it even was 0.06
