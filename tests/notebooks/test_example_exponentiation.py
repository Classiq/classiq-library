from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("example_exponentiation", timeout_seconds=216)
def test_notebook(tb: TestbookNotebookClient) -> None:
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=15,  # actual width: 12
        expected_depth=1750,  # actual depth: 1451
    )
