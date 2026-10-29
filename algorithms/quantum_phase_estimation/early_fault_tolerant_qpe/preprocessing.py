"""Classical pre-processing shared by every early-FT-QPE example: Hamiltonian rescaling, the
Fourier-Heaviside filter used to reconstruct the spectral CDF, and the deterministic/randomized
partition of a Hamiltonian for partially randomized product formulas.
"""

import numpy as np
from classiq import Pauli
from classiq.qmod.builtins.enums import Pauli as PauliEnum
from classiq.qmod.builtins.structs import IndexedPauli, SparsePauliOp, SparsePauliTerm
from scipy.special import (
    ive,
)  # exponentially scaled modified Bessel function e^{-beta} I_n(beta)


def rescale_hamiltonian(ham, h_norm, target=(np.pi / 3) * 0.9):
    """Map H -> scale * H with scale = target / h_norm, so that a spectrum within [-h_norm, h_norm] lands inside
    [-target, target].  Returns the rescaled Hamiltonian, the scale and the inverse map x -> x / scale.
    """
    scale = target / h_norm
    return ham * scale, scale, lambda x_scaled: x_scaled / scale


def heaviside_coeffs_bessel(d, beta):
    """Fourier coeffs F_k, k = -d..d, of a von Mises (Bessel) mollified, band-limited Heaviside step."""
    ks = np.arange(-d, d + 1)
    fhat = np.zeros_like(ks, dtype=complex)
    for i, k in enumerate(ks):
        if k == 0:
            fhat[i] = 0.5
        elif k % 2 != 0:  # odd modes only
            j = (abs(k) - 1) // 2
            val = (
                -1j
                * np.sqrt(beta / (2 * np.pi))
                * (ive(j, beta) + ive(j + 1, beta))
                / abs(k)
            )
            fhat[i] = val if k > 0 else -val
    return fhat


def dense_pauli_string(term, num_qubits):
    """A SparsePauliTerm's Paulis as a dense per-qubit array (Pauli.I elsewhere), as required by
    `single_pauli_exponent`. That function indexes its array big-endian (qubit 0 = LAST entry), unlike
    `IndexedPauli` / `hamiltonian_to_matrix`, so the mapping is reversed here."""
    dense = [PauliEnum.I] * num_qubits
    for p in term.paulis:
        dense[num_qubits - 1 - p.index] = p.pauli
    return dense


def partition_hamiltonian(ham, num_qubits, n_deterministic):
    """Split `ham`'s non-identity terms by |coefficient| into a deterministic head (the top `n_deterministic`
    terms) and a randomized tail.  Returns (head, tail, tail_weight, identity_coeff) with head/tail lists of
    (coefficient, dense Pauli string).  The identity term is a pure global phase and is returned separately.
    """
    identity_coeff = 0.0
    terms = []
    for term in ham.terms:
        if len(term.paulis) == 0:
            identity_coeff += float(np.real(term.coefficient))
        else:
            terms.append(
                (float(np.real(term.coefficient)), dense_pauli_string(term, num_qubits))
            )
    terms.sort(key=lambda t: -abs(t[0]))
    head, tail = terms[:n_deterministic], terms[n_deterministic:]
    return head, tail, sum(abs(c) for c, _ in tail), identity_coeff


def to_sparse_op(terms, num_qubits):
    """SparsePauliOp from (coefficient, dense Pauli string) pairs, the inverse of the dense representation above."""
    return SparsePauliOp(
        terms=[
            SparsePauliTerm(
                paulis=[
                    IndexedPauli(pauli=p, index=i)
                    for i, p in enumerate(reversed(dense))
                    if p != PauliEnum.I
                ],
                coefficient=c,
            )
            for c, dense in terms
        ],
        num_qubits=num_qubits,
    )
