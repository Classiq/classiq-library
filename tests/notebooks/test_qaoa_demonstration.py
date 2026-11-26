from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qaoa_demonstration", timeout_seconds=450)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=9,  # actual width: 7
        expected_depth=1300,  # actual depth: 1151-1185
    )

    # test notebook content
    assert tb.ref("depth_classiq") < tb.ref("depth_qiskit")
    assert tb.ref("cx_counts_classiq") < tb.ref("cx_counts_qiskit")
