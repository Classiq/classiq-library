import numpy as np
from testbook.client import TestbookNotebookClient

from tests.utils_for_testbook import validate_quantum_program_size, wrap_testbook


@wrap_testbook("quantum_drude_oscillator", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=4,  # actual width: 4
        expected_depth=11,  # actual depth: 11
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog2"),
        expected_width=6,  # actual width: 6
        expected_depth=21,  # actual depth: 21
    )

    # test notebook content
    for duration in tb.ref("durations"):
        assert duration < 30  # locally it is no longer than 30 seconds
    for duration in tb.ref("durations2"):
        assert duration < 50  # locally it is no longer than 50 seconds

    assert np.isclose(
        tb.ref("VQE_energy")[-1], tb.ref("exact_energies")[-1], atol=0.01
    )  # should be atol=0.01
