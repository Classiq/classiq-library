import numpy as np

from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("vlasov_ampere", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test notebook content
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_be"),
        expected_width=20,  # actual width: 17
        expected_depth=1900,  # actual depth: 1687
    )

    # mat_be = full_be_encoding.to_matrix() already returns the physical (alpha-scaled)
    # matrix directly, so it compares to mat_classical with no separate norm factor.
    measured_be = tb.ref_numpy("mat_be")
    classical_be = tb.ref_numpy("mat_classical")
    phase = np.angle(measured_be[0, 0] / classical_be[0, 0])
    assert np.allclose(measured_be * np.exp(-1j * phase), classical_be, atol=1e-2)
