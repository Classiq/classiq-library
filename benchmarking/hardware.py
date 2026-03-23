from dataclasses import dataclass, field
from classiq import (
    create_model,
    synthesize_async,
    Preferences,
    set_quantum_program_execution_preferences,
    ExecutionPreferences,
    QuantumProgram,
)
from hardwares_preferences import execution_preferences_wrapper
from benchmark import BenchmarkExample
from errors import StageError


@dataclass
class HardwareRunner:
    backend_service_provider: str
    backend_name: str
    max_timeout: int  # seconds
    num_shots: int
    backend_kwargs: dict = field(default_factory=dict)

    @property
    def _synthesis_preferences(self) -> Preferences:
        if self.backend_service_provider == "Classiq":
            return Preferences()
        return Preferences(
            backend_service_provider=self.backend_service_provider,
            backend_name=self.backend_name,
        )

    @property
    def _execution_preferences(self):
        return ExecutionPreferences(
            num_shots=self.num_shots,
            backend_preferences=execution_preferences_wrapper(
                self.backend_service_provider,
                self.backend_name,
                **self.backend_kwargs,
            ),
        )

    async def _synthesize(self, example: BenchmarkExample) -> QuantumProgram:
        try:
            qmod = create_model(
                example.main,
                preferences=self._synthesis_preferences,
                constraints=example.constraints,
            )
            qprog = await synthesize_async(qmod)
            qprog = set_quantum_program_execution_preferences(
                qprog, self._execution_preferences
            )
            return qprog
        except Exception as exc:
            raise StageError("synthesis", exc) from exc

    def _extract_circuit_metrics(self, qprog: QuantumProgram) -> dict:
        tc = qprog.transpiled_circuit

        depth = tc.depth
        count_ops = tc.count_ops

        two_qubit_gate_count = 0
        for key, count in count_ops.items():
            name = str(key).lower()
            if any(
                g in name
                for g in ["cx", "cz", "cnot", "swap", "ecr", "iswap", "xx", "yy", "zz"]
            ):
                two_qubit_gate_count += count

        return {
            "circuit_depth": depth,
            "two_qubit_gate_count": two_qubit_gate_count,
        }

    async def submit_execution(self, example: BenchmarkExample) -> tuple[str, dict]:
        try:
            qprog = await self._synthesize(example)
            metrics = self._extract_circuit_metrics(qprog)
            job_id = await example.submit(qprog)
            return job_id, metrics
        except StageError:
            raise
        except Exception as exc:
            raise StageError("submit_job", exc) from exc

    async def score(self, example: BenchmarkExample, job_id: str) -> dict:
        try:
            return await example.score(job_id)
        except StageError:
            raise
        except Exception as exc:
            raise StageError("score", exc) from exc

    def to_dict(self, example: BenchmarkExample, **kwargs):
        return {
            "example": example.name,
            "num_qubits": example.num_qubits,
            "backend_service_provider": self.backend_service_provider,
            "backend_name": self.backend_name,
            "num_shots": self.num_shots,
            **kwargs,
        }
