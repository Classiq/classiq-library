from tests.utils_for_testbook import wrap_testbook
from testbook.client import TestbookNotebookClient


# The notebook uses the shared public logical noise by default (INITIALIZE_OWN_NOISE is
# False), so it skips the ~1h logical-noise initialization. It still runs the full backend
# pipeline (synthesize -> export -> route -> view -> estimate), hence a generous timeout.
@wrap_testbook("fault_tolerance_engine_end_to_end", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # The circuit was routed onto a real 2-D surface-code patch footprint.
    assert tb.ref("num_patches") > 0

    # The total logical error is estimated at each requested code distance and
    # shrinks as the distance grows.
    total_errors = {int(k): float(v) for k, v in dict(tb.ref("total_errors")).items()}
    assert set(total_errors) == {11, 13, 15}
    assert total_errors[11] > total_errors[13] > total_errors[15]
