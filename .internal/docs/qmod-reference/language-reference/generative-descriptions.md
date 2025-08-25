---
search:
    boost: 2.776
---

# Generative Descriptions

Qmod supports classical variables, expressions, and control-flow statements. In addition,
in Qmod's Python embedding it is often useful to rely on Python itself to perform classical
computations at model construction time. This lets you leverage Python's language features,
libraries, and debugging tools.

The example below illustrates how the Python `for` statement and `math.asin` function
can be used to generate a Qmod description.

```python
from classiq import PHASE, QArray, QBit, qfunc
from math import asin


@qfunc
def foo(qa: QArray[QBit]):
    for i in range(qa.len):  # 'qa.len' is a Python integer
        PHASE(asin(i / qa.len), qa[i])  # the expression `i / qa.len` is a Python float
```

## Python-Type Function Parameters

In Python, Qmod functions may declare parameters of either Qmod classical types, or
their Python built-in counterparts. Variables of Qmod types are represented symbolically
in Python (see explanation below), while variables of standard Python types hold the actual
Python value. The values of Python-type parameters are known at model construction time, while
the value of Qmod variables are known only at a later compilation or execution stage.

The table below lists the mappings between Qmod classical types and Python built-in
types (for more on classical types, see [Classical Types](classical-types.md)). Using
Python types other than the ones listed below is flagged as an error.

| Qmod   | Python |
| :----- | :----: |
| CInt   |  int   |
| CReal  | float  |
| CBool  |  bool  |
| CArray |  list  |

Qmod functions can declare parameters of function type using the generic class `QCallable`
(see [Operators](operators.md)). In these cases too, parameters may be Python built-in types.
When the actual function argument is a Python lambda expression, the use of lambda parameters
as symbolic or Python values must conform to the declaration of the respective parameters
in the receiving function.

## Symbolic and Python-Value Expression Semantics

-   A classical expression is symbolic if it contains any variable declared with a Qmod
    type. A (non-symbolic) Python expression may contain only Python variables.
-   Python literal values, variables, and expressions can be passed as arguments to
    functions expecting Qmod types, or be used in Qmod statements. However, Qmod variables
    and expressions cannot be passed as arguments to functions expecting Python types,
    nor be used in general Python expression contexts.
-   The attributes of quantum variables - `size`, `len`, `is_signed`, and `fraction_digits` -
    are treated as Python (non-symbolic) expressions (see [Quantum Types](quantum-types.md)).
-   The `len` attribute of classical arrays is symbolic for type `CArray` and a Python value
    for type `list`.
-   The index variable in a Qmod `repeat` statement is a Qmod symbolic variable of type
    `CInt` (see [Classical Control Flow](statements/classical-control-flow.md)).
-   Execution parameters (i.e., parameters of function `main`) must be symbolic (see
    [Quantum Entry Point](quantum-entry-point.md)).

Notes:

-   The body of functions with Python parameters will be evaluated for every different set of
    arguments, while the body of a function with symbolic parameters will be evaluated only once.
    The overall Qmod compilation process for symbolic logic may be more efficient.
-   The Classiq SDK includes the package `classiq.qmod.symbolic` with useful math functions
    operating on Qmod symbolic expressions.
-   Qmod symbolic expressions and control-flow statements are processed by the Qmod compiler.
    Therefore, they can be translated back to the Qmod native syntax and visualized as such
    in the Classiq IDE. In contrast, Python expressions and statements are evaluated by the
    Python interpreter prior to reaching the Qmod toolchain and leave no trace in translation
    or visualization.
-   Python expressions and statements have the advantage of being supported by conventional Python
    debugging tools.

## Examples

### Example 1: Generative Description of QFT

The following example demonstrates the use of nested Python `for` loops to define
the quantum Fourier transform (QFT). An equivalent description can be written with nested
Qmod `repeat` statements, but the Python version is more readable and easier to debug.
The printouts with the `print` statement are meaningful only in this style, that is,
using non-symbolic Python expressions.

```python
from math import pi

from classiq import CPHASE, H, QArray, QBit, qfunc


@qfunc
def my_gen_qft(qa: QArray[QBit]):
    for i in range(qa.len):
        H(qa[i])
        for j in range(qa.len - i - 1):
            phase = pi / (2 ** (j + 1))
            print(f"phase on qubit {i}: {phase}")
            CPHASE(phase, qa[i + j + 1], qa[i])
```

Note that calling `my_gen_qft` multiple times with qubit arrays of different lengths will
evaluate the body multiple times, and the printouts will reflect these separate calls.

### Example 2: Symbolic and Python Expressions with Control-flow Statements

The example below shows the use of symbolic and Python expressions in the context of classical _if_ statements.
Function `foo` takes 2 classical parameters - `p1` of Qmod type `CInt`, and `p2` of the corresponding Python-type `int`.
The expression `p1 > 3` is a symbolic expression, while `p2 > 3` is a Python-value expression.
Both can be used as the condition in a Qmod `if_` statement, as is shown in case _A_ and _B_.
However, only `p2 > 3` can be used in a Python `if` statement, as shown in case _C_. Case _D_ is therefore illegal.

```python
from classiq import CInt, QBit, X, if_, qfunc


@qfunc
def foo(p1: CInt, p2: int, q: QBit):
    if_(p1 > 3, lambda: X(q))  # case A - OK

    if_(p2 > 3, lambda: X(q))  # case B - OK

    if p2 > 3:  # case C - OK
        X(q)

    # if p1 > 3:  # case D - Error: 'p1 > 3' is a symbolic expression
    #     X(q)
```

### Example 3: Python-Type Parameter in a Lambda Function

The example below demonstrates the declaration and use of a function parameter with
a Python type. The function `my_operator` takes a function parameter `my_operand`,
which expects a Python `float` as parameter. In function `main`, `my_operator` is called
and passed a lambda expression in which the corresponding `ratio` parameter is used
in Python context expression, namely as the argument of `math.asin`. If `ration*2` were
a symbolic expression, it would be illegal to use it in this context.

```python
import math

from classiq import RX, H, QBit, QCallable, allocate, qfunc


@qfunc
def my_operator(my_operand: QCallable[float, QBit], q: QBit):
    H(q)
    my_operand(0.5, q)
    H(q)


@qfunc
def main():
    q = QBit()
    allocate(q)
    my_operator(lambda ratio, target: RX(math.asin(ratio * 2), target), q)
```

### Example 4: Numeric Attributes as Python-value Expressions

In the following model, function `compute_arith` checks that the inferred number of
fraction digits required to store the result of some quantum computation does not
exceed some threshold. In function `main`, `compute_arith` is called twice, where the
second time violates the requirement. Therefore, an exception is raised during model
construction.There is no Qmod equivalent to raising an exception, so using Python logic
is necessary in this case.

```python
from classiq import Output, QNum, allocate, qfunc


@qfunc
def compute_arith(x: QNum, y: QNum, z: Output[QNum]):
    z |= x * y
    if z.fraction_digits > 4:
        raise ValueError("Fraction digits exceed max")


@qfunc
def main():
    x = QNum(size=4, is_signed=False, fraction_digits=2)
    y = QNum(size=4, is_signed=False, fraction_digits=2)
    allocate(x)
    allocate(y)
    tmp = QNum()
    res = QNum()
    compute_arith(x, y, tmp)
    compute_arith(tmp, y, res)
```
