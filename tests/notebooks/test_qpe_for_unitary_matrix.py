from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qpe_for_unitary_matrix", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:

    for qmod in tb.ref("qmods"):
        # test models
        validate_quantum_model(qmod)

    actual_widths = [3 + precision for precision in tb.ref("precisions")]
    for qprog, e_width, e_depth in zip(
        tb.ref_pydantic("qprogs"), actual_widths, tb.ref("classiq_depths")
    ):
        # test quantum programs
        validate_quantum_program_size(
            qprog,
            expected_width=e_width,  # expect to be exact
            expected_depth=int(e_depth * 1.5),  # 1.5* actual depth
        )

    # test notebook content
    for cx_count_classiq, cx_count_qiskit in zip(
        tb.ref("classiq_cx_counts"),
        tb.ref("qiskit_cx_counts"),
    ):
        assert cx_count_classiq < cx_count_qiskit

    for depth_classiq, depth_qiskit in zip(
        tb.ref("classiq_depths"),
        tb.ref("qiskit_depths"),
    ):
        assert depth_classiq < depth_qiskit
