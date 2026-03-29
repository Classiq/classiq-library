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

import pathlib
from typing import Iterable, Callable, Union

import sinter
import stim

from gen._core._patch import Patch
from gen._core._tile import Tile
from gen._flows._flow import Flow, PauliString
from gen._util import stim_circuit_with_transformed_coords, write_file


class Chunk:
    """A circuit chunk with accompanying stabilizer flow assertions."""

    def __init__(
        self,
        circuit: stim.Circuit,
        q2i: dict[complex, int],
        flows: Iterable[Flow],
        magic: bool = False,
        discarded_inputs: Iterable[PauliString] = (),
        discarded_outputs: Iterable[PauliString] = (),
    ):
        """
        Args:
            circuit: The circuit implementing the chunk's functionality.
            q2i: The coordinate-to-index mapping used by the circuit.
            flows: A series of stabilizer flows that the circuit implements.
            discarded_inputs: Explicitly rejected in flows. For example, a data
                measurement chunk might reject flows for stabilizers from the
                anticommuting basis. If they are not rejected, then compilation
                will fail when attempting to combine this chunk with a preceding
                chunk that has those stabilizers from the anticommuting basis
                flowing out.
            discarded_outputs: Explicitly rejected out flows. For example, an
                initialization chunk might reject flows for stabilizers from the
                anticommuting basis. If they are not rejected, then compilation
                will fail when attempting to combine this chunk with a following
                chunk that has those stabilizers from the anticommuting basis
                flowing in.
            magic: Whether or not the circuit is relying on magical noiseless
                operations like noiselessly measuring entire observables. This
                is useful when testing and debugging and initially building
                circuits, but prevents them from being run on hardware.
        """
        self.q2i = q2i
        self.magic = magic
        self.circuit = circuit
        self.flows = tuple(flows)
        self.discarded_inputs = discarded_inputs
        self.discarded_outputs = discarded_outputs

    def __eq__(self, other):
        if not isinstance(other, Chunk):
            return NotImplemented
        return (
            self.q2i == other.q2i
            and self.magic == other.magic
            and self.circuit == other.circuit
            and self.flows == other.flows
            and self.discarded_inputs == other.discarded_inputs
            and self.discarded_outputs == other.discarded_outputs
        )

    def write_viewer(
        self, path: str | pathlib.Path, *, patch: Patch | None = None
    ) -> None:
        from gen import stim_circuit_html_viewer

        if patch is None:
            patch = self.start_patch()
            if len(patch.tiles) == 0:
                patch = self.end_patch()
        write_file(path, stim_circuit_html_viewer(self.circuit, patch=patch))

    def with_flows_postselected(
        self, flow_predicate: Callable[[Flow], bool]
    ) -> "Chunk":
        return Chunk(
            circuit=self.circuit,
            q2i=self.q2i,
            magic=self.magic,
            flows=[
                flow.postselected() if flow_predicate(flow) else flow
                for flow in self.flows
            ],
            discarded_inputs=self.discarded_inputs,
            discarded_outputs=self.discarded_outputs,
        )

    def __mul__(self, other: int) -> "ChunkLoop":
        return ChunkLoop([self], repetitions=other)

    def with_repetitions(self, repetitions: int) -> "ChunkLoop":
        return ChunkLoop([self], repetitions=repetitions)

    def verify(self):
        """Checks that this chunk's circuit actually implements its flows."""
        for key, group in sinter.group_by(
            self.flows, key=lambda flow: (flow.start, flow.obs_index)
        ).items():
            if key[0] and len(group) > 1:
                raise ValueError(f"Multiple flows with same non-empty end: {group}")
        for key, group in sinter.group_by(
            self.flows, key=lambda flow: (flow.end, flow.obs_index)
        ).items():
            if key[0] and len(group) > 1:
                raise ValueError(f"Multiple flows with same non-empty end: {group}")

        from gen._flows._flow_verifier import FlowStabilizerVerifier

        FlowStabilizerVerifier.verify(self)

    def inverted(self) -> "Chunk":
        """Checks that this chunk's circuit actually implements its flows."""
        from gen._flows._flow_verifier import FlowStabilizerVerifier

        return FlowStabilizerVerifier.invert(self)

    def with_xz_flipped(self) -> "Chunk":
        return Chunk(
            q2i=self.q2i,
            magic=self.magic,
            circuit=circuit_with_xz_flipped(self.circuit),
            flows=[flow.with_xz_flipped() for flow in self.flows],
            discarded_inputs=[p.with_xz_flipped() for p in self.discarded_inputs],
            discarded_outputs=[p.with_xz_flipped() for p in self.discarded_outputs],
        )

    def with_transformed_coords(
        self, transform: Callable[[complex], complex]
    ) -> "Chunk":
        return Chunk(
            q2i={transform(q): i for q, i in self.q2i.items()},
            magic=self.magic,
            circuit=stim_circuit_with_transformed_coords(self.circuit, transform),
            flows=[flow.with_transformed_coords(transform) for flow in self.flows],
            discarded_inputs=[
                p.with_transformed_coords(transform) for p in self.discarded_inputs
            ],
            discarded_outputs=[
                p.with_transformed_coords(transform) for p in self.discarded_outputs
            ],
        )

    def magic_init_chunk(self) -> "Chunk":
        """Returns a chunk that initializes the stabilizers needed by this one.

        The stabilizers are initialized using direct measurement by MPP, with
        no care for connectivity or physical limitations of hardware.
        """
        from gen._flows._flow_util import magic_init_for_chunk

        return magic_init_for_chunk(self)

    def magic_end_chunk(self) -> "Chunk":
        """Returns a chunk that terminates the stabilizers produced by this one.

        The stabilizers are initialized using direct measurement by MPP, with
        no care for connectivity or physical limitations of hardware.
        """
        from gen._flows._flow_util import magic_measure_for_chunk

        return magic_measure_for_chunk(self)

    def _boundary_patch(self, end: bool) -> Patch:
        tiles = []
        for flow in self.flows:
            r = flow.end if end else flow.start
            if r.qubits and flow.obs_index is None:
                tiles.append(
                    Tile(
                        ordered_data_qubits=r.qubits.keys(),
                        bases="".join(r.qubits.values()),
                        measurement_qubit=list(r.qubits.keys())[0],
                    )
                )
        return Patch(tiles)

    def start_patch(self) -> Patch:
        return self._boundary_patch(False)

    def flattened(self) -> list["Chunk"]:
        return [self]

    def end_patch(self) -> Patch:
        return self._boundary_patch(True)

    def tick_count(self) -> int:
        return self.circuit.num_ticks + 1


class ChunkLoop:
    def __init__(self, chunks: Iterable[Union[Chunk, "ChunkLoop"]], repetitions: int):
        self.chunks = tuple(chunks)
        self.repetitions = repetitions

    @property
    def magic(self) -> bool:
        return any(c.magic for c in self.chunks)

    def verify(self):
        for c in self.chunks:
            c.verify()
        for k in range(len(self.chunks)):
            before: Chunk = self.chunks[k - 1]
            after: Chunk = self.chunks[k]
            after_in = {}
            before_out = {}
            for flow in before.flows:
                if flow.end:
                    before_out[flow.end] = flow.obs_index
            for flow in after.flows:
                if flow.start:
                    after_in[flow.start] = flow.obs_index
            for ps in before.discarded_outputs:
                after_in.pop(ps)
            for ps in after.discarded_inputs:
                before_out.pop(ps)
            if after_in != before_out:
                raise ValueError("Flows don't match between chunks.")

    def __mul__(self, other: int) -> "ChunkLoop":
        return self.with_repetitions(other * self.repetitions)

    def with_repetitions(self, new_repetitions: int) -> "ChunkLoop":
        return ChunkLoop(chunks=self.chunks, repetitions=new_repetitions)

    def magic_init_chunk(self) -> "Chunk":
        return self.chunks[0].magic_init_chunk()

    def magic_end_chunk(self) -> "Chunk":
        return self.chunks[-1].magic_end_chunk()

    def start_patch(self) -> Patch:
        return self.chunks[0].start_patch()

    def end_patch(self) -> Patch:
        return self.chunks[-1].end_patch()

    def tick_count(self) -> int:
        return sum(e.tick_count() for e in self.chunks) * self.repetitions

    def flattened(self) -> list["Chunk"]:
        return [e for c in self.chunks for e in c.flattened()]


XZ_FLIPPED = {
    "I": "I",
    "X": "Z",
    "Y": "Y",
    "Z": "X",
    "C_XYZ": "C_ZYX",
    "C_ZYX": "C_XYZ",
    "H": "H",
    "H_XY": "H_YZ",
    "H_XZ": "H_XZ",
    "H_YZ": "H_XY",
    "S": "SQRT_X",
    "SQRT_X": "S",
    "SQRT_X_DAG": "S_DAG",
    "SQRT_Y": "SQRT_Y",
    "SQRT_Y_DAG": "SQRT_Y_DAG",
    "S_DAG": "SQRT_X_DAG",
    "CX": "XCZ",
    "CY": "XCY",
    "CZ": "XCX",
    "ISWAP": None,
    "ISWAP_DAG": None,
    "SQRT_XX": "SQRT_ZZ",
    "SQRT_XX_DAG": "SQRT_ZZ_DAG",
    "SQRT_YY": "SQRT_YY",
    "SQRT_YY_DAG": "SQRT_YY_DAG",
    "SQRT_ZZ": "SQRT_XX",
    "SQRT_ZZ_DAG": "SQRT_XX_DAG",
    "SWAP": "SWAP",
    "XCX": "CZ",
    "XCY": "CY",
    "XCZ": "CX",
    "YCX": "YCZ",
    "YCY": "YCY",
    "YCZ": "YCX",
    "DEPOLARIZE1": "DEPOLARIZE1",
    "DEPOLARIZE2": "DEPOLARIZE2",
    "E": None,
    "ELSE_CORRELATED_ERROR": None,
    "PAULI_CHANNEL_1": None,
    "PAULI_CHANNEL_2": None,
    "X_ERROR": "Z_ERROR",
    "Y_ERROR": "Y_ERROR",
    "Z_ERROR": "X_ERROR",
    "M": "MX",
    "MPP": None,
    "MR": "MRX",
    "MRX": "MRZ",
    "MRY": "MRY",
    "MX": "M",
    "MY": "MY",
    "R": "RX",
    "RX": "R",
    "RY": "RY",
    "DETECTOR": "DETECTOR",
    "OBSERVABLE_INCLUDE": "OBSERVABLE_INCLUDE",
    "QUBIT_COORDS": "QUBIT_COORDS",
    "SHIFT_COORDS": "SHIFT_COORDS",
    "TICK": "TICK",
}


def circuit_with_xz_flipped(circuit: stim.Circuit) -> stim.Circuit:
    result = stim.Circuit()
    for inst in circuit:
        if isinstance(inst, stim.CircuitRepeatBlock):
            result.append(
                stim.CircuitRepeatBlock(
                    body=circuit_with_xz_flipped(inst.body_copy()),
                    repeat_count=inst.repeat_count,
                )
            )
        else:
            other = XZ_FLIPPED.get(inst.name)
            if other is None:
                raise NotImplementedError(f"{inst=}")
            result.append(
                stim.CircuitInstruction(
                    other, inst.targets_copy(), inst.gate_args_copy()
                )
            )
    return result
