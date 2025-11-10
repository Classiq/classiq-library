from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("deutsch_jozsa", timeout_seconds=48)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=12,  # actual width 10
        expected_depth=500,  # actual depth 239
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=19,  # actual width constrained to 19
        expected_depth=1200,  # actual depth 679
    )

    # test notebook content
    assert 0 not in tb.ref("results_list_1"), "The function is not balanced as expected"
    assert 0 not in tb.ref("results_list_2"), "The function is not balanced as expected"
