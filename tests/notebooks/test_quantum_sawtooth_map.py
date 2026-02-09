from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("quantum_sawtooth_map", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=5,  # actual 3
        expected_depth=100,  # actual 49
    )

    # test notebook content
    timesteps = tb.ref("timesteps")
    res_simulator = tb.ref_pydantic("results_simulator")
    for i in range(len(timesteps)):
        df = res_simulator[i].dataframe
        assert float(df.loc[df["p"] == -2, "probability"].iloc[0]) > 0.9
