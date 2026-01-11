from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qsvm", timeout_seconds=270)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_bloch"),
        expected_width=1,  # actual width: 1
        expected_depth=10,  # actual depth: 4
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_pauli"),
        expected_width=4,  # actual width: 2
        expected_depth=50,  # actual depth: 30
    )
    # test notebook content
    assert tb.ref("test_score") >= 0.98
    assert tb.ref("test_score_pauli") >= 0.98
