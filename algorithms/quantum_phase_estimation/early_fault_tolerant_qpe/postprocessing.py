"""Classical part of the Lin & Tong protocol, shared by the examples: the sampling distribution over the Fourier modes,
the hand-out of pooled shots to the samples, the estimate of the approximate CDF (ACDF), the threshold-crossing estimate
of the ground-state energy and the sample budget, plus the exact CDF used as a reference in the plots.
"""

import numpy as np


def exact_cdf(xgrid, evals_s, weights):
    """True spectral CDF (staircase): C(x) = sum_{lambda_k <= x} p_k."""
    return np.array([weights[evals_s <= x].sum() for x in xgrid])


def mode_distribution(fhat):
    """The distribution over the Fourier modes that the ACDF estimator samples from.
    fhat = F_k for k = -d..d.  Returns the modes that can be drawn (k > 0 with F_k != 0), their probabilities
    p_k = |F_k| / sum_{k>0} |F_k| (folded to k > 0 using g(-k) = g(k)^*) and the estimator scale
    A = 2 sum_{k>0} |F_k| (the k = 0 mode only adds the constant 1/2)."""
    d = (len(fhat) - 1) // 2
    a = np.abs(fhat[d + 1 :])  # |F_k| for k = 1..d
    k_array = np.arange(1, d + 1)[
        a > 0
    ]  # the even modes have zero weight and are never drawn
    a = a[a > 0]
    A = 2 * a.sum()
    return k_array, 2 * a / A, A


def draw_shots_partition(k_array, p_k, M):
    """Draw M indices J ~ p_k and count how often each k appears: n_k[i] = number of draws of k_array[i]."""
    return np.bincount(
        np.random.choice(len(k_array), size=M, p=p_k), minlength=len(k_array)
    )


def restore_samples(n_k, mean, S):
    """Restore the samples from a pool of i.i.d. +-1 shots.  At each k the pool holds S shots (scalar or one value per k)
    with mean `mean`; the n_k shots the samples need are a uniformly random subset of it, i.e. a hypergeometric draw
    from the pool's number of +1's.  Returns sums[i] = sum of the n_k[i] +-1 outcomes at k_array[i].
    """
    S = np.broadcast_to(np.asarray(S), (len(n_k),))
    sums = np.zeros(len(n_k))
    for i, n in enumerate(n_k):
        if n == 0:
            continue
        n_plus = int(round(S[i] * (1 + mean[i]) / 2))
        plus = np.random.hypergeometric(n_plus, int(S[i]) - n_plus, n)
        sums[i] = 2 * plus - n
    return sums


def acdf_estimate(x, k_array, A, M, sums_x, sums_y):
    """The estimate G(x) of the ACDF (Eq. (3) averaged over the M samples), for an array of points x:
    1/2 + (A/M) * sum over the samples of [sin(kx) X + cos(kx) Y], with <X> = Re g(k), <Y> = Im g(k).
    """
    kx = np.outer(np.atleast_1d(x), k_array)
    return 0.5 + (A / M) * (np.sin(kx) @ sums_x + np.cos(kx) @ sums_y)


def threshold_energy(
    sums_x, sums_y, k_array, A, M, threshold, delta, weights=None, x_shift=0.0
):
    """Ground-state energy (rescaled units) as the first point x in (-pi/3, pi/3), on a grid of spacing delta/10, where the
    ACDF estimate reaches `threshold`.  sums_x[i], sums_y[i] = sums of the +-1 X / Y outcomes at k_array[i] (M samples in
    total).  weights[i] multiplies the outcomes at k_array[i] (RTE: B_k; default 1); x_shift moves the energy axis
    (a dropped identity term c_I: G(x) = G'(x - c_I)).  Returns x* (None if there is no crossing) and the function G(x).
    """
    w = np.ones(len(k_array)) if weights is None else weights
    G = lambda x: acdf_estimate(
        np.asarray(x) - x_shift, k_array, A, M, sums_x * w, sums_y * w
    )
    xgrid = np.arange(-np.pi / 3, np.pi / 3, delta / 10)
    above = np.nonzero(G(xgrid) >= threshold)[0]
    return (xgrid[above[0]] if len(above) else None), G


def sample_budget(A, eta, delta, fail_prob=0.05):
    """Worst-case number of samples M for the threshold estimate to be within delta (plus the grid spacing) with probability
    1 - fail_prob: every sample of the estimator lies in an interval of width 2 sqrt(2) A, so by Hoeffding's inequality
    and a union bound over the n_grid points of the search grid, |G - ACDF| < eta/8 everywhere on the grid once
    M >= 256 A^2 / eta^2 * ln(2 n_grid / fail_prob)."""
    n_grid = int(np.ceil((2 * np.pi / 3) / (delta / 10)))
    return int(np.ceil(256 * A**2 / eta**2 * np.log(2 * n_grid / fail_prob)))
