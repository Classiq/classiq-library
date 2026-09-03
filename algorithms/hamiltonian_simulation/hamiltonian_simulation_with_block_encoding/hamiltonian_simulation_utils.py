import numpy as np

from classiq import calculate_state_vector


def get_projected_state_vector(qprog, data_size: int) -> np.ndarray:
    """
    Returns a reduced statevector from a quantum program.

    Simulates ``qprog`` on the Classiq statevector simulator via
    ``calculate_state_vector``, keeps only the amplitudes where the 'block'
    register is in the |0> state, and scatters them into a dense vector indexed
    by the 'data' register. ``data_size`` is the number of qubits in the 'data'
    register.
    """
    proj_statevector = np.zeros(2**data_size).astype(complex)

    df = calculate_state_vector(qprog, filters={"block": 0})
    filtered_st = df[np.abs(df.amplitude) > 1e-12]
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
