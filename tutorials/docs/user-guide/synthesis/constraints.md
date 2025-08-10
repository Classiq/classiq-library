# Quantum Program Constraints

When synthesizing a quantum program, you can pass in constraints to the generation; for example, requiring that no more than 53 qubits are used.
The Classiq engine allows the following constraints, each of which can pass to the synthesis engine:

-   Depth: the maximum depth of the quantum program
-   Width: the maximum number of qubits in the quantum program
-   Gate count: the maximum number of times a gate appears

Pass constraints as follows:

=== "SDK"

    ```python
    from classiq import (
        qfunc,
        Constraints,
        Output,
        QBit,
        TranspilerBasisGates,
        allocate,
        set_constraints,
        synthesize,
    )

    constraints = Constraints(
        max_width=20,
        max_depth=100,
        max_gate_count={
            TranspilerBasisGates.CX: 10,
            TranspilerBasisGates.T: 20,
        },
    )


    @qfunc
    def main(res: Output[QBit]) -> None:
        allocate(1, res)


    synthesize(main, constraints=constraints)
    ```

## Optimization Parameter

When synthesizing a quantum program, to optimize the quantum program according to a
parameter, set the `optimization_parameter` field. The possible
parameters are the same parameters that can be constrained.

The following example shows how to remove the width constraint in the quantum program, setting it instead
as the optimization parameter.

=== "SDK"

    ```python
    from classiq import (
        qfunc,
        Constraints,
        OptimizationParameter,
        Output,
        QBit,
        TranspilerBasisGates,
        allocate,
        set_constraints,
        synthesize,
    )

    constraints = Constraints(
        max_depth=100,
        max_gate_count={
            TranspilerBasisGates.CX: 10,
            TranspilerBasisGates.T: 20,
        },
        optimization_parameter=OptimizationParameter.WIDTH,
    )


    @qfunc
    def main(res: Output[QBit]) -> None:
        allocate(1, res)


    synthesize(main, constraints=constraints)
    ```
