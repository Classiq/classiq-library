from classiq import *
import sys
from pathlib import Path

sys.path.insert(0, "..")
from benchmark import BenchmarkExample

ADDER_DESCRIPTION = Path("../descriptions/adder.tex").read_text(encoding="utf-8")


class AdderExample(BenchmarkExample):
    def __init__(self, problem_size: int):
        super().__init__(
            name="adder",
            problem_size=problem_size,
            report_family_title="Adder",
            report_family_description=ADDER_DESCRIPTION,
            constraints=Constraints(optimization_parameter="width"),
        )

    def create_main(self) -> callable:
        @qfunc
        def main(
            y: Output[QNum[self.problem_size]], x: Output[QNum[self.problem_size]]
        ):
            allocate(y)
            allocate(x)
            hadamard_transform(x)
            y ^= x + 2 ** (y.size // 2) - 1

        return main

    async def submit(self, qprog: QuantumProgram) -> str:
        with ExecutionSession(qprog) as es:
            job = es.submit_sample()
            return job.id

    async def score(self, job_id):
        job = ExecutionJob.from_id(job_id)
        result = await job.result_async()
        df = result[0].value.dataframe

        mask = (
            (df["x"] + 2 ** (self.problem_size // 2) - 1 - df["y"])
            % 2**self.problem_size
        ) == 0

        exec_minutes = (job.end_time - job.start_time).total_seconds() / 60.0

        return {
            "score": df.loc[mask, "probability"].sum(),
            "execution_time": exec_minutes,
        }
