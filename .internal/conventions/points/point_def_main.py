"""Every notebook builds a circuit: @qfunc def main, or a recognised wrapper API."""

import re

from ._model import Notebook, Point

_ENTRY = re.compile(
    r"def\s+main\s*\("
    r"|construct_combinatorial_optimization_model"
    r"|CombinatorialProblem\("
    r"|\bIQAE\("
    r"|\bQSVM\("
    r"|benchmark_project\("
)


def detect(nb: Notebook) -> list[str]:
    return [] if _ENTRY.search(nb.code) else ["no def main / recognised wrapper entry"]


POINT = Point(
    title="def_main",
    detail="@qfunc def main(...)  |  CombinatorialProblem / IQAE / QSVM / benchmark_project",
    description="A circuit comes from def main or a known wrapper. Comparison notebooks "
    "and the pure-math jacobi_anger are documented exceptions.",
    static=True,
    detect=detect,
    exceptions=(
        ("jacobi_anger_expansion", "QSP coefficient math, builds no circuit"),
        ("classiq_paper/qsvt/qiskit_qsvt", "Qiskit comparison notebook"),
        ("classiq_paper/qsvt/tket_qsvt_example", "t|ket> comparison notebook"),
        (
            "classiq_paper/qsvt/pennylane_cat_qsvt_example",
            "PennyLane comparison notebook",
        ),
        (
            "classiq_paper/quantum_walk/qiskit_discrete_quantum_walk",
            "Qiskit comparison",
        ),
        ("classiq_paper/quantum_walk/tket_discrete_quantum_walk", "t|ket> comparison"),
        (
            "classiq_paper/quantum_walk/pennylane_catalyst_discrete_quantum_walk",
            "PennyLane comparison",
        ),
        ("vlasov_ampere/vlasov_ampere_qiskit", "Qiskit comparison notebook"),
    ),
)
