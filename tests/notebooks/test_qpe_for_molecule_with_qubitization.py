from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qpe_for_molecule_with_qubitization", timeout_seconds=1801)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_qpe_walk"),
        expected_depth=7300,  # actual 6670
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_qpe_naive"),
        expected_depth=29000,  # actual 26347
    )
    # test notebook content
    pass  # Todo
