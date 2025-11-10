---
search:
    boost: 3.365
---

# Skip Control

The _skip-control_ statement designates a statement block that should be applied
unconditionally, even when the enclosing function is subject directly or
indirectly to a [quantum control operator](https://docs.classiq.io/latest/qmod-reference/language-reference/statements/control/).
This construct is typically applied when the enclosing function involves
intermediate computation and uncomputation blocks in ways that cannot be
formulated using a simple conjunction (i.e., using the _within-apply_ statement).

## Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def skip_control(stmt_block: QCallable) -> None:
        pass
    ```

=== "Native"

    **skip_control** **{** _statements_ **}**

## Semantics

-   All statements nested under a _skip-control_ statement are applied
    unconditionally, including in states where a control condition from above is
    evaluated to `False`. It is the user's responsibility to ensure that the
    combined effect of the _skip-control_ blocks in the enclosing function is
    functionally equivalent to NOP (identity).
-   Using _skip-control_ inside the _within_ block of a _within-apply_ statement
    is redundant, since the _within_ block is itself designated as a
    _skip-control_ block.
-   Using _skip-control_ directly inside the _apply_ block of a _within-apply_
    statement is not allowed.

## Example

The following example demonstrates the use of `skip_control`. Function `foo`
rotates a qubit in steps, applying a controlled flip of other qubits at each
step. The controlling qubit ultimately returns to its original state. The
rotations are marked with `skip_control` because they can be safely applied even
for states where the whole function is under a negative control condition, as
demonstrated by function `main`.
Note that the computation of `qarr[0]` within `foo` cannot be encapsulated in an
_apply_ block of a _within-apply_ statement.

=== "Python"

    ```python
    from classiq import *
    from classiq.qmod.symbolic import pi


    @qfunc
    def foo(qarr: QArray[QBit, 5]) -> None:
        repeat(
            4,
            lambda i: [
                CX(qarr[0], qarr[i + 1]),
                skip_control(lambda: RX(pi / 2, qarr[0])),
            ],
        )


    @qfunc
    def main(ctrl: Output[QBit], qarr: Output[QArray[QBit, 5]]) -> None:
        allocate(qarr)
        hadamard_transform(qarr[0])
        allocate(ctrl)
        hadamard_transform(ctrl)
        control(ctrl, lambda: foo(qarr))
    ```

=== "Native"

    ```
    qfunc foo(qarr: qbit[5]) {
      repeat (i: 4) {
        CX(qarr[0], qarr[i+1]);
        skip_control {
          RX(pi/2, qarr[0]);
        }
      }
    }

    qfunc main(output ctrl: qbit, output qarr: qbit[5]) {
      allocate(qarr);
      hadamard_transform(qarr[0]);
      allocate(ctrl);
      hadamard_transform(ctrl);
      control(ctrl) {
        foo(qarr);
      }
    }
    ```
