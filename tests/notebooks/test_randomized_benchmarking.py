from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook(
    "randomized_benchmarking",
    timeout_seconds=60,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    for qmod in tb.ref("qmods"):
        validate_quantum_model(qmod)
    # test quantum programs
    for qprog in tb.ref("quantum_programs"):
        validate_quantum_program_size(
            qprog,
            expected_width=None,
            expected_depth=None,
        )

    # test notebook content
    pass  # Todo
