---
search:
    boost: 2.836
---

# Quantum Program Constraints

When synthesizing a quantum program, you can pass a maximum depth constraint to the generation; for example, requiring that no more than 53 qubits are used.

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

    constraints = Constraints(max_width=20)


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
        max_width=20,
        optimization_parameter=OptimizationParameter.DEPTH,
    )


    @qfunc
    def main(res: Output[QBit]) -> None:
        allocate(1, res)


    synthesize(main, constraints=constraints)
    ```
