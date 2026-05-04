from classiq import *
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "..")
from benchmark import BenchmarkExample


SP_DESCRIPTION = Path("../descriptions/state_preparation.tex").read_text(
    encoding="utf-8"
)


def linear_amplitudes_probabilities(n):
    N = 2**n
    amps = np.arange(N)
    amps = amps / np.linalg.norm(amps)
    return np.abs(amps) ** 2


class SPExample(BenchmarkExample):
    def __init__(self, problem_size: int):
        super().__init__(
            name="state_preparation",
            problem_size=problem_size,
            report_family_title="Linear State Preparation",
            report_family_description=SP_DESCRIPTION,
        )

    def create_main(self) -> callable:
        @qfunc
        def main(x: Output[QNum[self.problem_size]]):
            allocate(x)
            prepare_linear_amplitudes(x)

        return main

    async def submit(self, qprog: QuantumProgram) -> str:
        with ExecutionSession(qprog) as es:
            job = es.submit_sample()
            return job.id

    async def score(self, job_id):
        job = ExecutionJob.from_id(job_id)
        result = await job.result_async()
        df = result[0].value.dataframe

        n = self.problem_size
        N = 2**n

        p = np.zeros(N)
        p[df["x"]] = df["probability"].to_numpy()

        u = linear_amplitudes_probabilities(self.problem_size)
        d_tv = 0.5 * np.sum(np.abs(p - u))
        score = 1.0 - d_tv / (1.0 - 1.0 / n)

        exec_minutes = (job.end_time - job.start_time).total_seconds() / 60.0

        return {
            "score": float(score),
            "execution_time": exec_minutes,
        }
