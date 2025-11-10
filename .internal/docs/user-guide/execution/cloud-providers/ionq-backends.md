---
search:
    boost: 0.900
---

# Execution on IonQ Quantum Cloud

The Classiq executor supports execution on IonQ hardware and simulator.

## Usage

Execution on IonQ requires a valid IonQ API key.

=== "SDK"

    [comment]: DO_NOT_TEST

    ```python
    from classiq import IonqBackendPreferences

    preferences = IonqBackendPreferences(
        backend_name="Name of requested simulator or hardware",
        api_key="A Valid IonQ API key",
    )
    ```

=== "IDE"

    ![Opening info tab](../../../resources/excution_ionq_login.png)

### Supported Backends

Included hardware:

-   "qpu.aria-1"
-   "qpu.aria-2"
-   "qpu.forte-1"
-   "qpu.forte-enterprise-1"
-   "qpu.forte-enterprise-2"

Included simulators:

-   "simulator"
