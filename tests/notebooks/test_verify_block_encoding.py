from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("verify_block_encoding", timeout_seconds=120)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_pauli_be"),
        expected_width=10,  # actual 8
        expected_depth=800,  # actual 416
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_banded_be"),
        expected_width=15,  # actual 10
        expected_depth=1400,  # actual 834
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_pauli_sym_be"),
        expected_width=11,  # actual 9
        expected_depth=900,  # actual 493
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_banded_sym_be"),
        expected_width=16,  # actual 9
        expected_depth=3000,  # actual 1327
    )
