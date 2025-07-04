from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("example_exponentiation", timeout_seconds=216)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=15,  # actual width: 12
        expected_depth=1750,  # actual depth: 1451
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_minimize_error"),
        expected_width=10,  # actual width: 8
        expected_depth=350,  # actual depth: 301
    )

    # test notebook content
    pass  # Todo
