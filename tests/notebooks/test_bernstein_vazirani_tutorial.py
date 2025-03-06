from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("bernstein_vazirani_tutorial", timeout_seconds=30)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=6,  # actual width: 6
        expected_depth=5,  # actual depth: 5
    )

    # test notebook content
    assert np.floor(np.log2(tb.ref("SECRET_INT")) + 1) <= tb.ref(
        "STRING_LENGTH"
    ), "The STRING_LENGTH cannot be smaller than the secret string length"

    assert tb.ref("secret_integer_q") == tb.ref("SECRET_INT")
    assert tb.ref("result.parsed_counts[0].shots / NUM_SHOTS") == 1
