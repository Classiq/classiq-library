---
search:
    boost: 2.809
---

# Classical Variables

Classical variables store classical values such as integers, real numbers, Boolean values, and lists and structs
thereof (see [classical types](classical-types.md)).
In quantum circuits, classical values control rotation gates, like RX, and may be the results of quantum measurements.
Qmod provides additional abstractions involving classical values, including classical control flow constructs such as
`repeat`, `power`, and `if`.
Qmod also supports the use of classical values in the context of quantum
expressions.
Classical variables can be declared as [function parameters](functions.md) or
local variables.

## Local Classical Variables Syntax

=== "Python"

    Instead of explicitly declaring local Qmod classical variables, use local
    Python variables to store classical Qmod expressions.
    When run-time expressions, such as `measure`, are used, the corresponding
    Qmod variables are implicitly declared in the same scope.

=== "Native"

    Variable declaration:

    _classical-var_ **:** _classical-type_

    Variable assignment:

    _classical-var_ **=** _classical-expression_

<!-- prettier-ignore-start -->
!!! note
    Currently, only local classical variables of type `bool` are supported.
<!-- prettier-ignore-end -->

## Semantics

The Qmod compiler classifies classical variables according to their evaluation
time during the program's lifecycle:
_Compile-time_ variables are evaluated during compilation, _link-time_ variables
are evaluated after compilation but before execution, and _run-time_ variables
are evaluated during the program's execution.
The following table describes how the compiler classifies classical variables
that appear in each kind of Qmod expression.
For instance, if a classical variable is used as an array index, the compiler
classifies it as compile-time.

| Expression                   | Compile-time | Link-time | Run-time |
| ---------------------------- | ------------ | --------- | -------- |
| `allocate` size              | ✅           | ❌        | ❌       |
| `control` condition          | ✅           | ❌        | ❌       |
| `if` condition               | ✅           | ❌        | ✅       |
| `phase` classical expression | ✅           | ✅        | ❌       |
| `phase` quantum expression   | ✅           | ❌        | ❌       |
| `phase` theta                | ✅           | ✅        | ❌       |
| `power` count                | ✅           | ✅        | ❌       |
| `repeat` count               | ✅           | ❌        | ❌       |
| Array index                  | ✅           | ❌        | ❌       |
| Quantum arithmetics          | ✅           | ❌        | ❌       |
| Type attribute               | ✅           | ❌        | ❌       |

Function arguments are classified as either compile-time or link-time based on
the use of the parameter inside the function (run-time function parameters are
currently not supported).
While the compiler classifies the parameters of user-defined functions, the
classifications of atomic functions parameters are predefined.
For example, the `evolution_coefficient` parameter of `suzuki_trotter` is
link-time but the `reps` parameter is compile-time.
[Execution parameters](quantum-entry-point.md/#model-execution-parameters) must
be used as link-time variables.

Currently, local classical variables are classified as run-time variables, and
their use is restricted to _assignment_ and _if_ statements.

## Examples

The following examples demonstrates how the Qmod compiler classifies different
function parameters as either compile-time or link-time variables.

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    from classiq import *


    @qfunc
    def foo(qarr: QArray[QBit], index: CInt, angle: CReal):
        RX(angle * index, qarr[index])
    ```

=== "Native"

    ```
    qfunc foo(qarr: qbit[], index: int, angle: real) {
      RX(angle * index, qarr[index]);
    }
    ```

Since parameter `index` is used as an array subscript expression, it is
classified as a compile-time variable and will be evaluated and
eliminated from the program during compilation.
On the other hand, parameter `angle` is only used in a rotation expression, so
it is classified as a link-time parameter and will appear in the compiled
program.
Although `index` also appears in the rotation expression, this doesn't affect
its classification as a compile-time variable due to its other more restrictive
use.

See the [mid-circuit measurement](mid-circuit-measurement.md) documentation page
for code examples of run-time variables.
