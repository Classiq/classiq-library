---
search:
    boost: 3.130
---

# Execution Session

This section explains how to execute a quantum program using the `ExecutionSession` class.

The class enables executing a quantum program with parameters and operations, eliminating the need to resynthesize the model.

## Initializing

Initialize `ExecutionSession` with a quantum program; the output of the synthesis operation.
It is recommended to use `ExecutionSession` as a context manager in order to ensure resources are cleaned up. Alternatively, you can call the `close` method directly.
For example:

[comment]: DO_NOT_TEST

```python
from classiq import qfunc, synthesize, ExecutionSession


@qfunc
def main():
    pass


qprog = synthesize(main)

with ExecutionSession(qprog) as es:
    ...
```

## Operations

`ExecutionSession` supports two types of operations:

-   `sample`: Executes the quantum program with the specified parameters.

-   `estimate`: Computes the expectation value of the specified Hamiltonian using the quantum program.

When estimating using a simulator, the `ClassiqSimulatorBackendNames.SIMULATOR_STATEVECTOR` backend
calculates the expectation value directly from the computed state vector, as opposed to computing it from shots.

Each invocation mode can use one of these options:

-   `single`

-   `batch`: Samples/estimates the quantum program multiple times. The number of samples or estimations is determined by the length of the parameters list.

-   `submit`: When using submit as a prefix, the job object returns immediately, and the results should be polled. See `ExecutionJob` in the [sdk reference](../../sdk-reference/index.md).

For the `sample` method, these variations are available:

-   `es.sample(parameter: Optional[ExecutionParams])`

-   `es.batch_sample(parameter: List[ExecutionParams])`

-   `es.submit_sample(parameter: Optional[ExecutionParams])`

-   `es.submit_batch_sample(parameter: List[ExecutionParams])`

The `estimate` method has the same variations:

-   `es.estimate(hamiltonian: SparsePauliOp, parameters: Optional[ExecutionParams])`

-   `es.batch_estimate(hamiltonian, parameters: List[ExecutionParams])`

-   `es.submit_estimate(hamiltonia, parameters: Optional[ExecutionParams])`

-   `es.submit_batch_estimate(hamiltonian, parameters: List[ExecutionParams])`

## Examples

### sample()

A simple example of how to use `sample` and its variations:

[comment]: DO_NOT_TEST

```python
from classiq import (
    qfunc,
    Output,
    QBit,
    CReal,
    synthesize,
    RX,
    allocate,
    ExecutionSession,
)


@qfunc
def main(x: Output[QBit], t: CReal):
    allocate(1, x)
    RX(t, x)


qprog = synthesize(main)

with ExecutionSession(qprog) as execution_session:
    sample_result = execution_session.sample({"t": 0.5})
    print(sample_result.dataframe)
    batch_sample_result = execution_session.batch_sample([{"t": 0.5}, {"t": 0.6}])
    sample_job = execution_session.submit_sample({"t": 0.5})
    batch_sample_job = execution_session.submit_batch_sample([{"t": 0.5}, {"t": 0.6}])
```

### estimate()

An example that shows how to use `estimate` and its variations:

```python
from classiq import (
    qfunc,
    Output,
    QBit,
    CReal,
    synthesize,
    Pauli,
    RX,
    allocate,
    ExecutionSession,
)


@qfunc
def main(x: Output[QBit], t: CReal):
    allocate(1, x)
    RX(t, x)


qprog = synthesize(main)

with ExecutionSession(qprog) as execution_session:
    hamiltonian = Pauli.I(0) + 2 * Pauli.Z(0)

    estimate_result = execution_session.estimate(hamiltonian, {"t": 0.5})
    batch_estimate_result = execution_session.batch_estimate(
        hamiltonian, [{"t": 0.5}, {"t": 0.6}]
    )
    estimate_job = execution_session.submit_estimate(hamiltonian, {"t": 0.5})
    batch_estimate_job = execution_session.submit_batch_estimate(
        hamiltonian, [{"t": 0.5}, {"t": 0.6}]
    )
```

## Handling Long Jobs

When handling long-running jobs (jobs that are submitted to HW providers with potentially very long queues) it is advisable to retrieve and save the job ID for future reference:

[comment]: DO_NOT_TEST

```python
...
with ExecutionSession(qprog) as session:
    job = session.submit_sample()
    job_ID = job.id

restored_job = ExecutionJob.from_id(job_ID)
results = restored_job.get_sample_result()
```

Alternatively, for scenarios requiring result polling, e.g., iterative hybrid algorithms, consider the following partial code example.

This example runs a series of quantum estimation jobs, step by step.
It automatically submits each job, collects the results, checks they meet certain criteria (for example, does the cost exceed a certain threshold), and adjusts the parameters for the next job based on those results.

[comment]: DO_NOT_TEST

```python
from classiq import ExecutionSession, ExecutionJob


def get_data_from_file():
    # read data from file
    return data


def store_data_in_file(data):
    # save data in file
    return


with ExecutionSession(qprog) as session:
    iterations_data = get_data_from_file() or []

    for _ in range(max_iterations - len(iterations_data)):
        if iterations_data and "result" not in iterations_data[-1]:
            # continue the loop from the last iteration
            last_job = ExecutionJob.from_id(iterations_data[-1]["job_id"])
        else:
            last_job = session.submit_estimate(hamiltonian, params)
            iterations_data.append({"job_id": last_job.id, "params": params})
            store_data_in_file(iterations_data)

        result = last_job.get_estimate_result()
        iterations_data[-1]["result"] = result
        store_data_in_file(iterations_data)

        if result_is_good_enough(result):
            break

        params = compute_the_next_parameters(result)
```

## `@cfunc`

Note that Classiq does not support algorithms utilizing `@cfunc` (or `cscope` in Qmod native) for long job execution.
