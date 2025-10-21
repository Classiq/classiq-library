---
search:
    boost: 2.026
---

# Operators

<!-- cspell:ignore qfunc -->

A function in Qmod can take other functions as arguments and call these functions in its
body. Functions operating on other functions are often referred to as higher-order functions,
or operators. This mechanism is used to define reusable quantum algorithm patterns,
such as the Quantum Phase Estimation and the Grover operator.

## Function types

Parameters of function types are declared like parameters of other type categories. The
function type determines the list of arguments that must be accepted by the function
passed in as argument.
Array function types correspond to an indexable collection of function values with a common
signature.

### Syntax

=== "Python"

    The `QCallable` type hint is used to specify a function type. `QCallable` itself is a
    generic class, taking as parameters a list of type hints that declare the parameters of
    the function. The `QPerm` type hint is used to specify a _permutation_
    function type.

    The `QCallableList` type hint specifies a function array type, and
    `QPermList` specifies a _permutation_ function array type.

    The name of a parameter in a function type can optionally be specified using the form -
    **Annotated** **[** _type_ **, "** _name_ **"]**.

=== "Native"

    Function type syntax has the following form -

    (**qfunc** | **qperm**) **(** _function-type-parameters_ **)**

    _function-type-parameters_ is a list of zero or more comma-separated declarations
    in the form - [ _name_ **:** ] _type_.

    If **[]** follows the **qfunc**/**qperm** keyword, the parameter is interpreted as a function
    array -

    (**qfunc** | **qperm**) **[** **]** **(** _function-type-parameters_ **)**

### Semantics

-   The function passed as argument to an operator must agree in its signature with the number, types,
    and order of parameters declared in the respective function type. Note that names of
    parameters are optional in the function type, and where specified, are not required to
    match the argument.
-   A parameter of a function type can be called inside the function's body just like a
    regular function, passing arguments as per the declared signature.
-   An element of a function array type can be called with a subscript operator applied to
    the parameter, followed by the argument list.
-   The `qperm` keyword specifies guarantees (and restrictions) on how the quantum state
    may change within the function.
    See [Uncomputation](uncomputation.md) for more details.

### Example

In the following example, the function `my_operator` declares the parameter `my_operand`
of a function type with one classical parameter and one quantum parameter. The function
is called twice in its body, passing different argument values. In function
`main`, `my_operator` is called twice, each time passing a different function as its
argument.

=== "Python"

    ```python
    from classiq import CReal, QBit, QCallable, RX, qfunc, allocate
    from classiq.qmod.symbolic import pi


    @qfunc
    def my_operator(my_operand: QCallable[CReal, QBit], q: QBit) -> None:
        my_operand(pi / 2, q)
        my_operand(pi / 4, q)


    @qfunc
    def main() -> None:
        q = QBit()
        allocate(q)
        my_operator(lambda theta, target: RX(theta, target), q)
        my_operator(lambda theta, target: RY(theta, target), q)
    ```

    Notes:
    - Passing named functions in Python is currently not supported. This example
    uses Python lambda expressions - see more in the next section.
    - Function arguments in Python do not support specifying argument names. When
      translating Qmod Python description to native syntax, names `arg0`,
      `arg1`, etc. are associated with the arguments automatically.

=== "Native"

    ```
    qfunc my_operator(my_operand: qfunc (theta: real, target: qbit), q: qbit) {
      my_operand(pi / 2, q);
      my_operand(pi / 4, q);
    }

    qfunc main() {
      q: qbit;
      allocate(q);
      my_operator(RX, q);
      my_operator(RY, q);
    }
    ```

Synthesizing this model creates the quantum program shown below. You can see four
rotations in the circuit with their respective angles.

![operator_declaration.png](resources/operator_declaration.png)

## Lambda functions

You can pass a function to an operator in one of two forms - a named function, and a lambda
function. Lambda functions are anonymous functions defined in-line in the operator call site.
Note that in Python only the lambda function form is supported.

### Syntax

=== "Python"

    A Python `Callable` object is used as a Qmod lambda function. This can take one of two forms -
    a Python lambda expression, or a named _Python_ function (not decorated with `@qfunc`).
    When a named function is used with type hints on its arguments, the names of the
    operands will be reflected in the Qmod description.

=== "Native"

    Lambda function syntax is somewhat similar to a function definition. The
    keyword `qfunc` is replaced with `lambda`, the name of the function is omitted,
    and argument lists only specify only names, not types.

    **lambda** \[ **<** _classical-arg-names_ **>** \] **(** _quantum-arg-names_ **)** **{** _statements_ **}**

### Example 1

Consider the following snippet, where `my_operator` is called twice from function `main`,
once with a regular function and a second time with a lambda function. These two calls
are equivalent.

=== "Python"

    ```python
    from classiq import *
    from classiq.qmod.symbolic import pi


    @qfunc
    def my_operator(my_operand: QCallable[CReal, QBit], q: QBit) -> None:
        H(q)
        my_operand(pi / 2, q)


    def my_operand(angle: CReal, target: QBit) -> None:
        RX(angle, target)


    @qfunc
    def main() -> None:
        q = QBit()
        allocate(q)
        my_operator(my_operand, q)
        my_operator(lambda angle, target: RX(angle, target), q)
    ```

    Note that in the first call, the argument is a regular Python function, not decorated
    with `@qfunc`.

=== "Native"

    ```
    qfunc my_operator(my_operand: qfunc (angle: real, target: qbit), q: qbit) {
      H(q);
      my_operand(pi / 2, q);
    }

    qfunc my_operand(angle: real, target: qbit) {
      RX(angle, target);
    }

    qfunc main() {
      q: qbit;
      allocate(q);
      my_operator(my_operand, q);
      my_operator(lambda (angle, target) {
        RX(angle, target);
      }, q);
    }
    ```

### Example 2

An operator may pass expressions involving its own arguments to its operand.
The following example demonstrates this.

=== "Python"

    ```python
    from classiq import *
    from classiq.qmod.symbolic import pi


    @qfunc
    def foo_operator(
        n: CInt,
        my_operand: QCallable[CReal, QBit],
        qba: QArray[QBit, 2],
    ) -> None:
        H(qba[0])
        my_operand(pi / n, qba[1])


    @qfunc
    def main() -> None:
        qba = QArray()
        allocate(2, qba)
        foo_operator(n=4, my_operand=lambda theta, target: RX(theta, target), qba=qba)
    ```

=== "Native"

    ```
    qfunc foo_operator(n: int, my_operand: qfunc (angle: real, qb: qbit), qba: qbit[2]) {
      H(qba[0]);
      my_operand(pi / n, qba[1]);
    }

    qfunc main() {
      qba: qbit[];
      allocate(2, qba);
      foo_operator(4, lambda(angle, qb) {
        RX(angle, qb);
      }, qba);
    }
    ```

Synthesizing this model creates the quantum program shown below. You can see that the call to
`foo_operator` applies an X rotation on qubit 1, based on the value of `n` passed to it.

![operator_call.png](resources/operator_call.png)

## Capturing context variables and parameters

A lambda function that is passed as an argument to an operator may reference classical or
quantum variables in its own lexical scope. The objects whose references are captured are
available when the callable is invoked by the operator, even though the operator itself
is oblivious to them.

An operator must not implicitly change the initialized status of quantum variables captured
inside lambda functions that are passed to it. Only initialized variables may be
captured, and they remain initialized after the operator call. Hence, quantum variables
cannot be captured as output-only or input-only arguments inside a lambda function. Note
that an operator may actually invoke the operand once, multiple times, or not at all.

### Example

The following example is similar to _Example 2_ from the previous section. However, in this
case, the quantum variable used inside the lambda function is captured directly from the
scope rather than being passed to it indirectly through the operator. The resulting quantum program
in this case is identical to that of the previous version in _Example 2_ above.

=== "Python"

    ```python
    from classiq import CInt, CReal, H, QBit, QCallable, RX, allocate, qfunc
    from classiq.qmod.symbolic import pi


    @qfunc
    def foo_operator(
        n: CInt,
        my_operand: QCallable[CReal],
        qb: QBit,
    ) -> None:
        H(target=qb)
        my_operand(pi / n)


    @qfunc
    def main() -> None:
        qb1 = QBit()
        qb2 = QBit()
        allocate(qb1)
        allocate(qb2)
        foo_operator(n=4, my_operand=lambda t: RX(theta=t, target=qb1), qb=qb2)
    ```

=== "Native"

    ```
    qfunc foo_operator(n: int, my_operand: qfunc (angle: real), qb: qbit) {
      H(qb);
      my_operand(pi / n);
    }

    qfunc main() {
      qb1: qbit;
      qb2: qbit;
      allocate(qb1);
      allocate(qb2);
      foo_operator(4, lambda(t) {
        RX(t, qb1);
      }, qb2);
    }
    ```
