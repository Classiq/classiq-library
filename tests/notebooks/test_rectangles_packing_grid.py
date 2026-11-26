import numpy as np

from tests.utils_for_testbook import (
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("rectangles_packing_grid", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # best_solution is model.place, indexed [rectangle][i][j]: all 3 rectangles are placed
    assert np.sum(tb.ref("best_solution")) == 3
