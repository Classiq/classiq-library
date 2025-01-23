from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("shor", timeout_seconds=104)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=12,  # actual width: 12
        expected_depth=1111,  # actual depth: 1099
    )

    # test notebook content
    pass  # TODO


@wrap_testbook("shor_modular_exponentiation", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_1"),
        expected_width=8,  # actual width: 8
        expected_depth=300,  # actual depth: 296
    )
    validate_quantum_program_size(
        tb.ref("qprog_2"),
        expected_width=22,  # actual width: 22
        expected_depth=30000,  # actual depth: 26607
    )

    # test notebook content
    pass  # TODO
