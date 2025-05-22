from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("molecular_energy_curve", timeout_seconds=1200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    for qmod in tb.ref("qmods"):
        validate_quantum_model(qmod)
    # test quantum programs
    for qprog in tb.ref_pydantic("qprogs"):
        validate_quantum_program_size(
            qprog,
            expected_width=16,  # actual width: 16
            expected_depth=12000,  # actual depth: 11538
        )

    # test notebook content
    for duration in tb.ref("durations"):
        assert duration < 40  # locally it is no longer than 15 seconds

    assert all(
        np.isclose(tb.ref("exact_energy"), tb.ref("VQE_energy"), atol=0.02)
    )  # should be atol=0.01
