from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hhl_workshop", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_b_load"))
    validate_quantum_model(tb.ref("qmod_hhl"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_b_load"),
        expected_width=3,  # actual width: 2
        expected_depth=15,  # actual depth: 9
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_hhl"),
        expected_width=10,  # actual width: 7
        expected_depth=550,  # actual depth: 468
    )

    # test notebook content
    pass  # Todo
