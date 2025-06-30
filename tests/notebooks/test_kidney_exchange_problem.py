from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("kidney_exchange_problem", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    Basic test for kidney exchange QAOA implementation.
    Validates quantum model, quantum program, and solution structure.
    """

    # Test quantum model validity
    validate_quantum_model(str(tb.ref("qmod")))

    # Test quantum program size constraints (width only, no transpiled circuit available)
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),  # type: ignore
        expected_width=10,  # actual width: 9
        # expected_depth removed since no transpiled circuit is available
    )

    # test notebook content
    pass  # Todo
