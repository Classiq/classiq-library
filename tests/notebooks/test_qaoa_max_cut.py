from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np


@wrap_testbook("qaoa_max_cut", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=5,
        expected_depth=55,
    )

    # test notebook content
    maxcut_cost = tb.ref("maxcut_cost")
    for i, pc in enumerate(tb.ref_numpy("best_outcomes")):
        cost_value = maxcut_cost(pc.state["v"])
        assert np.isclose(cost_value, -5 / 6)
