from dataclasses import dataclass, field
import abc

from classiq import (
    Constraints,
    QuantumProgram,
    ExecutionJob,
    synthesize,
    show,
)
from errors import StageError


@dataclass
class BenchmarkExample(abc.ABC):
    name: str
    num_qubits: int
    constraints: Constraints = field(default_factory=Constraints)

    report_family_title: str | None = None
    report_family_description: str = ""

    def __post_init__(self):
        if self.report_family_title is None:
            self.report_family_title = self.name.capitalize()

        self.main = self.create_main()

    @property
    def report_instance_title(self) -> str:
        return f"{self.name} - {self.num_qubits} qubits"

    @abc.abstractmethod
    def create_main(self) -> callable:
        pass

    @abc.abstractmethod
    async def submit(self, qprog: QuantumProgram) -> str:
        """
        Submit the execution and return a job_id.
        """
        pass

    async def get_job_result(self, job_id: str):
        """
        Helper for concrete benchmarks.
        Use this inside score() so retrieve-job failures are tagged correctly.
        """
        try:
            job = ExecutionJob.from_id(job_id)
            result = await job.result_async()
            return job, result
        except Exception as exc:
            raise StageError("retrieve_job", exc) from exc

    @abc.abstractmethod
    async def score(self, job_id: str) -> dict:
        """
        Return a dict like {"score": float}.
        This method is responsible for reading the job result
        and computing the benchmark score.
        """
        pass

    def show(self) -> None:
        qprog = synthesize(
            self.main,
            constraints=self.constraints,
        )
        show(qprog)
