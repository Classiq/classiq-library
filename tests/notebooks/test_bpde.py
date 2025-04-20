import numpy as np
from testbook.client import TestbookNotebookClient

from tests.utils_for_testbook import (
    validate_quantum_model,
    validate_quantum_program_size,
    wrap_testbook,
)


@wrap_testbook("bpde", timeout_seconds=1200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    for qmod in tb.ref("QMODS"):
        validate_quantum_model(qmod)
    # test quantum programs
    for qprog in tb.ref("QPROGS"):
        validate_quantum_program_size(
            qprog,
            expected_width=2,  # actual width: 2
            expected_depth=85000,  # actual depth: 83651
        )

    # test notebook content
    for duration in tb.ref("DURATIONS"):
        assert duration < 500  # locally it is no longer than 200 seconds

    assert np.isclose(
        tb.ref("calculated_energy_gradient"),
        tb.ref("total_energy_gaps")[10],
        atol=0.01,
    )  # should be atol=0.01
