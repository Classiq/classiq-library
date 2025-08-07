from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np
import pandas as pd
from scipy.special import rel_entr


@wrap_testbook("discrete_log", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_Z5"))
    validate_quantum_model(tb.ref("qmod_Z13"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_Z5"),
        expected_width=12,  # actual width: 12
        expected_depth=5200,  # actual depth: 5082
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_Z13"),
        expected_width=22,  # actual width: 20
        expected_depth=24000,  # actual depth: 22185
    )

    # test notebook content
    df = _get_result_as_dataframe(tb)
    actual_values = _get_distribution(df)
    expected_values = _get_uniform_distribution(df)
    # check that the distribution we got is close to even distribution
    distance = rel_entr(actual_values, expected_values)  # 1.8, 3.01, 1.7, 3.1, 0.6, 4.4
    assert distance.sum() < 10


def _get_result_as_dataframe(tb: TestbookNotebookClient) -> pd.DataFrame:
    parsed_counts = tb.ref("[res.dict() for res in result_Z5.parsed_counts]")
    data_list = [
        (sample_state.state["func_res"], sample_state.shots)
        for sample_state in parsed_counts
    ]
    df = pd.DataFrame(data_list).rename(columns={0: "func_res", 1: "shots"})
    return df


def _get_distribution(df: pd.DataFrame) -> np.ndarray:
    grouped = df.groupby("func_res").sum()
    values = grouped.values.flatten()
    return values


def _get_uniform_distribution(df: pd.DataFrame) -> np.ndarray:
    total_num_shots = df["shots"].sum()
    num_func_res_options = len(df["func_res"].unique())

    expected_values = [total_num_shots / num_func_res_options] * num_func_res_options
    return expected_values
