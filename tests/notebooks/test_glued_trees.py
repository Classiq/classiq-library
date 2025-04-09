from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("glued_trees", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    actual_widths = [10] * 13 + [20] * 13
    actual_depths = [1265] * 13 + [1321] * 13

    for qmod in tb.ref("qmods"):
        # test models
        validate_quantum_model(qmod)
    for qprog, e_width, e_depth in zip(tb.ref("qprogs"), actual_widths, actual_depths):
        # test quantum programs
        validate_quantum_program_size(
            qprog,
            expected_width=int(e_width * 1.5),  # 1.5* actual width
            expected_depth=int(e_depth * 1.5),  # 1.5* actual depth
        )
