---
search:
    boost: 0.900
---

<!-- cspell:ignore cuquantum, statevector -->

# Execution on Google Cloud Platform

Classiq offers execution on a GPU based simulator that is located in the Google Cloud Platform.

<!-- prettier-ignore-start -->
!!! tip
    This simulator doesn't require an account on GCP.
<!-- prettier-ignore-end -->

## Simulator Usage

Execution on this simulator requires specific license permissions.
Before first use, contact [Classiq support](mailto:support@classiq.io).

=== "SDK"

    ```python
    from classiq import GCPBackendPreferences

    preferences = GCPBackendPreferences(backend_name="cuquantum")
    ```

=== "IDE"

    ![Opening info tab](../../../resources/execution_google_nvidia_simulator.png)

## Supported Backends

Included simulators:

-   "cuquantum"
-   "cuquantum_statevector"
