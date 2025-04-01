from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qpe_for_unitary_matrix", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # the `qmod`s and `qprog`s are in a for-loop
    # need to rewrite the notebook in order to test them

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
