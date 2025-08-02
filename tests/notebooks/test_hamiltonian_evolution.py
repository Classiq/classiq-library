from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hamiltonian_evolution", timeout_seconds=2400)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    for qprog in tb.ref_pydantic("all_qprogs"):
        validate_quantum_program_size(
            qprog,
            expected_width=None,
            expected_depth=None,
        )

    # test notebook content
    for cx_count_classiq, cx_count_qiskit in zip(
        tb.ref("classiq_cx_counts"),
        tb.ref("qiskit_cx_counts"),
    ):
        assert cx_count_qiskit <= cx_count_qiskit
