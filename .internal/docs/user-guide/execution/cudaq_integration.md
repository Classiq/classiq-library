# CUDA-Q Integration

## Overview

The Classiq–CUDA-Q integration enables users to design quantum algorithms at a high level using Classiq, while leveraging CUDA-Q for execution, simulation, and hybrid quantum–classical workflows.
This integration is particularly well suited for variational algorithms, such as QAOA, where circuit synthesis, parameterized execution, and classical optimization must work together efficiently.

## Prerequisites

Before using the integration, ensure the following are installed in your python environment:

-   Python 3.9 or later
-   Classiq SDK
-   CUDA-Q

Note: The integration is only supported on Linux. The simplest way to handle installations is to use [Classiq Studio](https://platform.classiq.io/studio/) and `pip install classiq[cudaq]`.

## Integration Core Functions

The Integration is built around two Classiq SDK helper functions:

-   `qprog_to_cudaq_kernel()`  
    Converts a synthesized Classiq quantum program (`qprog`) into a CUDA-Q kernel that can be executed using CUDA-Q SDK.

-   `pauli_operator_to_cudaq_spin_op()`  
    Transforms Qmod's `SparsePauliOp` data structure to CUDA-Q's `SpinOperator`.

## Usage Example

Here is a minimal example:

-   Defining and synthesizing a parametric model using Classiq.
-   Converting to CUDA-Q kernel, assigning value to the parameter and sampling.

[comment]: DO_NOT_TEST

```python
# ! pip install classiq[cudaq]
from classiq import *
import cudaq
import math


@qfunc
def main(theta: CReal, q: Output[QBit]):
    allocate(q)
    RX(theta, q)


qprog = synthesize(main)
my_kernel = qprog_to_cudaq_kernel(qprog)

counts = cudaq.sample(my_kernel, math.pi / 3)
print(counts)

# example outputs -
# { 0:753 1:247 }
```
