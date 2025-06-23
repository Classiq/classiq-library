from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("combi_workshop_Inequality_constriants_PO", timeout_seconds=700)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=13,  # actual width: 9
        expected_depth=180,  # actual depth: 137
    )

    # test notebook content
    pass  # Todo
