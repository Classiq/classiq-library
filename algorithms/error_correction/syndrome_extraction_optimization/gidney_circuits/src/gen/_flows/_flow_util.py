# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Union, Any, Literal, Iterable

import stim

from gen._core._builder import MeasurementTracker, Builder, AtLayer
from gen._core._util import sorted_complex
from gen._flows._chunk import Chunk, ChunkLoop
from gen._flows._flow import PauliString, Flow


def magic_init_for_chunk(
    chunk: Chunk,
) -> Chunk:
    builder = Builder(
        q2i=chunk.q2i,
        circuit=stim.Circuit(),
        tracker=MeasurementTracker(),
    )
    index = 0
    flows = []
    for flow in chunk.flows:
        if flow.start:
            builder.measure_pauli_string(flow.start, key=AtLayer(index, "solo"))
            flows.append(
                Flow(
                    center=flow.center,
                    end=flow.start,
                    measurement_indices=[index],
                    obs_index=flow.obs_index,
                    additional_coords=flow.additional_coords,
                )
            )
            index += 1

    return Chunk(
        circuit=builder.circuit,
        q2i=builder.q2i,
        flows=flows,
        magic=True,
    )


def magic_measure_for_chunk(
    chunk: Chunk,
) -> Chunk:
    return magic_measure_for_flows(chunk.flows)


def magic_measure_for_flows(
    flows: list[Flow],
) -> Chunk:
    all_qubits = sorted_complex({q for flow in flows for q in (flow.end.qubits or [])})
    q2i = {q: i for i, q in enumerate(all_qubits)}
    builder = Builder(
        q2i=q2i,
        circuit=stim.Circuit(),
        tracker=MeasurementTracker(),
    )
    index = 0
    out_flows = []
    for flow in flows:
        if flow.end:
            key = AtLayer(index, "solo")
            builder.measure_pauli_string(flow.end, key=key)
            out_flows.append(
                Flow(
                    center=flow.center,
                    start=flow.end,
                    measurement_indices=[index],
                    obs_index=flow.obs_index,
                    additional_coords=flow.additional_coords,
                )
            )
            index += 1

    return Chunk(
        circuit=builder.circuit,
        q2i=builder.q2i,
        flows=out_flows,
        magic=True,
    )


def _append_circuit_with_reindexed_qubits_to_circuit(
    *,
    circuit: stim.Circuit,
    old_q2i: dict[complex, int],
    new_q2i: dict[complex, int],
    out: stim.Circuit,
) -> None:
    i2i = {i: new_q2i[q] for q, i in old_q2i.items()}

    for inst in circuit:
        if isinstance(inst, stim.CircuitRepeatBlock):
            block = stim.Circuit()
            _append_circuit_with_reindexed_qubits_to_circuit(
                circuit=inst.body_copy(),
                old_q2i=old_q2i,
                new_q2i=new_q2i,
                out=block,
            )
            out.append(
                stim.CircuitRepeatBlock(repeat_count=inst.repeat_count, body=block)
            )
        elif isinstance(inst, stim.CircuitInstruction):
            if inst.name == "QUBIT_COORDS":
                continue
            targets = []
            for t in inst.targets_copy():
                if t.is_qubit_target:
                    targets.append(i2i[t.value])
                elif t.is_x_target:
                    targets.append(stim.target_x(i2i[t.value]))
                elif t.is_y_target:
                    targets.append(stim.target_y(i2i[t.value]))
                elif t.is_z_target:
                    targets.append(stim.target_z(i2i[t.value]))
                elif t.is_combiner:
                    targets.append(t)
                elif t.is_measurement_record_target:
                    targets.append(t)
                else:
                    raise NotImplementedError(f"{inst=}")
            out.append(inst.name, targets, inst.gate_args_copy())
        else:
            raise NotImplementedError(f"{inst=}")


class _ChunkCompileState:
    def __init__(
        self,
        *,
        open_flows: dict[tuple[PauliString, Any], Union[Flow, Literal["discard"]]],
        measure_offset: int,
    ):
        self.open_flows = open_flows
        self.measure_offset = measure_offset


def _compile_chunk_into_circuit_many_repetitions(
    *,
    chunk_loop: ChunkLoop,
    state: _ChunkCompileState,
    include_detectors: bool,
    ignore_errors: bool,
    out_circuit: stim.Circuit,
    q2i: dict[complex, int],
) -> _ChunkCompileState:
    if chunk_loop.repetitions == 0:
        return state
    if chunk_loop.repetitions == 1:
        return _compile_chunk_into_circuit_sequence(
            chunks=chunk_loop.chunks,
            state=state,
            include_detectors=include_detectors,
            ignore_errors=ignore_errors,
            out_circuit=out_circuit,
            q2i=q2i,
        )
    assert chunk_loop.repetitions > 1

    no_reps_loop = chunk_loop.with_repetitions(1)
    circuits = []
    measure_offset_start_of_loop = state.measure_offset
    while len(circuits) < chunk_loop.repetitions:
        fully_in_loop = (
            len(circuits) > 0
            and min(
                [
                    m
                    for flow in state.open_flows.values()
                    if isinstance(flow, Flow)
                    for m in flow.measurement_indices
                ],
                default=measure_offset_start_of_loop,
            )
            >= measure_offset_start_of_loop
        )

        circuits.append(stim.Circuit())
        state = _compile_chunk_into_circuit(
            chunk=no_reps_loop,
            state=state,
            include_detectors=include_detectors,
            ignore_errors=ignore_errors,
            out_circuit=circuits[-1],
            q2i=q2i,
        )

        if fully_in_loop:
            # The circuit is guaranteed to repeat now. Don't do each iteration individually.
            finish_reps = chunk_loop.repetitions - len(circuits) + 1
            while len(circuits) > 1 and circuits[-1] == circuits[-2]:
                finish_reps += 1
                circuits.pop()
            circuits[-1] *= finish_reps
            break

    # Fuse iterations that happened to be equal.
    k = 0
    while k < len(circuits):
        k2 = k + 1
        while k2 < len(circuits) and circuits[k2] == circuits[k]:
            k2 += 1
        out_circuit += circuits[k] * (k2 - k)
        k = k2

    return state


def _compile_chunk_into_circuit_sequence(
    *,
    chunks: Iterable[Union[Chunk, ChunkLoop]],
    state: _ChunkCompileState,
    include_detectors: bool,
    ignore_errors: bool,
    out_circuit: stim.Circuit,
    q2i: dict[complex, int],
) -> _ChunkCompileState:
    for sub_chunk in chunks:
        state = _compile_chunk_into_circuit(
            chunk=sub_chunk,
            state=state,
            include_detectors=include_detectors,
            ignore_errors=ignore_errors,
            out_circuit=out_circuit,
            q2i=q2i,
        )
    return state


def _compile_chunk_into_circuit_atomic(
    *,
    chunk: Chunk,
    state: _ChunkCompileState,
    include_detectors: bool,
    ignore_errors: bool,
    out_circuit: stim.Circuit,
    q2i: dict[complex, int],
) -> _ChunkCompileState:
    prev_flows = dict(state.open_flows)
    next_flows: dict[tuple[PauliString, Any], Union[Flow, Literal["discard"]]] = {}
    dumped_flows: list[Flow] = []
    if include_detectors:
        for flow in chunk.flows:
            flow = Flow(
                center=flow.center,
                start=flow.start,
                end=flow.end,
                obs_index=flow.obs_index,
                measurement_indices=[
                    m + state.measure_offset for m in flow.measurement_indices
                ],
                postselect=flow.postselect,
                additional_coords=flow.additional_coords,
            )
            if flow.start:
                prev = prev_flows.pop((flow.start, flow.obs_index), None)
                if prev is None:
                    if ignore_errors:
                        continue
                    else:
                        raise ValueError(f"Missing prev {flow!r} have {prev_flows!r}")
                elif prev == "discard":
                    if flow.end:
                        next_flows[(flow.end, flow.obs_index)] = "discard"
                    continue
                flow = prev.concat(flow, 0)
            if flow.end:
                if flow.obs_index is not None and flow.measurement_indices:
                    dumped_flows.append(flow)
                    flow = Flow(
                        start=flow.start,
                        end=flow.end,
                        obs_index=flow.obs_index,
                        center=flow.center,
                    )
                next_flows[(flow.end, flow.obs_index)] = flow
            else:
                dumped_flows.append(flow)
        for discarded in chunk.discarded_inputs:
            prev_flows.pop((discarded, None), None)
        for discarded in chunk.discarded_outputs:
            assert (discarded, None) not in next_flows
            next_flows[(discarded, None)] = "discard"
        for flow, val in prev_flows.items():
            if val != "discard" and not ignore_errors:
                raise ValueError(
                    f"Some flows were left over (not matched) when moving into chunk: {list(prev_flows.values())!r}"
                )

    new_measure_offset = state.measure_offset + chunk.circuit.num_measurements
    _append_circuit_with_reindexed_qubits_to_circuit(
        circuit=chunk.circuit, out=out_circuit, old_q2i=chunk.q2i, new_q2i=q2i
    )
    if include_detectors:
        any_detectors = False
        for flow in dumped_flows:
            targets = []
            for m in flow.measurement_indices:
                targets.append(stim.target_rec(m - new_measure_offset))
            if flow.obs_index is None:
                coords = (flow.center.real, flow.center.imag, 0)
                if flow.additional_coords:
                    coords += flow.additional_coords
                if flow.postselect:
                    coords += (999,)
                out_circuit.append("DETECTOR", targets, coords)
                any_detectors = True
            else:
                out_circuit.append("OBSERVABLE_INCLUDE", targets, flow.obs_index)
        if any_detectors:
            out_circuit.append("SHIFT_COORDS", [], (0, 0, 1))
    if len(out_circuit) > 0 and out_circuit[-1].name != "TICK":
        out_circuit.append("TICK")

    return _ChunkCompileState(
        measure_offset=new_measure_offset,
        open_flows=next_flows,
    )


def _compile_chunk_into_circuit(
    *,
    chunk: Union[Chunk, ChunkLoop],
    state: _ChunkCompileState,
    include_detectors: bool,
    ignore_errors: bool,
    out_circuit: stim.Circuit,
    q2i: dict[complex, int],
) -> _ChunkCompileState:
    if isinstance(chunk, ChunkLoop):
        return _compile_chunk_into_circuit_many_repetitions(
            chunk_loop=chunk,
            state=state,
            include_detectors=include_detectors,
            ignore_errors=ignore_errors,
            out_circuit=out_circuit,
            q2i=q2i,
        )

    return _compile_chunk_into_circuit_atomic(
        chunk=chunk,
        state=state,
        include_detectors=include_detectors,
        ignore_errors=ignore_errors,
        out_circuit=out_circuit,
        q2i=q2i,
    )


def compile_chunks_into_circuit(
    chunks: list[Union[Chunk, ChunkLoop]],
    *,
    include_detectors: bool = True,
    ignore_errors: bool = False,
) -> stim.Circuit:
    all_qubits = set()

    def _process(sub_chunk: Union[Chunk, ChunkLoop]):
        nonlocal all_qubits
        if isinstance(sub_chunk, ChunkLoop):
            for sub_sub_chunk in sub_chunk.chunks:
                _process(sub_sub_chunk)
        elif isinstance(sub_chunk, Chunk):
            all_qubits |= sub_chunk.q2i.keys()
        else:
            raise NotImplementedError(f"{sub_chunk=}")

    for c in chunks:
        _process(c)

    q2i = {q: i for i, q in enumerate(sorted_complex(set(all_qubits)))}
    full_circuit = stim.Circuit()
    for q, i in q2i.items():
        full_circuit.append("QUBIT_COORDS", i, [q.real, q.imag])

    state = _ChunkCompileState(open_flows={}, measure_offset=0)
    for k, chunk in enumerate(chunks):
        state = _compile_chunk_into_circuit(
            chunk=chunk,
            state=state,
            include_detectors=include_detectors,
            ignore_errors=ignore_errors,
            out_circuit=full_circuit,
            q2i=q2i,
        )
    if include_detectors:
        if state.open_flows:
            if not ignore_errors:
                raise ValueError("Unterminated")
    return full_circuit
