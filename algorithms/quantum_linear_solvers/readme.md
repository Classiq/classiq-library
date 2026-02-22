# Quantum Linear Solvers

A range of algorithms for quantum linear systems have been developed,
including adiabatic methods, the HHL algorithm, QSVT-based matrix inversion,
and variational solvers. The examples bellow illustrate different computational models—adiabatic
evolution, block-encoding with singular value transformation, and hybrid quantum–classical
optimization—providing a unified view of how linear algebraic problems can be addressed within
quantum computing frameworks.

- **Adiabatic linear solvers** - Demonstrates the mapping of the solution of a quantum linear system problem, $A |\mathbf{x}\rangle = |\mathbf{b}\rangle$,
  to a ground state of a corresponding Hamiltonian. An approximate solution is then achieved, employing a quantum
  adiabatic protocol, within the framework of quantum adiabatic computing.
- **HHL** - A fundamental quantum algorithm, designed to solve a set of linear equations, encoded in terms
  of a quantum operation on quantum states: $A |\mathbf{x}\rangle = |\mathbf{b}\rangle$. Under a restricted number of
  conditions the state $|x\rangle$ can be prepared, in a running time which scales polynomially with the number of qubits required
  to encode the state. This enables an exponential speed up relative to classical algorithms in the evaluation of observables of the form
  $\langle \mathbf{x}| M| \mathbf{x}\rangle$, where $M$ is a quantum operator.
- **Quantum Singular Value Transformation (QSVT) matrix inversion** - A general framework for solving linear
  systems is implemented, using the Quantum Singular Value Transform (QSVT). Given an efficient procedure for embedding a classical matrix
  as a quantum function via block-encoding, the framework provides a clean approach to matrix inversion.
  When a block-encoding of the matrix and its condition number are available, the algorithm admits a concise implementation
  by invoking the `qsvt_inversion` routine together with classical auxiliary functions from the `qsp` module.
- **Variational Quantum Linear Solver (VQLS) with Linear Combination of Unitaries (LCU)** A hybrid algorithm, employs
  a linear combination of unitaries to block-encode a matrix $A$ within a unitary. The operation of $A$ on a variational
  quantum state then enables performing classical optimization, to reach an approximate solution. As many variational algorithms
  The algorithm hardware requirements are limited, and is well suited for the contemporary NISQ devices.
