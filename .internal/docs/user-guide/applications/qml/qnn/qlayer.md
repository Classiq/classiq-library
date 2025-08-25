---
search:
    boost: 2.944
---

# Quantum Layer

The Classiq engine exports the `QLayer` object, which inherits from `torch.nn.Module` (like most objects in the `torch.nn` namespace), and it acts like one.

The `QLayer` object is defined like this:

[comment]: DO_NOT_TEST

```python
class QLayer(nn.Module):
    def __init__(
        self,
        quantum_program: QuantumProgram,
        execute: ExecuteFunction,
        post_process: PostProcessFunction,
    ) -> None: ...
```

Or,

[comment]: DO_NOT_TEST

```python
class QLayer(nn.Module):
    def __init__(
        self,
        quantum_program: QuantumProgram,
        post_process: PostProcessFunction,
    ) -> None: ...
```

The first parameter, `quantum_program`, is the result of [synthesizing a quantum model](../../../../user-guide/synthesis/index.md).
Note that the parameters are assumed to follow the API stated in [qnn](qnn.md).

The second parameter is a callable which is responsible for executing the quantum program, usually with [`execute_qnn`](#execution).
It takes a `QuantumProgram` and `MultipleArguments` (a list of arguments sets to assign to the quantum program parameters) as inputs, and returns a `ResultsCollection`.
Note that this argument can be left out, as demonstrated in the second code block.
If it is not supplied, the layer will create an `ExecutionSession` and sample the quantum program automagically.

???+ note

    In order to properly close the `ExecutionSession`, if it was created, call the `teardown` method of `QLayer`.

The third parameter is a callable which is responsible for post-processing each execution result. It takes a `SavedResult` as input, process it and returns a `Tensor`.

An example of such callables:

[comment]: DO_NOT_TEST

```python
import torch

from classiq.applications.qnn.types import (
    MultipleArguments,
    SavedResult,
    ResultsCollection,
)

from classiq import execute_qnn
from classiq.synthesis import QuantumProgram


def execute(
    quantum_program: QuantumProgram, arguments: MultipleArguments
) -> ResultsCollection:
    return execute_qnn(quantum_program, arguments)


def post_process(result: SavedResult) -> torch.Tensor:
    # for example, post-processing can take some value out of `result.value.counts`, which is a `dict`
    value = _post_process_result(result)
    return torch.tensor(value)
```

## Execution

To facilitate the execution of your quantum layer, we supply the utility function `execute_qnn`.
It enables you to easily execute a batch of input arguments, and instruct whether you want the sample results or the estimation results according to a specific observable.

The inputs for `execute_qnn` are:

-   `quantum_program` of type `QuantumProgram`
-   `arguments` of type `MultipleArguments`
-   (optionally) `observable` of type `PauliOperator`.

The function returns a `ResultsCollection`, which is a list of `SavedResult` objects (see [Execution Results](../../../../user-guide/execution/index.md#results) for more information).

The type of each `SavedResult` depends on the `observable` input:

-   If no `observable` were given, the type would be `ExecutionDetails`.
-   Otherwise, the type would be `EstimationResult`.

???+ note

    If only one observable was given, `execute_qnn` will estimate the execution of all batched arguments with this observable.

    If more than one observable was given, their number should match the number of batched arguments, and each execution with a set of arguments will be estimated with the matching observable.

### Examples

[comment]: DO_NOT_TEST

```python
# Execute and return the sample results
def execute(
    quantum_program: QuantumProgram, arguments: MultipleArguments
) -> ResultsCollection:
    return execute_qnn(quantum_program, arguments)


# Execute and return the estimation results according to a specific observable
def execute(
    quantum_program: QuantumProgram, arguments: MultipleArguments
) -> ResultsCollection:
    return execute_qnn(
        quantum_program,
        arguments,
        observable=PauliOperator(
            pauli_list=[("II", 1 / 2), ("IZ", -1 / 2), ("ZI", -1 / 2)]
        ),
    )
```

## Behind the Scenes

Behind the scenes, the `QLayer` handles the following actions:

-   Processing of the PQC
-   Initializing and tracking of parameters
-   Passing the inputs and weights (as multi-dimensional tensors) to the execution function
-   Passing the results from the execution function to the post-processing function
-   Gradient calculation on the PQC
