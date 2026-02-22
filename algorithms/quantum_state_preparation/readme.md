# Quantum State Preparation

State preparation algorithms are essential building blocks in quantum simulation and optimization.
The present folder explores advanced quantum state preparation techniques, including adaptive
variational eigensolvers and block-encoding–based Gibbs state generation. The examples emphasize
both practical hybrid workflows and algorithmic primitives.

- **ADAPT VQE** -
  The Adaptive Derivative-Assembled Pseudo-Trotter Variational Quantum Eigensolver (ADAPT-VQE)
  is a variational hybrid algorithm. It constitutes an extension of the Variational Quantum Eigensolver (VQE) framework,
  constructing problem-specific solution in an adaptive manner. By increasing the number of measurements the algorithms
  produces shallower circuit relative to the standard VQE algorithm.

- **Gibbs state preparation** - An important quantum primitive employed as a subroutine in higher-level algorithms,
  including quantum methods for solving semidefinite programs, Boltzmann sampling, and Metropolis-type algorithms.
  The procedure prepares a quantum thermal (Gibbs)
  state by implementing a block-encoding of the Lindbladian superoperator, which generates the open-system
  dynamics of a quantum system coupled to a thermal bath. Applying this block-encoding effectively drives
  the initial state toward thermal equilibrium, thereby producing the corresponding Gibbs state.
  The implementation relies on an operator Fourier transform combined with mid-circuit weak measurements,
  leveraging the quantum Zeno effect to enhance runtime performance and improve overall algorithmic efficiency.
