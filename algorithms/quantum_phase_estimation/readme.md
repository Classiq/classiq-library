# Quantum Phase Estimation (QPE)

The present folder explores Quantum Phase Estimation as a spectral analysis tool for Hermitian matrices.
The implementations include Trotterized Hamiltonian simulation and qubitization-based block-encoding
techniques, highlighting how eigenvalues can be extracted from controlled unitary dynamics.
These examples demonstrate core primitives underlying quantum chemistry, Hamiltonian simulation,
and advanced linear-algebraic quantum algorithms.

- **QPE for a matrix** - Quantum Phase Estimation (QPE) is a fundamental quantum algorithm and a common primitive in many algorithms,
  allowing one to estimate the eigenphase of a unitary matrix, $e^{i M t}$, where $M$ is a Hermitian matrix.
  By initializing the system in a random initial
  state, repeated execution of the QPE algorithm, utilizing a built-in Trotter propagator, `suzuki_trotter`,
  leads to an estimation of the phases, $\{e^{i\theta_i}\}$.
  These phases are then directly related to the eigenvalues of $M$.
- **QPE with qubitization** - Given a block-encoding of the Hermitian matrix of interest, we construct the Szegedy
  quantum walk operator and utilize it within a quantum phase estimation procedure
  to estimate the eigenvalues of a Hydrogen molecule.
