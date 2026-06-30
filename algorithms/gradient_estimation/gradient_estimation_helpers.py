from classiq import *
from typing import List
import numpy as np
import pandas as pd
from dataclasses import dataclass
from matplotlib import pyplot as plt
from classiq.qmod.symbolic import pi
import logging
from typing import Callable

# %matplotlib widget

# Module-level globals populated by params.unpack(globals()).
# Defaults match params class defaults.
l = 0.5
m = 2
n = 3
n0 = 3
N = 2**n
N0 = 2**n0
f = None
f_prams = None
f_normalized = None


@dataclass
class params:
    # Algorithm parameters
    l = 0.5
    m = 2
    n = 3
    n0 = 3

    @property
    def N(self):
        return 2**self.n

    @property
    def N0(self):
        return 2**self.n0

    # Function parameters
    f = None
    f_prams = None
    f_name = None

    def set_function(self, f, f_prams):
        self.f_prams = f_prams

        # Allow passing by name, e.g. "linear" or "quadratic"
        if isinstance(f, str):
            self.f_name = f
            self.f = getattr(self, f)
            return

        # If a method from another params instance is passed,
        # re-bind it to this instance to avoid mixed state.
        if hasattr(f, "__func__"):
            self.f = f.__func__.__get__(self, self.__class__)
        else:
            self.f = f

        self.f_name = getattr(self.f, "__name__", None)

    # Generated functions
    def f_normalized(self, x):
        val = self.f(self.l / self.N * x)
        val *= self.N / (self.l * self.m)
        return val

    def analytical_gradient(self, x):
        if self.f_name == "linear":
            return self.f_prams[0]
        elif self.f_name == "quadratic":
            return 2 * self.f_prams[0] * x + self.f_prams[1]
        else:
            raise NotImplementedError(
                "Analytical gradient not implemented for this function."
            )

    # A few example functions
    def linear(self, x):
        return self.f_prams[0] * x + self.f_prams[1]

    def quadratic(self, x):
        return self.f_prams[0] * x**2 + self.f_prams[1] * x + self.f_prams[2]

    # Unpack function, to be used in the notebook.
    # Pass globals() from the notebook cell so variables are injected there too:
    #   p.unpack(globals())
    def unpack(self, namespace=None):
        import sys

        vals = dict(
            l=self.l,
            m=self.m,
            n=self.n,
            n0=self.n0,
            N=self.N,
            N0=self.N0,
            f=self.f,
            f_prams=self.f_prams,
            f_normalized=self.f_normalized,
        )
        # Update this module's globals so helper functions (state_to_gradient, etc.) work
        vars(sys.modules[self.__class__.__module__]).update(vals)
        # Update the notebook's globals if provided
        if namespace is not None:
            namespace.update(vals)


# ****** Simulation ******
def run_statevector_simulation(
    qfunc_to_run, print_circuit_info=False, filter_ancilla=False, show_circuit=False
):
    # Run a statevector simulator
    qprog = synthesize(qfunc_to_run)
    if show_circuit:
        show(qprog)
    if print_circuit_info:
        print("Circuit Width:", qprog.data.width)
        print("Circuit Depth:", qprog.transpiled_circuit.depth)
        print("Gate Counts:", qprog.transpiled_circuit.count_ops)

    if filter_ancilla:
        df = calculate_state_vector(qprog, filters={"ancilla": 0})
    else:
        df = calculate_state_vector(qprog)
    df.sort_values(by="x", inplace=True)

    return df


# ****** Result Processing ******
def state_to_gradient(value, p):
    if type(value) == list:
        result = []
        for v in value:
            result.append(state_to_gradient(v, p))
        return result
    return value / (p.N / p.m)


def simplify_df(df, unwrap=True):
    # Get the phase from the df
    phases = np.angle(df["amplitude"]).astype(float)
    phases_over_2pi = phases / (2 * np.pi)
    f_classical = f_normalized(df["x"])
    simplified_df = pd.DataFrame(
        {"f_classical": f_classical, "phase_over_2pi": phases_over_2pi.round(5)}
    )
    simplified_df.index = df["x"]
    simplified_df.sort_index(inplace=True)

    # Unwrap the phase if requested
    if unwrap:
        # Unwrap the phase
        simplified_df["phase_over_2pi"] = np.unwrap(
            simplified_df["phase_over_2pi"], period=1
        )
        # Get rid of the global phase
        simplified_df["phase_over_2pi"] -= simplified_df["phase_over_2pi"].iloc[N // 2]
        simplified_df["f_classical"] -= simplified_df["f_classical"].iloc[N // 2]

    return simplified_df


def compute_success_rate(df, analytic_derivatives, p, tolerance=None):
    total_shots = int(df["counts"].sum())
    if total_shots == 0:
        return 0.0, 0, 0
    if tolerance is None:
        tolerance = 0.5 * p.m / p.N

    success_shots = 0

    for _, row in df.iterrows():
        correct = True
        for name, analytic_val in analytic_derivatives.items():
            measured_val = row[name]

            if isinstance(analytic_val, list):
                measured_val = state_to_gradient(measured_val, p)
                if measured_val is None or any(
                    abs(m - a) >= tolerance for m, a in zip(measured_val, analytic_val)
                ):
                    correct = False
                    break
            else:
                measured_val = state_to_gradient(measured_val, p)
                if (
                    measured_val is None
                    or abs(measured_val - analytic_val) >= tolerance
                ):
                    correct = False
                    break

        if correct:
            success_shots += int(row["counts"])

    success_rate = success_shots / total_shots
    return success_rate, success_shots, total_shots


def analyze_results(df, p):
    analytical_gradient = p.analytical_gradient(0)

    print("Parsed probabilities:", df.set_index("x").to_dict()["probability"])
    print(f"The analytical gradient is: {analytical_gradient}")
    majority_state = dict(df.iloc[0])
    majority_gradient = state_to_gradient(majority_state.get("x"), p)
    print(f"The majority gradient is: {majority_gradient}")

    resolution = m / N
    is_correct = abs(majority_gradient - analytical_gradient) < resolution / 2
    print(f"The majority result is", "correct" if is_correct else "incorrect")
    print("####################################################")

    success_rate, success_shots, total_shots = compute_success_rate(
        df, analytic_derivatives={"x": analytical_gradient}, p=p
    )
    print(f"Success rate: {success_rate:.2%} ({success_shots}/{total_shots} shots)")
    show_bar(success_rate)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

    x_array = np.arange(-N // 2, N // 2)
    f_classical = f_normalized(x_array)
    f_classical -= f_classical[N // 2]

    plt.sca(ax1)
    plot_classical()
    ax1.plot(x_array, f_classical, "o", label="Theoretical values", markersize=8)
    xmin, xmax = -N, N
    ymin, ymax = -N // 2, N // 2
    ax1.set_xlim(xmin, xmax)
    ax1.set_ylim(ymin, ymax)
    ax1.vlines(-N // 2, ymin, ymax, colors="lightgray", linestyles="dashed")
    ax1.vlines(N // 2 - 1, ymin, ymax, colors="lightgray", linestyles="dashed")
    ax1.hlines(-N / 4 + 0.5, xmin, xmax, colors="lightgray", linestyles="dashed")
    ax1.hlines(N / 4, xmin, xmax, colors="lightgray", linestyles="dashed")
    ax1.legend(fontsize=12)
    ax1.set_title("Theoretical Phases", fontsize=14, fontweight="bold")
    ax1.tick_params(labelsize=11)
    ax1.set_xlabel("x (index)", fontsize=12)
    ax1.set_ylabel("f (normalized)", fontsize=12)

    plt.sca(ax2)
    percentage = df["counts"] / df["counts"].sum() * 100
    ax2.bar(df["x"], percentage, color="lightblue", label="Measurement counts")
    ax2.set_xlabel("x (index)", fontsize=12)
    ax2.set_ylabel("Percentage of shots (%)", fontsize=12)
    ax2.set_xlim(-N // 2 - 1, N // 2)
    ax2.set_ylim(0, 100)
    ax2.set_title("Measurement Histogram", fontsize=14, fontweight="bold")
    ax2.tick_params(labelsize=11)
    if analytical_gradient is not None:
        x_analytic = analytical_gradient * (N / m)
        ax2.axvline(
            x=x_analytic,
            color="green",
            linestyle="dashed",
            label="Analytical gradient",
            linewidth=2,
        )
    ax2.legend(fontsize=12)

    plt.tight_layout()
    plt.show()
    return success_rate


# ****** Plotting ******
def plot_classical():
    x_values = np.linspace(-N, N, 1000)
    f_values = f_normalized(x_values)
    f_values -= f_normalized(0)
    plt.plot(x_values, f_values, color="lightgray", label="Original function")
    ax = plt.gca()
    ax.set_xticks(np.arange(-N // 2, N // 2))
    ax.set_xticklabels([str(i) for i in range(-N // 2, N // 2)])

    # Primary-axis labels (normalized coordinates)
    ax.set_xlabel("x (index)")
    ax.set_ylabel("f (normalized)")

    # Secondary X axis: signed quantum index -> real x  (x_real = x * l/N)
    x_to_real = lambda x: x * (l / N)
    real_to_x = lambda xr: xr * (N / l)
    secax_x = ax.secondary_xaxis("top", functions=(x_to_real, real_to_x), color="blue")
    secax_x.set_xlabel("x (real)")

    # Secondary Y axis: normalized f -> unnormalized f
    f_to_real = lambda y: (y + f_normalized(0)) * m * l / N
    real_to_f = lambda yr: yr / m / l * N - f_normalized(0)
    secax_y = ax.secondary_yaxis(
        "right", functions=(f_to_real, real_to_f), color="blue"
    )
    secax_y.set_ylabel("f (real, unnormalized)")


def style_subplots(ax1, ax2):
    for ax in [ax1, ax2]:
        ax.set_xlabel("x (index)", fontsize=12)
        ax.tick_params(labelsize=11)


def plot_theoretical(show=True):
    x_array = np.arange(-N // 2, N // 2)

    f_classical = f_normalized(x_array)
    f_classical -= f_classical[N // 2]  # index N//2 in [-N/2..N/2-1] is x=0

    if show:
        plt.figure()
    plot_classical()
    plt.plot(x_array, f_classical, "o", label="Theoretical values")
    xmin, xmax = -N, N
    ymin, ymax = -N // 2, N // 2
    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)
    plt.vlines(-N // 2, ymin, ymax, colors="lightgray", linestyles="dashed")
    plt.vlines(N // 2 - 1, ymin, ymax, colors="lightgray", linestyles="dashed")
    plt.hlines(-N / 4 + 0.5, xmin, xmax, colors="lightgray", linestyles="dashed")
    plt.hlines(N / 4, xmin, xmax, colors="lightgray", linestyles="dashed")
    plt.legend()
    if show:
        plt.show()


def plot_histogram(df, analytical_gradient=None, show=True):
    plt.figure()
    percentage = df["counts"] / df["counts"].sum() * 100
    plt.bar(df["x"], percentage, color="lightblue", label="Measurement counts")
    plt.xlabel("x (index)")
    plt.ylabel("Percentage of shots (%)")
    plt.xlim(-N // 2 - 1, N // 2)
    plt.ylim(0, 100)
    plt.title("Measurement Histogram")
    plt.legend()
    # plot the analytical gradient as a vertical line if provided
    if analytical_gradient is not None:
        x_analytic = analytical_gradient * (N / m)
        plt.axvline(
            x=x_analytic, color="green", linestyle="dashed", label="Analytical gradient"
        )
        plt.legend()
    if show:
        plt.show()


def plot_simplified_df(simplified_df, show=True):
    plt.figure()
    plot_theoretical(show=False)
    plt.plot(
        simplified_df.index,
        simplified_df["phase_over_2pi"],
        ".",
        label="Measured phases",
    )
    plt.legend()
    if show:
        plt.show()


def show_bar(success_rate):
    bar_length = 50
    filled = int(round(bar_length * success_rate))
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

    bar = f"{GREEN}{'█' * filled}{RED}{'-' * (bar_length - filled)}{RESET}"

    print(f"[{bar}] {success_rate * 100:.2f}%")
