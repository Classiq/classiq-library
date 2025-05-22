from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "approximated_state_preparation", timeout_seconds=3600
)  # took 1860 seconds on my computer
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    for qmod in tb.ref("qmods"):
        validate_quantum_model(qmod)

    # test quantum programs
    # classiq depths: [9874, 8721, 8259, 7908, 7677, 7447, 6986, 6755, 6525, 6295]
    # cx-counts depths: [6548, 5748, 5428, 5196, 5036, 4876, 4556, 4396, 4236, 4076]
    qprogs = tb.ref_pydantic("qprogs")
    depths = tb.ref("depths")
    validate_quantum_program_size(
        qprogs[0],
        expected_width=tb.ref("NUM_QUBITS"),
        expected_depth=10500,  # actual depth: 9874
    )
    for i in range(1, len(qprogs)):
        validate_quantum_program_size(
            qprogs[i],
            expected_width=tb.ref("NUM_QUBITS"),
            expected_depth=depths[i - 1]
            - 1,  # the depth has to improve from the previous runs
        )

    # test notebook content
    cx_counts = tb.ref("cx_counts")
    for i in range(1, len(cx_counts)):
        assert cx_counts[i] < cx_counts[i - 1]
