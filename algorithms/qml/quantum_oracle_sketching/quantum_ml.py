"""Quantum oracle sketching — stage 2: query algorithms.

This module hosts the *quantum query algorithms* that consume the sketched
oracles built by ``oracle_sketching.py``: QSVT polynomial design and
application, generic linear-system solving, the LS-SVM solver, and the
quantum PCA top-eigenvector extractor.

Stage 2 of the three-stage pipeline introduced in
``qauntum_oracle_sketching.ipynb`` (Sec. F of Zhao et al. 2026,
arXiv:2604.07639):

    classical samples  →  [stage 1: oracle_sketching] block encoding U_A
                       →  [stage 2: this module]      block encoding of P(A)
                       →  [stage 3: classical_shadow] compact classical model

The numpy reference functions here are the proxy used by the
``qos_block_encoding`` / ``qos_lssvm`` / ``qos_pca`` notebooks; the
corresponding Classiq qfunc wiring is built inline in those notebooks because
the synthesis cost depends on the polynomial degree and the block-encoding
geometry.

Versions:
* v1 (this file)  — QSVT polynomial design + numpy application.
* v2  (added in `qos_lssvm.ipynb` refactor) — `quantum_lssvm_solve`,
       `quantum_linear_solve`.
* v3  (added in `qos_pca.ipynb`  refactor) — `quantum_pca_top_eigenvector`,
       generic `qsvt_apply` helper.
"""

import numpy as np
from numpy.polynomial import chebyshev as cheb

__all__ = [
    "qsvt_polynomial_phases",
    "apply_qsvt_polynomial",
    "qsvt_inverse_polynomial",
    "qsvt_projector_polynomial",
    "chebyshev_inverse_polynomial",
    "chebyshev_projector_polynomial",
    "recover_matrix_from_phase_oracle",
    "quantum_linear_solve",
    "quantum_lssvm_solve",
    "quantum_pca_top_eigenvector",
]


# ---------------------------------------------------------------------------
# Polynomial design helpers
# ---------------------------------------------------------------------------


def chebyshev_inverse_polynomial(
    kappa: float,
    degree: int,
    n_points: int = 200,
) -> np.ndarray:
    """Odd-parity Chebyshev fit of ``c/x`` on ``[1/κ, 1] ∪ [-1, -1/κ]``.

    The constant ``c = 1/(2κ)`` ensures ``|P(x)| ≤ 1`` on the valid domain so
    the resulting polynomial can be implemented by a unitary block encoding
    via QSVT.

    Args:
        kappa:    condition number of the target operator.
        degree:   polynomial degree (must be odd; even coefficients are zeroed).
        n_points: number of sample points per branch for the Chebyshev fit.

    Returns:
        Length-``degree + 1`` numpy array of Chebyshev coefficients.
    """
    c = 1.0 / (2.0 * kappa)
    xs_pos = np.linspace(1.0 / kappa, 1.0, n_points)
    xs = np.concatenate([-xs_pos[::-1], xs_pos])
    ys = c / xs
    coeffs = cheb.chebfit(xs, ys, degree)
    coeffs[::2] = 0.0
    return coeffs


def chebyshev_projector_polynomial(
    threshold: float,
    delta: float,
    degree: int,
    n_points: int = 200,
) -> np.ndarray:
    """Even-parity Chebyshev fit of the shifted-sign indicator function.

    Approximates the spectral-projector kernel ``½ (1 + sgn(x − threshold))``,
    smoothed across a transition region of width ``delta`` so the target is
    Lipschitz on ``[-1, 1]``. Used in PCA to project onto eigenvalues above
    ``threshold`` (typically chosen between the top and second eigenvalues of
    ``X^T X``).

    Args:
        threshold: position of the step (e.g. midway between top and second
                   eigenvalues, normalised into ``[-1, 1]``).
        delta:     half-width of the transition region.
        degree:    polynomial degree.
        n_points:  number of sample points for the Chebyshev fit.

    Returns:
        Length-``degree + 1`` numpy array of Chebyshev coefficients.
    """
    xs = np.linspace(-1.0, 1.0, 2 * n_points)
    ys = 0.5 * (1.0 + np.tanh((xs - threshold) / delta))
    coeffs = cheb.chebfit(xs, ys, degree)
    return coeffs


def qsvt_polynomial_phases(
    coeffs: np.ndarray,
    parity: int = 1,
):
    """Convert Chebyshev coefficients to QSVT phase angles.

    Tries to dispatch to ``classiq.applications.qsp.qsvt_phases`` (which
    requires the ``classiq[qsp]`` extra); if unavailable, raises
    ``RuntimeError`` with an installation hint. The Chebyshev coefficients
    themselves are sufficient for numpy reference computation via
    ``apply_qsvt_polynomial``.

    Args:
        coeffs: Chebyshev coefficients of the target polynomial.
        parity: 0 for even, 1 for odd.

    Returns:
        Sequence of QSVT phase angles.
    """
    try:
        from classiq.applications.qsp import qsvt_phases
    except ImportError as exc:
        raise RuntimeError(
            "QSVT phase extraction requires `classiq[qsp]` (cvxpy + nlft_qsp). "
            "Install with `pip install classiq[qsp]`. "
            "For numpy reference computation, use `apply_qsvt_polynomial` directly "
            "on the Chebyshev coefficients."
        ) from exc
    return qsvt_phases(coeffs)


# ---------------------------------------------------------------------------
# Polynomial application (numpy reference)
# ---------------------------------------------------------------------------


def apply_qsvt_polynomial(A: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    """Apply a Chebyshev polynomial ``P(A) = Σ_k c_k T_k(A)`` to a Hermitian ``A``.

    The numpy reference for the QSVT action: given Chebyshev coefficients of
    a target polynomial and a Hermitian operator ``A`` (with eigenvalues
    in ``[-1, 1]``), returns ``P(A)`` as an explicit dense matrix.

    Args:
        A:      ``(N, N)`` Hermitian matrix with ``‖A‖ ≤ 1``.
        coeffs: Chebyshev coefficients of the target polynomial.

    Returns:
        ``(N, N)`` dense matrix ``P(A)``.
    """
    eigvals, U = np.linalg.eigh(A)
    p_eigvals = cheb.chebval(eigvals, coeffs)
    return U @ np.diag(p_eigvals) @ U.conj().T


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


def qsvt_inverse_polynomial(
    A: np.ndarray, kappa: float = None, degree: int = None, eps: float = 1e-3
) -> np.ndarray:
    """Apply ``A⁻¹`` to ``A`` via QSVT polynomial inversion (numpy reference).

    Convenience wrapper that picks an appropriate Chebyshev fit degree from
    the requested precision and condition number, then dispatches to
    ``apply_qsvt_polynomial``. Returns ``c · A⁻¹`` where ``c = 1/(2κ)`` keeps
    the polynomial within the QSVT-admissible range ``|P(x)| ≤ 1``.

    Args:
        A:      ``(N, N)`` Hermitian matrix with eigenvalues in ``[1/κ, 1] ∪ [-1, -1/κ]``.
        kappa:  condition number; if None, computed from ``A``.
        degree: polynomial degree; if None, set to ``ceil(κ log(1/ε))``.
        eps:    target precision (Chebyshev fit error).

    Returns:
        ``(N, N)`` dense matrix ``c · A⁻¹`` with ``c = 1/(2κ)``.
    """
    eigvals = np.linalg.eigvalsh(A)
    if kappa is None:
        kappa = float(np.max(np.abs(eigvals)) / np.min(np.abs(eigvals)))
    if degree is None:
        degree = int(np.ceil(kappa * np.log(1.0 / eps)))
        if degree % 2 == 0:
            degree += 1  # odd parity
    coeffs = chebyshev_inverse_polynomial(kappa, degree)
    return apply_qsvt_polynomial(A, coeffs)


def qsvt_projector_polynomial(
    A: np.ndarray,
    threshold: float,
    delta: float = 0.05,
    degree: int = None,
    eps: float = 1e-3,
) -> np.ndarray:
    """Apply the spectral-projector polynomial ``P_proj(A)`` (numpy reference).

    Builds a smooth approximation of ``½(1 + sgn(A − threshold))`` and applies
    it to ``A`` via Chebyshev expansion. Used by PCA to extract the top-
    eigenvector subspace.

    Args:
        A:         ``(N, N)`` Hermitian matrix with eigenvalues in ``[-1, 1]``.
        threshold: spectral cut.
        delta:     transition-region half-width.
        degree:    polynomial degree; if None, set to ``ceil(log(1/ε)/δ)``.
        eps:       target precision.

    Returns:
        ``(N, N)`` dense matrix ``P_proj(A)``.
    """
    if degree is None:
        degree = int(np.ceil(np.log(1.0 / eps) / delta))
    coeffs = chebyshev_projector_polynomial(threshold, delta, degree)
    return apply_qsvt_polynomial(A, coeffs)


# ---------------------------------------------------------------------------
# Quantum-machine-learning pipelines (v2)
# ---------------------------------------------------------------------------


def recover_matrix_from_phase_oracle(
    V_diag: np.ndarray, theta: float, n: int
) -> np.ndarray:
    """Recover the ``(n, n)`` matrix ``A`` from a sketched matrix-element phase oracle.

    Reads off the diagonal of ``V`` indexed by ``(i, j)``, unwraps the phase, and
    divides by ``θ``. Equivalent in expectation to applying a Hadamard test and
    reading the ``|1⟩``-branch amplitudes (up to a constant factor) — see
    ``oracle_sketching.hadamard_test_branches`` for the corresponding circuit
    interpretation.

    Args:
        V_diag: ``(n²,)`` diagonal of the sketched phase oracle.
        theta:  phase angle used in the sketch.
        n:      data-register dimension.

    Returns:
        ``(n, n)`` numpy array recovering ``A``.
    """
    return np.angle(V_diag).reshape(n, n) / theta


def quantum_linear_solve(
    A: np.ndarray,
    b: np.ndarray,
    M_matrix: int = 80_000,
    theta_be: float = 0.05,
    qsvt_kappa: float = None,
    qsvt_degree: int = 51,
    rng: np.random.Generator | None = None,
):
    """Generic ``A⁻¹ b`` via the QOS + QSVT pipeline (numpy reference).

    Sketches the matrix-element phase oracle of ``A``, applies the QSVT
    inversion polynomial, and returns ``A⁻¹ b``.

    Args:
        A:           ``(n, n)`` Hermitian matrix to invert.
        b:           ``(n,)`` right-hand-side vector.
        M_matrix:    number of matrix-element samples.
        theta_be:    phase-oracle angle (small for linear regime).
        qsvt_kappa:  QSVT condition-number target; auto-set from ``A`` if None.
        qsvt_degree: Chebyshev polynomial degree.
        rng:         numpy random generator.

    Returns:
        ``(x_quantum, diagnostics)`` where ``x_quantum`` ≈ ``A⁻¹ b`` and
        ``diagnostics`` is a dict of intermediate quantities.
    """
    # Avoid an import-time circular dependency by loading the sketching
    # primitive lazily; both modules co-exist in the same package directory.
    from oracle_sketching import matrix_element_sketch

    rng = rng or np.random.default_rng()
    n = A.shape[0]

    # --- Stage 1: matrix-element sketch -------------------------------------
    samples_ij = np.column_stack(
        [
            rng.integers(0, n, size=M_matrix),
            rng.integers(0, n, size=M_matrix),
        ]
    )
    V = matrix_element_sketch(A, samples_ij, theta_be)
    A_recovered = recover_matrix_from_phase_oracle(np.diag(V), theta_be, n)
    A_recovered = 0.5 * (A_recovered + A_recovered.T)  # enforce Hermiticity

    # --- Stage 2: QSVT inversion --------------------------------------------
    alpha = float(np.linalg.norm(A_recovered, 2))
    A_norm = A_recovered / alpha
    if qsvt_kappa is None:
        eigvals = np.linalg.eigvalsh(A_norm)
        qsvt_kappa = max(2.0, 1.0 / float(np.min(np.abs(eigvals))))
    coeffs = chebyshev_inverse_polynomial(qsvt_kappa, qsvt_degree)
    # apply_qsvt_polynomial returns (1/(2κ)) · A_norm⁻¹ = (α/(2κ)) · A⁻¹.
    A_inv_qsvt = apply_qsvt_polynomial(A_norm, coeffs)
    A_inv_full = A_inv_qsvt * (2 * qsvt_kappa / alpha)

    x_quantum = A_inv_full @ b

    diagnostics = {
        "alpha": alpha,
        "kappa_used": qsvt_kappa,
        "A_recovery_error": float(np.linalg.norm(A_recovered - A) / np.linalg.norm(A)),
        "A_inv_error": float(
            np.linalg.norm(A_inv_full - np.linalg.inv(A))
            / np.linalg.norm(np.linalg.inv(A))
        ),
    }
    return x_quantum, diagnostics


def quantum_lssvm_solve(
    X: np.ndarray,
    y: np.ndarray,
    lambd: float,
    M_matrix: int = 80_000,
    theta_be: float = 0.05,
    M_state: int = 4_000,
    theta_state: float = np.pi / 16,
    qsvt_kappa: float = None,
    qsvt_degree: int = 51,
    rng: np.random.Generator | None = None,
):
    """End-to-end quantum LS-SVM solver via QOS + QSVT (numpy reference).

    Solves ``(X^T X + λ I) w = X^T y`` using the three-stage QOS pipeline:

    1. ``matrix_element_sketch`` builds the sketched phase oracle of ``A = X^T X + λ I``.
    2. ``state_sketch`` builds the post-selected amplitude vector for ``b = X^T y``.
    3. QSVT inversion polynomial is applied via ``apply_qsvt_polynomial``.

    Args:
        X:           ``(N, D)`` feature matrix.
        y:           ``(N,)`` ±1 labels.
        lambd:       ridge regularisation strength.
        M_matrix:    samples for the matrix-element sketch.
        theta_be:    phase-oracle angle for ``A``.
        M_state:     samples for the state sketch of ``b``.
        theta_state: amplitude angle for the state sketch.
        qsvt_kappa:  QSVT condition-number target; auto-set if None.
        qsvt_degree: Chebyshev polynomial degree for the inversion.
        rng:         numpy random generator.

    Returns:
        ``(w_quantum, diagnostics)`` — recovered classifier weight + intermediates.
    """
    from oracle_sketching import matrix_element_sketch, state_sketch

    rng = rng or np.random.default_rng()
    d = X.shape[1]

    # --- Stage 1a: matrix-element sketch of A = X^T X + λ I -----------------
    a_target = X.T @ X + lambd * np.eye(d)
    samples_ij = np.column_stack(
        [
            rng.integers(0, d, size=M_matrix),
            rng.integers(0, d, size=M_matrix),
        ]
    )
    V = matrix_element_sketch(a_target, samples_ij, theta_be)
    a_recovered = recover_matrix_from_phase_oracle(np.diag(V), theta_be, d)
    a_recovered = 0.5 * (a_recovered + a_recovered.T)

    # --- Stage 1b: state sketch of b = X^T y --------------------------------
    b_target = X.T @ y
    b_norm = float(np.linalg.norm(b_target))
    b_unit = b_target / b_norm
    samples_b = rng.integers(0, d, size=M_state)
    amps = state_sketch(b_unit, samples_b, theta_state)
    b_unit_rec = amps / (theta_state / 2) * np.sqrt(d)
    b_unit_rec /= np.linalg.norm(b_unit_rec)
    b_recovered = b_unit_rec * b_norm

    # --- Stage 2: QSVT inversion --------------------------------------------
    alpha = float(np.linalg.norm(a_recovered, 2))
    a_norm = a_recovered / alpha
    if qsvt_kappa is None:
        eigvals = np.linalg.eigvalsh(a_norm)
        qsvt_kappa = max(2.0, 1.0 / float(np.min(np.abs(eigvals))))
    coeffs = chebyshev_inverse_polynomial(qsvt_kappa, qsvt_degree)
    a_inv_qsvt = apply_qsvt_polynomial(a_norm, coeffs)
    a_inv_full = a_inv_qsvt * (2 * qsvt_kappa / alpha)

    w_quantum = a_inv_full @ b_recovered

    diagnostics = {
        "alpha": alpha,
        "kappa_used": qsvt_kappa,
        "A_recovery_error": float(
            np.linalg.norm(a_recovered - a_target) / np.linalg.norm(a_target)
        ),
        "b_recovery_error": float(
            np.linalg.norm(b_recovered - b_target) / np.linalg.norm(b_target)
        ),
        "A_inv_error": float(
            np.linalg.norm(a_inv_full - np.linalg.inv(a_target))
            / np.linalg.norm(np.linalg.inv(a_target))
        ),
    }
    return w_quantum, diagnostics


def quantum_pca_top_eigenvector(
    X_data: np.ndarray,
    guiding_vector: np.ndarray,
    M_matrix: int = 80_000,
    theta_be: float = 0.05,
    spectral_gap_lower: float = None,
    spectral_gap_upper: float = None,
    qsvt_degree: int = 121,
    delta: float = 0.05,
    rng: np.random.Generator | None = None,
):
    """Recover the top principal direction of ``X^T X`` via QOS + QSVT projector.

    Stage-2 sibling of ``quantum_lssvm_solve``: uses the QSVT *spectral-projector*
    polynomial (Sec. F.3 of [[1]]) to extract the top-eigenvalue subspace of the
    Gram matrix ``A = X^T X``, then projects a guiding vector onto that subspace.

    Args:
        X_data:              ``(N, D)`` centred feature matrix with ``|X|_max ≤ 1``.
        guiding_vector:      ``(D,)`` initial guess for ``w`` with non-zero overlap.
        M_matrix:            number of matrix-element samples.
        theta_be:            phase-oracle angle.
        spectral_gap_lower:  ``λ₂`` (second eigenvalue, normalised). Auto-computed if None.
        spectral_gap_upper:  ``λ₁`` (top eigenvalue, normalised). Auto-computed if None.
        qsvt_degree:         Chebyshev polynomial degree for the projector.
        delta:               half-width of the projector's smoothed transition.
        rng:                 numpy random generator.

    Returns:
        ``(w_quantum, diagnostics)`` — sign-aligned top eigenvector + intermediates.
    """
    from oracle_sketching import matrix_element_sketch

    rng = rng or np.random.default_rng()
    n = X_data.shape[1]

    # Stage 1: matrix-element sketch of A = X^T X.
    a_target = X_data.T @ X_data
    samples_ij = np.column_stack(
        [
            rng.integers(0, n, size=M_matrix),
            rng.integers(0, n, size=M_matrix),
        ]
    )
    V = matrix_element_sketch(a_target, samples_ij, theta_be)
    a_recovered = recover_matrix_from_phase_oracle(np.diag(V), theta_be, n)
    a_recovered = 0.5 * (a_recovered + a_recovered.T)

    # Stage 2: QSVT projector.
    alpha = float(np.linalg.norm(a_recovered, 2))
    a_norm = a_recovered / alpha
    if spectral_gap_lower is None or spectral_gap_upper is None:
        eigvals_local = np.linalg.eigvalsh(a_norm)
        spectral_gap_upper = float(eigvals_local[-1])
        spectral_gap_lower = float(eigvals_local[-2])
    mu_norm = 0.5 * (spectral_gap_upper + spectral_gap_lower)
    coeffs = chebyshev_projector_polynomial(mu_norm, delta, qsvt_degree)
    projector = apply_qsvt_polynomial(a_norm, coeffs)

    # Stage 3: project the guiding vector onto the top-eigenvalue subspace.
    g_unit = guiding_vector / np.linalg.norm(guiding_vector)
    w_q_raw = projector @ g_unit
    norm_w = float(np.linalg.norm(w_q_raw))
    w_quantum = w_q_raw / norm_w

    # Sign-align with the guiding vector to remove the global ±1 freedom.
    if w_quantum @ g_unit < 0:
        w_quantum = -w_quantum

    diagnostics = {
        "alpha": alpha,
        "mu_norm": mu_norm,
        "A_recovery_error": float(
            np.linalg.norm(a_recovered - a_target) / np.linalg.norm(a_target)
        ),
        "post_projector_norm": norm_w,
    }
    return w_quantum, diagnostics
