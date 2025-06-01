from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "solving_qlsp_with_aqc",
    timeout_seconds=800,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    validate_quantum_model(tb.ref("qmod_3"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=3,  # actual width: 3
        expected_depth=35000,  # actual depth: 33308
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=3,  # actual width: 3
        expected_depth=35000,  # actual depth: 33308
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_3"),
        expected_width=3,  # actual width: 3
        expected_depth=70000,  # actual depth: 67208
    )

    # test notebook content
    pass  # TODO
