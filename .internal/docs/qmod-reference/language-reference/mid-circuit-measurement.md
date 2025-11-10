---
search:
    boost: 2.809
---

# Mid-Circuit Measurement

<!-- prettier-ignore-start -->
!!! warning
    This feature is under development.
<!-- prettier-ignore-end -->

## Syntax

=== "Python"

    **measure** **(** _quantum-var_ **)**

=== "Native"

    **measure** **(** _quantum-var_ **)**

## Semantics

-   A `measure` call receives a quantum variable of type `QBit` and returns a
    `CBool` value.
-   In Qmod Native, when `measure` is called, it must be immediately be assigned
    to a local classical variable, e.g., `x = measure(q);`.
-   Measurements are [run-time](classical-variables.md/#run-time-variables)
    values. Currently, `if` is the only control flow statements that supports
    run-time variables.
-   Following the `measure` operation, any superposition state of its operand
    collapses to a computational-basis state corresponding to the classical
    measured result.

## Example

The following function implements the `RESET` gate using a mid-circuit
measurement.

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    from classiq import *


    @qfunc
    def reset(q: QBit):
        val = measure(q)
        if_(val, lambda: X(q))
    ```

=== "Native"

    ```
    qfunc reset(q: qbit) {
      val: bool;
      val = measure(q);
      if (val) {
        X(q);
      }
    }
    ```
