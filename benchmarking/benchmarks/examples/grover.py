from classiq import *
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "..")
from benchmark import BenchmarkExample


GROVER_DESCRIPTION = Path("../descriptions/grover.tex").read_text(encoding="utf-8")

MARKED_STATE = 5


def num_grover_iterations(problem_size):
    N = 2**problem_size
    theta = np.arcsin(1 / np.sqrt(N))
    r = np.floor(np.pi / (4 * theta) - 0.5)
    P_success = np.sin((2 * r + 1) * theta) ** 2
    return r, P_success


class GroverExample(BenchmarkExample):
    def __init__(self, problem_size: int, c: int):
        super().__init__(
            name="grover",
            problem_size=problem_size,
            report_family_title="Grover Search Algorithm",
            report_family_description=GROVER_DESCRIPTION,
        )
        assert c <= 2**problem_size
        self.c = c

    def create_main(self) -> callable:
        @qperm
        def marked_oracle(x: Const[QNum], res: QBit) -> None:
            res ^= x == self.c

        @qfunc
        def main(x: Output[QNum[self.problem_size]]):
            allocate(x)
            hadamard_transform(x)

            r, _ = num_grover_iterations(self.problem_size)

            power(
                r,
                lambda: grover_operator(
                    lambda vars: phase_oracle(marked_oracle, vars),
                    hadamard_transform,
                    x,
                ),
            )

        return main

    async def submit(self, qprog: QuantumProgram) -> str:
        with ExecutionSession(qprog) as es:
            job = es.submit_sample()
            return job.id

    async def score(self, job_id):
        job = ExecutionJob.from_id(job_id)
        result = await job.result_async()
        df = result[0].value.dataframe

        marked_prob_sum = df.loc[df["x"] == MARKED_STATE, "probability"].sum()
        print(f"marked_prob_sum: {marked_prob_sum}")

        _, P_success = num_grover_iterations(self.problem_size)

        score = marked_prob_sum / P_success
        exec_minutes = (job.end_time - job.start_time).total_seconds() / 60.0

        return {
            "score": float(score),
            "execution_time": exec_minutes,
        }
