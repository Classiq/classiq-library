import numpy as np


def get_projected_state_vector(  # type: ignore[no-untyped-def]
    state_vector_df,
    measured_var: str,
    projected_size: int,
) -> np.ndarray:
    """
    Return a reduced (post-selected) statevector from a calculate_state_vector DataFrame.
    measured_var: the name of the reduced variable (a column in the DataFrame)
    projected_size: number of qubits of measured_var
    """
    proj_statevector = np.zeros(2**projected_size).astype(complex)
    filtered_st = state_vector_df[np.abs(state_vector_df.amplitude) > 1e-12]

    # Allocate values
    proj_statevector[filtered_st[measured_var]] = filtered_st.amplitude

    # global phase
    indices = np.where(np.abs(proj_statevector) > 1e-13)[0]  # Get non-zero indices
    if indices.shape[0] == 0:
        return np.zeros(2**projected_size)  # return zero state
    first_non_zero_entry = indices[0]
    global_phase = np.angle(proj_statevector[first_non_zero_entry])
    return np.real(proj_statevector / np.exp(1j * global_phase))


def get_svd_range(mat_raw_scr):
    mat_raw = mat_raw_scr.toarray()
    svd = np.linalg.svd(mat_raw)[1]
    w_min = min(svd)
    w_max = max(svd)
    return w_min, w_max
