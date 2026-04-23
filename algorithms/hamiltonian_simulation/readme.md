# Hamiltonian Simulation

Hamiltonian simulation methods are used to model and analyze physical systems in a controlled way. The present folder showcases a range of advanced Hamiltonian simulation methods,
including product-formula decompositions and block-encoding–based techniques such as QSP,
qubitization, and QSVT. The examples illustrate how quantum time evolution can be implemented
efficiently within modern algorithmic frameworks.

- **Hamiltonian simulation guide** - Provides an introduction and overview to standard Hamiltonian simulation methods.
  The methods are described and implemented utilizing Classiq's built-in functions. First, the product formula
  based methods, Suzuki-Trotter decomposition and qDrift are introduced and implemented.
- **Hamiltonian simulation with block encoding** - A collection of notebooks demonstrating Hamiltonian simulation via block-encoding–based methods:
  - **[GQSP](hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_gqsp.ipynb)** - Implements time evolution using Generalized Quantum Signal Processing, requiring only one auxiliary qubit and no amplitude amplification.
  - **[QSVT](hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_qsvt.ipynb)** - Implements time evolution using Quantum Singular Value Transformation via interleaved signal-processing rotations.
  - **[Qubitization](hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_qubitization.ipynb)** - Implements time evolution as a Linear Combination of Unitaries (LCU) over Chebyshev-polynomial block-encodings of the walk operator.
  - **[Jacobi–Anger expansion](hamiltonian_simulation_with_block_encoding/jacobi_anger_expansion.ipynb)** - Explains and demonstrates the Jacobi–Anger identity that underlies all three methods above.
