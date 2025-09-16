from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("time_marching", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    validate_quantum_model(tb.ref("qmod_naive"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=20,  # actual width: 16
        expected_depth=22000,  # actual depth: 18687
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_naive"),
        expected_width=20,  # actual width: 16
        expected_depth=3500,  # actual depth: 2913
    )

    # test notebook content
    for amplitude_amplified, amplitude_naive in zip(
        tb.ref("amplitudes_amplified"), tb.ref("amplitudes_naive")
    ):
        # should be a factor of 10 larger, taking some buffer.
        assert amplitude_naive - 0.1 * amplitude_amplified < 1e-2

    assert tb.ref("np.linalg.norm(sampled - expected)") < 0.1
