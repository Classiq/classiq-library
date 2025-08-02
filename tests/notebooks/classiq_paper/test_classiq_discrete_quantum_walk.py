from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("classiq_discrete_quantum_walk", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=20,  # actual width: 9
        expected_depth=500,  # actual depth: 243
    )

    # test notebook content
    pass  # TODO
