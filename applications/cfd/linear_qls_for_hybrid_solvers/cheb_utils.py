import cvxpy as cp
import matplotlib.pyplot as plt
from classiq.applications.qsp import qsp_approximate
import numpy as np
from scipy.special import eval_chebyt
from numpy.polynomial.chebyshev import Chebyshev


def optimize_inversion_polynomial(w_min, w_max, degree, scale):

    def target_function(x):
        return scale * (w_min) / x

    pcoefs, opt_res = qsp_approximate(
        target_function,
        degree=degree,
        parity=1,
        interval=[w_min, w_max],
        plot=False,
        bound=0.95,
    )

    return pcoefs


def reciprocal_approx(x, w_min, B, scale):
    x = np.asarray(x, dtype=float)
    num = 1.0 - (1.0 - x * x) ** B
    out = np.empty_like(x)
    nz = x != 0
    out[nz] = scale * w_min * num[nz] / x[nz]
    out[~nz] = 0.0  # limit at 0
    return out


def get_numpy_cheb_interpolate(w_min, B, scale, degree):

    # poly = Chebyshev.interpolate(
    #         lambda x: reciprocal_approx(x, w_min, B, scale), degree, domain=[-1, 1]
    #     )
    M = 8 * (degree + 1)
    k = np.arange(M)
    xs = np.cos(np.pi * (k + 0.5) / M)  # Chebyshev points (dense)
    poly = Chebyshev.fit(
        xs, reciprocal_approx(xs, w_min, B, scale), deg=degree, domain=[-1, 1]
    )

    even_coef = poly.coef[::2]
    assert np.allclose(even_coef, 0), "Non odd polynomial"
    poly.coef[::2] = 0
    return poly.coef


def get_numpy_cheb_trimmed(w_min, B, scale, degree, full_degree):

    poly = Chebyshev.interpolate(
        lambda x: reciprocal_approx(x, w_min, B, scale), full_degree, domain=[-1, 1]
    )

    even_coef = poly.coef[::2]
    assert np.allclose(even_coef, 0), "Non odd polynomial"
    poly.coef[::2] = 0
    return poly.coef[: degree + 1]


def get_cheb_coeff(
    w_min, degree, w_max=1, scale=1, method="interpolated", epsilon=0.01
):

    kappa = 1 / w_min
    B = int(kappa**2 * np.log(kappa / epsilon))
    j0 = int(np.sqrt(B * np.log(4 * B / epsilon)))
    print(
        f"For error {epsilon}, and given kappa, the needed polynomial degree is: 2*{j0}+1"
    )
    print(f"The Chebyshev LCU requires {j0.bit_length()} qubits")

    if method == "optimized":
        print(
            f"Performing convex optimization for the Chebyshev interpolation, with degree {degree}"
        )
        return optimize_inversion_polynomial(w_min, w_max, degree, scale)

    if method == "interpolated":
        print(f"Performing numpy Chebyshev interpolation, with degree {degree}")
        return get_numpy_cheb_interpolate(w_min, B, scale, degree)

    if method == "trimmed":
        print(
            f"Performing numpy Chebyshev interpolation, with degree {2*j0+1} and trimming to degree {degree}"
        )
        return get_numpy_cheb_trimmed(w_min, B, scale, degree, 2 * j0 + 1)


def plot_cheb_inv_approx(pcoefs, w_min, w_max=1, scale=1, half_space=True):
    if isinstance(pcoefs, np.ndarray):
        pcoefs = {"approximated": pcoefs}

    def eval_odd_cheb_poly(coef, x):
        return sum([coef[k] * eval_chebyt(2 * k + 1, x) for k in range(len(coef))])

    # Generate data for plotting
    if half_space:
        x_vals = np.linspace(0, w_max, 500)
    else:
        x_vals = np.linspace(-w_max, w_max, 500)

    xj_obj = x_vals[(np.abs(x_vals) >= w_min) & (np.abs(x_vals) <= w_max)]
    target_vals = scale * (w_min) / xj_obj

    # Plot the results
    fig, axes = plt.subplots(len(pcoefs), 1, figsize=(12, 12))
    axes = np.atleast_1d(axes)
    axes = axes.flatten()
    for i, (label, coeffs) in enumerate(pcoefs.items()):
        axes[i].plot(xj_obj, target_vals, "-k", label="Target Function", linewidth=2)
        axes[i].plot(
            x_vals,
            eval_odd_cheb_poly(coeffs[1::2], x_vals),
            label=label,
            linestyle="--",
        )

        axes[i].set_xlabel("x")
        axes[i].set_ylabel(rf"{scale}$\lambda_{{\min}}/x$")
        axes[i].set_title("Target Function vs. Approximated Polynomial")
        axes[i].legend()
        axes[i].grid(True)
