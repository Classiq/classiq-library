---
search:
    boost: 2.610
---

# State Vector Filtering

Before measurement, a quantum circuit creates a state which can be described
as a vector of $2^n$ amplitudes, where $n$ is the number of qubits. Though this
state vector cannot be directly accessed on a quantum computer (as measurement
destroys the state), certain quantum simulators make this information available.
Classiq supports two simulators which return the full statevector, both under
the Classiq provider: `simulator_statevector` and `nvidia_simulator_statevector`.

Since the data size grows exponentially, large circuits cannot be simulated.
However, in certain applications such as those that use block encoding, not all
of the $2^n$ amplitudes are of interest. For example, some methods of
post-processing discard certain results wholesale, and thus the amplitudes
corresponding to those measured states are irrelevant.

In these instances, filtering out the amplitudes that are not of interest can
greatly save memory and network footprint. Use the method
`ExecutionSession.set_measured_state_filter`, to specify the execution output
values of interest.

## Example

```python
from classiq import *


@qfunc
def main(x: Output[QBit], y: Output[QNum], z: Output[QNum]) -> None:
    allocate(1, x)
    hadamard_transform(x)
    prepare_state(probabilities=[0.5, 0, 0.25, 0.25], bound=0.01, out=y)
    z |= y + 1


quantum_program = synthesize(main)

execution_preferences = ExecutionPreferences(
    backend_preferences=ClassiqBackendPreferences(
        backend_name=ClassiqNvidiaBackendNames.SIMULATOR_STATEVECTOR
    )
)
with ExecutionSession(
    quantum_program, execution_preferences=execution_preferences
) as session:
    session.set_measured_state_filter("x", lambda state: state == 1)
    session.set_measured_state_filter("y", lambda state: state == 2)
    results = session.sample()
```

Filtering ensures that `results` will contain only the amplitudes that correspond
to states where x is 1 and y is 2.

## Limitations

Currently, filtering is only available on Classiq's `simulator_statevector`
(`ClassiqSimulatorBackendNames.SIMULATOR_STATEVECTOR`) and
`nvidia_simulator_statevector` (`ClassiqNvidiaBackendNames.SIMULATOR_STATEVECTOR`).
Filtering is only available for quantum scalars (`QuantumBit`s and `QuantumNumeric`s).
Additionally, only a single value per variable is supported. For example,
`session.set_measured_state_filter("x", lambda x: x < 5)` is not allowed.
