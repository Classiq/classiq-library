from classiq import *
from classiq.qmod.symbolic import pi
import sys
from pathlib import Path

sys.path.insert(0, "..")
from benchmark import BenchmarkExample


LOCALIZATION_DESCRIPTION = Path("../descriptions/dynamical_localization.tex").read_text(
    encoding="utf-8"
)


@qfunc
def single_step(kick_mag: CReal, p: QNum):
    within_apply(lambda: qft(p), lambda: phase((kick_mag * pi / (2**p.size)) * p**2))
    phase(-(pi / 2**p.size) * p**2)


class QSMExample(BenchmarkExample):
    def __init__(self):
        super().__init__(
            name="localization",
            problem_size=3,
            report_family_title="Dynamical Localization",
            report_family_description=LOCALIZATION_DESCRIPTION,
        )

    def create_main(self) -> callable:
        @qfunc
        def main(num_kicks: CInt, p: Output[QNum[self.problem_size, SIGNED, 0]]):
            allocate(p)
            p ^= -2
            power(num_kicks, lambda: single_step(0.1, p))

        return main

    async def submit(self, qprog: QuantumProgram) -> str:
        with ExecutionSession(qprog) as es:
            job = es.submit_batch_sample([{"num_kicks": 2}, {"num_kicks": 3}])
            return job.id

    async def score(self, job_id):
        job = ExecutionJob.from_id(job_id)
        result = await job.result_async()
        df_t_2 = result[0].value.details[0].dataframe
        df_t_3 = result[0].value.details[1].dataframe

        def get_peak_prob(df):
            match = df.loc[df["p"] == -2, "probability"]
            return 0.0 if match.empty else float(match.iloc[0])

        def normalize_peak(p):
            N = 2**self.problem_size
            return max(0.0, min(1.0, (p - 1 / N) / (1 - 1 / N)))

        p2 = get_peak_prob(df_t_2)
        p3 = get_peak_prob(df_t_3)

        s2 = normalize_peak(p2)
        s3 = normalize_peak(p3)

        score = (s2 * s3) ** 0.5

        exec_minutes = (job.end_time - job.start_time).total_seconds() / 60.0

        return {
            "score": score,
            "execution_time": exec_minutes,
        }
