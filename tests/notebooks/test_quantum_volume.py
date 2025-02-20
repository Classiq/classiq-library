from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook(
    "quantum_volume",
    timeout_seconds=516,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # need to rewrite the notebook
    # everything is inside functions, it's hard to test it
    pass
