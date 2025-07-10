from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np


@wrap_testbook("rainbow_options_direct_method", timeout_seconds=1000)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=tb.ref("MAX_WIDTH"),
        expected_depth=5000,  # actual depth: 4320
    )

    # test notebook content
    parsed_result = tb.ref("parsed_result")
    conf_interval = tb.ref("conf_interval")
    ALPHA = tb.ref("ALPHA")
    expected_payoff = tb.ref("expected_payoff")
    ALPHA_ASSERTION = tb.ref("ALPHA_ASSERTION")
    measured_confidence = conf_interval[1] - conf_interval[0]
    confidence_scale_by_alpha = np.sqrt(
        np.log(ALPHA / ALPHA_ASSERTION)
    )  # based on e^2=(1/2N)*log(2T/alpha) from "Iterative Quantum Amplitude Estimation" since our alpha is low, we want to check within a bigger confidence interval
    assert (
        np.abs(parsed_result - expected_payoff)
        <= 0.5 * measured_confidence * confidence_scale_by_alpha
    ), f"Payoff result is out of the {ALPHA_ASSERTION*100}% confidence interval: |{parsed_result} - {expected_payoff}| > {0.5*measured_confidence * confidence_scale_by_alpha}"
