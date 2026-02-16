# Quantum Algorithms Implementations

This directory gathers implementations for both canonical and recent works, that
include concrete quantum algorithms. Researchers are invited to add their work
to the table. We also encourage the community to add implementations to papers listed
in the table or to add new ones.

The directory is organized into multiple subject areas:

**Amplitude Amplification and Estimation** - Includes variants of amplitude amplification and
estimation algorithms, which generalize Grover’s search to boost the probability of measuring
marked states and achieve a quadratic speedup—finding a state of initial probability
$𝑝$
p with near certainty using $O(1/
\sqrt{p})$ iterations.

**Foundational** - Fundamental quantum algorithms, providing the foundations for future advancements
and demonstrating query complexity advantages.

**Hamiltonian Simulation** - Advanced methods to simulate physical systems,
including product-formula decompositions and block-encoding–based techniques such as QSP,
qubitization, and QSVT.

**Number Theory and Cryptography** - Contains quantum algorithms for number-theoretic
problems that achieve dramatic speedups over classical methods and underpin cryptographic
attacks on widely used schemes such as RSA, elliptic-curve cryptography, and Diffie–Hellman.

**Quantum Machine Learning** - Hybrid quantum–classical machine learning algorithms that
integrate parameterized quantum circuits with classical optimization frameworks to perform
tasks such as classification, generative modeling, and data compression,

**Quantum Differential Equation Solvers** - Shows how partial differential equations and dynamical evolution
problems can be mapped to linear systems or block-encoded operators and solved with quantum hardware,
to enable efficient scientific and engineering simulations.

**Quantum Linear Solvers** - Brings together principal quantum algorithms for solving linear systems—including
adiabatic approaches, HHL, QSVT-based matrix inversion, and variational methods.

**Quantum Phase Estimation** - Demonstrates how eigenvalues of Hermitian operators can be extracted via controlled
unitary evolution using techniques such as Trotterized simulation and qubitization-based block-encoding,
with applications to quantum chemistry and advanced linear algebra algorithms.

**Quantum Primitives** - Provides core quantum algorithmic primitives—such as the Hadamard test, Swap test, and
Generalized Quantum Signal Processing (GQSP)—that act as modular building blocks for higher-level algorithms

**Quantum State Preparation** - Presents advanced quantum state preparation techniques—including adaptive variational
methods such as ADAPT-VQE and block-encoding–based Gibbs state generation.

**Quantum Walks** - Demonstrates discrete quantum walk implementations, including explicit comparisons with classical
random walks and specialized constructions for structured graphs.

**Search and Optimization** - Showcases quantum algorithms for unstructured search and combinatorial
optimization—including Grover’s amplitude amplification,
Decoded Quantum Interferometry, and variational frameworks such as QAOA and Grover-based mixers.

A representative selection of algorithms is presented below:

<table>
    <tr>
        <th>Algorithm</th>
        <th>Paper Name</th>
        <th>Implementations</th>
        <th>Short Description</th>
    </tr>
    <tr>
        <td>Shor</td>
        <td><a href="https://arxiv.org/abs/quant-ph/9508027" target="_blank">Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer</a></td>
        <td>
          <a href="number_theory_and_cryptography/shor/shor.ipynb">Prime Factorization</a><br>
          <a href="number_theory_and_cryptography/discrete_log/discrete_log.ipynb">Discrete Logarithm</a><br>
        </td>
        <td>Shor's algorithm for prime factorization and discrete logarithms</td>
    </tr>
    <tr>
        <td>Grover</td>
        <td><a href="https://arxiv.org/abs/quant-ph/9605043" target="_blank">A fast quantum mechanical algorithm for database search</a></td>
        <td>
          <a href="search_and_optimization/grover/grover.ipynb">Grover search for a 3-SAT problem</a>
        </td>
        <td>Grover's algorithm for fast database search</td>
    </tr>
    <tr>
        <td>HHL</td>
        <td><a href="https://arxiv.org/abs/0811.3171" target="_blank">Quantum algorithm for solving linear systems of equations</a></td>
        <td>
          <a href="quantum_linear_solvers/hhl/hhl.ipynb">HHL Implementation</a>
        </td>
        <td>HHL algorithm for solving linear systems</td>
    </tr>
    <tr>
        <td>QAOA</td>
        <td><a href="https://arxiv.org/abs/1411.4028" target="_blank">A Quantum Approximate Optimization Algorithm</a></td>
        <td>
          <a href="search_and_optimization/qaoa/qaoa.ipynb">Max Cut Problem</a>
        </td>
        <td>QAOA for combinatorial optimization problems</td>
    </tr>
    <tr>
        <td>VQE</td>
        <td><a href="https://arxiv.org/abs/1304.3061" target="_blank">A variational eigenvalue solver on a quantum processor</a></td>
        <td>
          <a href="../applications/chemistry/molecular_energy_curve/molecular_energy_curve.ipynb">VQE Implementation for molecule ground state solving</a>
        </td>
        <td>Variational Quantum Eigensolver (VQE) for finding eigenvalues</td>
    </tr>
    <tr>
        <td>Quantum Walk (Glued Trees)</td>
        <td><a href="https://arxiv.org/abs/2303.13012" target="_blank">Exponential quantum speedup in simulating coupled classical oscillators</a></td>
        <td>
          <a href="quantum_walks/glued_trees/glued_trees.ipynb">Glued Trees Implementation</a>
        </td>
        <td>Exponential speedup in solving system of coupled harmonic oscillators</td>
    </tr>
    <tr>
        <td>Deutsch–Jozsa</td>
        <td><a href="https://royalsocietypublishing.org/doi/epdf/10.1098/rspa.1992.0167" target="_blank">Rapid solution of problems by quantum computation</a></td>
        <td>
          <a href="foundational/deutsch_jozsa/deutsch_jozsa.ipynb">Deutsch-Jozsa Implementation</a>
        </td>
        <td>Deutsch-Jozsa algorithm for rapid problem solving</td>
    </tr>
    <tr>
        <td>QSVT</td>
        <td><a href="https://arxiv.org/abs/1806.01838" target="_blank">Quantum singular value transformation and beyond: exponential improvements for quantum matrix arithmetics</a></td>
        <td>
          <a href="quantum_linear_solvers/qsvt_matrix_inversion/qsvt_matrix_inversion.ipynb">QSVT matrix inversion</a><br>
          <a href="amplitude_amplification_and_estimation/qsvt_fixed_point_amplitude_amplification/qsvt_fixed_point_amplitude_amplification.ipynb">QSVT fixed point amplitude amplification</a><br>
        </td>
        <td>Introduction of the QSVT Algorithmic framework and its applications</td>
    </tr>
    <tr>
        <td>Simon</td>
        <td><a href="https://epubs.siam.org/doi/10.1137/S0097539796298637" target="_blank">On the Power of Quantum Computation</a></td>
        <td>
          <a href="foundational/simon/simon.ipynb">Simon's Algorithm Implementation</a>
        </td>
        <td>Simon's algorithm demonstrating quantum computational power</td>
    </tr>
    <tr>
        <td>DQI</td>
        <td><a href="https://arxiv.org/abs/2408.08292" target="_blank">Optimization by Decoded Quantum Interferometry</a></td>
        <td>
          <a href="search_and_optimization/dqi/dqi_max_xorsat.ipynb">DQI Algorithm Implementation</a>
        </td>
        <td>Decoded Quantum Interferometry Algorithm for discrete optimization problems</td>
    </tr>
    <tr>
        <td>Quantum Amplitude Loading</td>
        <td>
            <a href="https://arxiv.org/abs/2402.05574" target="_blank">Quantum Amplitude Loading for Rainbow Options Pricing</a>
        </td>
        <td>
          <a href="../applications/finance/rainbow_options/rainbow_options_direct_method.ipynb">Direct Method</a><br>
          <a href="../applications/finance/rainbow_options/rainbow_options_integration_method.ipynb">Integration Method</a>
        </td>
        <td>
            Implementation of the quantum monte-carlo integration method for the use case of rainbow option pricing
        </td>
    </tr>
</table>
