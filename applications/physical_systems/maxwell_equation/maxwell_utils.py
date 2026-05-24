from typing import Callable

import numpy as np
import pandas as pd
import scipy.linalg
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from classiq import *


def fidelity(a: np.ndarray, b: np.ndarray) -> float:
    """
    fidelity of the normalized vectors
    """
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(abs(np.vdot(a, b)) ** 2)


def vaildate_block_encoding(
    block_encoding: QCallable[QNum, QNum],
    block_size: int,
    ref_mat: np.ndarray,
    expected_scale=None,
    show: bool = False,
) -> None:
    dim = int(ref_mat.shape[0]).bit_length() - 1

    vec = np.random.rand(2**dim)
    vec /= np.linalg.norm(vec)

    @qfunc
    def main(state: Output[QNum], block: Output[QNum]):
        prepare_amplitudes(list(vec), 0, state)
        from classiq import allocate

        allocate(block_size, block)
        block_encoding(state, block)

    execution_prefs = ExecutionPreferences(
        num_shots=1,
        backend_preferences=ClassiqBackendPreferences(
            backend_name=ClassiqSimulatorBackendNames.SIMULATOR_STATEVECTOR
        ),
        include_zero_amplitude_outputs=True,
    )
    qprog = synthesize(main, auto_show=show)
    with ExecutionSession(qprog, execution_preferences=execution_prefs) as es:
        es.set_measured_state_filter("block", lambda state: state == 0)
        res = es.sample()

    df = res.dataframe.sort_values("state")
    vec_res = df[(df.block == 0)].amplitude.values
    vec_expected = ref_mat @ vec
    quantum_fidelity = fidelity(vec_res, vec_expected)

    print(f"Fidelity: {quantum_fidelity:.6f}")
    print(
        f"Encoding Scaling: {np.linalg.norm(vec_expected)/np.linalg.norm(vec_res):.6f}",
        f"Expected: {expected_scale:.6f}" if expected_scale is not None else "",
    )


def normalize_phase(data: np.ndarray) -> np.ndarray:
    """
    Normalize the phase of a complex vector so that the maximum amplitude is real and positive.
    This is useful for comparing quantum and classical solutions up to a global phase.
    """
    _max = max(data, key=np.abs)
    return data * (np.abs(_max) / _max)


def get_block_encoding(
    block_encoding: QCallable[QNum, QNum],
    state_size: int,
    block_size: int,
    show: bool = False,
) -> np.ndarray:
    """
    Retrieve the block-encoded matrix using the reference trick.

    Creates a maximally entangled state between a data register and a
    reference register, applies the block encoding, then reconstructs the
    encoded matrix from the statevector amplitudes (projected onto block==0).

    Args:
        block_encoding: A QCallable operating on (state: QNum, block: QNum).
        state_size: Number of qubits in the state (data) register.
        block_size: Number of qubits in the block register.

    Returns:
        The block-encoded matrix as a complex numpy array of shape
        (2**state_size, 2**state_size).
    """

    @qfunc
    def prepare_ref(data: QNum, data_ref: Output[QNum]):
        hadamard_transform(data)
        data_ref |= data

    @qfunc
    def main(
        state: Output[QNum],
        state_ref: Output[QNum],
        block: Output[QNum],
    ):
        allocate(state_size, state)
        prepare_ref(state, state_ref)
        allocate(block_size, block)
        block_encoding(state, block)

    qprog = synthesize(
        main,
        preferences=Preferences(optimization_level=0),
        constraints=Constraints(optimization_parameter="width"),
        auto_show=show,
    )

    execution_prefs = ExecutionPreferences(
        num_shots=1,
        backend_preferences=ClassiqBackendPreferences(
            backend_name=ClassiqSimulatorBackendNames.SIMULATOR_STATEVECTOR
        ),
        include_zero_amplitude_outputs=True,
    )

    with ExecutionSession(qprog, execution_preferences=execution_prefs) as es:
        es.set_measured_state_filter("block", lambda val: val == 0)
        res = es.sample()

    df = res.dataframe
    df = df[(df.block == 0) & (np.abs(df.amplitude) > 1e-12)].copy()
    df["amplitude_real"] = np.real(normalize_phase(df.amplitude))
    df["amplitude_imag"] = np.imag(normalize_phase(df.amplitude))

    dim = 2**state_size
    full_mat = np.zeros((dim, dim), dtype=complex)
    for i, part in enumerate(["real", "imag"]):
        matrix = df.pivot_table(
            index="state",
            columns="state_ref",
            values=f"amplitude_{part}",
            fill_value=0,
        )
        full_index = np.arange(dim)
        matrix = matrix.reindex(index=full_index, columns=full_index, fill_value=0)
        matrix_np = matrix.to_numpy() * np.sqrt(dim)
        full_mat += matrix_np.astype("complex128") * [1, 1j][i]

    if np.isclose(np.linalg.norm(np.imag(full_mat)), 0):
        full_mat = np.real(full_mat)

    return full_mat


def run_simulation(
    main_func,
    # backend_name=ClassiqSimulatorBackendNames.SIMULATOR_STATEVECTOR,
    backend_name=ClassiqNvidiaBackendNames.SIMULATOR_STATEVECTOR,
    block_name: str | None = "block",
    show: bool = False,
) -> tuple[pd.DataFrame, QuantumProgram]:
    from classiq.interface.generator.model.preferences.preferences import (
        TranspilationOption,
    )

    qmod = create_model(
        main_func,
        constraints=Constraints(max_width=1000),
        preferences=Preferences(
            transpilation_option=TranspilationOption.NONE,
            timeout_seconds=10 * 60,
            symbolic_loops=True,
        ),
    )
    print("Synthesizing...")
    qprog = synthesize(qmod, auto_show=show)
    print("Synthesis completed.")
    execution_prefs = ExecutionPreferences(
        num_shots=1,
        backend_preferences=ClassiqBackendPreferences(backend_name=backend_name),
        transpile_to_hardware=TranspilationOption.INTENSIVE,
    )
    print("Starting execution...")
    with ExecutionSession(qprog, execution_preferences=execution_prefs) as es:
        if block_name is not None:
            es.set_measured_state_filter(block_name, lambda state: state == 0)
        res = es.sample()
    print("Execution completed.")

    return res.dataframe, qprog


def dataframe_to_state_vector(
    df: pd.DataFrame, struct_name: str = "em_state"
) -> tuple[np.ndarray, int, int]:
    """
    Reconstruct the state vector from a Classiq execution dataframe.

    Filters for block == 0, infers L_x and L_y from the data, and builds
    the 4*L_x*L_y complex amplitude vector using the y*L_x + x spatial
    indexing convention.

    Returns:
        (vec, L_x, L_y) where vec has length 4*L_x*L_y.
    """
    col_x = f"{struct_name}.x"
    col_y = f"{struct_name}.y"
    col_dir = f"{struct_name}.direction"
    col_field = f"{struct_name}.field"

    df_block0 = df[df["block"] == 0].copy()
    L_x = int(df_block0[col_x].max()) + 1
    L_y = int(df_block0[col_y].max()) + 1
    LL = L_x * L_y
    vec = np.zeros(4 * LL, dtype=complex)
    for _, row in df_block0.iterrows():
        idx = (
            int(row[col_field]) * 2 * LL
            + int(row[col_dir]) * LL
            + int(row[col_y]) * L_x
            + int(row[col_x])
        )
        vec[idx] = row.amplitude
    return vec, L_x, L_y


def plot_fields_from_dataframe(
    df: pd.DataFrame,
    title: str = "",
    struct_name: str = "em_state",
    field_vmax: np.ndarray | list[float] | None = None,
) -> None:
    """
    Plot Ez, Bx, By from a classiq execution dataframe whose main function
    outputs (em_state: EMState, block: QNum).
    """
    vec, L_x, L_y = dataframe_to_state_vector(df, struct_name)
    plot_fields(vec, L_x, L_y, title, field_vmax)


def fields_max_abs(vec: np.ndarray | list[float], L_x: int, L_y: int) -> np.ndarray:
    """
    Return the max absolute value of each field component (Ez, Hx, Hy)
    Useful as a reference scale for ``plot_fields``.
    """
    vec = np.asarray(vec)
    LL = L_x * L_y
    components = [vec[0:LL], vec[2 * LL : 3 * LL], vec[3 * LL : 4 * LL]]
    return np.array([np.max(np.abs(comp.real)) for comp in components])


def plot_fields(
    vec: np.ndarray | list[float],
    L_x: int,
    L_y: int,
    title: str = "",
    field_vmax: np.ndarray | list[float] | None = None,
) -> None:
    """
    Plot Ez, Hx, Hy from a state vector.

    Args:
        vec: State vector of length 4*L_x*L_y.
        L_x, L_y: Grid dimensions.
        title: Figure title.
        field_vmax: Optional array of 3 normalization values (one per field).
            When provided, the color scale for each field is [-field_vmax[i], field_vmax[i]]
            and no per-field self-normalization is applied. Useful for plotting
            differences on the same scale as a reference solution.
    """
    vec = np.asarray(vec)
    vec = normalize_phase(vec)

    LL = L_x * L_y
    components = [vec[0:LL], vec[2 * LL : 3 * LL], vec[3 * LL : 4 * LL]]
    data = [comp.reshape(L_y, L_x).real for comp in components]

    if field_vmax is None:
        raw_max = fields_max_abs(vec, L_x, L_y)
        data_max = np.where(raw_max > 0, raw_max, 1.0)
        data = [d / m for d, m in zip(data, data_max)]
        plot_max = np.array([np.max(np.abs(d)) for d in data])
    else:
        field_vmax = np.asarray(field_vmax, dtype=float)
        plot_max = np.where(field_vmax > 0, field_vmax, 1.0)

    names = ("Ez", "Hx", "Hy")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    if title:
        fig.suptitle(title)
    for ind in range(3):
        ax = axes[ind]
        im = ax.imshow(
            data[ind],
            origin="lower",
            aspect="equal",
            vmin=-plot_max[ind],
            vmax=plot_max[ind],
            cmap="twilight",
        )
        ax.set_title(names[ind])
        plt.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.show()


def build_maxwell_evolution_matrix(
    L_x: int,
    L_y: int,
    bottom_x: int,
    top_x: int,
    bottom_y: int,
    top_y: int,
) -> np.ndarray:
    """
    Build the anti-symmetric Maxwell evolution matrix on a Yee lattice with
    PEC exterior boundary conditions and a rectangular PEC obstacle.

    Args:
        L_x, L_y: Grid dimensions (must be powers of 2).
        bottom_x, top_x, bottom_y, top_y: Rectangle obstacle bounds.

    Returns:
        The anti-symmetric evolution matrix of shape (4*L_x*L_y, 4*L_x*L_y).
    """
    LL = L_x * L_y

    id_Lx = np.eye(L_x, dtype=float)
    id_Ly = np.eye(L_y, dtype=float)
    zero_LL = np.zeros((LL, LL), dtype=float)

    _grad_b_x = id_Lx - np.roll(id_Lx, 1, 0)
    _grad_f_x = np.roll(id_Lx, -1, 0) - id_Lx
    _grad_b_y = id_Ly - np.roll(id_Ly, 1, 0)
    _grad_f_y = np.roll(id_Ly, -1, 0) - id_Ly

    grad_b_x = (
        np.tensordot(id_Ly, _grad_b_x, axes=0).transpose(0, 2, 1, 3).reshape(LL, LL)
    )
    grad_b_y = (
        np.tensordot(_grad_b_y, id_Lx, axes=0).transpose(0, 2, 1, 3).reshape(LL, LL)
    )
    grad_f_x = (
        np.tensordot(id_Ly, _grad_f_x, axes=0).transpose(0, 2, 1, 3).reshape(LL, LL)
    )
    grad_f_y = (
        np.tensordot(_grad_f_y, id_Lx, axes=0).transpose(0, 2, 1, 3).reshape(LL, LL)
    )

    mat_em = np.block(
        [
            [zero_LL, zero_LL, -grad_b_y, grad_b_x],
            [zero_LL, zero_LL, zero_LL, zero_LL],
            [-grad_f_y, zero_LL, zero_LL, zero_LL],
            [grad_f_x, zero_LL, zero_LL, zero_LL],
        ]
    )

    # PEC exterior boundary conditions
    mat_em[1:L_x, :] = 0
    mat_em[:, 1:L_x] = 0
    mat_em[L_x:LL:L_x, :] = 0
    mat_em[:, L_x:LL:L_x] = 0

    # Rectangle obstacle boundary conditions
    if top_x > bottom_x and top_y > bottom_y:
        ins = []
        for iy in range(bottom_y, top_y):
            for ix in range(bottom_x, top_x):
                ins.append(iy * L_x + ix)
        outs = list(set(range(4 * LL)) - set(ins))
        for in_ in ins:
            for out_ in outs:
                mat_em[in_, out_] = 0
                mat_em[out_, in_] = 0

    assert np.isclose(
        np.sum(np.abs(mat_em + mat_em.T)), 0
    ), "Matrix is not anti-symmetric"

    return mat_em


def build_initial_state_vector(
    L_x: int,
    L_y: int,
    initial_state_func: Callable[[float, float, int, int], float],
    normalize: bool = True,
) -> np.ndarray:
    """
    Build the initial state vector by evaluating a callable on every grid point.

    The state vector has length 4*L_x*L_y, indexed as
    field * 2*LL + direction * LL + y * L_x + x  (LL = L_x * L_y).

    Args:
        L_x, L_y: Grid dimensions.
        initial_state_func: Callable(x, y, direction, field) -> float.
        normalize: If True, normalize the vector to unit norm.

    Returns:
        The state vector of shape (4*L_x*L_y,).
    """
    LL = L_x * L_y
    state = np.zeros(4 * LL, dtype=float)
    for field in range(2):
        for direction in range(2):
            for iy in range(L_y):
                for ix in range(L_x):
                    idx = field * 2 * LL + direction * LL + iy * L_x + ix
                    state[idx] = initial_state_func(
                        float(ix), float(iy), direction, field
                    )
    if normalize:
        norm = np.linalg.norm(state)
        if norm > 0:
            state = state / norm
    return state


def classical_maxwell_simulation(
    L_x: int,
    L_y: int,
    coeff: float,
    initial_state_func: Callable[[float, float, int, int], float],
    bottom_x: int,
    top_x: int,
    bottom_y: int,
    top_y: int,
) -> np.ndarray:
    """
    Classical reference simulation for 2D Maxwell equations on a Yee lattice.

    Builds the anti-symmetric evolution matrix with PEC exterior boundary conditions
    and a rectangular PEC obstacle, then computes exp(coeff * A) @ initial_state.

    Args:
        L_x, L_y: Grid dimensions (must be powers of 2).
        coeff: Evolution coefficient (c * dt / dL).
        initial_state_func: Callable(x, y, direction, field) -> float returning the
            amplitude at each grid point.
        bottom_x, top_x, bottom_y, top_y: Rectangle obstacle bounds.

    Returns:
        The evolved state vector.
    """
    initial_state = build_initial_state_vector(L_x, L_y, initial_state_func)
    mat_em = build_maxwell_evolution_matrix(L_x, L_y, bottom_x, top_x, bottom_y, top_y)
    exp_em = scipy.linalg.expm(coeff * mat_em)
    return exp_em @ initial_state


def plot_geometry(
    L_x: int,
    L_y: int,
    bottom_x: int,
    top_x: int,
    bottom_y: int,
    top_y: int,
    mu_x: float | None = None,
    mu_y: float | None = None,
    sigma_x: float | None = None,
    sigma_y: float | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 7))

    for i in range(L_x + 1):
        ax.plot([i, i], [0, L_y], color="lightgray", linewidth=0.5)
    for j in range(L_y + 1):
        ax.plot([0, L_x], [j, j], color="lightgray", linewidth=0.5)

    xs, ys = np.meshgrid(range(L_x), range(L_y))
    ax.scatter(xs, ys, s=8, color="dimgray", zorder=2, alpha=0.7)

    exterior = mpatches.Rectangle(
        (0, 0),
        L_x,
        L_y,
        linewidth=2.5,
        edgecolor="navy",
        facecolor="none",
    )
    ax.add_patch(exterior)

    if top_x > bottom_x and top_y > bottom_y:
        obstacle = mpatches.Rectangle(
            (bottom_x, bottom_y),
            top_x - 1 - bottom_x,
            top_y - 1 - bottom_y,
            linewidth=2,
            edgecolor="firebrick",
            facecolor="mistyrose",
            zorder=4,
        )
        ax.add_patch(obstacle)
        ax.text(
            (bottom_x + top_x) / 2,
            (bottom_y + top_y) / 2,
            "PEC\nobstacle",
            ha="center",
            va="center",
            fontsize=9,
            color="firebrick",
            fontweight="bold",
            zorder=5,
        )

    if mu_x is not None and mu_y is not None:
        ax.plot(
            mu_x,
            mu_y,
            "x",
            color="darkorange",
            markersize=12,
            markeredgewidth=2.5,
            zorder=5,
        )
        if sigma_x is not None and sigma_y is not None:
            ellipse = mpatches.Ellipse(
                (mu_x, mu_y),
                2 * sigma_x,
                2 * sigma_y,
                linewidth=1.5,
                edgecolor="darkorange",
                facecolor="darkorange",
                alpha=0.15,
            )
            ax.add_patch(ellipse)
        ax.annotate(
            r"$E_z$ initial",
            (mu_x, mu_y),
            textcoords="offset points",
            xytext=(10, 10),
            fontsize=10,
            color="darkorange",
            fontweight="bold",
        )

    ax.text(
        L_x / 2,
        -0.6,
        "PEC boundary",
        ha="center",
        fontsize=9,
        color="navy",
    )

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(-0.5, L_x + 0.5)
    ax.set_ylim(-0.8, L_y + 0.5)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"Simulation geometry ({L_x} x {L_y})")
    ax.set_xticks(range(0, L_x + 1, max(1, L_x // 4)))
    ax.set_yticks(range(0, L_y + 1, max(1, L_y // 4)))
    ax.tick_params(axis="both", pad=2, length=3)
    plt.tight_layout()
    plt.show()


def plot_yee_lattice(nx: int = 4, ny: int = 4) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))

    for i in range(nx + 1):
        ax.plot([i, i], [0, ny], color="lightgray", linewidth=0.8)
    for j in range(ny + 1):
        ax.plot([0, nx], [j, j], color="lightgray", linewidth=0.8)

    for i in range(nx):
        for j in range(ny):
            ax.plot(i, j, "s", color="royalblue", markersize=8, zorder=3)

    a = 0.18
    for i in range(nx):
        for j in range(ny):
            ax.annotate(
                "",
                xy=(i + a, j + 0.5),
                xytext=(i - a, j + 0.5),
                arrowprops=dict(arrowstyle="->", color="crimson", lw=1.8),
                zorder=3,
            )

    for i in range(nx):
        for j in range(ny):
            ax.annotate(
                "",
                xy=(i + 0.5, j + a),
                xytext=(i + 0.5, j - a),
                arrowprops=dict(arrowstyle="->", color="forestgreen", lw=1.8),
                zorder=3,
            )

    ez_patch = mpatches.Patch(color="royalblue", label=r"$E_z\;(i,\,j)$")
    hx_patch = mpatches.Patch(color="crimson", label=r"$H_x\;(i,\,j+\frac{1}{2})$")
    hy_patch = mpatches.Patch(color="forestgreen", label=r"$H_y\;(i+\frac{1}{2},\,j)$")
    ax.legend(
        handles=[ez_patch, hx_patch, hy_patch],
        fontsize=11,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=3,
        frameon=False,
    )

    ax.set_xlim(-0.3, nx - 0.2)
    ax.set_ylim(-0.3, ny - 0.2)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Yee Lattice (2D TM mode)")
    plt.tight_layout()
    plt.show()


def plot_matrix(mat: np.ndarray, title: str = "") -> None:
    max_entry = np.max(np.abs(mat))
    plt.figure(figsize=(8, 8))
    plt.imshow(
        mat, cmap="seismic", interpolation="none", vmin=-max_entry, vmax=max_entry
    )
    plt.colorbar()
    plt.title(title)
    plt.xlabel("DOF Index")
    plt.ylabel("DOF Index")
    plt.show()
