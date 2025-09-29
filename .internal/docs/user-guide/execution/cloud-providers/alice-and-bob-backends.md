---
search:
    boost: 0.900
---

# Execution on Alice and Bob Quantum Cloud

The Classiq executor supports execution on Alice and Bob logical hardwares.

## Usage

Alice and Bob provide multiple logical targets that we can use.
Execution on Alice and Bob requires a valid API key. Additionally, Alice and Bob introduces several
customizable hardware parameters (Available through SDK only):

### average_nb_photons

Bit-flip probability decreases exponentially with this parameter, phase-flip probability increases linearly.

### kappa_1

The rate at which the cat qubit loses one photon, creating a bit-flip. Lower values mean lower error rates.

### kappa_2

The rate at which the cat qubit is stabilized using two-photon dissipation. Higher values mean lower error rates.

### distance

The number of times information is duplicated in the repetition code. Phase-flip probability decreases exponentially with this parameter, bit-flip probability increases linearly.

## Execution

=== "SDK"

    ### Setting up Backend Preferences

    [comment]: DO_NOT_TEST

    ```python
    from classiq import AliceBobBackendNames, AliceBobBackendPreferences

    backend_preferences = AliceBobBackendPreferences(
        backend_service_provider="Alice & Bob",
        api_key="<API KEY>",
        backend_name=AliceBobBackendNames.LOGICAL_TARGET,
        kappa_1=10.0,  # OR Remove it to keep default value
        kappa_2=1000,  # OR Remove it to keep default value
        distance=3,  # OR Remove it to keep default value
        average_nb_photons=7,  # OR Remove it to keep default value
    )
    ```
    ### Setting up execution preferences and adding number of shots

    [comment]: DO_NOT_TEST

    ```python
    from classiq import ExecutionPreferences

    execution_preferences = ExecutionPreferences(
        num_shots=1000,
        backend_preferences=backend_preferences,
    )
    ```

    ### Prepare for Hardware-aware synthesis

    [comment]: DO_NOT_TEST

    ```python
    from classiq import Preferences

    preferences = Preferences(
        backend_service_provider=ProviderVendor.ALICE_AND_BOB,
        backend_name=AliceBobBackendNames.LOGICAL_TARGET,
    )
    ```

    ### Execute

    At this point you should just create your model, set execution preferences and perform Hardware-aware synthesize then execute.

    [comment]: DO_NOT_TEST

    ```python
    quantum_program = synthesize(your_model, preferences=preferences)
    quantum_program = set_quantum_program_execution_preferences(
        quantum_program, execution_preferences
    )

    result = execute(quantum_program).result()
    ```

=== "IDE"

    Choose Model/Graphical Model tab in IDE, and go to **_"Synthesis Configuration"_** section

    ![HW aware synthesis](resources/hw_aware_synthesis_alice_and_bob.png)


    **_After synthesizing_**, you will be navigated to **_Execution_** page, or you can just navigate to it and choose **_Alice & Bob_** backend(s)

    ![Execute Alice & Bob](resources/execute_alicebob.png)

## Supported Backends

-   "LOGICAL_EARLY"
-   "LOGICAL_TARGET"
-   "LOGICAL_NOISELESS"
