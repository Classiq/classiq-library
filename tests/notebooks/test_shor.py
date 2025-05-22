from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("shor", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=8,  # actual width: 8
        expected_depth=300,  # actual depth: 296
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=22,  # actual width: 22
        expected_depth=30000,  # actual depth: 26607
    )

    # test notebook content
    parsed_counts = tb.ref(
        "[res.dict() for res in result_2.parsed_counts_of_outputs('pow')]"
    )
    d = {item["state"]["pow"]: item["shots"] for item in parsed_counts}
    for val in [0, 171, 341, 512, 683, 853]:
        assert val in d and d[val] > 120, "Unexpected shor execution results"
