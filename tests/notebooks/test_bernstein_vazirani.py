from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    test_notebook,
)
from testbook.client import TestbookNotebookClient


@test_notebook("bernstein_vazirani", timeout_seconds=20)
def test_bernstein_vazirani(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(tb.ref("qprog"), expected_width=6, expected_depth=5)

    # test notebook content
    assert int(tb.ref("secret_integer_q")) == tb.ref("SECRET_INT")
