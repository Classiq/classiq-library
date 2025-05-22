from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "rainbow_options_bruteforce_method",
    timeout_seconds=1000,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=tb.ref("MAX_WIDTH_1"),
        expected_depth=1000,  # actual depth: 794
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=tb.ref("MAX_WIDTH_2"),
        expected_depth=2750,  # actual depth: 2441
    )

    # test notebook content
    pass  # TODO
