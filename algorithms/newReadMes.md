# README texts for the various folders in the algorithms directory

# Amplitude Amplification and Estimation

The directory contains algorithmic variations of the amplitude amplification and estimation algorithm.
Amplitude amplification is a technique, constitutes a generalization of the Grover's search,
allowing to increase the probability of measuring marked ("good") states.
Generally, producing a quadratic speedup, relative to classical repetition. Specifically, a marked state which
has probability $p$ to be measured, can be found with a probability close to unity by employing $O(1/\sqrt{p})$
measurements.

The directory contains the following methods

- **Oblivious Amplitude Amplification** - Amplifies a coherent transformation by increasing the probability that a desired
  operation is successfully applied, where success is indicated by the state of an auxiliary qubit. The algorithm is
  oblivious to the input state, meaning it works uniformly for any input, does not rely on efficient state preparation,
  and avoids measurements. As a result, it can be implemented as part of a larger unitary quantum circuit without
  interrupting coherence.
- **Quantum Monte Carlo Integration** - Employs Quantum Amplitude Estimation (QAE) to evaluate a definite integral. Obtains a
  quadratic improvement of the analogous classical method, exhibiting an error which scales as $O(1/M)$, where $M$ is the
  number of controlled applications of the Grover operator within the QAE.
- **Quantum Singular Value Transformation (QSVT) fixed point amplitude amplification** - solves unstructured
  search problems without requiring prior knowledge of the fraction of marked solutions.
  By leveraging QSVT together with an efficiently block-encoded operator, it implements amplitude amplification
  in a fixed-point manner, guaranteeing monotonic convergence toward the marked subspace and eliminating
  the risk of overshooting the target state.
- **Quantum Counting** - Efficiently estimates the number of valid solutions to a search problem. The algorithm
  employs QAE to obtain a quadratic query complexity speed up relative to classical algorithms.

# Foundational

Fundamental quantum algorithms, providing the foundations for future advancements
and demonstrating query complexity advantages.

- **Bernstein Vazirani**-
  Demonstrating a linear query complexity advantage over deterministic and
  probabilistic classical method.
  The algorithm finds the hidden-bit string $a$ by a single query call to an oracle function
  $f(x) = (a\cdot x) \mod 2$, where $x$ is also a bit string and $\cdot$ denotes the bitwise multiplication.
  This problem constitutes a specific case of the general hidden-shift problem.
- **Deutsch Jozsa** - Widely regarded as the first quantum algorithm, it demonstrates an exponential advantage in query
  complexity over classical approaches. Given oracle access to a Boolean function promised to be either
  constant or balanced, the algorithm deterministically identifies which case holds using a single query to
  the function.
- **Quantum Teleportation** - A foundational quantum communication protocol, employing quantum entanglement and
  classical communication to transfer ("teleport") an arbitrary qubit state from one place to another.
- **Simon** - Given an oracle binary function, satisfying $f(x)=f(y)$ if and only if $y=x\oplus s$ for some secret key $s$, the
  algorithm recovers $s$. It does so using a number of oracle queries linear in the input size, yielding an exponential
  improvement in query complexity compared to the best classical approaches.

# Hamiltonian Simulation

- **Hamiltonian simulation guide**
- **Hamiltonian simulation with block encoding**

# Number Theory and Cryptography

- **Discrete log**
- **Elliptic curves**
- **Hidden shift problem**
- **Shor's algorithm**

# QML

- **Hybrid Quantum Neural Networks (QNN)**
- **Quantum Generative Adversarial Networks (GANs)**
- **Quantum Support Vector Machine (QSVM)**
- **Quantum autoencoder**

# Quantum Differential Equation Solvers

- **Discrete Poisson solver**
- **Time marching**

# Quantum Linear Solvers

- **Adiabatic linear solvers** -
- **HHL** -
- **Quantum Singular Value Transformation (QSVT) matrix inversion**
- **Variational Quantum Linear Solver (VQLS) with Linear Combination of Unitaries (LCU)**

# Quantum Phase Estimation (QPE)

- **QPE for a matrix**
- **QPE with qubitization**

# Quantum Primitives

- **Generalized Quantum Signal Processing (GQSP)**
- **Swap test**

# Quantum State Preparation

- **ADAPT VQE** -
  The Adaptive Derivative-Assembled Pseudo-Trotter Variational Quantum Eigensolver (ADAPT-VQE)
  is a variational hybrid algorithm. It constitutes an extension of the Variational Quantum Eigensolver (VQE) framework,
  constructing problem-specific solution in an adaptive manner. By increasing the number of measurements the algorithms
  produces shallower circuit relative to the standard VQE algorithm.

- **Gibbs state preparation**

# Quantum Walks/Glued trees

# Search and Optimization

- **Decoded Quantum Interferometry**
- **Grover**
- **Grover Mixers for QAOA**
- **Quantum Approximate Optimization Algorithm (QAOA)**
