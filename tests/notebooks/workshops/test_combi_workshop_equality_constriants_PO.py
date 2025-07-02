from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("combi_workshop_equality_constriants_PO", timeout_seconds=700)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=10,  # actual width: 6
        expected_depth=150,  # actual depth: 94
    )

    # test notebook content
    pass  # Todo
