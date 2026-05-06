"""Runtime comparison: Classiq vs PennyLane classical-shadow tomography.

Both implementations use the random-Pauli measurement channel on the Bell
state ``|Phi^-> = (|00> - |11>)/sqrt(2)`` and reconstruct rho via the
single-qubit inverse channel ``rho_hat = ⊗_j (3 U_j^dagger |b_j><b_j| U_j - I)``.

The Classiq path follows the notebook in this directory: a fresh quantum
program is synthesized for every snapshot, so the random Pauli basis is
baked into the circuit at synthesis time. The PennyLane path uses
``lightning.qubit`` with one shot per snapshot, sampling the basis in
Python and reading expectation values of ``+/-1`` directly.

Run as a script. Tweak ``NUM_SNAPSHOTS`` and ``NUM_QUBITS`` at the top.


Analysis:

A few things worth calling out about why the gap is this big, since they shape what the comparison actually measures:

Cloud round-trip per snapshot. The Classiq path resynthesizes and re-launches an ExecutionSession for every snapshot
(mirroring the notebook). At ~3.6 s/snapshot, almost all of that is HTTP latency to
the Classiq cloud, not classical compute. PennyLane's lightning.qubit is an in-process
C++ statevector sim — no network involved.
Reconstruction quality is comparable (~0.85 Frobenius distance for both).
The two pipelines are statistically equivalent, as expected — they both implement
the random-Pauli inverse channel from Huang et al.
⟨Z₀Z₁⟩ = 0 is undersampled, not wrong. With 50 snapshots split into 10
median-of-means chunks, the chance of both qubits landing in Z basis is 1/9 per
snapshot, so most chunks contribute 0 and the median collapses to 0. The notebook itself derives that ~9,008 snapshots are needed to bound this estimator's error at 0.2.
If you want a more representative head-to-head, the meaningful tweaks would be:
(1) bump NUM_SNAPSHOTS (each one costs ~3.6 s of cloud time, so 200 ≈ 12 min,
1000 ≈ 1 hr), or (2) refactor the Classiq path to synthesize once and reuse —
that would isolate the actual quantum-execution cost from the synthesis/transport
overhead. Let me know if you want either.
"""

import time
from dataclasses import dataclass

import numpy as np


NUM_QUBITS = 2
NUM_SNAPSHOTS = 50
RNG_SEED = 552


# Phi^- = (|00> - |11>)/sqrt(2)
PHI_MINUS_DM = np.array(
    [[0.5, 0, 0, -0.5], [0, 0, 0, 0], [0, 0, 0, 0], [-0.5, 0, 0, 0.5]],
    dtype=complex,
)


@dataclass
class BenchResult:
    backend: str
    shadow_seconds: float
    reconstruct_seconds: float
    frobenius_distance: float
    zz_estimate: float


# ---------------------------------------------------------------------------
# Shared classical post-processing (identical formula in both pipelines).
# ---------------------------------------------------------------------------

ZERO_DM = np.array([[1, 0], [0, 0]], dtype=complex)
ONE_DM = np.array([[0, 0], [0, 1]], dtype=complex)
S_MAT = np.array([[1, 0], [0, 1j]], dtype=complex)
H_MAT = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
I_MAT = np.eye(2, dtype=complex)
# Index convention: 0 -> X basis (apply H), 1 -> Y basis (apply S then H), 2 -> Z basis.
PAULI_UNITARIES = [H_MAT, H_MAT @ S_MAT, I_MAT]


def snapshot_density_matrix(bits: np.ndarray, basis_ids: np.ndarray) -> np.ndarray:
    rho = np.array([[1.0 + 0j]])
    for i in range(NUM_QUBITS):
        state = ZERO_DM if bits[i] == 0 else ONE_DM
        u = PAULI_UNITARIES[int(basis_ids[i])]
        local = 3 * (u.conj().T @ state @ u) - I_MAT
        rho = np.kron(rho, local)
    return rho


def reconstruct(snapshots: np.ndarray, basis_ids: np.ndarray) -> np.ndarray:
    rho = np.zeros((2**NUM_QUBITS, 2**NUM_QUBITS), dtype=complex)
    for snap, ids_row in zip(snapshots, basis_ids):
        rho += snapshot_density_matrix(snap, ids_row)
    return rho / len(snapshots)


def estimate_zz(snapshots: np.ndarray, basis_ids: np.ndarray, k: int = 10) -> float:
    """Median-of-means estimator of <Z_0 Z_1>."""
    target = np.array([2, 2])  # both qubits measured in Z basis
    n = len(snapshots)
    k = max(1, min(k, n))
    chunk = max(1, n // k)
    means = []
    for start in range(0, n, chunk):
        ids_chunk = basis_ids[start : start + chunk]
        bits_chunk = snapshots[start : start + chunk]
        match = np.all(ids_chunk == target, axis=1)
        if match.any():
            signs = np.where(bits_chunk[match] == 0, 3.0, -3.0)
            means.append(float(np.prod(signs, axis=1).mean()))
        else:
            means.append(0.0)
    return float(np.median(means))


# ---------------------------------------------------------------------------
# Classiq path - mirrors the notebook (synthesize per snapshot).
# ---------------------------------------------------------------------------


_CLASSIQ_BASIS_IDS: list[list[int]] = []


def run_classiq() -> BenchResult:
    from classiq import (
        ExecutionPreferences,
        ExecutionSession,
        H,
        Output,
        QArray,
        S,
        prepare_bell_state,
        qfunc,
        synthesize,
    )

    rng = np.random.default_rng(RNG_SEED)
    _CLASSIQ_BASIS_IDS.clear()

    # The qfunc samples the basis at trace time and appends to the module-level
    # list, exactly mirroring the notebook's pattern (which Classiq's tracer
    # handles cleanly).
    @qfunc
    def unitary_application(state: QArray) -> None:
        row = list(rng.integers(0, 3, size=NUM_QUBITS))
        _CLASSIQ_BASIS_IDS.append([int(x) for x in row])
        for i in range(NUM_QUBITS):
            if row[i] == 0:
                H(state[i])
            if row[i] == 1:
                S(state[i])
                H(state[i])

    @qfunc
    def main(qarr: Output[QArray]) -> None:
        prepare_bell_state(1, qarr)
        unitary_application(qarr)

    snapshots = np.zeros((NUM_SNAPSHOTS, NUM_QUBITS), dtype=int)

    t0 = time.perf_counter()
    for i in range(NUM_SNAPSHOTS):
        qprog = synthesize(main)
        prefs = ExecutionPreferences(num_shots=1, random_seed=int(rng.integers(1e6)))
        with ExecutionSession(qprog, prefs) as es:
            counts = es.sample().parsed_counts
            bits = list(counts[0].state["qarr"])
        snapshots[i] = bits
    shadow_seconds = time.perf_counter() - t0
    basis_ids = list(_CLASSIQ_BASIS_IDS)

    basis_arr = np.array(basis_ids, dtype=int)
    t1 = time.perf_counter()
    rho_hat = reconstruct(snapshots, basis_arr)
    reconstruct_seconds = time.perf_counter() - t1

    return BenchResult(
        backend="classiq",
        shadow_seconds=shadow_seconds,
        reconstruct_seconds=reconstruct_seconds,
        frobenius_distance=float(np.linalg.norm(PHI_MINUS_DM - rho_hat, "fro")),
        zz_estimate=estimate_zz(snapshots, basis_arr),
    )


# ---------------------------------------------------------------------------
# Classiq parametric path - synthesize once, batch-execute with parameters.
# ---------------------------------------------------------------------------
#
# Each per-qubit basis-change unitary is expressed as RY(theta) . RZ(phi):
#   I  -> theta=0,    phi=0          (Z basis, no rotation)
#   H  -> theta=pi/2, phi=pi         (X basis: H = RY(pi/2).RZ(pi) up to phase)
#   HS -> theta=pi/2, phi=3pi/2      (Y basis: HS up to phase)
# Global phases are irrelevant for measurement outcomes, and the classical
# post-processing in `snapshot_density_matrix` uses the exact PAULI_UNITARIES
# matrices, which match what the circuit physically applies.

_BASIS_ANGLES = np.array(
    [
        [np.pi / 2, np.pi],  # 0 -> X basis
        [np.pi / 2, 3 * np.pi / 2],  # 1 -> Y basis
        [0.0, 0.0],  # 2 -> Z basis
    ],
    dtype=float,
)


def run_classiq_parametric() -> BenchResult:
    from classiq import (
        CArray,
        CReal,
        ExecutionPreferences,
        ExecutionSession,
        Output,
        QArray,
        RY,
        RZ,
        prepare_bell_state,
        qfunc,
        synthesize,
    )

    rng = np.random.default_rng(RNG_SEED)
    n = NUM_QUBITS

    @qfunc
    def basis_change(
        thetas: CArray[CReal, n], phis: CArray[CReal, n], state: QArray
    ) -> None:
        for i in range(n):
            RZ(phis[i], state[i])
            RY(thetas[i], state[i])

    @qfunc
    def main(
        thetas: CArray[CReal, n],
        phis: CArray[CReal, n],
        qarr: Output[QArray],
    ) -> None:
        prepare_bell_state(1, qarr)
        basis_change(thetas, phis, qarr)

    basis_ids = rng.integers(0, 3, size=(NUM_SNAPSHOTS, NUM_QUBITS))
    snapshots = np.zeros((NUM_SNAPSHOTS, NUM_QUBITS), dtype=int)

    t0 = time.perf_counter()
    qprog = synthesize(main)
    prefs = ExecutionPreferences(num_shots=1, random_seed=int(rng.integers(1e6)))
    with ExecutionSession(qprog, prefs) as es:
        param_batch = [
            {
                "thetas": _BASIS_ANGLES[basis_ids[i], 0].tolist(),
                "phis": _BASIS_ANGLES[basis_ids[i], 1].tolist(),
            }
            for i in range(NUM_SNAPSHOTS)
        ]
        results = es.batch_sample(param_batch)
        for i, res in enumerate(results):
            bits = list(res.parsed_counts[0].state["qarr"])
            snapshots[i] = bits
    shadow_seconds = time.perf_counter() - t0

    t1 = time.perf_counter()
    rho_hat = reconstruct(snapshots, basis_ids)
    reconstruct_seconds = time.perf_counter() - t1

    return BenchResult(
        backend="classiq-param",
        shadow_seconds=shadow_seconds,
        reconstruct_seconds=reconstruct_seconds,
        frobenius_distance=float(np.linalg.norm(PHI_MINUS_DM - rho_hat, "fro")),
        zz_estimate=estimate_zz(snapshots, basis_ids),
    )


# ---------------------------------------------------------------------------
# PennyLane path - lightning.qubit with one shot per snapshot.
# ---------------------------------------------------------------------------


def run_pennylane() -> BenchResult:
    import pennylane as qml

    rng = np.random.default_rng(RNG_SEED)
    pauli_obs = [qml.PauliX, qml.PauliY, qml.PauliZ]

    dev = qml.device("lightning.qubit", wires=NUM_QUBITS, shots=1)

    @qml.qnode(dev)
    def circuit(observable):
        # Phi^- = (|00> - |11>)/sqrt(2): H on qubit 0, then Z, then CNOT.
        qml.Hadamard(wires=0)
        qml.PauliZ(wires=0)
        qml.CNOT(wires=[0, 1])
        return [qml.expval(o) for o in observable]

    basis_ids = rng.integers(0, 3, size=(NUM_SNAPSHOTS, NUM_QUBITS))
    snapshots_pm = np.zeros((NUM_SNAPSHOTS, NUM_QUBITS), dtype=int)

    t0 = time.perf_counter()
    for i in range(NUM_SNAPSHOTS):
        obs = [pauli_obs[int(basis_ids[i, q])](q) for q in range(NUM_QUBITS)]
        outcomes = circuit(obs)
        snapshots_pm[i] = np.array(outcomes, dtype=int)
    shadow_seconds = time.perf_counter() - t0

    # PennyLane returns +/-1; convert to bit convention {0, 1} used by reconstruct().
    snapshots = (1 - snapshots_pm) // 2

    t1 = time.perf_counter()
    rho_hat = reconstruct(snapshots, basis_ids)
    reconstruct_seconds = time.perf_counter() - t1

    return BenchResult(
        backend="pennylane",
        shadow_seconds=shadow_seconds,
        reconstruct_seconds=reconstruct_seconds,
        frobenius_distance=float(np.linalg.norm(PHI_MINUS_DM - rho_hat, "fro")),
        zz_estimate=estimate_zz(snapshots, basis_ids),
    )


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------


def format_row(r: BenchResult) -> str:
    return (
        f"{r.backend:<10} "
        f"shadow={r.shadow_seconds:8.2f}s  "
        f"reconstruct={r.reconstruct_seconds:7.4f}s  "
        f"||rho_hat - Phi^-||_F={r.frobenius_distance:6.3f}  "
        f"<ZZ>={r.zz_estimate:+.3f}"
    )


def main() -> None:
    print(
        f"Classical-shadow benchmark: {NUM_SNAPSHOTS} snapshots, "
        f"{NUM_QUBITS} qubits, target = Phi^-"
    )
    print("-" * 80)

    results: list[BenchResult] = []
    for runner, label in [
        (run_pennylane, "pennylane"),
        (run_classiq, "classiq"),
        (run_classiq_parametric, "classiq-param"),
    ]:
        try:
            results.append(runner())
        except ImportError as exc:
            print(f"{label}: skipped ({exc})")
            continue
        except Exception as exc:  # surface, don't abort the other backend
            print(f"{label}: failed - {type(exc).__name__}: {exc}")
            continue

    print("-" * 80)
    for r in results:
        print(format_row(r))

    if len(results) >= 2:
        baseline = min(results, key=lambda r: r.shadow_seconds)
        print()
        for r in results:
            if r.backend == baseline.backend:
                continue
            ratio = (
                r.shadow_seconds / baseline.shadow_seconds
                if baseline.shadow_seconds
                else float("nan")
            )
            print(
                f"shadow-collection: {r.backend} is {ratio:,.1f}x slower than "
                f"{baseline.backend} ({r.shadow_seconds:.2f}s vs "
                f"{baseline.shadow_seconds:.3f}s)"
            )


if __name__ == "__main__":
    main()
