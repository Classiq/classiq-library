from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook(
    "rainbow_options_integration_method",
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
        expected_depth=1700,  # actual depth: 1456
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=tb.ref("MAX_WIDTH_2"),
        expected_depth=5500,  # actual depth: 4930
    )

    # test notebook content
    expected_payoff = 23.0238
    alpha_assertion = 1e-5

    measured_confidence = tb.ref("conf_interval[1] - conf_interval[0]")
    # based on e^2=(1/2N)*log(2T/alpha) from "Iterative Quantum Amplitude Estimation" since our alpha is low, we want to check within a bigger confidence interval
    confidence_scale_by_alpha = np.sqrt(np.log(tb.ref("ALPHA") / alpha_assertion))

    parsed_result = tb.ref("parsed_result")
    assert (
        np.abs(parsed_result - expected_payoff)
        <= 0.5 * measured_confidence * confidence_scale_by_alpha
    ), f"Payoff result is out of the {alpha_assertion*100}% confidence interval: |{parsed_result} - {expected_payoff}| > {0.5*measured_confidence * confidence_scale_by_alpha}"
