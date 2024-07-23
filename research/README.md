# Quantum Algorithms Research Papers And Implementations

This page gathers research papers for both canonical and recent works, that
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
          <a href="../algorithms/algebraic/shor/shor_modular_exponentiation.ipynb">Prime Factorization</a><br>
          <a href="../algorithms/algebraic/discrete_log/discrete_log.ipynb">Discrete Logarithm</a><br>
        </td>
        <td>Shor's algorithm for prime factorization and discrete logarithms</td>
        <td>#algebraic #prime_factorization #discrete_logarithms</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/quant-ph/9605043" target="_blank">A fast quantum mechanical algorithm for database search</a></td>
        <td>
          <a href="../algorithms/grover/3_sat_grover/3_sat_grover.ipynb">Grover search for a 3-SAT problem</a>
        </td>
        <td>Grover's algorithm for fast database search</td>
        <td>#grover #database_search</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/0811.3171" target="_blank">Quantum algorithm for solving linear systems of equations</a></td>
        <td>
          <a href="../algorithms/hhl/hhl/hhl.ipynb">HHL Implementation</a>
        </td>
        <td>HHL algorithm for solving linear systems</td>
        <td>#hhl #linear_systems</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/1411.4028" target="_blank">A Quantum Approximate Optimization Algorithm</a></td>
        <td>
          <a href="../applications/optimization/max_cut/max_cut.ipynb">Max Cut Problem</a>
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
          <a href="../algorithms/glued_trees/glued_trees.ipynb">Glued Trees Implementation</a>
        </td>
        <td>Exponential speedup in solving system of coupled harmonic oscilators</td>
        <td>#quantum_speedup</td>
    </tr>
    <tr>
        <td><a href="https://royalsocietypublishing.org/doi/epdf/10.1098/rspa.1992.0167" target="_blank">Rapid solution of problems by quantum computation</a></td>
        <td>
          <a href="../algorithms/deutsch_jozsa/deutsch_jozsa.ipynb">Deutsch-Jozsa Implementation</a>
        </td>
        <td>Deutsch-Jozsa algorithm for rapid problem solving</td>
        <td>#deutsch_jozsa #problem_solving</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/1806.01838" target="_blank">Quantum singular value transformation and beyond: exponential improvements for quantum matrix arithmetics</a></td>
        <td>
          <a href="../algorithms/qsvt/qsvt_matrix_inversion/qsvt_matrix_inversion.ipynb
">QSVT matrix inversion</a><br>
          <a href="../algorithms/qsvt/qsvt_fixed_point_amplitude_amplification/qsvt_fixed_point_amplitude_amplification.ipynb">QSVT fixed point amplitude amplification</a><br>
        </td>
        <td>Introduction of the QSVT Algorithmic framework and its applications</td>
        <td>#qsvt #quantum_algorithms</td>
    </tr>
    <tr>
        <td><a href="https://epubs.siam.org/doi/10.1137/S0097539796298637" target="_blank">On the Power of Quantum Computation</a></td>
        <td>
          <a href="../algorithms/simon/simon.ipynb">Simon's Algorithm Implementation</a>
        </td>
        <td>Simon's algorithm demonstrating quantum computational power</td>
        <td>#simon #quantum_computation</td>
    </tr>
    <tr>
        <td><a href="https://www.nature.com/articles/s41586-019-1666-5" target="_blank">Quantum supremacy using a programmable superconducting processor</a></td>
        <td></td>
        <td>Google's demonstration of quantum supremacy</td>
        <td>#quantum_supremacy #google</td>
    </tr>
    <tr>
        <td><a href="https://arxiv.org/abs/2406.01743" target="_blank">Quantum optimization using a 127-qubit gate-model IBM quantum computer can outperform quantum annealers for nontrivial binary optimization problems</a></td>
        <td></td>
        <td>Q Ctrl optimization using a 127-qubit gate-model IBM quantum computer</td>
        <td>#quantum_optimization #ibm</td>
    </tr>
<tr>
        <td>
            <a href="https://arxiv.org/abs/2402.05574" target="_blank">Quantum Amplitude Loading for Rainbow Options Pricing</a>
        </td>
        <td style="min-width: 200px;">
          <a href="../research/rainbow_options_direct_method/rainbow_options_direct_method.ipynb">Direct Method</a><br>
          <a href="../research/rainbow_options_integration_method/rainbow_options_integration_method.ipynb">Integration Method</a>
        </td>
        <td>
            Implementation of the quantum monte-carlo integration method for the use case of rainbow option pricing
        </td>
        <td>
            #option_pricing<br>
            #amplitude_estimation
        </td>
    </tr>
    <tr>
        <td>
            <a href="https://arxiv.org/pdf/2205.04844" target="_blank">Solving workflow scheduling problems with QUBO modeling</a>
        </td>
        <td style="min-width: 200px;">
          <a href="../applications/logistics/task_scheduling_problem/task_scheduling_problem.ipynb">Workflow Scheduing</a>
        </td>
        <td>
            Workflow scheduling with QAOA
        </td>
        <td>
            #optimization<br>
            #QAOA<br>
            #logistics
        </td>
    </tr>
    <tr>
        <td>
            <a href="https://www.nature.com/articles/s41534-021-00368-4" target="_blank">Resource-efficient quantum algorithm for protein folding</a>
        </td>
        <td style="min-width: 200px;">
          <a href="../applications/chemistry/protein_folding/protein_folding.ipynb">Protein Folding</a>
        </td>
        <td>
            Protein Folding, implemented with QAOA
        </td>
        <td>
            #optimization<br>
            #QAOA<br>
            #chemistry
        </td>
    </tr>
    <tr>
        <td>
            <a href="https://arxiv.org/abs/quant-ph/0111038" target="_blank">Discrete Cosine Transforms on Quantum Computers</a>
        </td>
        <td style="min-width: 200px;">
          <a href="../functions/qmod_library_reference/classiq_open_library/qct_qst/qct_qst.ipynb">Quantum Discrete Cosine Transform</a>
        </td>
        <td>
            Quantum Discrete Cosine Transform Function
        </td>
        <td>
            #functions
        </td>
    </tr>
    <tr>
        <td>
            <a href="https://arxiv.org/pdf/2208.01203" target="_blank">Unsupervised quantum machine learning for fraud detection</a>
        </td>
        <td style="min-width: 200px;">
          <a href="../applications/finance/credit_card_fraud/credit_card_fraud.ipynb">Credit Card Fraud Detection</a>
        </td>
        <td>
            Credit card fraud detection with Quantum Stave Vector Machine (QSVM)
        </td>
        <td>
            #applications<be>
            #finance<be>
            #qml
        </td>
    </tr>
    
</table>
