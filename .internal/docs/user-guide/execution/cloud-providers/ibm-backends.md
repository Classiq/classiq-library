---
search:
    boost: 0.900
---

<!-- cspell:ignore pittsburg -->

# Execution on IBM Quantum Cloud

The Classiq executor supports execution on IBM simulators and hardware.

## Usage

### Execution on IBM Simulators

=== "SDK"

    [comment]: DO_NOT_TEST

    ```python
    from classiq import IBMBackendPreferences

    preferences = IBMBackendPreferences(backend_name="Name of requsted quantum simulator")
    ```

=== "IDE"

    ![Opening info tab](../../../resources/excution_ibm_simulation_login.png)

The supported simulators are fake hardware simulators.

### Execution on IBM Hardware

Execution on IBM hardware requires a valid IBM Quantum Cloud API access token, and access to the requested hardware with an IBM Quantum hub, group, and project name.
The access token is the API token that appears at the top of the [IBM Quantum Cloud page](https://quantum.cloud.ibm.com/), when you are logged in. You must create an account with IBM quantum if you do not have one already.

=== "SDK"

    [comment]: DO_NOT_TEST

    ```python
    from classiq import (
        IBMBackendPreferences,
    )

    preferences = IBMBackendPreferences(
        backend_name="Name of requsted quantum hardware",
        access_token="A Valid API access token to IBM Quantum",
        channel="IBM Cloud Channel",
        instance_crn="IBM Cloud Instance CRN",
    )
    ```

=== "IDE"

    ![Opening info tab](../../../resources/excution_ibm_hardware_login.png)

## Supported Backends

Included hardware:

-   "ibm_kingston"
-   "ibm_brisbane"
-   "ibm_marrakesh"
-   "ibm_torino"
-   "ibm_fez"
-   "ibm_pittsburg"
