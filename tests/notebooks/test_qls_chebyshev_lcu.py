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
        expected_width=15,  # actual 13
        expected_depth=90000,  # actual 45643
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_cheb_lcu_pauli"),
        expected_width=15,  # actual 13
        expected_depth=50000,  # actual 20578
    )
