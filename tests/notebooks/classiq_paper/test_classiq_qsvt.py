from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("classiq_qsvt", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=30,  # actual width: 18
        expected_depth=1400,  # actual depth: 701
    )

    # test notebook content
    pass  # TODO
