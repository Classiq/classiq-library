---
search:
    boost: 3.471
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
