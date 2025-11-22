import math
from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("3sat_oracles", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    expected_widths = [
        39,  # 25
        43,  # 25
        47,  # 27
        51,  # 33
        55,  # 35
        59,  # 34
        63,  # 36
        67,  # 37
        71,  # 40
        75,  # 48
        79,  # 47
        83,  # 45
        87,  # 53
        95,  # 55
        103,  # 64
        119,  # 72
        131,  # 70
        151,  # 82
        167,  # 100
        191,  # 101
        211,  # 110
        239,  # 118
        267,  # 136
        # 137,
    ]

    for qmod in tb.ref("qmods"):
        validate_quantum_model(qmod)
    for qprog, expected_width in zip(tb.ref_pydantic("qprogs"), expected_widths):
        # 10% buffer, plus flat 5 for the shorter ones
        expected_width = math.ceil(1.1 * expected_width + 5)

        validate_quantum_program_size(
            qprog,
            expected_width=expected_width + 5,  # actual width + 5
            expected_depth=None,  # actual depth: 0
            allow_zero_size=True,
        )

    # test notebook content
    for cl_time in tb.ref("cl_times"):
        assert cl_time < 30  # actual time is less than 15 sec for all models
