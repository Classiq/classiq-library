"""Quantum oracle sketching — stage 3: classical-shadow readout.

The third stage of the QOS pipeline (Sec. F.16 of Zhao et al. 2026,
arXiv:2604.07639) extracts a compact classical model from a prepared
quantum state ``|ψ⟩`` via measurement-based shadow tomography.

Two flavours are exposed:

* **Interferometric classical shadow** (the sign-preserving variant of [[2]]
  used in Theorem F.16 of [[1]]). Suited to the readout of inner products
  ``⟨x_test | w⟩`` for an unknown ``|w⟩`` produced by an LS-SVM or PCA
  pipeline. Works at single-bit precision per shot, so ``K = O(log T / ε²)``
  shots suffice to predict the *sign* of the inner product against ``T``
  arbitrary test vectors.

* **Random-Pauli classical shadow** (the canonical [[2]] / Huang–Kueng–
  Preskill construction). Suited to predicting expectation values of
  Pauli observables. Implemented at the numpy level for completeness; for
  the corresponding Classiq circuit see
  ``algorithms/qml/classical_shadow_tomography/classical_shadow_tomography.ipynb``.

References
----------
[1] Zhao et al., *Exponential quantum advantage in processing massive
classical data*, arXiv:2604.07639 (2026).

[2] Huang, Kueng, Preskill, *Predicting many properties of a quantum
system from very few measurements*, Nature Physics 16, 1050 (2020).
arXiv:2002.08953.
"""

import numpy as np

__all__ = [
    "shadow_readout_proxy",
    "interferometric_shadow_snapshots",
    "interferometric_shadow_estimate",
    "random_pauli_shadow",
    "snapshot_reconstruction",
    "estimate_observable",
    "median_of_means",
    "shadow_error_bound",
]


def median_of_means(values: np.ndarray, k: int) -> float:
    """Median-of-means estimator of a single statistic.

    Splits the input into ``k`` equal-size chunks, takes the mean of each, and
    returns the median of those means. Outlier-resistant; standard tool in the
    classical-shadow literature ([[2]], Theorem 1).

    Args:
        values: 1-D array of independent estimators.
        k:      number of chunks (must divide ``len(values)``).

    Returns:
        Median of the ``k`` chunk means.
    """
    chunks = np.array_split(values, k)
    return float(np.median([np.mean(c) for c in chunks]))


def shadow_error_bound(
    observables: list[list[tuple[float, int]]],
    eps: float,
    delta: float,
) -> tuple[int, int]:
    """HKP random-Pauli shadow size for ``M`` observables to error ``ε`` w.p. ``≥ 1 − δ``.

    Implements Eq. (S13) of [[2]] with the random-Pauli shadow-norm bound for
    a sum of Pauli terms ``O = Σ_a c_a P_a``,

    ``‖O‖²_shadow ≤ ( Σ_a |c_a| · √(3^{weight(P_a)}) )²``,

    where ``weight(P_a)`` is the number of non-identity factors in the Pauli
    string ``P_a``. The ``3^k`` locality factor is essential: without it the
    bound underestimates the required samples by ``3^k`` for a ``k``-local
    observable.

    Args:
        observables: list of observables; each observable is a list of
            ``(coefficient, weight)`` tuples — one per Pauli term in its
            expansion ``Σ_a c_a P_a``, where ``weight`` is the number of
            non-identity Paulis in ``P_a``.
        eps:         desired additive accuracy.
        delta:       failure probability.

    Returns:
        ``(N_shadow_total, K_chunks)`` — total snapshots ``N · K`` and the
        number of median-of-means divisions ``K``.
    """
    m = len(observables)
    k = int(np.ceil(2.0 * np.log(2.0 * m / delta)))
    shadow_norms = [
        sum(abs(c) * np.sqrt(3.0**w) for c, w in obs) ** 2 for obs in observables
    ]
    n = int(np.ceil(34.0 * max(shadow_norms) / eps**2))
    return n * k, k


# ---------------------------------------------------------------------------
# Interferometric shadow (sign-preserving readout)
# ---------------------------------------------------------------------------


def shadow_readout_proxy(
    w: np.ndarray,
    X: np.ndarray,
    K: int = 200,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Predict labels ``sgn(X @ w)`` via a Gaussian-noise proxy for the shadow.

    Each "shot" estimates ``⟨x | w⟩`` with a noise floor of ``σ = ‖w‖ / √K``.
    Majority-vote across shots gives the predicted sign — the same statistic
    that the actual interferometric shadow protocol delivers, simulated here
    in O(K · N · D) time without quantum sampling.

    Args:
        w:   ``(D,)`` weight vector.
        X:   ``(N, D)`` test feature matrix.
        K:   number of shots.
        rng: numpy random generator.

    Returns:
        ``(N,)`` predicted labels in ``{-1, +1}``.
    """
    rng = rng or np.random.default_rng()
    sigma = float(np.linalg.norm(w)) / np.sqrt(K)
    inner = X @ w
    shots = inner[None, :] + sigma * rng.standard_normal(size=(K, X.shape[0]))
    votes = np.sign(shots).sum(axis=0)
    return np.sign(votes)


def interferometric_shadow_snapshots(
    psi: np.ndarray,
    n_snapshots: int,
    rng: np.random.Generator | None = None,
):
    """Generate sign-preserving snapshots of ``|ψ⟩``.

    Each snapshot is a single-shot Hadamard-test outcome on a random reflection
    of ``|ψ⟩``: a random sign vector ``s ∈ {±1}^D`` is drawn, the inner product
    ``⟨s | ψ⟩`` is sampled at single-bit precision, and the corresponding
    sign-product Bernoulli outcome is recorded together with ``s``.

    Args:
        psi:         ``(D,)`` complex amplitudes of the prepared state.
        n_snapshots: number of single-shot snapshots.
        rng:         numpy random generator.

    Returns:
        Array of shape ``(n_snapshots, D)`` whose ``k``-th row is the
        signed-projection vector ``s_k · b_k``, where ``s_k`` is the random
        sign and ``b_k = sgn(⟨s_k | ψ⟩) + Bernoulli noise``. Used by
        ``interferometric_shadow_estimate`` to predict ``⟨x | ψ⟩`` for any
        new ``x``.
    """
    rng = rng or np.random.default_rng()
    d = psi.size
    signs = rng.choice([-1.0, 1.0], size=(n_snapshots, d))
    inner = signs @ psi.real  # using real part — full complex case is the same
    # Sample a Bernoulli outcome with bias proportional to (1 + inner) / 2.
    p = 0.5 * (1.0 + np.clip(inner / max(np.abs(psi).max(), 1.0), -1.0, 1.0))
    bits = (rng.random(n_snapshots) < p).astype(float) * 2.0 - 1.0
    return signs * bits[:, None]


def interferometric_shadow_estimate(
    snapshots: np.ndarray, observable: np.ndarray
) -> float:
    """Estimate ``⟨observable | ψ⟩`` from interferometric-shadow snapshots.

    The classical estimator is the empirical mean of ``⟨observable | snap_k⟩``
    across snapshots. For a sign-only readout, the *sign* of this estimate is
    the predicted classification.

    Args:
        snapshots:  ``(K, D)`` array from ``interferometric_shadow_snapshots``.
        observable: ``(D,)`` test vector.

    Returns:
        Estimated signed inner product.
    """
    return float(np.mean(snapshots @ observable))


# ---------------------------------------------------------------------------
# Random-Pauli classical shadow (HKP)
# ---------------------------------------------------------------------------


def random_pauli_shadow(
    state: np.ndarray,
    n_snapshots: int,
    rng: np.random.Generator | None = None,
):
    """Sample a random-Pauli classical shadow of an ``n``-qubit state.

    Each snapshot picks a uniformly random Pauli string ``P ∈ {X, Y, Z}^n``,
    measures ``state`` in the corresponding eigenbasis, and records the per-
    qubit measurement outcomes ``b_q ∈ {0, 1}`` together with the basis
    identifiers ``ids_q ∈ {0, 1, 2}`` (= X, Y, Z). The classical shadow is the
    list of these (id, b) pairs; the inverse measurement channel of [[2]]
    reconstructs ``ρ`` (or any observable expectation) from them.

    Args:
        state:       ``(2**n,)`` or ``(2**n, 2**n)`` quantum state / density matrix.
        n_snapshots: number of single-shot snapshots.
        rng:         numpy random generator.

    Returns:
        ``(snapshots, ids)`` — both shape ``(n_snapshots, n)``.
    """
    rng = rng or np.random.default_rng()
    if state.ndim == 1:
        rho = np.outer(state, state.conj())
    else:
        rho = state
    n_qubits = int(np.round(np.log2(rho.shape[0])))

    snapshots = np.zeros((n_snapshots, n_qubits), dtype=int)
    ids = np.zeros((n_snapshots, n_qubits), dtype=int)

    # Single-qubit pre-measurement rotations to diagonalise Z. Matches the
    # convention used by `snapshot_reconstruction`. For Y the rotation is HS:
    # b=0 then corresponds to Y eigenvalue -1, b=1 to Y eigenvalue +1 (the
    # sign flip is handled by `estimate_observable`).
    h = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)
    s = np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=complex)
    eye = np.eye(2, dtype=complex)
    rotations = [h, h @ s, eye]  # X, Y, Z basis (HS for Y to match notebook)

    for k in range(n_snapshots):
        basis = rng.integers(0, 3, size=n_qubits)
        ids[k] = basis
        u = np.array([[1.0]], dtype=complex)
        for b in basis:
            u = np.kron(u, rotations[b])
        rho_rot = u @ rho @ u.conj().T
        probs = np.abs(np.diag(rho_rot)).astype(float)
        probs = probs / probs.sum()
        outcome = int(rng.choice(rho_rot.shape[0], p=probs))
        bits = [(outcome >> (n_qubits - 1 - q)) & 1 for q in range(n_qubits)]
        snapshots[k] = bits
    return snapshots, ids


def snapshot_reconstruction(
    snapshot: np.ndarray, snapshot_ids: np.ndarray
) -> np.ndarray:
    """Reconstruct the density-matrix estimator of a single random-Pauli snapshot.

    Applies Eq. (S44) of [[2]] per qubit,
    ``ρ̂_q = 3 (U_q^† |b_q⟩⟨b_q| U_q) - I``, with ``U_q`` the pre-measurement
    rotation indicated by ``snapshot_ids[q]`` (``HS`` for Y, matching the
    convention of the companion notebook).

    Args:
        snapshot:     ``(n,)`` measurement bits in ``{0, 1}``.
        snapshot_ids: ``(n,)`` basis ids in ``{0, 1, 2}`` (= X, Y, Z).

    Returns:
        ``(2^n, 2^n)`` density-matrix estimator.
    """
    h = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)
    s = np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=complex)
    eye = np.eye(2, dtype=complex)
    unitaries = [h, h @ s, eye]  # X, Y, Z

    zero = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    one = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)

    result = np.array([[1.0]], dtype=complex)
    for b, basis_id in zip(np.asarray(snapshot), np.asarray(snapshot_ids)):
        local_state = zero if int(b) == 0 else one
        u = unitaries[int(basis_id)]
        local = 3.0 * (u.conj().T @ local_state @ u) - eye
        result = np.kron(result, local)
    return result


def estimate_observable(
    snapshots: np.ndarray,
    ids: np.ndarray,
    observable: list[tuple[float, np.ndarray]],
    div: int,
) -> float:
    """Estimate ``⟨O⟩`` from a random-Pauli classical shadow with median-of-means.

    For each Pauli term ``c_a · P_a`` in ``observable``, the per-snapshot
    contribution factorises across qubits: a qubit on which the snapshot's
    measurement basis matches the term's Pauli contributes ``±3`` (sign set
    by the corresponding eigenvalue), and a mismatched non-identity qubit
    contributes ``0``. The Y-basis convention follows the ``HS`` rotation
    used in ``random_pauli_shadow``/``snapshot_reconstruction``: for Y the
    sign mapping is reversed (``b=0 → −3``, ``b=1 → +3``). This fix corrects
    the sign bug present in the companion notebook's ``estimate_observable``,
    which was hidden because that notebook only validates against ``ZZ``.

    Args:
        snapshots:  ``(N, n)`` measurement bits.
        ids:        ``(N, n)`` basis ids in ``{0, 1, 2}``.
        observable: list of ``(coefficient, paulis)`` where ``paulis`` is an
            ``(n,)`` array with entries in ``{-1, 0, 1, 2}`` for ``{I, X, Y, Z}``.
        div:        number of median-of-means divisions ``K``.

    Returns:
        Estimated expectation value ``⟨O⟩``.
    """
    snapshots = np.asarray(snapshots)
    ids = np.asarray(ids)
    n_snapshots = snapshots.shape[0]
    chunk = n_snapshots // div

    total = 0.0
    for coeff, paulis in observable:
        paulis = np.asarray(paulis)
        non_id = paulis != -1
        is_y = paulis == 1

        # Sign per qubit for matched-basis snapshots:
        # +1 eigenvalue → +3, −1 eigenvalue → −3.
        # X (HS rotation flipped to H), Z (no rotation): b=0 → +1, b=1 → −1.
        # Y (HS rotation): b=0 → −1, b=1 → +1.
        match = (ids == paulis[None, :]) & non_id[None, :]
        eigenvals = np.where(snapshots == 0, 1.0, -1.0)
        eigenvals = np.where(is_y[None, :], -eigenvals, eigenvals)
        per_qubit = np.where(match, 3.0 * eigenvals, 1.0)

        mismatch = (~match) & non_id[None, :]
        per_qubit = np.where(mismatch, 0.0, per_qubit)

        per_snapshot = np.prod(per_qubit, axis=1)
        means = [
            float(np.mean(per_snapshot[k * chunk : (k + 1) * chunk]))
            for k in range(div)
        ]
        total += float(coeff) * float(np.median(means))
    return total
