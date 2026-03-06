import numpy as np
from testbook.client import TestbookNotebookClient

from tests.utils_for_testbook import validate_quantum_program_size, wrap_testbook


@wrap_testbook("quantum_walk_fmo", timeout_seconds=100)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum program
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=3,  # actual width: 3
        expected_depth=None,
        expected_cx_count=None,
    )

    # test notebook content
    for duration in tb.ref("durations"):
        assert duration < 5  # locally it is no longer than 5 seconds

    assert np.isclose(
        tb.ref("trotter_results")[0][0],
        tb.ref("probs")[0][0],
        atol=0.01,
    )  # should be atol=0.01
