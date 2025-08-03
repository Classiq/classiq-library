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
    # classiq depths: [114, 8662, 7853, 7622, 7392, 6932, 6702, 6472, 6241, 6010]
    # cx-counts depths: [62, 5722, 5171, 5011, 4851, 4531, 4371, 4211, 4051, 3891]
    # The depth has to improve from the previous runs. The difference between runs 0 and 1 is an exception,
    # since for 0 error we use a different algorithm for exact state preparation.
    qprogs = tb.ref_pydantic("qprogs")
    depths = tb.ref("depths")
    validate_quantum_program_size(
        qprogs[0],
        expected_width=tb.ref("NUM_QUBITS"),
        expected_depth=300,  # actual depth: 114
    )
    validate_quantum_program_size(
        qprogs[1],
        expected_width=tb.ref("NUM_QUBITS"),
        expected_depth=10000,  # actual depth: 8662
    )
    for i in range(2, len(qprogs)):
        validate_quantum_program_size(
            qprogs[i],
            expected_width=tb.ref("NUM_QUBITS"),
            expected_depth=depths[i - 1]
            - 1,  # the depth has to improve from the previous runs
        )

    # test notebook content
    cx_counts = tb.ref("cx_counts")
    for i in range(2, len(cx_counts)):
        assert cx_counts[i] < cx_counts[i - 1]
