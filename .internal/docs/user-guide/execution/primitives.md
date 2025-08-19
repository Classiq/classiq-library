---
search:
    boost: 3.098
---

# Execution Primitives

As well as designing quantum programs, the Classiq quantum model contains
classical instructions for the execution process.

<!-- prettier-ignore-start -->
!!! note
    When designing a model, you must specify classical instructions for the execution process
    to take part.
<!-- prettier-ignore-end -->

## Sample

The `sample` execution primitive instructs the execution process to
sample the state of the quantum program.

=== "SDK"

    Upon execution, the results of a program with a `sample` primitive are of type
    `ExecutionDetails`, describing the measurement results of the quantum program.
    Ways to access these measurements:

    - The `counts` attribute allows access to the measurement results of all qubits.
       The qubit order of each state in `counts` is indicated by the `counts_lsb_right` Boolean flag.
    - The `parsed_counts` attribute contains parsed states according to the arithmetic information of the output registers.
    - The `parsed_counts_of_outputs` method allows access to the parsed counts
      of specific given outputs. It receives either a single output name or a tuple of output names.
    - The `counts_of_qubits` method allows access to results of specific qubits. The order of qubits in the measurement result is determined by their order in the `qubits` argument of the method.
    - The `counts_of_output` method is similar to `counts_of_qubits`, but receives an output name as an argument. Note it may only be used if the generated model has outputs.
    - The `counts_of_multiple_outputs` is similar to `counts_of_output`.
       It receives a tuple of output names, and returns the counts of all specified outputs, keyed by a tuple of states matching the requested outputs.
    - The `counts_by_qubit_order` method allows access to the `counts` attribute in the required qubit order.
    - The `num_shots` attribute is the sum of all of the resulting count fields.

    The `ExecutionDetails` object also contains a `dataframe` property that displays the relevant information in a pandas dataframe for easy manipulation.

## VQE

The `vqe` execution primitive instructs the execution process to perform the
Variational Quantum Eigensolver (VQE) algorithm.
Given a parametric quantum program (an ansatz) and an Hamiltonian, the algorithm tries
to minimize the expectation value of the Hamiltonian with respect to the resulting quantum states of the quantum program.

The `vqe` primitive accepts these parameters:

-   `hamiltonian`: The Hamiltonian with which to optimize.
-   `initial_point`: The initial parameter assignment. Default: `None`.
-   `maximize`: If `True`, maximizes the expectation value instead of minimizing it.
-   `optimizer`: The kind of optimizer to use: `COBYLA`, `SPSA`, `L_BFGS_B`, `NELDER_MEAD`, `ADAM`, or `SLSQP`.
-   `max_iteration`: The maximum number of optimizer iterations.
-   `tolerance`: The final accuracy in the optimization. Default: `0`.
-   `step_size`: The step size for numerically calculating the gradient. Default: `0`.
-   `skip_compute_variance`: If `True`, the optimizer does not compute the variance of the ansatz. Default: `False`.
-   `alpha_cvar`: The parameter for the CVaR[[1]](#1) summarizing method. Default: `1`.

The following example defines a quantum model with a single RX gate
with the parameter $\theta$,
and executes the `vqe` primitive with `0.3Z` as the Hamiltonian.

=== "SDK"

The results of a program with a `vqe` primitive are of type `VQESolverResult`, which
describes the algorithm results. It contains this information:

-   `optimal_parameters`: The optimal parameters found by the algorithm.
-   `energy`: The expectation value of the ansatz with the optimal parameters (the
    minimum/maximum eigenvalue of the Hamiltonian).
-   `optimized_circuit_sample_results`: The results of sampling the ansatz with the optimal parameters. If executed with state vector simulation, the inner field `state_vector` is the eigenstate of the Hamiltonian.
-   `time`: The execution time of the algorithm (in seconds).
-   `num_shots`: The number of shots used in each iteration.
-   `intermediate_results`: List of per-iteration results.
-   `convergence_graph_str`: A string representing the energy convergence graph
    (shown in the IDE).

## IQAE

The `iqae` execution primitive instructs the execution process to perform the
Iterative Quantum Amplitude Estimation algorithm [[2]](#2).
Given $A$ such that $A|0\rangle_n|0\rangle = \sqrt{1-a}|\psi_0\rangle_n|0\rangle + \sqrt{a}|\psi_1\rangle_n|1\rangle$,
the algorithm tries to estimate $a$ by iteratively sampling $Q^kA$, where $Q=AS_0A^{\dagger}S_{\psi_0}$ and $k$ is an integer variable.

<!-- prettier-ignore-start -->
!!! note
    The `iqae` primitive assumes you have correctly defined the quantum model;
    i.e., $Q^kA$, where $k$ is specified by adding `power="k"` to the function
    parameters of the desirable function.
    In addition, the only output port should be the last qubit.
<!-- prettier-ignore-end -->

There are two parameters to the `iqae` primitive: `epsilon` specifies the
target accuracy, and `alpha` specifies the confidence level (meaning the
precision probability is $1 - \alpha$).

The following example defines $A = RY(\theta)$ and $Q = RY(2\theta)$.
The estimation result should be $a = \sin^2(\frac{\theta}{2})$, as
$A|0\rangle = \cos\frac{\theta}{2}|0\rangle + \sin\frac{\theta}{2}|1\rangle$.

The results of a program with an `iqae` primitive are of type `IQAEResult`, which
describes the algorithm results. It contains this information:

-   `estimation`: The estimated value of $a$.
-   `confidence_interval`: The confidence interval for the value of $a$.
-   `iterations_data`: List of per-iteration information. Each item contains:
    -   `grover_iterations`: The value of $k$ for this iteration.
    -   `sample_results`: The results of sampling $Q^kA$ in this iteration.
-   `warnings`: List of warnings yielded throughout the algorithm execution, such
    as reaching the maximum number of iterations.

## References

<a name="1">[1]</a> Barkoutsos, P. K. et al., [Improving variational quantum optimization using CVaR](https://arxiv.org/abs/1907.04769), Quantum 4, 256 (2019).

<a name="2">[2]</a> Grinko, D., Gacon, J., Zoufal, C. et al., [Iterative quantum amplitude estimation](https://doi.org/10.1038/s41534-021-00379-1), npj Quantum Inf 7, 52 (2021).
