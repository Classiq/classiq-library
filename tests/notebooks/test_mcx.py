from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("mcx", timeout_seconds=236)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    validate_quantum_model(tb.ref("qmod_3"))
    validate_quantum_model(tb.ref("qmod_4"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_1"),
        expected_width=tb.ref("MAX_WIDTH_1"),
        expected_depth=125,  # actual depth: 94
    )
    validate_quantum_program_size(
        tb.ref("qprog_2"),
        expected_width=tb.ref("MAX_WIDTH_2"),
        expected_depth=500,  # actual depth: 391
    )
    validate_quantum_program_size(
        tb.ref("qprog_3"),
        expected_width=tb.ref("MAX_WIDTH_3"),
        expected_depth=250,  # actual depth: 221
    )
    validate_quantum_program_size(
        tb.ref("qprog_4"),
        expected_width=80,  # actual width: 69
        expected_depth=1500,  # actual depth: 494 ; also was 920
    )

    # test notebook content
    pass  # Todo
