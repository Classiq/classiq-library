from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("high_level_modeling_flexible_qpe", timeout_seconds=100)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=10,  # actual width: 7
        expected_depth=2300,  # actual depth: 2053
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=15,  # actual width: 13
        expected_depth=3500,  # actual depth: 3400, previous depth before degradation: 2339
    )

    # test notebook content
    pass  # Todo
