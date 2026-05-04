from classiq import *
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "..")
from benchmark import BenchmarkExample


GHZ_DESCRIPTION = Path("../descriptions/ghz.tex").read_text(encoding="utf-8")


def parity_from_df(df):
    signs = 1 - 2 * df["x"].apply(lambda x: int(x).bit_count() % 2)
    return (df["probability"] * signs).sum()


def population_from_df(df, n_qubits):
    return df.loc[
        (df["x"] == 0) | (df["x"] == 2**n_qubits - 1),
        "probability",
    ].sum()


def fit_coherence(phases, parities, n_qubits):
    """
    Fit parity(phi) ~= a*cos(n*phi) + b*sin(n*phi) + c
    coherence C = oscillation amplitude = sqrt(a^2 + b^2)
    """
    phases = np.asarray(phases, dtype=float)
    parities = np.asarray(parities, dtype=float)

    X = np.column_stack(
        [
            np.cos(n_qubits * phases),
            np.sin(n_qubits * phases),
            np.ones_like(phases),
        ]
    )
    coeffs, *_ = np.linalg.lstsq(X, parities, rcond=None)
    a, b, c = coeffs
    C = float(np.sqrt(a * a + b * b))
    return C, {"a": float(a), "b": float(b), "offset": float(c)}


class GHZExample(BenchmarkExample):
    """
    Currently, this example is defined with problem_size=3, and 6 different samples of \phi for
    extracting the coherence. For the general case one should defined the number of samples as a function of problem_size.
    """

    def __init__(self, problem_size):
        super().__init__(
            name="ghz",
            problem_size=problem_size,
            report_family_title="GHZ State Preparation",
            report_family_description=GHZ_DESCRIPTION,
        )
        self.phis = np.linspace(0, np.pi, 2 * self.problem_size, endpoint=False)

    def create_main(self) -> callable:
        @qfunc
        def main(theta: CReal, phi: CReal, x: Output[QNum]):
            prepare_ghz_state(self.problem_size, x)
            apply_to_all(lambda q: R(theta, phi, q), x)

        return main

    async def submit(self, qprog: QuantumProgram) -> str:
        with ExecutionSession(qprog) as es:
            job = es.submit_batch_sample(
                [{"theta": 0, "phi": np.pi}]
                + [{"theta": -np.pi / 2, "phi": p} for p in self.phis]
            )
            return job.id

    async def score(self, job_id):
        job = ExecutionJob.from_id(job_id)
        result = await job.result_async()

        P = population_from_df(result[0].value.details[0].dataframe, self.problem_size)
        parities = [
            parity_from_df(res.dataframe) for res in result[0].value.details[1:]
        ]

        C, fit_info = fit_coherence(self.phis, parities, self.problem_size)
        F = min(1.0, max(0.0, 0.5 * (P + C)))

        exec_minutes = (job.end_time - job.start_time).total_seconds() / 60.0

        return {
            "score": F,
            "execution_time": exec_minutes,
        }
