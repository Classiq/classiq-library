"""Quantum Volume circuit example.

Known limitations
-----------------
1. **Qubit pairing.**  Each layer pairs qubits by splitting a random
   permutation into a first half and a second half (indices 0..n/2-1 paired
   with n/2..n-1).  When the circuit width is odd, one qubit is idle every
   layer.  The standard QV convention pairs consecutive elements instead
   (0 with 1, 2 with 3, …).  For even widths the two schemes are equivalent
   up to relabelling; for odd widths the dropped qubit is consistent with both
   conventions, but users should be aware of the pairing order.

2. **Ideal-vs-hardware circuit mismatch.**  The heavy-output set is computed by
   re-synthesizing the model and simulating it on a statevector backend
   (`_get_heavy_states`).  Because the main execution path uses
   hardware-aware synthesis (target-specific gate set, connectivity, and
   optimisation), the circuit actually run on the device may differ from the
   one used to determine the ideal distribution.  In principle this can shift
   the heavy-output set.  A more robust approach would store the compiled
   `QuantumProgram` at submission time and reuse it for the ideal simulation.
"""

import sys

sys.path.insert(0, "..")
from benchmark import BenchmarkExample
from reporting import *
from classiq import *
from scipy.stats import unitary_group
from scipy.linalg import qr


import numpy as np
import pandas as pd


def _validate_bitlist_column(col: pd.Series, label: str) -> None:
    """Assert that every entry in *col* is a list/tuple of 0/1 values."""
    sample = col.iloc[0]
    if not isinstance(sample, (list, tuple)):
        raise TypeError(
            f"Expected '{label}' column to contain lists/tuples of bits, "
            f"but got {type(sample).__name__}: {sample!r}"
        )

    if not all(int(b) in (0, 1) for b in sample):
        raise TypeError(
            f"Expected '{label}' column entries to contain only 0/1 values, "
            f"but got {sample!r}"
        )


def _heavy_states_from_df(df_ideal: pd.DataFrame) -> set[tuple[int, ...]]:
    """Compute the set of heavy output states from an ideal simulation.

    A state x is "heavy" if its ideal probability p(x) exceeds the median
    of the full output distribution (Eq. 3 of Cross et al.).
    """
    _validate_bitlist_column(df_ideal["x"], "x (ideal)")
    ideal_x = df_ideal["x"].map(lambda bits: tuple(int(b) for b in bits))
    ideal_probs = df_ideal["probability"].to_numpy(dtype=float)

    median = np.median(ideal_probs)
    heavy_mask = ideal_probs > median

    return set(ideal_x[heavy_mask].tolist())


class QVExample(BenchmarkExample):
    """A single Quantum Volume trial circuit.

    Each trial builds a random model circuit of depth = width = num_qubits,
    composed of layers of Haar-random SU(4) gates applied to random qubit
    pairs (see Fig. 1 of Cross et al., arXiv:1811.12926).
    """

    def __init__(self, num_qubits: int, trial_id: int, seed: int):
        self.trial_id = trial_id
        self.seed = int(seed)
        # Pre-build the random circuit layers (deterministic given the seed)
        self.layers = self._build_layers(num_qubits, self.seed)

        # Cache for the heavy-output set (computed lazily on first score call)
        self._heavy_states: set[int] | None = None

        super().__init__(
            name=f"qv_{num_qubits}_{trial_id}",
            num_qubits=num_qubits,
        )

    def _build_layers(self, num_qubits: int, seed: int):
        """Generate `num_qubits` layers of random two-qubit gates.

        Each layer randomly permutes the qubits, pairs the first half with
        the second half, and assigns a Haar-random SU(4) gate to each pair.
        Returns a list of layers, where each layer is a list of
        (qubit_a, qubit_b, 4x4_unitary) tuples.
        """
        rng = np.random.default_rng(seed)

        def haar(m: int) -> np.ndarray:
            """Sample a Haar-random unitary of dimension m."""
            # FIXME: this implementation applied QR decomposition on top of already Haar-random unitaries, producing a non-Haar distribution, should be:
            #   return unitary_group.rvs(m, random_state=rng)
            u1 = unitary_group.rvs(m, random_state=rng)
            u2 = unitary_group.rvs(m, random_state=rng)
            Z = u1 + 1j * u2
            Q, R = qr(Z)
            Lambda = np.diag([R[i, i] / np.abs(R[i, i]) for i in range(m)])
            return Q @ Lambda

        layers = []
        # depth = width per the QV convention (square circuits)
        for _ in range(num_qubits):
            # Random permutation determines qubit pairing for this layer
            qubit_list = rng.permutation(num_qubits).tolist()

            layer = []
            # Pair qubit_list[i] with qubit_list[n//2 + i] for each i
            for idx in range(num_qubits // 2):
                a = qubit_list[idx]
                b = qubit_list[num_qubits // 2 + idx]
                # Each pair gets an independent Haar-random SU(4) gate
                gate_matrix = haar(4)
                layer.append((a, b, gate_matrix))

            layers.append(layer)

        return layers

    def create_main(self) -> callable:
        """Build the Classiq quantum function for this QV circuit."""
        layers = self.layers
        n = self.num_qubits

        @qfunc
        def main(x: Output[QArray[n]]):
            allocate(x)
            # Apply each layer's two-qubit unitaries
            for layer in layers:
                for a, b, gate_matrix in layer:
                    unitary(gate_matrix.tolist(), [x[a], x[b]])

        return main

    async def submit(self, qprog: QuantumProgram) -> str:
        """Submit the compiled circuit for sampling and return the job ID."""
        with ExecutionSession(qprog) as es:
            job = es.submit_sample()
            return job.id

    async def score(self, job_id) -> dict:
        """Retrieve results and compute the heavy-output probability.

        Compares measured outcomes against the ideal heavy-output set (Eq. 5
        of Cross et al.) and returns the fraction of probability mass that
        landed on heavy states.
        """
        job = ExecutionJob.from_id(job_id)
        result = await job.result_async()
        df = result[0].value.dataframe
        heavy_states = self._get_heavy_states()

        # Validate and convert measured bitstrings to tuples for set lookup
        _validate_bitlist_column(df["x"], "x (measured)")
        measured_x = df["x"].map(lambda bits: tuple(int(b) for b in bits))
        # Sum probabilities of outcomes that fall in the heavy-output set
        p_heavy = df.loc[measured_x.isin(heavy_states), "probability"].sum()

        exec_minutes = (job.end_time - job.start_time).total_seconds() / 60.0

        return {
            "heavy_output_probability": float(p_heavy),
            "execution_time": exec_minutes,
        }

    def _get_heavy_states(self) -> set[tuple[int, ...]]:
        """Return the heavy-output set, computing it lazily on first call.

        Synthesizes the model circuit (without hardware-aware optimisation),
        simulates it on a statevector backend, and identifies the states whose
        probability exceeds the median.  The result is cached for reuse.

        Note: see module docstring regarding ideal-vs-hardware circuit mismatch.
        """
        if self._heavy_states is not None:
            return self._heavy_states

        # Re-synthesize without hardware constraints for ideal simulation
        qprog_ideal = synthesize(self.main)
        execution_preferences = ExecutionPreferences(
            num_shots=1,  # statevector backend returns full distribution regardless
            backend_preferences=ClassiqBackendPreferences(
                backend_name="simulator_statevector"
            ),
        )

        with ExecutionSession(qprog_ideal, execution_preferences) as es:
            result_ideal = es.sample()

        df_ideal = result_ideal.dataframe
        self._heavy_states = _heavy_states_from_df(df_ideal)
        return self._heavy_states
