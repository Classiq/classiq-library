from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("shor", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum program
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=26,  # actual width: 26
        expected_depth=60000,  # actual depth: 52721
    )

    # test notebook content
    positions = tb.ref("positions")
    f1, f2 = tb.ref("factor1"), tb.ref("factor2")
    assert f1 * f2 == 21

    for p in positions:
        assert (p * 6).is_integer()
