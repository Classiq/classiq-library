from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("Qmod_tutorial_part2", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # todo: Has many overwrites of `qmod` and `qprog`
    #   as well as many missing places of "put your code"

    # test models
    validate_quantum_model(tb.ref("qmod"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=5,  # actual width: 3
        expected_depth=40,  # actual depth: 22
    )

    # test notebook content
    pass  # Todo
