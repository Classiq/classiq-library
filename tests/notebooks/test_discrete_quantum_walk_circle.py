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
    # classiq depths: [407, 727, 1161, 1725, 2435, 3307, 4357]
    expected_depths = [500, 900, 1400, 2000, 2800, 3800, 5000]
    # classiq cx_counts: [272, 512, 848, 1296, 1872, 2592, 3472]
    expected_cx_counts = [350, 650, 1050, 1550, 2200, 3000, 4000]
    # classiq widths: [6, 7, 8, 9, 10, 11, 12]

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
    ## cx-optimized
    # classiq depths: [183, 269, 345, 481, 557, 681, 761]
    expected_depths = [230, 330, 420, 580, 680, 820, 920]
    # classiq cx_counts: [108, 168, 216, 318, 366, 504, 552]
    expected_cx_counts = [140, 210, 270, 390, 450, 610, 670]
    # classiq widths: [7, 9, 10, 12, 13, 15, 16]

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
