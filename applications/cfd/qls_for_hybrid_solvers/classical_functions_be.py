from openfermion import QubitOperator
import numpy as np
from scipy.sparse import csr_matrix
from classiq import SparsePauliOp


def get_projected_state_vector(  # type: ignore[no-untyped-def]
    execution_result,
    measured_var: str,
) -> np.ndarray:
    """
    This function returns a reduced statevector from execution results.
    measured var: the name of the reduced variable
    """
    projected_size = len(execution_result.output_qubits_map[measured_var])
    proj_statevector = np.zeros(2**projected_size).astype(complex)
    df = execution_result.dataframe
    filtered_st = df[np.abs(df.amplitude) > 1e-12]

    # Allocate values
    proj_statevector[filtered_st[measured_var]] = filtered_st.amplitude

    # global phase
    indices = np.where(np.abs(proj_statevector) > 1e-13)[0]  # Get non-zero indices
    if indices.shape[0] == 0:
        return np.zeros(2**projected_size)  # return zero state
    first_non_zero_entry = indices[0]
    global_phase = np.angle(proj_statevector[first_non_zero_entry])
    return np.real(proj_statevector / np.exp(1j * global_phase))


"""
Functions for treating Pauli decomposition
"""


def elementary_to_pauli(e_basis, k):
    if e_basis == 0:
        return QubitOperator(" ", 1 / 2) + QubitOperator(f"Z{k}", 1 / 2)
    elif e_basis == 1:
        return QubitOperator(f"X{k}", 1 / 2) + QubitOperator(f"Y{k}", 1j / 2)
    elif e_basis == 2:
        return QubitOperator(f"X{k}", 1 / 2) + QubitOperator(f"Y{k}", -1j / 2)
    else:
        return QubitOperator(" ", 1 / 2) + QubitOperator(f"Z{k}", -1 / 2)


# This function returns the difference in the binary representation, and in turn, [0,1,2,3] which corresponds to the elementry basis
def binary_diff_to_elementary(b1: str, b2: str) -> np.ndarray:
    return 2 * np.array(list(b1), dtype=int) + np.array(list(b2), dtype=int)


def initialize_paulis_from_csr(
    rowstt: np.ndarray, col: np.ndarray, nq: int, to_symmetrize: bool = True
):
    transform_matrix: list[list[complex]] = list()
    coe_size = rowstt[-1::][0]
    terms_list: list[tuple()] = list()

    scr_entry = 0
    for i in range(len(rowstt) - 1):
        for j in range(rowstt[i], rowstt[i + 1]):

            b1 = np.binary_repr(i, width=nq)
            b2 = np.binary_repr(col[j], width=nq)
            diffarray = binary_diff_to_elementary(
                b1, b2
            )  # this is an array of size N, contains 0,1,2, or 3. Each corresponds to elementry matrix

            entry_decomposed = np.prod(
                [elementary_to_pauli(e_basis, k) for k, e_basis in enumerate(diffarray)]
            )
            for term, value in entry_decomposed.terms.items():
                if term in terms_list:
                    # Update the coefficient of the existing term
                    index = terms_list.index(term)
                    transform_matrix[index][scr_entry] += value
                else:
                    # Add the new term and its coefficient
                    new_raw = [0.0j] * coe_size
                    new_raw[scr_entry] = value
                    terms_list.append(term)
                    transform_matrix.append(new_raw)

            scr_entry += 1

    if not to_symmetrize:
        return terms_list.copy(), transform_matrix.copy()

    else:
        paulis_sym_list = list()
        transform_matrix_sym = list()
        for term, coe in zip(terms_list, transform_matrix):
            if [p[1] for p in term].count("Y") % 2 == 0:
                paulis_sym_list.append(
                    ((0, "X"),) + tuple((p[0] + 1, p[1]) for p in term)
                )
                transform_matrix_sym.append((np.real(coe)).tolist())
            else:
                paulis_sym_list.append(
                    ((0, "Y"),) + tuple((p[0] + 1, p[1]) for p in term)
                )
                transform_matrix_sym.append((np.imag(coe)).tolist())

        return paulis_sym_list.copy(), transform_matrix_sym.copy()


# This function returns an evaluation of a symbolic pauli decomposition given a csr entries
def eval_pauli_op(
    paulis_list: list[tuple()],
    transform_mat: np.ndarray,
    rval: np.ndarray,
    precision: float = 1e-50,
) -> QubitOperator:
    coes_list = np.array(transform_mat) @ np.array(rval)
    return sum(
        [
            QubitOperator(term, coe)
            for term, coe in zip(paulis_list, coes_list)
            if abs(coe) >= precision
        ]
    )


def trim_hamiltonian(hamiltonian, relative_threshold, jump_threshold=1.1):
    """
    Trim a Hamiltonian by keeping only Pauli terms with magnitude ≥ a data-driven cutoff.

    The coefficients are sorted (descending), “big jumps” are detected via
    ratio ≥ `jump_threshold`, and contiguous value-intervals are formed. A
    cutoff is chosen as the right edge of the interval that contains
    `relative_threshold * second_largest_coeff` (or the interval immediately
    to its left if the value lies between intervals). Terms with |coeff| >
    this cutoff are retained.

    Parameters
    ----------
    hamiltonian : SparsePauliOp
        The Hamiltonian to trim.
    relative_threshold : float
        Multiplier applied to the 2nd largest coefficient to form the probe value.
    jump_threshold : float, optional
        Consecutive-coefficient ratio that defines a “big jump” (default 1.1).

    Returns
    -------
    SparsePauliOp
        New Hamiltonian containing only the retained terms.
    """

    # sort pauli terms
    pauli_coe = np.array(
        [np.abs(term.coefficient) for term in hamiltonian.terms], dtype=float
    )
    sort_ind = np.argsort(pauli_coe)[::-1]
    pauli_coe_sorted = pauli_coe[sort_ind]

    # relative error is w.r.t. the 2nd term (skip the 1st if it has a big jump)
    relative_error = relative_threshold * pauli_coe_sorted[1]

    # jumps and their indices
    jumps = pauli_coe_sorted[:-1] / pauli_coe_sorted[1:]
    cut_idx = np.flatnonzero(jumps >= jump_threshold)  # cut is between i and i+1

    # left/right boundary values at the jump locations
    left_points = pauli_coe_sorted[:-1][cut_idx]
    right_points = pauli_coe_sorted[1:][cut_idx]

    # Build value-intervals from the cuts (inclusive)
    # indices [0..cut0], [cut0+1..cut1], ..., [last_cut+1..N-1]
    starts = np.r_[0, cut_idx + 1]
    ends = np.r_[cut_idx, len(pauli_coe_sorted) - 1]
    L = pauli_coe_sorted[starts]  # interval left (larger)
    R = pauli_coe_sorted[ends]  # interval right (smaller)

    # Choose the right point according to the following rule:
    # - if relative_error inside an interval [R[i], L[i]] -> pick R[i]
    # - else (between intervals) -> pick R of the interval to its left
    within = (relative_error <= L) & (relative_error >= R)
    if np.any(within):
        chosen_right = R[np.argmax(within)]
        print("within")
    else:
        # find largest i with L[i] >= relative_error (L is descending)
        i_left = np.searchsorted(-L, -relative_error, side="left") - 1
        i_left = max(i_left, 0)  # clamp to first interval if before all
        chosen_right = R[i_left]

    trimmed_hamiltonian = SparsePauliOp(
        terms=[
            term
            for term in hamiltonian.terms
            if np.abs(term.coefficient) >= chosen_right
        ],
        num_qubits=hamiltonian.num_qubits,
    )

    return trimmed_hamiltonian


"""
Functions for treating banded block encoding
"""


def nonzero_diagonals(sparse_mat: csr_matrix) -> list[int]:
    """
    Return a sorted list of diagonal offsets (k) for which the
    diagonal of the sparse matrix is non-zero (i.e., has at least one nonzero element).

    k = 0 -> main diagonal
    k > 0 -> superdiagonals
    k < 0 -> subdiagonals
    """
    if not isinstance(sparse_mat, csr_matrix):
        raise TypeError("Input must be a scipy.sparse.csr_matrix")

    rows, cols = sparse_mat.shape
    diagonals = []

    for k in range(-rows + 1, cols):  # all possible diagonals
        diag = sparse_mat.diagonal(k)
        if np.any(diag != 0):
            diagonals.append(k)

    return diagonals


def extract_diagonals(csr_mat: csr_matrix, offsets: list[int]) -> list[np.ndarray]:
    """extracts the diagonals of a csr matrix given a list with the offsets - minus sign means lower diagonal"""
    return [csr_mat.diagonal(offset) for offset in offsets]


def pad_arrays(
    arrays: list[np.ndarray], offsets: list[int], pad_value: int = 0
) -> list[np.ndarray]:
    """
    Pads all NumPy arrays in a list to match the length of the longest one.
    For negative offsets, padding is added to the beginning of the array.

    Parameters:
    - arrays (list of np.ndarray): List of NumPy arrays with different lengths.
    - offsets (list of int): List of diagonal offsets, same order as arrays.
    - pad_value (int, optional): The value to pad with (default is 0).

    Returns:
    - list of np.ndarray: Padded NumPy arrays.
    """
    if not arrays:  # Handle case where list is empty
        return []

    max_length = max(len(arr) for arr in arrays)  # Find max length

    padded_arrays = []
    for arr, offset in zip(arrays, offsets):
        padding_length = max_length - len(arr)
        if offset < 0:
            # Pad at the beginning
            pad_width = (padding_length, 0)
        else:
            # Pad at the end
            pad_width = (0, padding_length)

        padded_arr = np.pad(arr, pad_width, constant_values=pad_value)
        padded_arrays.append(padded_arr)

    return padded_arrays


def get_be_banded_data(
    sparse_mat: csr_matrix,
) -> tuple[list[int], list[list[float]], list[float], float]:
    offsets = nonzero_diagonals(sparse_mat)
    num_q_diag = int(np.ceil(np.log2(len(offsets))))
    diags = extract_diagonals(sparse_mat, offsets)
    diags = pad_arrays(diags, offsets, 0)
    diags_maxima = [np.max(np.abs(d)) for d in diags]
    normalized_diags = [(d / d_max).tolist() for d, d_max in zip(diags, diags_maxima)]
    prepare_norm = sum(diags_maxima)
    normalized_diags_maxima = [d_max / prepare_norm for d_max in diags_maxima] + [0] * (
        2**num_q_diag - len(offsets)
    )

    return offsets, normalized_diags, normalized_diags_maxima, prepare_norm
