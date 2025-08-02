from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import itertools


@wrap_testbook("discrete_quantum_walk_circle", timeout_seconds=1500)
def test_notebook(tb: TestbookNotebookClient) -> None:

    # test quantum programs

    ## width-optimized
    # classiq depths: [419, 749, 1195, 1773, 2499, 3389, 4099]
    expected_depths = [500, 1000, 1500, 2000, 2750, 3500, 4500]
    # classiq cx_counts: [274, 514, 850, 1298, 1874, 2594, 3194]
    expected_cx_counts = [500, 1000, 1500, 2000, 2750, 3500, 4500]
    # classiq widths: [6, 7, 8, 9, 10, 11, 13]

    for qprog, num_qubits, expected_depth, expected_cx_count in zip(
        tb.ref_pydantic("qprogs_width"),
        range(tb.ref("NUM_QUBITS_MIN"), tb.ref("NUM_QUBITS_MAX")),
        expected_depths,
        expected_cx_counts,
    ):
        validate_quantum_program_size(
            qprog,
            expected_width=num_qubits + 2,
            expected_depth=expected_depth,
            expected_cx_count=expected_cx_count,
        )
    """
    classiq depths: [193, 245, 335, 419, 509, 602, 704]
    classiq cx_counts: [120, 152, 200, 260, 352, 436, 552]
    classiq widths: [8, 9, 11, 12, 14, 15, 17]
    """
    ## cx-optimized
    # classiq depths: [193, 245, 335, 419, 509, 602, 704]
    expected_depths = [250, 350, 450, 500, 550, 650, 750]
    # classiq cx_counts: [120, 152, 200, 260, 352, 436, 552]
    expected_cx_counts = [150, 200, 250, 300, 400, 500, 600]
    # classiq widths: [8, 9, 11, 12, 14, 15, 17]

    for qprog, num_qubits, expected_depth, expected_cx_count in zip(
        tb.ref_pydantic("qprogs_cx"),
        range(tb.ref("NUM_QUBITS_MIN"), tb.ref("NUM_QUBITS_MAX")),
        expected_depths,
        expected_cx_counts,
    ):
        validate_quantum_program_size(
            qprog,
            expected_width=2
            * num_qubits,  # that's the width that's being set as a constraint in the notebook
            expected_depth=expected_depth,
            expected_cx_count=expected_cx_count,
        )
