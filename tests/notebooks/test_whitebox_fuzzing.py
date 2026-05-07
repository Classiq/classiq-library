from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("whitebox_fuzzing", timeout_seconds=720)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_oracle"),
        expected_width=tb.ref("MAX_WIDTH_ORACLE"),
        expected_depth=700,  # actual depth: 603
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_grover"),
        expected_width=tb.ref("MAX_WIDTH_GROVER"),
        expected_depth=20000,  # actual depth: 18523
    )

    # test notebook content
    pass  # Todo
