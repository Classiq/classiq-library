# Quantum Primitives

The folder contains foundational quantum algorithmic primitives that serve as building blocks for higher-level applications.
The examples include Generalized Quantum Signal Processing (GQSP), enabling flexible polynomial
transformations of block-encoded unitaries, as well as the Swap Test, a standard subroutine for estimating
quantum state overlaps and the Hadamard test. Together, these primitives underpin a wide range of algorithms in
Hamiltonian simulation, matrix functions, variational optimization, and quantum machine learning.

- **Hadamard test** - A basic quantum primitive, utilized to extract the real part of an expectation value of
  a unitary matrix.
- **Generalized Quantum Signal Processing (GQSP)** - A quantum algorithmic primitive that extends standard QSP,
  allowing one to block-encode arbitrary polynomials of unitary operations.
  Utilizing, Classiq's built-in module `gqsp_phases`, the generalized version removes restrictions that appear in QSP,
  providing a direct and flexible method for state preparation,
  phase function transformations and Hamiltonian simulation.
- **Swap test** - A quantum function that checks the overlap between two quantum states.
  Given two quantum registers of the same size, the function returns as output a single test qubit whose state encodes
  the overlap between the two inputs. The swap test is commonly employed as a subroutine in quantum
  variational and machine learning algorithms, such as quantum kernel method and neural networks.
