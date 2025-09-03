from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qls_qsvt", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_banded"),
        expected_width=9,  # actual 7
        expected_depth=120000,  # actual 61666
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_pauli"),
        expected_width=11,  # actual 9
        expected_depth=120000,  # actual 65325
    )
