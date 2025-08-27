from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "hidden_shift",
    timeout_seconds=272,  # we may lower this value
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_simple"))
    validate_quantum_model(tb.ref("qmod_complex"))
    validate_quantum_model(tb.ref("qmod_no_dual"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_simple"),
        expected_width=7,  # actual width: 7
        expected_depth=50,  # actual depth: 47
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_complex"),
        expected_width=27,  # actual width: 23
        expected_depth=1700,  # actual depth: 1656
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_no_dual"),
        expected_width=27,  # actual width: 22
        expected_depth=1700,  # actual depth: 1685
    )

    # test notebook content
    pass  # TODO
