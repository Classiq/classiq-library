from scipy.sparse import csr_matrix
from classiq import *
import numpy as np

ANGLE_THRESHOLD = 1e-13

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


""" Loading of a single diagonal with a given offset"""


@qfunc
def load_diagonal(offset: int, diag: list[float], ind: QBit, x: QNum) -> None:

    if offset != 0:
        inplace_add(offset, x)
    assign_amplitude_table(diag, x, ind)


@qfunc
def load_banded_diagonals(
    offsets: list[int], diags: list[list[float]], ind: QBit, x: QNum, s: QNum
) -> None:
    for i in range(len(offsets)):
        control(s == i, lambda: load_diagonal(-offsets[i], diags[i], ind, x))


@qfunc
def block_encode_banded(
    offsets: list[int],
    diags: list[list[float]],
    prep_diag: CArray[CReal],
    block: QNum,
    data: QNum,
) -> None:
    s = QNum(size=block.size - 1)
    ind = QBit()
    bind(block, [s, ind])
    within_apply(
        lambda: inplace_prepare_state(prep_diag, 0.0, s),
        lambda: load_banded_diagonals(offsets, diags, ind, data, s),
    )

    X(ind)
    bind([s, ind], block)


@qfunc
def block_encode_banded_controlled(
    ctrl_state: CInt,
    offsets: list[int],
    diags: list[list[float]],
    prep_diag: CArray[CReal],
    block: QNum,
    data: QNum,
    ctrl: QNum,
) -> None:
    if offsets.len < 2 ** ((offsets.len - 1).bit_length()):
        """
        Efficient controlled version when the number of diagonals is not an exact power of 2.
        """
        s = QNum(size=block.size - 1)
        ind = QBit()
        bind(block, [s, ind])
        within_apply(
            lambda: control(
                ctrl == ctrl_state,
                lambda: inplace_prepare_state(prep_diag, 0.0, s),
                lambda: apply_to_all(X, s),
            ),
            lambda: load_banded_diagonals(offsets, diags, ind, data, s),
        )
        control(ctrl == ctrl_state, lambda: X(ind))
        bind([s, ind], block)
    else:
        control(
            ctrl == ctrl_state,
            lambda: block_encode_banded(offsets, diags, prep_diag, block, data),
        )


@qfunc
def be_e3(data: QBit, block: QBit):
    lcu(
        coefficients=[1, 1],
        unitaries=[lambda: RY(np.pi, data), lambda: X(data)],
        block=block,
    )


@qfunc
def block_encode_banded_sym(
    offsets: list[int],
    diags: list[list[float]],
    prep_diag: CArray[CReal],
    block: QArray,
    data: QArray,
) -> None:
    """
    This is a simple LCU of block encoding the upper-right and lower-left block.
    However, we use an explicit controlled version of block_encode_banded, given by the function
    block_encode_banded_controlled.
    """
    lcu_block = QBit()
    sym_block = QBit()
    sym_data = QBit()
    reduced_block = QArray()
    reduced_data = QArray()
    within_apply(
        lambda: (
            bind(
                data, [reduced_data, sym_data]
            ),  # separate to different variables for clarity
            bind(block, [reduced_block, sym_block, lcu_block]),
            H(lcu_block),
        ),
        lambda: (
            control(lcu_block == 1, lambda: be_e3(sym_data, sym_block)),
            block_encode_banded_controlled(
                ctrl=lcu_block,
                ctrl_state=1,
                offsets=offsets,
                diags=diags,
                prep_diag=prep_diag,
                block=reduced_block,
                data=reduced_data,
            ),
            control(lcu_block == 0, lambda: invert(lambda: be_e3(sym_data, sym_block))),
            invert(
                lambda: block_encode_banded_controlled(
                    ctrl=lcu_block,
                    ctrl_state=0,
                    offsets=offsets,
                    diags=diags,
                    prep_diag=prep_diag,
                    block=reduced_block,
                    data=reduced_data,
                )
            ),
        ),
    )


def get_banded_diags_be(mat_raw_scr):
    """
    Get relevant block-encoding properties for `block_encode_banded` block encoding,

    Parameters
    ----------
    mat_raw_scr : scipy.sparse.spmatrix
        Square sparse matrix of shape (N, N), real or complex, to be block-encoded.

    Returns
    -------
    data_size : int
       Size of the data variable.
    block_size : int
        Size of the block variable.
    be_scaling_factor : float
        The scaling factor of the block-encoding unitary
    BlockEncodedState : QStruct
        QSVT-compatible QStruct holding the quantum variables, with fields:
          - data  : QNum[data_size]
          - block : QNum[block_size]
    be_qfunc : qfunc
        Quantum function that implements the block encoding. Signature:
        be_qfunc(be: BlockEncodedState) → None
    """
    raw_size = mat_raw_scr.shape[0]
    data_size = max(1, (raw_size - 1).bit_length())
    offsets, diags, diags_maxima, prepare_norm = get_be_banded_data(mat_raw_scr)
    block_size = int(np.ceil(np.log2(len(offsets)))) + 1
    be_scaling_factor = prepare_norm

    @qfunc
    def be_qfunc(block: QNum, data: QNum):
        block_encode_banded(
            offsets=offsets,
            diags=diags,
            prep_diag=diags_maxima,
            block=block,
            data=data,
        )

    return data_size, block_size, be_scaling_factor, be_qfunc
