---
search:
    boost: 3.166
---

# Classical Control Flow

Loops and conditionals on classical expressions are useful means to describe reusable
building blocks. Qmod has two basic forms - the _repeat_ statement and the _if_ statement.

## Classical Repeat

### Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def repeat(count: CInt, iteration: QCallable[CInt]) -> None:
        pass
    ```

=== "Native"

    **repeat** **(** _iteration_variable_ **:** _count_ **)** **{** _iteration-statements_ **}**

### Semantics

-   Invoke the _iteration_ block _count_ times, binding the index variable to the respective
    iteration number - 0, 1,... _count_-1.
-   Inside the statement block, use of quantum variables declared outside it is restricted
    to contexts where the variable is initialized and remains initialized (see [Quantum Variables](../quantum-variables.md))

### Example

The following example defines a useful function - applying the Hadamard function across
all qubits in a qubit array - using _repeat_. Note that a similar function is available
in the Classiq open-library.

=== "Python"

    ```python
    from classiq import H, QArray, QBit, qfunc, repeat


    @qfunc
    def my_hadamard_transform(qba: QArray[QBit]):
        repeat(
            count=qba.len,
            iteration=lambda index: H(qba[index]),
        )
    ```

=== "Native"

    ```
    qfunc my_hadamard_transform(qba: qbit[]) {
      repeat (index: qba.len) {
        H(qba[index]);
      }
    }
    ```

## Classical If

### Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def if_(condition: CBool, then: QCallable, else_: Optional[QCallable] = None) -> None:
        pass
    ```

    Note that identifiers in Qmod that happen to conflict with Python keywords have `_`
    suffix. This is the case with `if_` and `else_` in the second function.

=== "Native"

    **if** **(** condition **)** **{** _then-statements_ **}** else **{** _else-statements_ **}**

### Semantics

-   Invoke the _then_ block if _condition_ evaluates to `true` and otherwise invoke the _else_ block
-   Inside the statement block, use of quantum variables declared outside it is restricted
    to contexts where the variable is initialized and remains initialized (see [Quantum Variables](../quantum-variables.md))

### Example

=== "Python"

    ```python
    from classiq import CBool, X, Y, QBit, qfunc, if_


    @qfunc
    def my_conditional_gate(cond: CBool, qb: QBit):
        if_(
            condition=cond,
            then=lambda _: X(qb),
            else_=lambda _: Y(qb),
        )
    ```

=== "Native"

    ```
    qfunc my_conditional_gate(cond: bool, qb: qbit) {
      if (cond) {
        X(qb);
      } else {
        Y(qb);
      }
    }
    ```

## Classical Foreach

The _foreach_ statement iterates through the elements of a classical array.
Its compilation and simulation are more efficient.

<!-- prettier-ignore-start -->
!!! warning
    The `foreach` statement is an experimental feature. It is only supported in
    Qmod Python.
<!-- prettier-ignore-end -->

### Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def foreach(values: CArray | list, iteration: Callable) -> None:
        pass
    ```

The `iteration` callable accepts one or more iteration variables.

### Semantics

-   Invoke the _iteration_ block once for every element of _values_.
-   If the _iteration_ block accepts a single iteration variable, the elements
    of _values_ will be bound to it sequentially.
-   If _values_ is a nested array (`CArray[CArray]`), the length of _values_'
    elements is $n$, $n>=2$, and the _iteration_ block has $n$ iteration
    variables, then _values_' elements will be unpacked into the iteration
    variables in each iteration.
-   Inside the statement block, use of quantum variables declared outside it is restricted
    to contexts where the variable is initialized and remains initialized (see [Quantum Variables](../quantum-variables.md))
-   _values_ must be a value of type `CArray[CReal]` or `CArray[CArray[CReal]]`.

### Examples

In the following example, the `foreach` statement iterates through the elements
of the classical list `[0.1, 0.2]` and assigns its elements into the iteration
variable `i`.
This is equivalent to calling `RX` and `Y` twice, once with angle `0.1` and
once with `0.2`.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(q: Output[QBit]) -> None:
        allocate(q)
        foreach(
            [0.1, 0.2],
            lambda i: [
                RX(i, q),
                Y(q),
            ],
        )
    ```

In the following example, the `foreach` statement iterates through the elements
of the classical list `[[0.1, 0.2], [0.3, 0.4]]` and assigns its elements into the iteration
variables `i` and `j`.
In each iteration, the elements of the nested arrays are "unpacked" into the
iteration variables.
The first iteration assigns `0.1` into `i` and `0.2` into `j`, and the second
iteration assigns `0.3` into `i` and `0.4` into `j`.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(q: Output[QBit]) -> None:
        allocate(q)
        foreach(
            [[0.1, 0.2], [0.3, 0.4]],
            lambda i, j: [
                RX(i, q),
                RY(j, q),
            ],
        )
    ```
