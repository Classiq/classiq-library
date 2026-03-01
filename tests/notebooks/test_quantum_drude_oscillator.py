import numpy as np
from testbook.client import TestbookNotebookClient

from tests.utils_for_testbook import validate_quantum_program_size, wrap_testbook


@wrap_testbook("quantum_drude_oscillator", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    for qprog in tb.ref_pydantic("qprogs"):
        validate_quantum_program_size(
            qprog,
            expected_width=4,  # actual width: 4
            expected_depth=85000,  # actual depth: 83651
        )

    # test notebook content
    for duration in tb.ref("durations"):
        assert duration < 50  # locally it is no longer than 50 seconds

    assert np.isclose(
        tb.ref("VQE_energy")[-1], tb.ref("exact_energies")[-1], atol=0.01
    )  # should be atol=0.01
