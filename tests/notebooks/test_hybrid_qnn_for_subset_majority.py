from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "hybrid_qnn_for_subset_majority",
    timeout_seconds=150,  # note: 2025.02.20, bumping from 120 to 150. If it raises further, there's a problem.
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
        expected_width=5,  # actual width: 2
        expected_depth=10,  # actual depth: 6
    )

    # test notebook content
    assert (
        tb.ref("accuracy") > 0.85
    ), "The network is not trained, although we load a pre-trained model."
    pass
