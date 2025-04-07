# Quantum Algorithms Implementations

This page gathers implementations for both canonical and recent works, that
include concrete quantum algorithms. Researchers are invited to add their work
to the table. We also encourage the community to add implementations to papers listed
in the table or to add new ones.

<table>
    <tr>
        <th>Paper Name</th>
        <th>Implementations</th>
        <th>Short Description</th>
        <th>Tags</th>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/quant-ph/9508027" target="_blank">Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer</a></td>
        <td>
          <a href="algebraic/shor/shor_modular_exponentiation.ipynb">Prime Factorization</a><br>
          <a href="algebraic/discrete_log/discrete_log.ipynb">Discrete Logarithm</a><br>
        </td>
        <td>Shor's algorithm for prime factorization and discrete logarithms</td>
        <td>#algebraic #prime_factorization #discrete_logarithms</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/quant-ph/9605043" target="_blank">A fast quantum mechanical algorithm for database search</a></td>
        <td>
          <a href="grover/3_sat_grover/3_sat_grover.ipynb">Grover search for a 3-SAT problem</a>
        </td>
        <td>Grover's algorithm for fast database search</td>
        <td>#grover #database_search</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/0811.3171" target="_blank">Quantum algorithm for solving linear systems of equations</a></td>
        <td>
          <a href="hhl/hhl/hhl.ipynb">HHL Implementation</a>
        </td>
        <td>HHL algorithm for solving linear systems</td>
        <td>#hhl #linear_systems</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/1411.4028" target="_blank">A Quantum Approximate Optimization Algorithm</a></td>
        <td>
          <a href="../algorithms/qaoa/maxcut/qaoa_maxcut.ipynb">Max Cut Problem</a>
        </td>
        <td>QAOA for combinatorial optimization problems</td>
        <td>#qaoa #optimization</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/1304.3061" target="_blank">A variational eigenvalue solver on a quantum processor</a></td>
        <td>
          <a href="../applications/chemistry/molecular_energy_curve/molecular_energy_curve.ipynb">VQE Implementation for molecule ground state solving</a>
        </td>
        <td>Variational Quantum Eigensolver (VQE) for finding eigenvalues</td>
        <td>#vqe</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/2303.13012" target="_blank">Exponential quantum speedup in simulating coupled classical oscillators</a></td>
        <td>
          <a href="glued_trees/glued_trees.ipynb">Glued Trees Implementation</a>
        </td>
        <td>Exponential speedup in solving system of coupled harmonic oscilators</td>
        <td>#quantum_speedup</td>
    </tr>
    <tr>
        <td><a href="https://royalsocietypublishing.org/doi/epdf/10.1098/rspa.1992.0167" target="_blank">Rapid solution of problems by quantum computation</a></td>
        <td>
          <a href="deutsch_jozsa/deutsch_jozsa.ipynb">Deutsch-Jozsa Implementation</a>
        </td>
        <td>Deutsch-Jozsa algorithm for rapid problem solving</td>
        <td>#deutsch_jozsa #problem_solving</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/1806.01838" target="_blank">Quantum singular value transformation and beyond: exponential improvements for quantum matrix arithmetics</a></td>
        <td>
          <a href="../algorithms/qsvt/qsvt_matrix_inversion/qsvt_matrix_inversion.ipynb
">QSVT matrix inversion</a><br>
          <a href="qsvt/qsvt_fixed_point_amplitude_amplification/qsvt_fixed_point_amplitude_amplification.ipynb">QSVT fixed point amplitude amplification</a><br>
        </td>
        <td>Introduction of the QSVT Algorithmic framework and its applications</td>
        <td>#qsvt #quantum_algorithms</td>
    </tr>
    <tr>
        <td><a href="https://epubs.siam.org/doi/10.1137/S0097539796298637" target="_blank">On the Power of Quantum Computation</a></td>
        <td>
          <a href="simon/simon.ipynb">Simon's Algorithm Implementation</a>
        </td>
        <td>Simon's algorithm demonstrating quantum computational power</td>
        <td>#simon #quantum_computation</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/2408.08292" target="_blank">Optimization by Decoded Quantum Interferometry
</a></td>
        <td>
          <a href="dqi/dqi_max_xorsat.ipynb">DQI Algorithm Implementation</a>
        </td>
        <td>Decoded Quantum Interferometry Algorithm for discrete optimization problems</td>
        <td>#dqi #quantum_algorithms</td>
    </tr>
    <tr>
        <td>
            <a href="https://arxiv.org/abs/2402.05574" target="_blank">Quantum Amplitude Loading for Rainbow Options Pricing</a>
        </td>
        <td style="min-width: 200px;">
          <a href="../applications/finance/rainbow_options/rainbow_options_direct_method.ipynb">Direct Method</a><br>
          <a href="../applications/finance/rainbow_options/rainbow_options_integration_method.ipynb">Integration Method</a>
        </td>
        <td>
            Implementation of the quantum monte-carlo integration method for the use case of rainbow option pricing
        </td>
        <td>
            #option_pricing<br>
            #amplitude_estimation
        </td>
    </tr>
</table>
