from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("heat_eq_qsvt", timeout_seconds=600 * 10)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=13,
        expected_depth=None,
        expected_cx_count=None,
    )

    norm_factor = tb.ref("norm_factor")
    results = tb.ref("results")

    assert 1 > (norm_factor * results[0][4]) > 0.7
    assert 0.2 > (norm_factor * results[1][4]) > 0.01
