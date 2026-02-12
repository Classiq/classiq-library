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
- **Quantum Singular Value Transformation (QSVT) fixed point amplitude amplification** - Solves unstructured
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
  the function. We define a general quantum algorithm that accepts a quantum predicate as an input parameter
  and explore multiple concrete examples. By using Classiq’s quantum arithmetic capabilities, the compilation
  of both simple and highly complex functions becomes straightforward.
- **Quantum Teleportation** - A foundational quantum communication protocol, employing quantum entanglement and
  classical communication to transfer ("teleport") an arbitrary qubit state from one place to another.
- **Simon** - Given an oracle binary function, satisfying $f(x)=f(y)$ if and only if $y=x\oplus s$ for some secret key $s$, the
  algorithm recovers $s$. It does so using a number of oracle queries linear in the input size, yielding an exponential
  improvement in query complexity compared to the best classical approaches. After defining the quantum and classical parts
  of the algorithm, it is run on two examples of Simon’s function: one definable with simple arithmetic, and another with
  a shallow low-level implementation.

# Hamiltonian Simulation

- **Hamiltonian simulation guide** - Provides an introduction and overview to standard Hamiltonian simulation methods.
  The methods are described and implemented utilizing Classiq's built-in functions. First, the product formula
  based methods, Suzuki-Trotter decomposition and qDrift are introduced and implemented. Following,
  more advanced block-encoding, as qubitization and quantum singular value decomposition, are presented.
  - **Hamiltonian simulation with block encoding** - The notebook demonstrates how to implement Hamiltonian simulation with
    three block-encoding methods: Generalized Quantum Signal Processing (QSP), Qubitization, and Quantum Singular Value Transformation (QSVT).
    Each method is explained and defined independently and finally compared.

# Number Theory and Cryptography

- **Discrete log** - Solves the Discrete logarithm problem, i.e., given an element, $x$, of a cyclic group
  with generator $g$, finds the least positive integer $s$, such that $g^s = x$. The algorithm provides an exponential
  speedup relative to the best known classical algorithm. The hardness of the problem, provides the basis for the
  Diffie-Hellman key exchange protocol. Similarly to order-finding and elliptic curve, the problem
  constitutes an instance of the Abelian Hidden Subgroup Problem (HSP).
- **Elliptic curves** - A quantum algorithm solving the elliptic curve discrete logarithm problem in polynomial running time. The
  hardness of the problem constitutes the basis of elliptic curve cryptography, which is widely used for key-exchange, cryptocurrency
  and high-security communications.
  - **Hidden shift problem** - Implementation of an algorithm to find the hidden-shift for the family of Boolean bent functions, which
    are characterized by high non-linearity and a perfectly flat Fourier transform. Given access to queries of a functions $f$,
    the algorithm finds the shift, a boolean string, which satisfies $f(x) = f(x \oplus s)$. The quantum algorithm provides
    an exponential separation in query complexity relative to any (even the best) classical algorithm.
- **Shor's algorithm** - Evaluates the prime factors of a large integer. The algorithm played a foundational role in
  the development of the field, providing an exponential speedup over currently known classical algorithms. The quantum component
  is naturally structured as a Quantum Phase Estimation (QPE) routine, utilizing
  Classiq’s built-in `flexible_qpe` and modular arithmetic.

# QML

- **Hybrid Quantum Neural Networks (QNN)** A hybrid quantum-classical algorithm, incorporating quantum layers into the structure of
  a classical neural network. A state preparation maps classical states in the quantum Hilbert state, following quantum layers are
  implemented by parameterized quantum circuits, providing different expressibility relative to the classical networks.
  Considering a specific example function we construct, train, and verify the hybrid classical-quantum neural network, building
  upon the deep-learning PyTorch module.
- **Quantum Generative Adversarial Networks (GANs)** - A quantum analogue of a classical learning algorithm that generates new
  data which mimics the training set data. The original model is trained by an adversarial optimization in a two-player minmax game,
  utilizing a gradient-based learning. In the quantum algorithm, the classical neural networks are replaced by quantum neural networks.
- **Quantum Support Vector Machine (QSVM)** - Quantum version of the classical machine learning algorithm, classifying
  data points between into two distinct categories. Employing the dual problem formulation, the classification is dictated by a
  defined feature map and the
  kernel matrix. In the quantum algorithm, the feature map is implemented by a quantum circuit and the elements of the
  kernel matrix are evaluated by quantum measurements. The performance of various quantum feature maps are analyzed,
  for both a simplex and complex data sets.
- **Quantum autoencoder** - A quantum program is trained to reduce the memory required to encode data
  with a given structure. The example demonstrates how to use the encoder for anomaly detection.
  Two training approaches for the quantum autoencoder are presented, leveraging Classiq’s integration with PyTorch.

# Quantum Differential Equation Solvers

- **Discrete Poisson solver** - Quantum solver for the discrete Poisson equation, a partial differential equation
  (PDE) widely used in physics and engineering. The equation models the distribution of a potential field due
  to a prescribed source term. The problem is reformulated as a system of linear equations and solved using
  the HHL algorithm. Leveraging quantum cosine and sine transforms from the open library enables a concise
  implementation that can be generalized to higher dimensions.

- **Time marching** - A method for solving linear differential equations, by integrating the dynamics in small discrete steps.
  Given an equation of the form $\frac{d|\psi(t)\rangle}{dt} = A(t) |\psi(t)\rangle$, the algorithm utilizes a block-encoding
  of the time-dependent matrix $A(t)$ to solve for $|\psi(t)\rangle$.

# Quantum Linear Solvers

- **Adiabatic linear solvers** - Demonstrates the mapping of the solution of a quantum linear system problem, $A |\boldsymbol{x}\rangle = |\boldsymbol{b}\rangle$,
  to a ground state of a corresponding Hamiltonian. An approximate solution is then achieved, employing a quantum
  adiabatic protocol, within the framework of quantum adiabatic computing.
  - **HHL** - A fundamental quantum algorithm, designed to solve a set of linear equations, encoded in terms
    of a quantum operation on quantum states: $A |\boldsymbol{x}\rangle = |\boldsymbol{b}\rangle$. Under a restricted number of
    conditions the state $|x\rangle$ can be prepared, in a running time which scales polynomially with the number of qubits required
    to encode the state. This enables an exponential speed up relative to classical algorithms in the evaluation of observables of the form
    $\langle \boldsymbol{x}| M| \boldsymbol{x}\rangle$, where $M$ is a quantum operator.
- **Quantum Singular Value Transformation (QSVT) matrix inversion** - A general framework for solving linear
  systems is implemented, using the Quantum Singular Value Transform (QSVT). Given an efficient procedure for embedding a classical matrix
  as a quantum function via block-encoding, the framework provides a clean approach to matrix inversion.
  When a block-encoding of the matrix and its condition number are available, the algorithm admits a concise implementation
  by invoking the `qsvt_inversion` routine together with classical auxiliary functions from the `qsp` module.
- **Variational Quantum Linear Solver (VQLS) with Linear Combination of Unitaries (LCU)** A hybrid algorithm, employs
  a linear combination of unitaries to block-encode a matrix $A$ within a unitary. The operation of $A$ on a variational
  quantum state then enables performing classical optimization, to reach an approximate solution. As many variational algorithms
  The algorithm hardware requirements are limited, and is well suited for the contemporary NISQ devices.

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

- **Quantum Walks** Demonstrates the encoding of a quantum random walk. The example includes a one-to-one
  comparison between classical random walks and quantum walks through a specific case: a walk on a circle.
  In addition, it illustrates how to implement a generic discrete quantum walk routine, specialized for a
  walk on a hypercube. The implementation makes use of built-in arithmetic and defines quantum functions that
  take a list of quantum callables as a parameter.

# Search and Optimization

- **Decoded Quantum Interferometry**
- **Grover** - A canonical quantum algorithms, providing the solution of an unstructured search problem.
  A general routine is defined and then applied to generic use cases, including the 3-SAT problem and the Max-Cut problem on a graph.
  The use of the phase_oracle quantum function from the Classiq open library, together with the Qmod language for high-level
  arithmetic operations, helps avoid the low-level implementation details typically required on other platforms.

- **Grover Mixers for QAOA**
- **Quantum Approximate Optimization Algorithm (QAOA)**
