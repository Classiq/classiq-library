from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("grover", timeout_seconds=120)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_small_3sat"),
        expected_width=15,  # actual 12
        expected_depth=600,  # actual 362
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_large_3sat"),
        expected_width=24,  # actual 20
        expected_depth=1200,  # actual 921
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_max_cut"),
        expected_width=15,  # actual 13
        expected_depth=1100,  # actual 880
    )

    # test SAT
    res_names = [
        "res_3_sat_small",
        "res_3_sat_large",
    ]
    formula_names = ["small_3sat_formula", "large_3sat_formula"]
    for res_name, formula_name in zip(res_names, formula_names):
        prob = tb.ref(f'{res_name}.iloc[0]["counts"] / {res_name}["counts"].sum()')
        state = tb.ref(f'{res_name}.iloc[0]["x"]')
        orcale_cl = tb.get(formula_name)
        assert orcale_cl(state) == True and prob > 0.08

    # test Max Cut
    cut_size = tb.ref("CUT_SIZE")
    prob = tb.ref('res_max_cut.iloc[0]["counts"] / res_max_cut["counts"].sum()')
    state = tb.ref('res_max_cut.iloc[0]["nodes"]')
    orcale_cl = tb.get("cut_predicate")
    assert orcale_cl(cut_size, state) == True and prob > 0.08
