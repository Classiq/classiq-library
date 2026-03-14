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
}

from classiq import (
    IBMBackendPreferences,
    IonqBackendPreferences,
    ClassiqBackendPreferences,
)


def execution_preferences_wrapper(
    backend_service_provider: str,
    backend_name: str,
    *,
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

    elif backend_service_provider == "Classiq":
        return ClassiqBackendPreferences(
            backend_name=backend_name,
        )

    else:
        raise ValueError(
            f"Unknown backend_service_provider: {backend_service_provider}"
        )
