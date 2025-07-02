from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("3sat_oracles", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    expected_widths = [
        25,
        25,
        27,
        33,
        35,
        34,
        36,
        37,
        40,
        48,
        47,
        45,
        53,
        55,
        64,
        72,
        70,
        82,
        100,
        101,
        110,
        118,
        136,
        137,
    ]

    for qmod in tb.ref("qmods"):
        validate_quantum_model(qmod)
    for qprog, expected_width in zip(tb.ref_pydantic("qprogs"), expected_widths):
        validate_quantum_program_size(
            qprog,
            expected_width=expected_width + 5,  # actual width + 5
            expected_depth=None,  # actual depth: 0
            allow_zero_size=True,
        )

    # test notebook content
    for cl_time in tb.ref("cl_times"):
        assert cl_time < 30  # actual time is less than 15 sec for all models
