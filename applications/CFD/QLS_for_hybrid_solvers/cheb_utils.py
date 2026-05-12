import numpy as np
from numpy.polynomial.chebyshev import Chebyshev


def reciprocal_approx(x, w_min, B, scale):
    x = np.asarray(x, dtype=float)
    num = 1.0 - (1.0 - x * x) ** B
    out = np.empty_like(x)
    nz = x != 0
    out[nz] = scale * w_min * num[nz] / x[nz]
    out[~nz] = 0.0
    return out


def get_numpy_cheb_trimmed(w_min, B, scale, degree, full_degree):
    poly = Chebyshev.interpolate(
        lambda x: reciprocal_approx(x, w_min, B, scale), full_degree, domain=[-1, 1]
    )
    even_coef = poly.coef[::2]
    assert np.allclose(even_coef, 0), "Non-odd polynomial"
    poly.coef[::2] = 0
    return poly.coef[: degree + 1]


def endpoints_line_fit(odd_coeffs: np.ndarray):
    """
    Return (m, b) for the line y = m*x + b that connects the first and last
    points of y = odd_coeffs[0::2] plotted against x = 2*arange(len(y)).
    """
    y = np.asarray(odd_coeffs)[0::2]
    if y.size < 2:
        raise ValueError("Need at least two points to define a line from endpoints.")
    x_last = 2 * (y.size - 1)  # since x = 2*arange(...)
    m = (y[-1] - y[0]) / x_last
    b = y[0]  # because x[0] = 0
    return m, b


def fit_linear_coeffs_for_cheb(cheb_coefs):
    coeffs_to_fit = np.abs(cheb_coefs[1::2])
    m, b = endpoints_line_fit(coeffs_to_fit)
    fitted_cheb_coeffs = np.array(
        [(-1) ** k * (b + k * m) for k in range(len(coeffs_to_fit))]
    )
    print(f"linear fit parameters: slope = {m}, b= {b}")
    return fitted_cheb_coeffs
