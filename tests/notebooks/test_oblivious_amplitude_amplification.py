from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("oblivious_amplitude_amplification", timeout_seconds=20)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=4,  # actual width: 4
        expected_depth=100,  # actual depth: 94
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=5,  # actual width: 5
        expected_depth=300,  # actual depth: 278
    )

    # test notebook content
    assert _get_fraction_of_good_results(tb, "result") < 0.5
    assert _get_fraction_of_good_results(tb, "result_2") == 1


def _get_fraction_of_good_results(
    tb: TestbookNotebookClient, result_name: str
) -> float:
    block_sum = tb.ref(
        f'sum([d.shots for d in {result_name}.parsed_counts if d.state["block"] == 0])'
    )
    num_shots = tb.ref(f"{result_name}.num_shots")
    return block_sum / num_shots
