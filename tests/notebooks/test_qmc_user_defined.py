from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qmc_user_defined", timeout_seconds=176)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("model"))
    validate_quantum_model(tb.ref("model_2"))
    validate_quantum_model(tb.ref("model_3"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=4,  # actual width: 4
        expected_depth=150,  # actual depth: 104
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=5,  # actual width: 4
        expected_depth=350,  # actual depth: 236
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_3"),
        expected_width=7,  # actual width: 7
        expected_depth=2500,  # actual depth: 2008
    )

    # test notebook content
    pass  # TODO
