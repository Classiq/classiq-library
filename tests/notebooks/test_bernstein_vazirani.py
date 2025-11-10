from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("bernstein_vazirani", timeout_seconds=30)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=6,
        expected_depth=5,
    )

    # test notebook content
    assert int(tb.ref_numpy("secret_integer_q")) == tb.ref("SECRET_INT")
