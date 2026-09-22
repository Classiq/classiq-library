from scipy.sparse import csr_matrix
from classiq import *
from classiq.applications.block_encoding import BlockEncoding
import numpy as np

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


def get_banded_diags_be(mat_raw_scr):
    """
    Get a `BlockEncoding` for the banded-diagonal matrix `mat_raw_scr`.

    Parameters
    ----------
    mat_raw_scr : scipy.sparse.spmatrix
        Square sparse matrix of shape (N, N), real or complex, to be block-encoded.
    """
    offsets = nonzero_diagonals(mat_raw_scr)
    diags = extract_diagonals(mat_raw_scr, offsets)
    return BlockEncoding.from_dense_diagonals(list(zip(diags, offsets)))
