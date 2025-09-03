from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qls_chebyshev_lcu", timeout_seconds=800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_cheb_lcu_banded"),
        expected_width=20,  # actual 17
        expected_depth=120000,  # actual 60330
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_cheb_lcu_pauli"),
        expected_width=17,  # actual 15
        expected_depth=50000,  # actual 17963
    )
