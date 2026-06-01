from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("glued_trees", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # 6-qubit circuit recalculates with all ~1088 terms; depth is not fixed, only validate width
    # 20-qubit circuit uses cached 200-term Hamiltonian; actual depth: ~2626
    actual_widths = [6, 20]
    actual_depths = [29122, 13104]

    for qprog, e_width, e_depth in zip(
        tb.ref_pydantic("qprogs"), actual_widths, actual_depths
    ):
        validate_quantum_program_size(
            qprog,
            expected_width=int(e_width * 1.5),  # 1.5* actual width
            expected_depth=int(e_depth * 1.5),
        )
