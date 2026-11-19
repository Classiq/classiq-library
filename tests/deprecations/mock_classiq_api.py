"""Mock the classiq API inside a notebook's kernel, and record deprecation warnings.

`test_deprecations.py` injects a cell that imports this module and calls `install()`.
- Every classiq API call returns a fake but valid result (a quantum program, samples,
  a state vector, expectation values, ...), so the notebook runs to its end and reaches
  all of its API calls. Nothing is sent to the Classiq platform: an API call without
  a fake raises `MockedClassiqApiCall`.
- The fakes can't reproduce real results, so the notebook's `assert` statements are
  skipped, like with `python -O`.
- Every deprecation warning is recorded. `report()` returns them.
"""

import ast
import datetime
import math
import random
import warnings
from collections import Counter

from IPython import get_ipython

DEPRECATIONS = (
    DeprecationWarning,
    PendingDeprecationWarning,
    FutureWarning,
    SyntaxWarning,
)

# A fake sample returns every combination of the outputs' values, up to this many
MAX_STATES = 1024
# The size of an output whose size the notebook doesn't set (e.g. `Output[QNum]`)
UNKNOWN_SIZE = 4
DEFAULT_NUM_SHOTS = 2048


class MockedClassiqApiCall(Exception):
    """The deprecation test has no fake result for this classiq API call."""


def install() -> None:
    global _first_cell
    _first_cell = get_ipython().execution_count
    get_ipython().ast_transformers.append(_SkipAsserts())
    warnings.showwarning = _record_warning
    warnings.simplefilter("always")
    _mock_client()
    _install_fakes()


def report() -> list[dict]:
    return list(_warnings.values())


class _SkipAsserts(ast.NodeTransformer):
    def visit_Assert(self, node: ast.Assert) -> ast.Pass:
        return ast.copy_location(ast.Pass(), node)


#
# Recording warnings
#

_first_cell = 0  # the execution count of the cell that installs the mock
_warnings: dict[tuple, dict] = {}
_showwarning = warnings.showwarning


def _record_warning(message, category, filename, lineno, file=None, line=None):
    # IPython compiles each cell twice. The first compile, named "<>", warns before the cell starts.
    if issubclass(category, DEPRECATIONS) and filename != "<>":
        location = f"{filename.split('site-packages/')[-1]}:{lineno}"
        _warnings.setdefault(
            (category, str(message), location),
            {
                # The notebook's code cell: 1, 2, ... (the mock is installed right before them)
                "cell": get_ipython().execution_count - _first_cell,
                "category": category.__name__,
                "message": str(message),
                "location": location,
            },
        )
    _showwarning(message, category, filename, lineno, file, line)


#
# The client: no authentication, and no request leaves the kernel
#


def _mock_client() -> None:
    from classiq._internals import client
    from classiq._internals.authentication import password_manager, token_manager

    async def request(self, http_client, method, url, *args, **kwargs):
        raise MockedClassiqApiCall(f"{method.upper()} {url}")

    def sync_call_api(self, http_method, url, *args, **kwargs):
        raise MockedClassiqApiCall(f"{http_method.upper()} {url}")

    async def authenticate(self, overwrite):
        pass

    token_manager.TokenManager._make_password_manager = classmethod(
        lambda cls, config: password_manager.DummyPasswordManager()
    )
    client.Client.check_host = lambda self: None
    client.Client.authenticate = authenticate
    client.Client.request = request
    client.Client.sync_call_api = sync_call_api


#
# Fake results
#


def _install_fakes() -> None:
    from classiq._internals.api_wrapper import ApiWrapper

    fakes = {
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
    for name, fake in fakes.items():
        setattr(ApiWrapper, name, classmethod(_api_call(fake)))


def _api_call(fake):
    async def api_call(cls, *args, **kwargs):
        return fake(*args, **kwargs)

    return api_call


_random = random.Random(0)
_programs: dict = {}  # program id -> quantum program
_sessions: dict = {}  # session id -> quantum program
_jobs: dict = {}  # job id -> (quantum program, primitives input)


def _nothing(*_, **__) -> None:
    pass


def _synthesize(model, *_, **__):
    from classiq.interface.compression_utils import compress_pydantic
    from classiq.interface.generator.generated_circuit_data import (
        GeneratedCircuitData,
    )
    from classiq.interface.generator.hardware.hardware_data import (
        SynthesisHardwareData,
    )
    from classiq.interface.generator.model.model import ExecutionModel
    from classiq.interface.generator.quantum_program import QuantumProgram
    from classiq.interface.model.classical_parameter_declaration import (
        ClassicalParameterDeclaration,
    )

    output_types = _output_types(model)
    parameters = [
        parameter
        for parameter in model.main_func.positional_arg_declarations
        if isinstance(parameter, ClassicalParameterDeclaration)
    ]
    program = QuantumProgram(
        outputs={},
        hardware_data=SynthesisHardwareData(),
        data=GeneratedCircuitData(
            width=max(1, sum(output.size for output in output_types.values()))
        ),
        model=ExecutionModel(
            circuit_outputs=model.main_func.outputs_dict,
            circuit_output_types=output_types,
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
    from classiq.interface.generator.functions.port_declaration import (
        PortDeclarationDirection,
    )
    from classiq.interface.model.quantum_type import (
        quantum_type_to_register_quantum_type,
    )

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
    from classiq.interface.generator.functions.type_name import TypeName
    from classiq.interface.model.quantum_type import QuantumBitvector

    if isinstance(quantum_type, QuantumBitvector):
        _with_fields(quantum_type.element_type, structs)
    elif isinstance(quantum_type, TypeName) and quantum_type.name in structs:
        fields = structs[quantum_type.name].fields
        quantum_type.set_fields(
            {name: _with_fields(field, structs) for name, field in fields.items()}
        )
    return quantum_type


def _same_program(params, *_, **__):
    return params.quantum_program


def _export(params, *_, **__):
    from classiq.interface.executor.quantum_program_params import (
        TargetCode,
        TargetLanguage,
    )

    width = params.quantum_program.data.width
    if params.target_language == TargetLanguage.QASM2:
        code = f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{width}];\n'
    else:
        code = f'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[{width}] q;\n'
    return TargetCode(code=code)


def _circuit_metrics(program, *_, **__):
    from classiq.interface.ide.visual_model import CircuitMetrics

    width = program.data.width
    model = program.compiled_qmod
    gates = model.preferences.custom_hardware_settings.basis_gates if model else []
    return CircuitMetrics(
        width=width, depth=width, count_ops={str(gate): width for gate in gates}
    )


def _transpiled_circuit_metrics(program, *_, **__):
    from classiq.interface.generator.hardware.hardware_data import (
        SynthesisHardwareData,
    )
    from classiq.interface.ide.visual_model import ProgramData

    return ProgramData(
        hardware_data=SynthesisHardwareData(),
        circuit_metrics=_circuit_metrics(program),
    )


def _rb_analysis(params, *_, **__):
    from classiq.interface.analyzer.result import RbResults

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


def _execute(execution_input: dict, *_, **__):
    program = _programs[execution_input["program_id"]]
    return _new_job(program, program.execution_primitives_input)


def _create_session(program, *_, **__) -> str:
    session_id = f"session-{len(_sessions)}"
    _sessions[session_id] = program
    return session_id


def _create_openqasm_session(qasm, execution_preferences, *_, **__) -> str:
    from classiq.interface.generator.generated_circuit_data import (
        GeneratedCircuitData,
    )
    from classiq.interface.generator.hardware.hardware_data import (
        SynthesisHardwareData,
    )
    from classiq.interface.generator.model.model import ExecutionModel
    from classiq.interface.generator.quantum_program import QuantumProgram

    program = QuantumProgram(
        outputs={},
        hardware_data=SynthesisHardwareData(),
        data=GeneratedCircuitData(width=1),
        model=ExecutionModel(execution_preferences=execution_preferences),
    )
    return _create_session(program)


def _create_session_job(session_id: str, primitives_input, *_, **__):
    return _new_job(_sessions[session_id], primitives_input)


def _new_job(program, primitives_input):
    job_id = f"job-{len(_jobs)}"
    _jobs[job_id] = (program, primitives_input)
    return _job_details(job_id)


def _job_details(job_id, *_, **__):
    from classiq.interface.executor.execution_request import ExecutionJobDetails

    job_id = getattr(job_id, "job_id", job_id)
    program, primitives_input = _jobs[job_id]
    return ExecutionJobDetails(
        id=job_id,
        start_time=datetime.datetime.now(datetime.timezone.utc),
        end_time=datetime.datetime.now(datetime.timezone.utc),
        status="COMPLETED",
        program_id=program.program_id,
    )


def _job_result(job_id, *_, **__):
    from classiq.interface.executor.execution_result import (
        ExecuteGeneratedCircuitResults,
    )

    program, primitives_input = _jobs[job_id.job_id]
    if "vqe(" in program.model.classical_execution_code:
        return ExecuteGeneratedCircuitResults(results=_vqe_results(program))
    return ExecuteGeneratedCircuitResults(results=[_result(program, primitives_input)])


def _vqe_results(program) -> list:
    """The legacy flow: the program's classical code runs VQE, and saves its result and the hamiltonian."""
    import base64
    import io

    from classiq.interface.executor.execution_result import (
        TaggedUnstructured,
        TaggedVQESolverResult,
    )
    from classiq.interface.executor.vqe_result import (
        VQEIntermediateData,
        VQESolverResult,
    )
    from PIL import Image

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
    from classiq.interface.executor.execution_result import (
        TaggedEstimationResults,
        TaggedExecutionDetails,
        TaggedMinimizeResult,
        TaggedMultipleExecutionDetails,
    )
    from classiq.interface.executor.result import (
        EstimationResult,
        EstimationResults,
        MultipleExecutionDetails,
    )

    preferences = program.model.execution_preferences
    num_shots = (
        getattr(primitives_input, "num_shots", None)
        or preferences.num_shots
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


def _sample(program, num_shots: int):
    """Every possible value of the outputs, with similar counts."""
    from classiq.interface.executor.result import ExecutionDetails
    from classiq.interface.executor.result_parsing import parse_states

    output_types = program.model.circuit_output_types
    qubits, width = {}, 0
    for name, output_type in output_types.items():
        qubits[name] = tuple(range(width, width + output_type.size))
        width += output_type.size
    bitstrings = _bitstrings(qubits, max(width, 1))
    parsed_states = parse_states(bitstrings, qubits, output_types)

    backend = str(program.model.execution_preferences.backend_preferences.backend_name)
    if "statevector" in backend:
        amplitude = complex(1 / math.sqrt(len(bitstrings)))
        return ExecutionDetails(
            vendor_format_result={},
            state_vector={bitstring: amplitude for bitstring in bitstrings},
            parsed_state_vector_states=parsed_states,
            physical_qubits_map=qubits,
            output_qubits_map=qubits,
            output_type_map=output_types,
        )
    # Each value once (as far as the shots go), and the other shots at random
    counts = Counter(bitstrings[:num_shots])
    counts.update(_random.choices(bitstrings, k=num_shots - counts.total()))
    return ExecutionDetails(
        vendor_format_result={},
        counts=dict(counts),
        parsed_states=parsed_states,
        output_qubits_map=qubits,
        output_type_map=output_types,
        num_shots=num_shots,
    )


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
