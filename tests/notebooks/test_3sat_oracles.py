from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("3sat_oracles", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:

    num_models = len(tb.ref("qmods"))
    actual_widths = [
        25,
        27,
        29,
        32,
        30,
        38,
        40,
        40,
        39,
        40,
        50,
        48,
        53,
        56,
        56,
        62,
        81,
        85,
        104,
        103,
        114,
        150,
        153,
    ]
    for i in range(num_models):
        # test models
        validate_quantum_model(tb.ref("qmods"[i]))
        # test quantum programs
        validate_quantum_program_size(
            tb.ref("qprogs"[i]),
            expected_width=int(
                actual_widths[i] * 1.5
            ),  # actual width: actual_widths[i]
            expected_depth=None,  # actual depth: 429
        )

    # test notebook content
    rounded_cl_times = [
        9.0,
        4.0,
        4.0,
        5.0,
        4.0,
        5.0,
        9.0,
        5.0,
        5.0,
        5.0,
        6.0,
        5.0,
        6.0,
        7.0,
        5.0,
        6.0,
        6.0,
        8.0,
        9.0,
        9.0,
        9.0,
        11.0,
        13.0,
    ]
    for i in range(num_models):
        assert tb.ref("cl_times"[i]) < 2 * rounded_cl_times[i]
