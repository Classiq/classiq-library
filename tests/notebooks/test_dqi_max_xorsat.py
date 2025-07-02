from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("dqi_max_xorsat", timeout_seconds=200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_one_hot"),
        expected_width=16,  # actual width: 16
        expected_depth=120,  # actual depth: 111
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_dicke"),
        expected_width=7,  # actual width: 7
        expected_depth=250,  # actual depth: 223
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=13,  # actual width: 13
        expected_depth=7250,  # actual depth: 7079
    )

    # test notebook content
    assert (
        tb.ref('sum(sum(sample.state["y"]) for sample in res.parsed_counts)') == 0
    ), "the y vector is not clean"
