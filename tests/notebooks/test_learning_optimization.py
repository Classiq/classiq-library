from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "learning_optimization", timeout_seconds=100
)  # 2025.03.06 bump from 80 seconds
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=10,  # actual width: 8
        expected_depth=60,  # actual depth: 44
    )

    # test notebook content
    pass  # Todo
