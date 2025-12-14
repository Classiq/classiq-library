from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("network_traffic_optimization", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=30,  # actual width: 24
        expected_depth=300,  # actual depth: 126
    )

    # test notebook content
    pass  # Todo
