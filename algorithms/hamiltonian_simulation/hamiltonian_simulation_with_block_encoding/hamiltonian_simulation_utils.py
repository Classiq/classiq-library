import numpy as np


def get_projected_state_vector(res) -> np.ndarray:
    """
    Returns a reduced statevector from execution results.
    Expects a 'data' variable, and a 'block' variable to be filtered out when not in the |0> state.
    """
    state_size = 2 ** len(res.output_qubits_map["data"])
    proj_statevector = np.zeros(state_size).astype(complex)

    df = res.dataframe
    filtered_st = df[(df.block == 0) & (np.abs(df.amplitude) > 1e-12)]
    proj_statevector[filtered_st.data] = filtered_st.amplitude
    return proj_statevector


def compare_quantum_classical_states(
    expected_state: np.ndarray,
    resulted_state: np.ndarray,
    post_selection_factor: float,
):
    """
    Aligns global phase, renormalizes, and computes overlap between the expected classical
    state and the one resulting from the quantum program. Since we work with a projected
    statevector, we need to insert the post-selection factor by hand.

    Parameters
    ----------
    expected_state : array_like of complex, the classical (reference) statevector.
    resulted_state : array_like of complex, the simulated statevector, projected onto the block=0 space.
    post_selection_factor : float, the post-selection success probability of the block=0,
        to be applied uniformly to `resulted_state`.

    Returns
    -------
    renormalized_state : the `resulted_state` after global-phase alignment and
        multiplication by `post_selection_factor`.
    overlap : The absolute value of the normalized inner product between
        `renormalized_state` and `expected_state`.
    """
    relative_phase = np.angle(expected_state[0] / resulted_state[0])
    resulted_state = resulted_state * np.exp(1j * relative_phase)

    renormalized_state = post_selection_factor * resulted_state
    overlap = (
        np.vdot(renormalized_state, expected_state)
        / np.linalg.norm(renormalized_state)
        / np.linalg.norm(expected_state)
    )

    return renormalized_state, abs(overlap)
