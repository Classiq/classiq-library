from openfermion import QubitOperator
from classiq import SparsePauliOp
from typing import cast
from openfermion.utils.operator_utils import count_qubits
from sympy import fwht
from classiq import *
import numpy as np
from classiq.open_library.functions.state_preparation import apply_phase_table


# TODO: remove after bug fix
def of_op_to_cl_op(qubit_op: QubitOperator) -> SparsePauliOp:
    n_qubits = cast(int, count_qubits(qubit_op))
    return SparsePauliOp(
        terms=[
            SparsePauliTerm(
                paulis=[  # type:ignore[arg-type]
                    IndexedPauli(
                        pauli=getattr(Pauli, pauli),
                        index=qubit,
                    )
                    for qubit, pauli in term
                ],
                coefficient=coeff,
            )
            for term, coeff in qubit_op.terms.items()
        ],
        num_qubits=n_qubits,
    )


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

            b1 = np.binary_repr(i, width=nq)[::-1]
            b2 = np.binary_repr(col[j], width=nq)[::-1]
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
                paulis_sym_list.append(((nq, "X"),) + tuple((p[0], p[1]) for p in term))
                transform_matrix_sym.append((np.real(coe)).tolist())
            else:
                paulis_sym_list.append(((nq, "Y"),) + tuple((p[0], p[1]) for p in term))
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


ANGLE_THRESHOLD = 1e-13


def get_graycode(size, i) -> int:
    if i == 2**size:
        return get_graycode(size, 0)
    return i ^ (i >> 1)


def get_graycode_angles_wh(size, angles):
    transformed_angles = fwht(np.array(angles) / 2**size)
    return [transformed_angles[get_graycode(size, j)] for j in range(2**size)]


def get_graycode_ctrls(size):
    return [
        (get_graycode(size, i) ^ get_graycode(size, i + 1)).bit_length() - 1
        for i in range(2**size)
    ]


@qfunc
def multiplex_ra(a_y: float, a_z: float, angles: list[float], qba: QArray, ind: QBit):
    assert a_y**2 + a_z**2 == 1
    # TODO support general (0,a_y,a_z) rotation
    assert (
        a_z == 1.0 or a_y == 1.0
    ), "currently only strict y or z rotations are supported"
    size = max(1, (len(angles) - 1).bit_length())
    extended_angles = angles + [0] * (2**size - len(angles))
    transformed_angles = get_graycode_angles_wh(size, extended_angles)
    controllers = get_graycode_ctrls(size)

    for k in range(2**size):
        if np.abs(transformed_angles[k]) > ANGLE_THRESHOLD:
            if a_z == 0.0:
                RY(transformed_angles[k], ind)
            else:
                RZ(transformed_angles[k], ind)

        skip_control(lambda: CX(qba[controllers[k]], ind))


@qfunc
def lcu_paulis_graycode(terms: list[SparsePauliTerm], data: QArray, block: QArray):
    n_qubits = data.len
    n_terms = len(terms)
    table_z = np.zeros([n_qubits, n_terms])
    table_y = np.zeros([n_qubits, n_terms])
    probs = [abs(term.coefficient) for term in terms] + [0.0] * (2**block.len - n_terms)
    hamiltonian_coeffs = np.angle([term.coefficient for term in terms]).tolist() + [
        0.0
    ] * (2**block.len - n_terms)
    accumulated_phase = np.zeros(2**block.len).tolist()

    for k in range(n_terms):
        for pauli in terms[k].paulis:
            if pauli.pauli == Pauli.Z:
                table_z[pauli.index, k] = -np.pi
                accumulated_phase[k] += np.pi / 2
            elif pauli.pauli == Pauli.Y:
                table_y[pauli.index, k] = -np.pi
                accumulated_phase[k] += np.pi / 2
            elif pauli.pauli == Pauli.X:
                table_z[pauli.index, k] = -np.pi
                table_y[pauli.index, k] = np.pi
                accumulated_phase[k] += np.pi / 2

    def select_graycode(block: QArray, data: QArray):
        for i in range(n_qubits):
            multiplex_ra(0, 1, table_z[i, :], block, data[i])
            multiplex_ra(1, 0, table_y[i, :], block, data[i])
        apply_phase_table(
            [p1 - p2 for p1, p2 in zip(hamiltonian_coeffs, accumulated_phase)], block
        )

    within_apply(
        lambda: inplace_prepare_state(probs, 0.0, block),
        lambda: select_graycode(block, data),
    )


def get_pauli_be(mat_raw_scr, pauli_trim_rel_tol=0.1):
    """
    Get relevant block-encoding properties for `lcu_paulis_graycode` block encoding,

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
    rval = mat_raw_scr.data
    col = mat_raw_scr.indices
    rowstt = mat_raw_scr.indptr
    nr = mat_raw_scr.shape[0]

    raw_size = mat_raw_scr.shape[0]
    data_size = max(1, (raw_size - 1).bit_length())

    # Set to_symmetrize=False, since we are working with QSVT
    paulis_list, transform_matrix = initialize_paulis_from_csr(
        rowstt, col, data_size, to_symmetrize=False
    )

    qubit_op = eval_pauli_op(paulis_list, transform_matrix, rval)
    qubit_op.compress(1e-12)
    hamiltonian = of_op_to_cl_op(qubit_op)
    hamiltonian_trimmed = trim_hamiltonian(
        hamiltonian, pauli_trim_rel_tol, jump_threshold=1.1
    )

    be_scaling_factor = sum(
        [np.abs(term.coefficient) for term in hamiltonian_trimmed.terms]
    )
    block_size = max(1, (len(hamiltonian_trimmed.terms) - 1).bit_length())

    hamiltonian_trimmed = hamiltonian_trimmed * (1 / be_scaling_factor)

    print(
        f"number of Paulis before/after trimming {len(hamiltonian.terms)}/{len(hamiltonian_trimmed.terms)}"
    )

    @qfunc
    def be_qfunc(block: QNum, data: QNum):
        lcu_paulis_graycode(hamiltonian_trimmed.terms, data, block)

    return data_size, block_size, be_scaling_factor, be_qfunc
