from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hardware_aware_mcx", timeout_seconds=56)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_linear"),
        expected_width=20,  # actual width: 17
        expected_depth=2200,  # actual depth: 1677 or 1993
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_all_to_all"),
        expected_width=20,  # actual width: 18
        expected_depth=1000,  # actual depth: 828
    )

    # test notebook content
    pass  # Todo
