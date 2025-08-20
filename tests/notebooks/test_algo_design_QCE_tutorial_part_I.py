from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("algo_design_QCE_tutorial_part_I", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    # validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=None,
        expected_depth=None,
    )

    # test notebook content
    pass  # Todo
