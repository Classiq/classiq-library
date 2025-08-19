---
search:
    boost: 2.148
---

# Hardware-Aware Synthesis

Quantum computers differ from one other in many significant parameters, such as basis
gates, connectivity, and error rates. The device specifications determine the
possibility of executing the quantum program, and logically equivalent programs might
require different implementations to optimize the probability of success.

The Classiq platform allows you to provide information about the hardware you want to use
to run your quantum program. The synthesis engine takes the parameters of this hardware into
account. For example, the engine could choose the implementation of a function that
requires the least number of swaps, given the connectivity of the hardware.

If the hardware device's basis gate set contains the Clifford gates `X`, `Z`,
`H`, `T`, and `CX` but does not contain arbitrary-angle rotation gates such as `RX`,
the Classiq platform uses the Solovay-Kitaev algorithm to approximate
single-qubit gates when necessary. You can set the maximum iterations of the
Solovay-Kitaev algorithm in the preferences, thus tuning the algorithm target
accuracy. (Larger values usually result in better and longer approximations,
at the expense of longer running times.)

## Specifying a Backend

To synthesize your quantum program for a specific backend, specify the backend provider and the name of the backend.

The Classiq platform supports these backend providers:

-   Amazon Braket: All gate-based backends in [Amazon Braket](https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html) including all Rigetti devices, `Lucy`, and `IonQ Device`.
-   Azure Quantum: `ionq` and `quantinuum`.
-   IBM Quantum: Those listed on [IBM Quantum's official website](https://quantum-computing.ibm.com/services/resources?tab=systems). Note that you should specify the name of the backend without the `ibmq_` prefix.

=== "SDK"

    ```python
    from classiq import (
        qfunc,
        Output,
        Preferences,
        QBit,
        allocate,
        synthesize,
        set_preferences,
    )


    @qfunc
    def main(res: Output[QBit]) -> None:
        allocate(1, res)


    preferences = Preferences(
        backend_service_provider="IBM Quantum", backend_name="ibmq_kolkata"
    )
    synthesize(main, preferences=preferences)
    ```

## Customizing Hardware Settings

To synthesize the quantum program for hardware that is not available in
the Classiq platform, you can specify the custom settings of the hardware.
This includes the basis gate set and the connectivity map of the hardware.

Note that all hardware parameters are optional.

### Basis Gate Set

These are the allowed gates:

-   Single-qubit gates: `u1`, `u2`, `u`, `p`, `x`, `y`, `z`, `t`, `tdg`, `s`, `sdg`, `sx`, `sxdg`, `rx`, `ry`, `rz`, `r`, `id`, `h`
-   Basic two-qubit gates: `cx`, `cy`, `cz`
-   Extra two-qubit gates: `swap`, `rxx`, `ryy`, `rzz`, `rzx`, `ecr`, `crx`,
    `cry`, `crz`, `csx`, `cu1`, `cu`, `cp`, `ch`
-   Three-qubit gates: `ccx`, `cswap`

If you do not specify gates, the default set consists of all single-qubit gates and the basic
two-qubit gates.

### Connectivity Map

The connectivity map is given by a list of pairs of qubit IDs. Each pair in the list means
that a two-qubit gate (e.g., `cx`) can be performed on the pair of qubits. If the coupling map is symmetric,
then both qubits can act as control. If the coupling map is asymmetric, then the first
qubit can act only as control, and the second qubit can act only as target.
To determine whether the provided map is symmetric, set the ` is_symmetric_connectivity` argument.

If you do not specify the connectivity map, the engine assumes full connectivity.

### Example

The following example specifies a backend with 6 qubits in a 2-by-3 grid, where each
qubit connects to its immediate neighbors. The backend uses four basis gates:
`cx`, `rz`, `sx`, and `x`.

=== "SDK"

    ```python
    from classiq import (
        qfunc,
        CustomHardwareSettings,
        Output,
        Preferences,
        QBit,
        allocate,
        synthesize,
        set_preferences,
    )


    @qfunc
    def main(res: Output[QBit]) -> None:
        allocate(1, res)


    custom_hardware_settings = CustomHardwareSettings(
        basis_gates=["cx", "rz", "sx", "x"],
        connectivity_map=[(0, 1), (0, 3), (1, 4), (1, 2), (2, 5), (3, 4), (4, 5)],
        is_symmetric_connectivity=True,
    )
    preferences = Preferences(custom_hardware_settings=custom_hardware_settings)

    synthesize(main, preferences=preferences)
    ```
