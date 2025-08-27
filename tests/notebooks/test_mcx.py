from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "mcx", timeout_seconds=350
)  # changed timeout due to additional time synthesis needs with optimization parameter
def test_notebook(tb: TestbookNotebookClient) -> None:

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=tb.ref("MAX_WIDTH_1"),
        expected_depth=125,  # actual depth: 94
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=tb.ref("MAX_WIDTH_2"),
        expected_depth=500,  # actual depth: 391
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_3"),
        expected_width=tb.ref("MAX_WIDTH_3"),
        expected_depth=250,  # actual depth: 221
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_4"),
        expected_width=80,  # actual width: 69
        expected_depth=1700,  # actual depth: 494 ; also was 920; also was 1550
    )

    # test notebook content
    pass  # Todo
