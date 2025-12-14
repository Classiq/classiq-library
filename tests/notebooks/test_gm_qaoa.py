from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("gm_qaoa", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_gmqaoa"),
        expected_width=None,
        expected_depth=None,
        expected_cx_count=None,
    )

    # test notebook content
    pass  # Todo
