from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qpe_for_molecule_with_qubitization", timeout_seconds=1801)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_qpe_walk"),
        expected_depth=6700,  # actual 4824
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_qpe_naive"),
        expected_depth=25000,  # actual 18772
    )
    # test notebook content
    pass  # Todo
