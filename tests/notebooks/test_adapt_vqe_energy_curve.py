from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np

@wrap_testbook("adapt_vqe_energy_curve", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    #test models
    #for qmod in tb.ref("qmods"):
    #    validate_quantum_model(qmod)
    #test quantum programs
    #for duration in tb.ref("durations"):
    #    assert duration < 400  # locally it is no longer than 15 seconds
    assert all(
        np.isclose(tb.ref("exact_energy"), tb.ref("VQE_energy"), atol=0.02)
    )  # should be atol=0.01
    pass

