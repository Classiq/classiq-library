---
search:
    boost: 3.191
---

# Quantum Entry Point

A quantum model in Qmod is compiled into a quantum program - a concrete executable
description. You can execute a quantum program any number of times on quantum hardware
or simulators, and specify execution preferences (such as number of shots).
When executing a parametric quantum program you must assign values to its parameters.
Both compilation and execution start from a user-defined quantum function called 'main',
which is the quantum program entry point. Function `main` specifies the inputs and outputs
of the quantum program, that is, its interface with the external classical execution logic.

## Model Outputs

Function `main` can declare quantum output arguments. Upon invocation, the quantum program
executes the specified number-of-shot times, and its outputs are measured each time. When
using the `sample` operation, each output variable is measured in the computational (z) basis.
Their names and values, along with the respective counts, are available in the returned result.
The values are interpreted according to their specified types (see [Quantum Types](quantum-types.md)).

Function `main` cannot declare quantum arguments other than using the `output`
modifier, since the classical execution logic cannot pass quantum states as arguments.

For example, consider the following model:

=== "Python"

    ```python
    from classiq import qfunc, Output, QBit, QNum, UNSIGNED, allocate, H, control, X


    @qfunc
    def main(a: Output[QBit], b: Output[QNum[2, UNSIGNED, 2]]) -> None:
        allocate(a)
        H(a)
        allocate(b)
        control(a, lambda: apply_to_all(lambda target: X(target), b))
    ```

=== "Native"

    ```
    qfunc main(output a: qbit, output b: qnum<2, UNSIGNED, 2>) {
      allocate(a);
      H(a);
      allocate(b);
      control (a) {
        apply_to_all(lambda(target) {
          X(target);
        }, b);
      }
    }
    ```

This model can be synthesized and executed in the SDK with the following code -

[comment]: DO_NOT_TEST

```python
qprog = synthesize(main)
job = execute(qprog)
result = job.result()[0]
print(result.value.parsed_counts)
```

The printout will show the counts of the measured values of `a` and `b` thus -

```
[{'a': 1.0, 'b': 0.75}: 503, {'a': 0.0, 'b': 0.0}: 497]
```

Similarly, the results of the execution job in the Classiq web application show the
values as tooltip on the histogram bars.

![parsed_results.png](resources/parsed_results.png)

## Model execution parameters

Function `main` can declare classical parameters of scalar types (integers and reals)
and arrays thereof with explicitly specified lengths. These are called execution parameters.
They are assigned by the external classical execution logic using arguments to
the execution operations `sample` and `estimate`. Execution parameters are left in their
symbolic form in the quantum program, so that passing different sets of parameter values
does not require re-synthesis of the model.

Execution parameters can figure in restricted contexts only as rotation angles in
gate-level functions and as the exponent value of the `power` operation. They cannot
be used in classical control flow statements (`repeat` and `if`) or in subscript/slice
expressions.

Below is a full SDK example of a very simple model with an execution parameter.
The quantum program is invoked in a loop using the method `sample` of `ExecutionSession`.

```Python
from math import pi
from classiq import qfunc, Output, QBit, CReal, RX, synthesize, allocate, ExecutionSession, ExecutionPreferences


@qfunc
def main(angle: CReal, res: Output[QBit]) -> None:
    allocate(res)
    RX(angle, res)


qprog = synthesize(main)

with ExecutionSession(qprog, ExecutionPreferences(num_shots=10000)) as es:
    for i in range(4):
        result = es.sample({"angle": i * pi / 4})
        print(result.parsed_counts)
```

Running this script will print, for example -

```
[{'res': 0.0}: 10000]
[{'res': 0.0}: 8560, {'res': 1.0}: 1440]
[{'res': 0.0}: 5019, {'res': 1.0}: 4981]
[{'res': 1.0}: 8514, {'res': 0.0}: 1486]
```
