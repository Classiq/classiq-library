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
    # no qmods are created (synthesized directly from main)
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=2,
        expected_depth=3,
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_bell"),
        expected_width=2,
        expected_depth=3,
    )
