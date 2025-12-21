from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("tensor_hypercontraction", timeout_seconds=1801)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_prepare_part1"),
        expected_width=100,  # actual is 82
        expected_depth=5000,  # actual is 3576
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog_prepare_part2"),
        expected_width=120,  # actual is 93
        expected_depth=7000,  # actual is 5039
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog_select"),
        expected_width=130,  # actual is 108
        expected_depth=5000,  # actual is 3195
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=140,  # actual is 114
    )

    # test notebook content
    pass  # Todo
