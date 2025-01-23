from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "3_sat_grover",
    timeout_seconds=36,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    validate_quantum_model(tb.ref("qmod_large"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=10,  # actual width: 10
        expected_depth=450,  # actual depth: 429
    )
    validate_quantum_program_size(
        tb.ref("qprog_large"),
        expected_width=20,  # actual width: 19
        expected_depth=2500,  # actual depth: 2375
    )

    # test notebook content
    pass  # TODO
