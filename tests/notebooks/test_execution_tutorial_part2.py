from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("execution_tutorial_part2", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("execution_tutorial_part2"))
    validate_quantum_model(tb.ref("execution_tutorial_part2_bell"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=2,
        expected_depth=3,
    )
    validate_quantum_program_size(
        tb.ref("qprog_bell"),
        expected_width=2,
        expected_depth=3,
    )

    # test notebook content
    first_estimate = tb.ref("first_estimate")
    tolerance = 0.1 #This value can be reduced if we increase the number of shots on the execution preferences.
    np.isclose(first_estimate, 0.20, atol=tolerance)