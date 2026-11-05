from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

from classiq import assign_parameters


@wrap_testbook("early_fault_tolerant_qpe", timeout_seconds=1200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    # the TFIM program is parametric in k; check the deepest circuit, k = D_TFIM - 1
    validate_quantum_program_size(
        assign_parameters(tb.ref_pydantic("qprog_tfim"), {"k": tb.ref("D_TFIM - 1")}),
        expected_width=4,  # actual width: 3
        expected_depth=7000,  # actual depth: 5902
        expected_cx_count=4000,  # actual cx count: 3306
    )

    # test notebook content
    # rough tolerance: the demo uses relaxed parameters, so the target precision is not guaranteed
    tolerance = 0.05  # Ha
    assert abs(tb.ref("gs_tfim") - tb.ref("gs_true_tfim")) < tolerance
    assert abs(tb.ref("gs_h4") - tb.ref("gs_true_h4")) < tolerance
