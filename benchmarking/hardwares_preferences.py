HARDWARES = {
    "IBM Quantum": [
        "ibm_kingston",
        "ibm_boston",
        "ibm_marrakesh",
        "ibm_torino",
        "ibm_fez",
        "ibm_pittsburg",
    ],
    "IonQ": [
        "qpu.forte-1",
        "qpu.forte-enterprise-1",
        "qpu.forte-enterprise-2",
    ],
    "Classiq": [
        "simulator",
        "simulator_statevector",
        "simulator_density_matrix",
        "nvidia_simulator",
    ],
    "Amazon Braket": ["Ankaa-3", "Garnet", "Forte 1", "Emerald", "IBEX Q1"],
    "Azure Quantum": [
        "ionq.qpu.forte-enterprise-1",
        "ionq.qpu.aria-1",
        "ionq.qpu.forte-1",
    ],
    "C12": ["Callisto Emulator"],
}

from classiq import (
    IBMBackendPreferences,
    IonqBackendPreferences,
    ClassiqBackendPreferences,
    AwsBackendPreferences,
    AzureBackendPreferences,
    C12BackendPreferences,
)


def execution_preferences_wrapper(
    backend_service_provider: str,
    backend_name: str,
    *,
    emulate: bool = False,
    access_token: str | None = None,
    channel: str | None = None,
    instance_crn: str | None = None,
):
    if backend_service_provider == "IBM Quantum":
        assert access_token is not None, "access_token must be provided for IBM Quantum"
        assert channel is not None, "channel must be provided for IBM Quantum"
        assert instance_crn is not None, "instance_crn must be provided for IBM Quantum"

        return IBMBackendPreferences(
            backend_name=backend_name,
            access_token=access_token,
            channel=channel,
            instance_crn=instance_crn,
        )

    elif backend_service_provider == "IonQ":
        return IonqBackendPreferences(
            backend_name=backend_name,
            run_via_classiq=True,
        )

    elif backend_service_provider == "Amazon Braket":
        return AwsBackendPreferences(
            backend_name=backend_name, run_via_classiq=True, emulate=emulate
        )

    elif backend_service_provider == "Azure Quantum":
        return AzureBackendPreferences(
            backend_name=backend_name,
            run_via_classiq=True,
        )

    elif backend_service_provider == "Classiq":
        return ClassiqBackendPreferences(
            backend_name=backend_name,
        )

    elif backend_service_provider == "C12":
        return C12BackendPreferences(backend_name=backend_name)

    else:
        raise ValueError(
            f"Unknown backend_service_provider: {backend_service_provider}"
        )


def print_all_hardwares(hardwares: dict[str, list[str]]) -> None:
    for backend_service_provider, backend_names in hardwares.items():
        print(f"{backend_service_provider}: {', '.join(backend_names)}")
