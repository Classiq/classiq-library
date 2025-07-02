from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qgan_bars_and_strips", timeout_seconds=360)
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
        expected_width=5,  # actual width: 4
        expected_depth=20,  # actual depth: 12
    )

    # test notebook content
    assert 0.5 < tb.ref("accuracy_classical") < 0.9
    assert tb.ref("accuracy") == 1
