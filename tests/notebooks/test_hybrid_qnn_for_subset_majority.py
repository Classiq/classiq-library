from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "hybrid_qnn_for_subset_majority",
    timeout_seconds=120,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """

    assert (
        tb.ref("accuracy") > 0.85
    ), "The network is not trained, although we load a pre-trained model."
    pass
