from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("randomized_benchmarking", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    for qprog in tb.ref_pydantic("quantum_programs"):
        # generated qasm should contains more than 10 lines for any case
        assert len([line for line in qprog.qasm.splitlines() if line.strip()]) > 10
