from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("grover", timeout_seconds=120)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("one_rep_qprog_small_3sat"),
        expected_width=15,  # actual 12
        expected_depth=600,  # actual 362
    )
    validate_quantum_program_size(
        tb.ref_pydantic("one_rep_qprog_large_3sat"),
        expected_width=24,  # actual 20
        expected_depth=1200,  # actual 921
    )
    validate_quantum_program_size(
        tb.ref_pydantic("one_rep_qprog_max_cut"),
        expected_width=15,  # actual 13
        expected_depth=1100,  # actual 880
    )

    # test SAT
    res_names = ["res_3_sat_small", "res_3_sat_large"]
    formula_names = ["small_3sat_formula", "large_3sat_formula"]
    for res_name, formula_name in zip(res_names, formula_names):
        assert tb.ref(f"bool({formula_name}({res_name}.iloc[0]['x']))") == True
        assert tb.ref(f"{res_name}.iloc[0]['probability']") > 0.08

    # test Max Cut
    assert tb.ref("bool(cut_predicate(CUT_SIZE, res_max_cut.iloc[0]['nodes']))") == True
    assert tb.ref("res_max_cut.iloc[0]['probability']") > 0.08
