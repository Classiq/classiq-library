"""Fake results for the classiq API calls, by `ApiWrapper` method.

Each fake returns a fake but valid result (a quantum program, samples, a state vector,
expectation values, ...), so the notebook runs to its end and reaches all of its API calls.
"""

import base64
import datetime
import io
import math
import random
from collections import Counter

from classiq.interface.analyzer.result import RbResults
from classiq.interface.compression_utils import compress_pydantic
from classiq.interface.executor.execution_request import ExecutionJobDetails
from classiq.interface.executor.execution_result import (
    ExecuteGeneratedCircuitResults,
    TaggedEstimationResults,
    TaggedExecutionDetails,
    TaggedMinimizeResult,
    TaggedMultipleExecutionDetails,
    TaggedUnstructured,
    TaggedVQESolverResult,
)
from classiq.interface.executor.quantum_program_params import TargetCode, TargetLanguage
from classiq.interface.executor.result import (
    EstimationResult,
    EstimationResults,
    ExecutionDetails,
    MultipleExecutionDetails,
)
from classiq.interface.executor.result_parsing import parse_states
from classiq.interface.executor.vqe_result import VQEIntermediateData, VQESolverResult
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.generator.generated_circuit_data import GeneratedCircuitData
from classiq.interface.generator.hardware.hardware_data import SynthesisHardwareData
from classiq.interface.generator.model.model import ExecutionModel
from classiq.interface.generator.quantum_program import QuantumProgram
from classiq.interface.ide.visual_model import CircuitMetrics, ProgramData
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)
from classiq.interface.model.quantum_type import (
    QuantumBitvector,
    quantum_type_to_register_quantum_type,
)
from PIL import Image

# A fake sample returns every combination of the outputs' values, up to this many
MAX_STATES = 2**14
# The size of an output whose size the notebook doesn't set (e.g. `Output[QNum]`)
UNKNOWN_SIZE = 4
DEFAULT_NUM_SHOTS = 2048


_random = random.Random(0)
_programs: dict = {}  # program id -> quantum program
_sessions: dict = {}  # session id -> quantum program
_jobs: dict = {}  # job id -> (quantum program, primitives input)


def _nothing(*_, **__) -> None:
    pass


def _program(model: ExecutionModel, **fields) -> QuantumProgram:
    width = sum(output.size for output in model.circuit_output_types.values())
    return QuantumProgram(
        outputs={},
        hardware_data=SynthesisHardwareData(),
        data=GeneratedCircuitData(width=max(1, width)),
        model=model,
        **fields,
    )


def _synthesize(model, *_, **__) -> QuantumProgram:
    parameters = [
        parameter
        for parameter in model.main_func.positional_arg_declarations
        if isinstance(parameter, ClassicalParameterDeclaration)
    ]
    program = _program(
        ExecutionModel(
            circuit_output_types=_output_types(model),
            circuit_outputs=model.main_func.outputs_dict,
            circuit_execution_params={p.name: p for p in parameters},
            execution_preferences=model.execution_preferences,
            classical_execution_code=model.classical_execution_code,
        ),
        compressed_compiled_qmod=compress_pydantic(model),
    )
    _programs[program.program_id] = program
    return program


def _output_types(model) -> dict:
    """The types of main's outputs, with each struct's fields and a size for each."""
    structs = {struct.name: struct for struct in model.qstructs}
    output_types = {}
    for port in model.main_func.port_declarations:
        if port.direction == PortDeclarationDirection.Input:
            continue
        quantum_type = _with_fields(port.quantum_type, structs)
        size = (
            quantum_type.size_in_bits if quantum_type.has_size_in_bits else UNKNOWN_SIZE
        )
        output_types[port.name] = quantum_type_to_register_quantum_type(
            quantum_type, size
        )
    return output_types


def _with_fields(quantum_type, structs: dict):
    if isinstance(quantum_type, QuantumBitvector):
        _with_fields(quantum_type.element_type, structs)
    elif isinstance(quantum_type, TypeName) and quantum_type.name in structs:
        fields = structs[quantum_type.name].fields
        quantum_type.set_fields(
            {name: _with_fields(field, structs) for name, field in fields.items()}
        )
    return quantum_type


def _same_program(params, *_, **__) -> QuantumProgram:
    return params.quantum_program


def _export(params, *_, **__) -> TargetCode:
    width = params.quantum_program.data.width
    if params.target_language == TargetLanguage.QASM2:
        code = f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{width}];\n'
    else:
        code = f'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[{width}] q;\n'
    return TargetCode(code=code)


def _circuit_metrics(program, *_, **__) -> CircuitMetrics:
    width = program.data.width
    model = program.compiled_qmod
    gates = model.preferences.custom_hardware_settings.basis_gates if model else []
    return CircuitMetrics(
        width=width, depth=width, count_ops={str(gate): width for gate in gates}
    )


def _transpiled_circuit_metrics(program, *_, **__) -> ProgramData:
    return ProgramData(
        hardware_data=SynthesisHardwareData(),
        circuit_metrics=_circuit_metrics(program),
    )


def _rb_analysis(params, *_, **__) -> RbResults:
    return RbResults(
        mean_fidelity=0.99,
        average_error=0.01,
        A=0.5,
        B=0.5,
        success_probability=[0.9] * len(params.num_clifford),
        parameters_error=(0.01, 0.01, 0.01),
    )


def _convert(program, *_, **__) -> dict:
    _programs[program.program_id] = program
    return {"program_id": program.program_id}


def _execute(execution_input: dict, *_, **__) -> ExecutionJobDetails:
    program = _programs[execution_input["program_id"]]
    return _new_job(program, program.execution_primitives_input)


def _create_session(program, *_, **__) -> str:
    session_id = f"session-{len(_sessions)}"
    _sessions[session_id] = program
    return session_id


def _create_openqasm_session(qasm, execution_preferences, *_, **__) -> str:
    program = _program(ExecutionModel(execution_preferences=execution_preferences))
    return _create_session(program)


def _create_session_job(session_id, primitives_input, *_, **__) -> ExecutionJobDetails:
    return _new_job(_sessions[session_id], primitives_input)


def _new_job(program, primitives_input) -> ExecutionJobDetails:
    job_id = f"job-{len(_jobs)}"
    _jobs[job_id] = (program, primitives_input)
    return _job_details(job_id)


def _job_details(job_id, *_, **__) -> ExecutionJobDetails:
    job_id = getattr(job_id, "job_id", job_id)
    program, primitives_input = _jobs[job_id]
    now = datetime.datetime.now(datetime.timezone.utc)
    return ExecutionJobDetails(
        id=job_id,
        start_time=now,
        end_time=now,
        status="COMPLETED",
        program_id=program.program_id,
    )


def _job_result(job_id, *_, **__) -> ExecuteGeneratedCircuitResults:
    program, primitives_input = _jobs[job_id.job_id]
    if "vqe(" in program.model.classical_execution_code:
        return ExecuteGeneratedCircuitResults(results=_vqe_results(program))
    return ExecuteGeneratedCircuitResults(results=[_result(program, primitives_input)])


def _vqe_results(program) -> list:
    """The legacy flow: the program's classical code runs VQE, and saves its result and the hamiltonian."""
    sample = _sample(program, DEFAULT_NUM_SHOTS)
    probabilities = {
        bitstring: count / sample.num_shots
        for bitstring, count in sample.counts.items()
    }
    convergence_graph = io.BytesIO()
    Image.new("RGB", (1, 1)).save(convergence_graph, format="PNG")
    vqe_result = VQESolverResult(
        energy=0.5,
        time=1.0,
        eigenstate={bitstring: math.sqrt(p) for bitstring, p in probabilities.items()},
        reduced_probabilities=probabilities,
        optimized_circuit_sample_results=sample,
        intermediate_results=[
            VQEIntermediateData(
                utc_time=datetime.datetime.now(datetime.timezone.utc),
                iteration_number=1,
                parameters=[0.0],
                mean_all_solutions=0.5,
                solutions=[],
                standard_deviation=0.1,
            )
        ],
        optimal_parameters={"param_0": 0.0},
        convergence_graph_str=base64.b64encode(convergence_graph.getvalue()).decode(),
        num_shots=sample.num_shots,
    )
    return [
        TaggedVQESolverResult(
            value_type="VQESolverResult", name="vqe_result", value=vqe_result
        ),
        TaggedUnstructured(value_type="Unstructured", name="hamiltonian", value=[]),
    ]


def _result(program, primitives_input):
    num_shots = (
        getattr(primitives_input, "num_shots", None)
        or program.model.execution_preferences.num_shots
        or DEFAULT_NUM_SHOTS
    )
    if primitives_input is not None and primitives_input.estimate is not None:
        estimate = primitives_input.estimate
        observables = estimate.observables
        count = (len(observables) if isinstance(observables, list) else 1) * max(
            1, len(estimate.parameters)
        )
        results = [
            EstimationResult(value=_random.uniform(0.25, 0.75), metadata={})
            for _ in range(count)
        ]
        return TaggedEstimationResults(
            value_type="EstimationResults",
            name="result",
            value=EstimationResults(results=results),
        )
    if primitives_input is not None and primitives_input.minimize is not None:
        minimize = primitives_input.minimize
        parameters = list(minimize.initial_params.values())
        iterations = [
            {"expectation_value": 1 / iteration, "parameters": parameters}
            for iteration in range(1, max(1, minimize.max_iteration) + 1)
        ]
        return TaggedMinimizeResult(
            value_type="MinimizeResult", name="result", value=iterations
        )
    samples = getattr(primitives_input, "sample", None) or [{}]
    if len(samples) == 1:
        return TaggedExecutionDetails(
            value_type="ExecutionDetails",
            name="result",
            value=_sample(program, num_shots),
        )
    return TaggedMultipleExecutionDetails(
        value_type="MultipleExecutionDetails",
        name="result",
        value=MultipleExecutionDetails(
            details=[_sample(program, num_shots) for _ in samples]
        ),
    )


def _sample(program, num_shots: int) -> ExecutionDetails:
    """Every possible value of the outputs, with similar counts."""
    output_types = program.model.circuit_output_types
    qubits, width = {}, 0
    for name, output_type in output_types.items():
        qubits[name] = tuple(range(width, width + output_type.size))
        width += output_type.size
    width = max(width, 1)
    bitstrings = _bitstrings(qubits, width)
    # Keep the states that pass the filters, e.g. of `calculate_state_vector(filters=...)`
    for name, legal_values in program.model.register_filter_bitstrings.items():
        start, end = width - qubits[name][-1] - 1, width - qubits[name][0]
        bitstrings = [b for b in bitstrings if b[start:end] in legal_values]
    parsed_states = parse_states(bitstrings, qubits, output_types)

    # Each value once (if the shots suffice), and the other shots at random
    counts = Counter(bitstrings if num_shots >= len(bitstrings) else [])
    counts.update(_random.choices(bitstrings, k=num_shots - counts.total()))
    details = ExecutionDetails(
        vendor_format_result={},
        counts=dict(counts),
        parsed_states=parsed_states,
        output_qubits_map=qubits,
        output_type_map=output_types,
        num_shots=num_shots,
    )
    backend = str(program.model.execution_preferences.backend_preferences.backend_name)
    if "statevector" in backend:
        amplitude = complex(1 / math.sqrt(len(bitstrings)))
        details.state_vector = {bitstring: amplitude for bitstring in bitstrings}
        details.parsed_state_vector_states = parsed_states
        details.physical_qubits_map = qubits
    return details


def _bitstrings(qubits: dict, width: int) -> list[str]:
    """Every combination of the outputs' values.
    If there are too many, every value of each output (up to MAX_STATES), while the others are 0.
    """
    if 2**width <= MAX_STATES:
        values = range(2**width)
    else:
        values = sorted(
            {
                value << indices[0]
                for indices in qubits.values()
                if indices
                for value in range(min(2 ** len(indices), MAX_STATES))
            }
        )
    return [format(value, f"0{width}b") for value in values]


FAKES = {
    "call_generation_task": _synthesize,
    "call_transpilation_task": _same_program,
    "call_assign_parameters_task": _same_program,
    "call_export_task": _export,
    "call_circuit_metrics_task": _circuit_metrics,
    "call_transpiled_circuit_metrics_task": _transpiled_circuit_metrics,
    "call_convert_quantum_program": _convert,
    "call_execute_execution_input": _execute,
    "call_create_execution_session": _create_session,
    "call_create_openqasm_execution_session": _create_openqasm_session,
    "call_close_execution_session": _nothing,
    "call_create_session_job": _create_session_job,
    "call_get_execution_job_details": _job_details,
    "call_get_execution_job_result": _job_result,
    "call_cancel_execution_job": _nothing,
    "call_get_all_hardware_devices": lambda *_, **__: [],
    "call_rb_analysis_task": _rb_analysis,
}
