# Solver Customization

The `execution_parameters` input to the `construct_chemistry_model` function details the parameters of the VQE optimization scheme.

The `ChemistryExecutionParameters` class consists of these parameters:

1. `name: OptimizerType` – Classical optimization algorithms: `COBYLA`, `SPSA`, `ADAM`, `L_BFGS_B`, `NELDER_MEAD`, `SLSQP`.
2. `max_iteration: int` – Maximal number of optimizer iterations.
3. `initial_point: Optional[np.ndarray]` – Initial values for the ansatz parameters.
4. `tolerance: float` – Final accuracy of the optimization.
5. `step_size: float` – Step size for numerically calculating the gradient in `L_BFGS_B` and `ADAM` optimizers.
6. `skip_compute_variance: bool` – If True, the optimizer does not compute the variance of the ansatz.

## Example

=== "SDK"

    ```python
    from classiq.applications.chemistry import ChemistryExecutionParameters
    from classiq import OptimizerType

    execution_params = ChemistryExecutionParameters(
        optimizer=OptimizerType.COBYLA,
        max_iteration=30,
    )
    ```
