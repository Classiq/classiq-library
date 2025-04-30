from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

@wrap_testbook("adapt_vqe_energy_curve", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test models
#    for qmod in tb.ref("qmods"):
#        validate_quantum_model(qmod)
    # test quantum programs
    #validate_quantum_program_size(
    #    tb.ref("model"),
    #    expected_width=1,  # actual width: 1
    #    expected_depth=10,  # actual depth: 4
    )
    # test notebook content
    pass  # TODO
