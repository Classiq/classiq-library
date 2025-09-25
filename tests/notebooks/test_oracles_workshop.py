from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("oracles_workshop", timeout_seconds=100)
def test_notebook(tb: TestbookNotebookClient) -> None:
    def test_notebook(tb: TestbookNotebookClient) -> None:
        # test quantum programs
        validate_quantum_program_size(
            tb.ref_pydantic("qprog_oracle"),
            expected_width=10,  # actual 7
            expected_depth=120,  # actual 79
        )
        validate_quantum_program_size(
            tb.ref_pydantic("qprog_phase_kickback"),
            expected_width=10,  # actual 7
            expected_depth=400,  # actual 240
        )
        validate_quantum_program_size(
            tb.ref_pydantic("qprog_deutsch_jozsa"),
            expected_width=10,  # actual 4
            expected_depth=80,  # actual 10
        )
        validate_quantum_program_size(
            tb.ref_pydantic("qprog_grover"),
            expected_width=15,  # actual 7
            expected_depth=500,  # actual 283
        )

    # test notebook content
    pass
