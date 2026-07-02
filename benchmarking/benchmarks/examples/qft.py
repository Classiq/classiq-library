from classiq import *
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "..")
from benchmark import BenchmarkExample

QFT_DESCRIPTION = Path("../descriptions/qft.tex").read_text(encoding="utf-8")


class QFTExample(BenchmarkExample):
    def __init__(self, problem_size: int, m: int):
        super().__init__(
            name="qft",
            problem_size=problem_size,
            report_family_title="QFT",
            report_family_description=QFT_DESCRIPTION,
        )
        assert m < problem_size
        self.m = m

    def create_main(self) -> callable:
        @qfunc
        def prepare_comb(m: CInt, qba: QArray):
            hadamard_transform(qba[m : qba.len])

        @qfunc
        def main(x: Output[QNum[self.problem_size]]):
            allocate(x)
            prepare_comb(self.m, x)
            qft(x)

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

        u = np.zeros(N)
        if self.m == 0:
            u[0] = 1.0
        else:
            step = 2 ** (n - self.m)
            u[np.arange(0, N, step)] = 1.0 / (2**self.m)

        score = 1.0 - 0.5 * np.abs(p - u).sum() / (1.0 - 1.0 / n)

        exec_minutes = (job.end_time - job.start_time).total_seconds() / 60.0

        return {
            "score": float(score),
            "execution_time": exec_minutes,
        }
