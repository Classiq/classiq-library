from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("simon", timeout_seconds=40)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    validate_quantum_model(tb.ref("qmod_3"))
    validate_quantum_model(tb.ref("qmod_4"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=20,  # actual width: 17
        expected_depth=700,  # actual depth: 576
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=20,  # actual width: 17
        expected_depth=700,  # actual depth: 577
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_3"),
        expected_width=15,  # actual width: 12
        expected_depth=10,  # actual depth: 5
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_4"),
        expected_width=15,  # actual width: 12
        expected_depth=10,  # actual depth: 6
    )

    # test notebook content
    pass  # TODO
