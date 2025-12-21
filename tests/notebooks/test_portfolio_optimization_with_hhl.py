from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("portfolio_optimization_with_hhl", timeout_seconds=900)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_qpe"),
        expected_width=8,  # actual 6
        expected_depth=500,  # actual 215
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_feed_forward_hhl"),
        expected_width=16,  # actual 12
        expected_depth=500,  # actual 416
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_hhl_optimized_width"),
        expected_width=12,  # actual 9
        expected_depth=750,  # actual 443
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_hhl_basic"),
        expected_width=12,  # actual 10
        expected_depth=750,  # actual 417
    )

    fidelity_basic = tb.ref("fidelity_basic")
    fidelity_C = tb.ref("fidelity_C")

    assert fidelity_basic > 0.8
    assert fidelity_C > 0.8
