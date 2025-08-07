import numpy as np

from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("vlasov_ampere", timeout_seconds=1200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test notebook content
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_be"),
        expected_width=25,  # actual width: 25
        expected_depth=2300,  # actual depth: 2181
    )

    measured_be = tb.ref_numpy("mat_be")
    classical_be = tb.ref_numpy("mat_classical")
    norm_factor = tb.ref("BE_NORM_FACTOR")
    phase = np.angle(measured_be[0, 0] / classical_be[0, 0])
    assert np.allclose(measured_be * norm_factor * np.exp(-1j * phase), classical_be)
