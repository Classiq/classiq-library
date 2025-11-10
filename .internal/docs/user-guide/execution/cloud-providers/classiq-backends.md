---
search:
    boost: 0.900
---

<!-- cspell:ignore statevector -->

# Execution on Classiq simulators

Classiq offers execution on simulators that are located at the Classiq backend.

<!-- prettier-ignore-start -->
!!! tip
    These simulators don't require an account on a different cloud, and are usually
    fast to execute.
<!-- prettier-ignore-end -->

## Simulator Usage

=== "SDK"

    [comment]: DO_NOT_TEST

    ```python
    from classiq import ClassiqBackendPreferences

    preferences = ClassiqBackendPreferences(
        backend_name="Name of requested quantum simulator"
    )
    ```

=== "IDE"

    ![Opening info tab](../../../resources/execution_classiq_simulators.png)

Classiq supports following simulators:

1. `simulator`: A general-purpose quantum simulator capable of handling circuits with up to 25 qubits.

2. `simulator_statevector`: Returns he full state vector, including phase information of the output state produced by the quantum circuit. Due to the exponential growth of the state vector, this simulator is suitable only for circuits with up to 18 qubits.

3. `simulator_density_matrix`: Uses density matrices to simulate open quantum circuits and supports simulations for circuits containing up to 25 qubits.

4. `simulator_matrix_product_state`: Efficiently simulates quantum circuits of up to 25 qubits, especially suited for circuits exhibiting low entanglement.

You can access these simulators through `ClassiqSimulatorBackendNames`.

## Nvidia Simulator Usage

Execution on Nvidia simulators requires specific license permissions.
Before first use, contact [Classiq support](mailto:support@classiq.io).

Classiq supports two types of Nvidia simulators, with the same inputs and outputs but different underlying infrastructure, capable of simulating circuits with up to 29 qubits:

1. The backends `ClassiqNvidiaBackendNames.SIMULATOR` and `ClassiqNvidiaBackendNames.SIMULATOR_STATEVECTOR` are better suited when multiple circuits need to be executed in sequence.
2. The backends `ClassiqNvidiaBackendNames.BRAKET_NVIDIA_SIMULATOR` and `ClassiqNvidiaBackendNames.BRAKET_NVIDIA_SIMULATOR_STATEVECTOR` are executed using Amazon Braket's infrastructure, and provide faster execution for single circuits. Credentials for AWS are not needed.

Both `ClassiqNvidiaBackendNames.SIMULATOR_STATEVECTOR` and `ClassiqNvidiaBackendNames.braket_nvidia_simulator_statevector` return the state vector at the end of the circuit's execution (analogous to the
above `simulator_statevector`).

=== "SDK"

    ```python
    from classiq import ClassiqBackendPreferences, ClassiqNvidiaBackendNames

    preferences = ClassiqBackendPreferences(
        backend_name=ClassiqNvidiaBackendNames.SIMULATOR
    )
    ```

=== "IDE"

    ![Opening info tab](../../../resources/execution_nvidia_simulator.png)

<!-- prettier-ignore-start -->
!!! note
    The number of execution requests to the NVIDIA simulator may be limited.
    If you encounter any problem, contact
    [Classiq support](mailto:support@classiq.io).
<!-- prettier-ignore-end -->

## Supported Backends

Included simulators:

-   "nvidia_simulator_statevector"
-   "simulator"
-   "simulator_statevector"
-   "simulator_density_matrix"
-   "nvidia_simulator"
-   "braket_nvidia_simulator"
-   "simulator_matrix_product_state"
-   "braket_nvidia_simulator_statevector"
