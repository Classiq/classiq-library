"""Quantum oracle sketching — stage 1 primitives.

This module collects the data-loading helpers from the
``qauntum_oracle_sketching.ipynb`` notebook so they can be reused across the
companion notebooks (block encoding, LS-SVM, PCA, examples).

The functions implement Sec. III.A and Sec. D.4 of Zhao et al. (2026)
``Exponential quantum advantage in processing massive classical data``
(arXiv:2604.07639): from a stream of classical samples ``z_t = (x_t, f(x_t))``
build per-sample phase rotations whose product approaches a target oracle.

Two layers are exposed:

* numpy reference functions, useful for verification and for the LS-SVM /
  PCA pipelines (which are simulated end-to-end in numpy);
* Classiq ``@qfunc`` building blocks that synthesise to the same operation
  on a quantum register.

The naming follows the paper:

* ``sketched_oracle``        — Boolean phase oracle ``O|x⟩ = (-1)^{f(x)}|x⟩``.
* ``state_sketch``           — real-valued state sketch via Hadamard test.
* ``matrix_element_sketch``  — sketched matrix-element phase oracle.
* ``hadamard_test_branches`` — convert phase oracle to amplitudes (numpy).
* ``stream_sketch``          — running-counts simulation of the streaming view.
"""

import numpy as np

from classiq import (
    CArray,
    CInt,
    CReal,
    H,
    Output,
    QBit,
    QNum,
    allocate,
    control,
    hadamard_transform,
    phase,
    qfunc,
    repeat,
)

__all__ = [
    # numpy reference
    "ideal_oracle",
    "sketched_oracle",
    "state_sketch",
    "stream_sketch",
    "matrix_element_sketch",
    "ideal_phase_oracle",
    "hadamard_test_branches",
    # Classiq qfuncs
    "apply_basis_phase",
    "quantum_oracle_sketch",
    "real_valued_oracle_sketch",
    "state_sketch_circuit",
    "apply_basis_phase_2d",
    "matrix_element_oracle_sketch",
]


# ---------------------------------------------------------------------------
# numpy reference implementations
# ---------------------------------------------------------------------------


def ideal_oracle(f: np.ndarray) -> np.ndarray:
    """Diagonal Boolean phase oracle ``O = diag((-1)^f)``.

    Parameters
    ----------
    f
        Length-``N`` Boolean (or 0/1) array.

    Returns
    -------
    (N, N) diagonal numpy array implementing ``O|x⟩ = (-1)^{f(x)}|x⟩``.
    """
    return np.diag((-1.0) ** f.astype(float))


def sketched_oracle(f: np.ndarray, x_samples: np.ndarray) -> np.ndarray:
    """Build the sketched Boolean phase oracle from M classical samples.

    Implements eq. (2) of the notebook with τ = π N: the diagonal phases are
    ``τ · m_x · f(x)`` where ``m_x`` is the empirical frequency of sample
    label ``x``. As ``M → ∞`` the empirical frequency concentrates around
    ``1/N`` and the diagonal converges to ``(-1)^{f(x)}``.

    Parameters
    ----------
    f
        Length-``N`` Boolean target.
    x_samples
        Length-``M`` array of sample labels in ``[0, N)``.

    Returns
    -------
    (N, N) diagonal sketched unitary.
    """
    n = f.size
    m_count = x_samples.size
    counts = np.bincount(x_samples, minlength=n)
    m = counts / m_count
    tau = np.pi * n
    return np.diag(np.exp(1j * tau * m * f))


def state_sketch(v: np.ndarray, x_samples: np.ndarray, theta: float) -> np.ndarray:
    """Post-selected amplitude vector after the Hadamard-test state sketch.

    For a real unit vector ``v`` with components ``|v_x| ≤ 1``, the procedure:

    1. Build the sketched real-valued phase oracle
       ``V|x⟩ = exp(i θ v_x)|x⟩`` from samples ``(x_t, v_{x_t})``.
    2. Apply the Hadamard test on a single ancilla.
    3. Post-select on ``|1⟩_aux`` to read amplitudes
       ``sin(θ v_x / 2) / √N`` on each ``|x⟩``.

    For small ``θ`` the resulting (unnormalised) state is approximately
    ``(θ/2)·|v⟩``; oblivious amplitude amplification (out of scope here)
    raises this to unit amplitude in ``O(1/θ)`` extra calls.

    Parameters
    ----------
    v
        Length-``N`` real components of the target unit vector.
    x_samples
        Length-``M`` array of sample labels in ``[0, N)``.
    theta
        Amplitude angle. Smaller values give a more linear response and a
        proportionally smaller post-selection success probability.

    Returns
    -------
    Length-``N`` numpy array of post-selected amplitudes.
    """
    n = v.size
    m_count = x_samples.size
    counts = np.bincount(x_samples, minlength=n)
    m = counts / m_count
    phases = theta * n * m * v
    return np.sin(phases / 2) / np.sqrt(n)


def stream_sketch(
    f: np.ndarray,
    m_total: int,
    snapshots_at: list,
    rng: np.random.Generator,
) -> list:
    """Simulate the streaming runtime view of the Boolean sketch.

    Maintains running counts of ``x`` in ``O(N)`` memory and snapshots the
    diagonal sketched unitary ``V`` at the requested sample counts, never
    materialising the full sample list.

    Parameters
    ----------
    f
        Length-``N`` Boolean target.
    m_total
        Total number of samples to draw.
    snapshots_at
        Sample indices at which to snapshot ``||V - O||_2``.
    rng
        Numpy random generator (e.g. ``np.random.default_rng(0)``).

    Returns
    -------
    List of ``(M_so_far, ||V - O||_2)`` pairs.
    """
    n = f.size
    o_ideal = ideal_oracle(f)
    counts = np.zeros(n, dtype=int)
    tau = np.pi * n
    target = set(snapshots_at)
    out: list = []
    for t in range(1, m_total + 1):
        x = int(rng.integers(0, n))
        counts[x] += 1
        if t in target:
            m = counts / t
            v_t = np.diag(np.exp(1j * tau * m * f))
            out.append((t, float(np.linalg.norm(v_t - o_ideal, ord=2))))
    return out


# ---------------------------------------------------------------------------
# Classiq qfunc building blocks
# ---------------------------------------------------------------------------


@qfunc
def apply_basis_phase(theta: CReal, x_int: CInt, qvar: QNum) -> None:
    """Apply ``exp(i · θ · |x_int⟩⟨x_int|)`` on ``qvar``.

    Implemented by controlling on the equality predicate ``qvar == x_int``;
    the inner ``phase(θ)`` becomes a relative phase on the controlled
    subspace and the identity elsewhere — exactly ``V_t``.
    """
    control(qvar == x_int, lambda: phase(theta))


@qfunc
def quantum_oracle_sketch(theta: CReal, x_samples: CArray[CInt], qvar: QNum) -> None:
    """Sketched Boolean phase oracle ``V = ∏_t exp(i θ |x_t⟩⟨x_t|)``.

    ``x_samples`` should be pre-filtered to the indices with ``f(x_t) = 1``;
    a single fixed angle ``θ = π N / M`` is then applied per sample.
    """
    repeat(
        count=x_samples.len,
        iteration=lambda t: apply_basis_phase(theta, x_samples[t], qvar),
    )


@qfunc
def real_valued_oracle_sketch(
    angles_per_sample: CArray[CReal],
    x_samples: CArray[CInt],
    qvar: QNum,
) -> None:
    """Real-valued sketched phase oracle.

    ``V = ∏_t exp(i · angles_per_sample[t] · |x_samples[t]⟩⟨x_samples[t]|)``.

    Generalises ``quantum_oracle_sketch`` so each sample carries its own
    rotation angle: the Boolean ``f(x_t) ∈ {0, 1}`` is replaced by a
    continuous ``v_{x_t} ∈ [-1, 1]``, with the angle baked in classically as
    ``angles_per_sample[t] = θ · N · v_{x_samples[t]} / M``.
    """
    repeat(
        count=x_samples.len,
        iteration=lambda t: apply_basis_phase(angles_per_sample[t], x_samples[t], qvar),
    )


@qfunc
def state_sketch_circuit(
    angles_per_sample: CArray[CReal],
    x_samples: CArray[CInt],
    aux: QBit,
    qvar: QNum,
) -> None:
    """Hadamard-test wrapping of the real-valued sketch.

    Starting from ``|0⟩_aux ⊗ |+⟩^n``, applies::

        H(aux); control(aux == 1, real_valued_oracle_sketch); H(aux)

    Post-selecting ``aux == 1`` yields the unnormalised target amplitudes
    ``sin(θ v_x / 2) |x⟩`` on the data register, which approximates
    ``(θ/2) |v⟩`` for small ``θ``.
    """
    H(aux)
    control(
        aux == 1,
        lambda: real_valued_oracle_sketch(angles_per_sample, x_samples, qvar),
    )
    H(aux)


# ---------------------------------------------------------------------------
# Matrix-element phase oracle (block-encoding bridge)
# ---------------------------------------------------------------------------


def matrix_element_sketch(
    A: np.ndarray, samples_ij: np.ndarray, theta: float
) -> np.ndarray:
    """Sketched matrix-element phase oracle ``V|i,j⟩ = e^{i θ A_{ij}}|i,j⟩``.

    Each sample ``z_t = (i_t, j_t, A_{i_t j_t})`` contributes a 2-register
    controlled phase. Setting ``τ = θ · N²`` cancels the empirical-frequency
    mean ``1/N²`` so the cumulative phase converges to ``θ A_{ij}``.

    Args:
        A:           ``(N, N)`` target matrix.
        samples_ij:  ``(M, 2)`` array of sample indices.
        theta:       phase angle.

    Returns:
        ``(N², N²)`` diagonal sketched unitary indexed by ``i * N + j``.
    """
    n = A.shape[0]
    m_count = samples_ij.shape[0]
    counts = np.zeros((n, n), dtype=int)
    np.add.at(counts, (samples_ij[:, 0], samples_ij[:, 1]), 1)
    m = counts / m_count
    tau = theta * n * n
    return np.diag(np.exp(1j * tau * m * A).ravel())


def ideal_phase_oracle(A: np.ndarray, theta: float) -> np.ndarray:
    """Exact target ``O_A^{el} = diag(exp(i θ A_{ij}))`` as an ``(N², N²)`` matrix."""
    return np.diag(np.exp(1j * theta * A).ravel())


def hadamard_test_branches(V_diag: np.ndarray, n: int) -> tuple:
    """Convert a sketched phase oracle into Hadamard-test branch amplitudes.

    Starting from ``|0⟩_aux ⊗ |+⟩^{⊗n}_row ⊗ |+⟩^{⊗n}_col`` and applying
    ``H_aux · C-V · H_aux``, returns the per-(i, j) amplitudes on the two
    aux-branches. The ``|1⟩_aux`` branch holds amplitudes
    ``(-i / N) · sin(θ A_{ij}/2) · e^{i θ A_{ij}/2}`` ≈ ``-i θ A_{ij}/(2N)``
    for small ``θ`` — a block encoding of ``diag(A_{ij}) / α`` with ``α = 2N/θ``.

    Args:
        V_diag: ``(N²,)`` diagonal of the sketched phase oracle.
        n:      data-register dimension ``N``.

    Returns:
        ``(amp_0, amp_1)`` numpy arrays of shape ``(N, N)``.
    """
    phases = np.angle(V_diag).reshape(n, n)
    common = np.exp(1j * phases / 2) / n
    return common * np.cos(phases / 2), -1j * common * np.sin(phases / 2)


# ---------------------------------------------------------------------------
# 2-register Classiq qfuncs (matrix-element block-encoding bridge)
# ---------------------------------------------------------------------------


@qfunc
def apply_basis_phase_2d(
    theta: CReal,
    i_int: CInt,
    j_int: CInt,
    qvar_i: QNum,
    qvar_j: QNum,
) -> None:
    """Apply ``exp(i · θ · |i_int, j_int⟩⟨i_int, j_int|)`` on the (qvar_i, qvar_j) registers.

    Implemented by nested ``control`` modifiers on the two equality predicates.
    """
    control(
        qvar_i == i_int,
        lambda: control(qvar_j == j_int, lambda: phase(theta)),
    )


@qfunc
def matrix_element_oracle_sketch(
    angles_per_sample: CArray[CReal],
    i_samples: CArray[CInt],
    j_samples: CArray[CInt],
    qvar_i: QNum,
    qvar_j: QNum,
) -> None:
    """Sketched matrix-element phase oracle as a Classiq qfunc.

    ``V = ∏_t exp(i · angles[t] · |i_samples[t], j_samples[t]⟩⟨i_samples[t], j_samples[t]|)``.

    Per-sample angle is baked in as ``angles_per_sample[t] = θ N² A_{i_t j_t} / M``.
    """
    repeat(
        count=i_samples.len,
        iteration=lambda t: apply_basis_phase_2d(
            angles_per_sample[t],
            i_samples[t],
            j_samples[t],
            qvar_i,
            qvar_j,
        ),
    )
