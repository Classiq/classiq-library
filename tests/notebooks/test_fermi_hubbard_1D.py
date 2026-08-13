from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("fermi_hubbard_1D", timeout_seconds=1801)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_state_check"),
        expected_width=None,
        expected_depth=None,
        expected_cx_count=None,
    )

    # test notebook content
    pass
