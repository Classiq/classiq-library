from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hhl", timeout_seconds=312)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_hhl_exact"))
    validate_quantum_model(tb.ref("qmod_hhl_trotter"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_hhl_exact"),
        expected_width=7,  # actual width: 7
        expected_depth=500,  # actual depth: 468
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_hhl_trotter"),
        expected_width=7,  # actual width: 7
        expected_depth=5250,  # actual depth: 5074
    )

    # test notebook content
    pass  # TODO
