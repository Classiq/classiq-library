from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "approximated_state_preparation", timeout_seconds=3600
)  # took 1860 seconds on my computer
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    # The depth has to improve from the previous runs.
    qprogs = tb.ref_pydantic("qprogs")
    depths = tb.ref("depths")
    cx_counts = tb.ref("cx_counts")
    validate_quantum_program_size(
        qprogs[0],
        expected_width=tb.ref("NUM_QUBITS"),
        expected_depth=600,  # actual depth: 493
        expected_cx_count=350,  # actual cx: 254
    )
    for i in range(1, len(qprogs)):
        validate_quantum_program_size(
            qprogs[i],
            expected_width=tb.ref("NUM_QUBITS"),
            expected_depth=depths[
                i - 1
            ],  # the depth has to improve from the previous runs
            expected_cx_count=cx_counts[i - 1],
        )
