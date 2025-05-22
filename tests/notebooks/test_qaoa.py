from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qaoa", timeout_seconds=450)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=9,  # actual width: 7
        expected_depth=1250,  # actual depth: 1072
    )

    # test notebook content
    assert tb.ref("depth_classiq") < tb.ref("depth_qiskit")
    assert tb.ref("cx_counts_classiq") < tb.ref("cx_counts_qiskit")
