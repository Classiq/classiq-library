from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("quantum_volume", timeout_seconds=516)
def test_notebook(tb: TestbookNotebookClient) -> None:

    actual_widths = [3] * 10 + [4] * 10 + [5] * 10 + [6] * 10
    actual_depths = [19] * 10 + [25] * 10 + [31] * 10 + [37] * 10
    for qprog, e_width, e_depth in zip(
        tb.ref_pydantic("qprogs"), actual_widths, actual_depths
    ):
        # test quantum programs
        validate_quantum_program_size(
            qprog,
            expected_width=e_width,  # not expected to change
            expected_depth=int(e_depth * 1.5),  # 1.5* actual depth
        )
