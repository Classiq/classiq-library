from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("quantum_counting", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_qpe"),
        expected_width=11,  # actual width: 11
        expected_depth=8100,  # actual depth: 8058
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_iqae"),
        expected_width=6,  # actual width: 6
        expected_depth=500,  # actual depth: 486
    )

    # test notebook content
    pass  # TODO
