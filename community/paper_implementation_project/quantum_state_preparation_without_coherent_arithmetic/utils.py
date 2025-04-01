# Import relevant modules and methods.
import numpy as np
from pyqsp import angle_sequence, response
from pyqsp.poly import polynomial_generators, PolyTaylorSeries
from pyqsp.angle_sequence import QuantumSignalProcessingPhases
from classiq import QuantumProgram
from scipy.stats import norm
from scipy.integrate import quad


def find_angle(func, polydeg, max_scale, encoding="amplitude"):
    """
    With PolyTaylorSeries class, compute Chebyshev interpolant to degree
    'polydeg' (using twice as many Chebyshev nodes to prevent aliasing).
    """

    if encoding == "amplitude":
        phiset = compute_qsvt_phases(poly=func, degree=polydeg, max_scale=max_scale)
        return phiset
    elif encoding == "imaginary":
        # Compute full phases (and reduced phases, parity) using symmetric QSP.
        poly = PolyTaylorSeries().taylor_series(
            func=func,
            degree=polydeg,
            max_scale=max_scale,
            chebyshev_basis=True,
            cheb_samples=2 * polydeg,
        )

        (phiset, red_phiset, parity) = angle_sequence.QuantumSignalProcessingPhases(
            poly, method="sym_qsp", chebyshev_basis=True
        )
        # (phiset) = angle_sequence.QuantumSignalProcessingPhases(poly, method="laurent")

        # true_func = lambda x: max_scale * func(x)  # For error, include scale.
        # response.PlotQSPResponse(
        #     phiset, pcoefs=poly, target=true_func, sym_qsp=True, simul_error_plot=True
        # )

        return phiset, red_phiset, parity
    else:
        raise ValueError("Invalid encoding type.")


def adjust_qsvt_conventions(phases: np.ndarray, degree: int) -> np.ndarray:
    phases = np.array(phases)
    phases = phases - np.pi / 2
    phases[0] = phases[0] + np.pi / 4
    phases[-1] = phases[-1] + np.pi / 2 + (2 * degree - 1) * np.pi / 4

    # verify conventions. minus is due to exp(-i*phi*z) in qsvt in comparison to qsp
    return -2 * phases


def compute_qsvt_phases(poly, degree, max_scale):
    chebyshev_poly = PolyTaylorSeries().taylor_series(
        func=poly,
        degree=degree,
        max_scale=max_scale,
        chebyshev_basis=True,
        cheb_samples=degree,
    )
    phases = QuantumSignalProcessingPhases(
        chebyshev_poly, signal_operator="Wx", method="laurent", measurement="x"
    )
    return adjust_qsvt_conventions(phases, degree).tolist()


def normalize(list):
    return list / np.sum(list)


def amp_to_prob(amplitude):
    return (np.linalg.norm(amplitude)) ** 2


def h(f, min, max):
    """
    Eq. (3) in https://arxiv.org/pdf/2210.14892
    """
    return lambda y: f((max - min) * np.arcsin(y) + min)


def h_scale(h):
    """
    Maximal value of h(y) in the y interval [0, sin(1)]. (i.e, maximal value of f(x) in the x interval [a, b])
    """
    raise NotImplementedError


def h_hat(h, h_max):
    """
    Eq. (4) in https://arxiv.org/pdf/2210.14892
    """
    return lambda y: h(y) / h_max


def get_metrics(qprog):
    """
    Extract circuit metrics from a quantum program.

    Parameters:
        qprog: The quantum program object.

    Returns:
        dict: A dictionary containing the circuit metrics:
              - "depth": Circuit depth.
              - "width": Circuit width (number of qubits used).
              - "cx_count": Number of CX gates (returns 0 if none are present).
    """
    # Generate the optimized quantum circuit
    circuit = QuantumProgram.from_qprog(qprog)

    # Extract metrics
    metrics = {
        "depth": circuit.transpiled_circuit.depth,
        "width": circuit.data.width,
        "cx_count": circuit.transpiled_circuit.count_ops.get(
            "cx", 0
        ),  # Default to 0 if 'cx' not found
    }

    return metrics


# def discretized_l2_norm(f, N, min, max):
#     """
#     Compute the discretized L2-norm of the function f over the interval [a, b] with N points.

#     Eq. (6) in https://arxiv.org/pdf/2210.14892

#     Args:
#         f (function): The function to evaluate.
#         N (int): The number of discretization points.
#         min (float): The start of the interval.
#         max (float): The end of the interval.

#     Returns:
#         float: The discretized L2-norm of the function.
#     """
#     x = np.linspace(min, max, N)
#     f_values = f(x)
#     l2_norm = np.sqrt((max - min) / N * np.sum(np.abs(f_values) ** 2))
#     return l2_norm


# def l2_norm_filling_fraction(f, N, min, max):
#     """
#     Compute the L2-norm filling-fraction of the function f over the interval [a, b] with N points.

#     Eq. (7) in https://arxiv.org/pdf/2210.14892

#     Args:
#         f (function): The function to evaluate.
#         N (int): The number of discretization points.
#         min (float): The start of the interval.
#         max (float): The end of the interval.

#     Returns:
#         float: The L2-norm filling-fraction of the function.
#     """
#     l2_norm_discretized = discretized_l2_norm(f, N, min, max)
#     f_max = np.max(np.abs(f(np.linspace(min, max, N))))
#     # l2_norm_continuous = np.sqrt(np.trapz(np.abs(f(np.linspace(a, b, 1000))) ** 2, np.linspace(a, b, 1000)))
#     filling_fraction = l2_norm_discretized / np.sqrt((max - min) * f_max**2)
#     return filling_fraction


def squared_gaussian_integral(a, b, mean=0.0, sigma=1.0):
    """
    Computes the integral of f(x)^2 from a to b,
    where f(x) is the Gaussian PDF with mean=0 and std=sigma.
    """
    prefactor = 1 / (2 * np.pi * sigma**2)

    def integrand(x):
        return prefactor * np.exp(-((x - mean) ** 2) / sigma**2)

    result, _ = quad(integrand, a, b)
    return result


def gaussian_max(a, b, mean=0.0, sigma=1.0):
    x1 = a
    x2 = b
    x3 = 0
    if a < mean and b > mean:
        x3 = mean
    else:
        x3 = a
    X = np.array([x1, x2, x3])
    return max(norm.pdf(X, mean, sigma))


def get_gaussian_amplitude(a, b, mean=0.0, sigma=1.0, factor=1.45):
    Numerator = np.sqrt(squared_gaussian_integral(a, b, mean, sigma))
    Denominator = np.sqrt((b - a)) * gaussian_max(a, b, mean, sigma)
    return (Numerator / Denominator) * (factor / 2.0)
