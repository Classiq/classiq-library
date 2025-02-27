from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("discrete_quantum_walk_circle", timeout_seconds=400)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    for qmod in itertools.chain(
        tb.ref("qmods"),
        tb.ref("qmods_width"),
        tb.ref("qmods_cx"),
    ):
        validate_quantum_model(qmod)

    # test quantum programs
    """
    classiq depths: [419, 749, 1195, 1773, 2499, 3389, 4099]
    classiq cx_counts: [274, 514, 850, 1298, 1874, 2594, 3194]
    classiq widths: [6, 7, 8, 9, 10, 11, 13]
    """
    for qprog, num_qubits in zip(
        tb.ref("qprogs_width"),
        range(tb.ref("NUM_QUBITS_MIN"), tb.ref("NUM_QUBITS_MAX")),
    ):
        validate_quantum_program_size(
            qprog,
            expected_width=None,
            expected_depth=None,
        )
    """
    classiq depths: [193, 245, 335, 419, 509, 602, 704]
    classiq cx_counts: [120, 152, 200, 260, 352, 436, 552]
    classiq widths: [8, 9, 11, 12, 14, 15, 17]
    """
    for qprog in tb.ref("qprogs_cx"):
        validate_quantum_program_size(
            qprog,
            expected_width=2
            * num_qubits,  # that's the width that's being set as a constraint in the notebook
            expected_depth=None,
        )

    # test notebook content
    pass  # Todo
