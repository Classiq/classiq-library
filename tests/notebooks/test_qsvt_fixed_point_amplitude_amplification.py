from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np
import scipy


@wrap_testbook(
    "qsvt_fixed_point_amplitude_amplification",
    timeout_seconds=376,
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
        tb.ref("qprog"),
        expected_width=13,  # actual width: 11
        expected_depth=18000,  # actual depth: 15432
    )

    # test notebook content
    measured_good_shots = tb.ref("measured_good_shots")
    p_good_shot = tb.ref("p_good_shot")
    num_shots = tb.ref("NUM_SHOTS")
    assert np.isclose(
        measured_good_shots,
        num_shots * p_good_shot,
        atol=5 * scipy.stats.binom.std(num_shots, p_good_shot),
    )
