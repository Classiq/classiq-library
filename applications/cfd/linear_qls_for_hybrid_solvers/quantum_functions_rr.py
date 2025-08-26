from sympy import fwht
from classiq import *
import numpy as np
from classiq.open_library.functions.state_preparation import apply_phase_table
from classiq.qmod.symbolic import subscript


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
    size = max(1, (len(angles) - 1).bit_length())
    extended_angles = angles + [0] * (2**size - len(angles))
    transformed_angles = get_graycode_angles_wh(size, extended_angles)
    controllers = get_graycode_ctrls(size)

    for k in range(2**size):
        if a_z == 0.0:
            RY(transformed_angles[k], ind)
        elif a_y == 0.0:
            RZ(transformed_angles[k], ind)
        else:
            pass
        CX(qba[controllers[k]], ind),


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


""" Loading of a single diagonal with a given offset"""


@qfunc
def load_diagonal(offset: CInt, diag: CArray[CReal], ind: QBit, x: QNum) -> None:
    if_(offset != 0, lambda: inplace_add(offset, x))
    ind *= subscript(diag, x)


@qfunc
def load_banded_diagonals(
    offsets: CArray[CInt], diags: CArray[CArray[CReal]], ind: QBit, x: QNum, s: QNum
) -> None:
    repeat(
        offsets.len,
        lambda i: (
            control(s == i, lambda: load_diagonal(-offsets[i], diags[i], ind, x))
        ),
    )


@qfunc
def block_encode_banded(
    offsets: CArray[CInt],
    diags: CArray[CArray[CReal]],
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
