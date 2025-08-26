from openfermion import QubitOperator
import numpy as np
from scipy.sparse import csr_matrix


def get_projected_state_vector(  # type: ignore[no-untyped-def]
    execution_result,
    measured_var: str,
    projections: dict,
) -> np.ndarray:
    """
    This function returns a reduced statevector from execution results.
    measured var: the name of the reduced variable
    projections: on which values of the other variables to project, e.g., {"ind": 1}
    """
    projected_size = len(execution_result.output_qubits_map[measured_var])
    proj_statevector = np.zeros(2**projected_size).astype(complex)
    df = execution_result.dataframe
    filtered_st = df[np.abs(df.amplitude) > 1e-12]

    # Filter only the successful states.
    filtered_st = filtered_st.query(
        " and ".join(f"{k} == @{k}" for k in projections), local_dict=projections
    )

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


"""
Functions for treating banded block encoding
"""


def nonzero_diagonals(sparse_mat: csr_matrix) -> list[int]:
    """
    Return a sorted list of diagonal offsets (k) for which the
    diagonal of the sparse matrix is non-zero (i.e., has at least one nonzero element).

    k = 0 → main diagonal
    k > 0 → superdiagonals
    k < 0 → subdiagonals
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
