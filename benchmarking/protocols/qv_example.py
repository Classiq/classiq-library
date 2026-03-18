import sys

sys.path.insert(0, "..")
from benchmark import BenchmarkExample
from reporting import *
from classiq import *
from scipy.stats import unitary_group
from scipy.linalg import qr


import numpy as np
import pandas as pd


def _heavy_states_from_df(df_ideal: pd.DataFrame) -> set[tuple[int, ...]]:
    ideal_x = df_ideal["x"].map(lambda bits: tuple(int(b) for b in bits))
    ideal_probs = df_ideal["probability"].to_numpy(dtype=float)

    median = np.median(ideal_probs)
    heavy_mask = ideal_probs > median

    return set(ideal_x[heavy_mask].tolist())


class QVExample(BenchmarkExample):
    def __init__(self, num_qubits: int, trial_id: int, seed: int):
        self.trial_id = trial_id
        self.seed = int(seed)
        self.layers = self._build_layers(num_qubits, self.seed)

        # cache
        self._heavy_states: set[int] | None = None

        super().__init__(
            name=f"qv_{num_qubits}_{trial_id}",
            num_qubits=num_qubits,
        )

    def _build_layers(self, num_qubits: int, seed: int):
        rng = np.random.default_rng(seed)

        def haar(m: int) -> np.ndarray:
            u1 = unitary_group.rvs(m, random_state=rng)
            u2 = unitary_group.rvs(m, random_state=rng)
            Z = u1 + 1j * u2
            Q, R = qr(Z)
            Lambda = np.diag([R[i, i] / np.abs(R[i, i]) for i in range(m)])
            return Q @ Lambda

        layers = []
        for _ in range(num_qubits):
            qubit_list = rng.permutation(num_qubits).tolist()

            layer = []
            for idx in range(num_qubits // 2):
                a = qubit_list[idx]
                b = qubit_list[num_qubits // 2 + idx]
                gate_matrix = haar(4)
                layer.append((a, b, gate_matrix))

            layers.append(layer)

        return layers

    def create_main(self) -> callable:
        layers = self.layers
        n = self.num_qubits

        @qfunc
        def main(x: Output[QArray[n]]):
            allocate(x)
            for layer in layers:
                for a, b, gate_matrix in layer:
                    unitary(gate_matrix.tolist(), [x[a], x[b]])

        return main

    async def submit(self, qprog: QuantumProgram) -> str:
        with ExecutionSession(qprog) as es:
            job = es.submit_sample()
            return job.id

    async def score(self, job_id):
        job = ExecutionJob.from_id(job_id)
        result = await job.result_async()
        df = result[0].value.dataframe
        heavy_states = self._get_heavy_states()

        measured_x = df["x"].map(lambda bits: tuple(int(b) for b in bits))
        p_heavy = df.loc[measured_x.isin(heavy_states), "probability"].sum()

        exec_minutes = (job.end_time - job.start_time).total_seconds() / 60.0

        return {
            "heavy_output_probability": float(p_heavy),
            "execution_time": exec_minutes,
        }

    def _get_heavy_states(self) -> set[tuple[int, ...]]:
        if self._heavy_states is not None:
            return self._heavy_states

        qprog_ideal = synthesize(self.main)
        execution_preferences = ExecutionPreferences(
            num_shots=1,
            backend_preferences=ClassiqBackendPreferences(
                backend_name="simulator_statevector"
            ),
        )

        with ExecutionSession(qprog_ideal, execution_preferences) as es:
            result_ideal = es.sample()

        df_ideal = result_ideal.dataframe
        self._heavy_states = _heavy_states_from_df(df_ideal)
        return self._heavy_states
