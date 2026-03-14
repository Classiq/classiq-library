from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("rainbow_options_workshop_bruteforce", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs state preparation of the iqae
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=23,
    )
    # test quantum program of full the iqae
    validate_quantum_program_size(
        tb.ref_pydantic("iqae_qprog"),
        expected_width=25,
    )

    pass  # Todo
