from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("quantum_oracle_sketching_boolean", timeout_seconds=800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=5,  # actual width: 4
        expected_depth=7000,  # actual depth: 6197
    )

    # test notebook content
    pass  # Todo
