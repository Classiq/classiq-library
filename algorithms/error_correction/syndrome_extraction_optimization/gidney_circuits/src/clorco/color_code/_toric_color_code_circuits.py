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

from typing import Literal, Iterable, Callable

import stim

import gen
from clorco.color_code._color_code_layouts import make_toric_color_code_layout


def make_toric_color_code_circuit_with_magic_time_boundaries(
    *,
    rounds: int,
    width: int,
    height: int,
    noise: gen.NoiseModel,
    ablate_into_matchable_code: bool = False,
    style: Literal["superdense", "midout"],
    convert_to_cz: bool,
) -> stim.Circuit:
    if style == "superdense":
        rounds_per_chunk = 1
        chunk = make_toric_color_code_circuit_round_chunk_superdense(
            width=width,
            height=height,
            noise=noise,
            ablate_into_matchable_code=ablate_into_matchable_code,
            convert_to_cz=convert_to_cz,
        )
    elif style == "midout":
        rounds_per_chunk = 2
        chunk = make_toric_color_code_circuit_double_round_chunk_midout(
            width=width,
            height=height,
            noise=noise,
            ablate_into_matchable_code=ablate_into_matchable_code,
            convert_to_cz=convert_to_cz,
        )
    else:
        raise NotImplementedError(f"{style=}")

    assert rounds % rounds_per_chunk == 0
    return gen.compile_chunks_into_circuit(
        [
            chunk.magic_init_chunk(),
            gen.ChunkLoop([chunk], repetitions=rounds // rounds_per_chunk),
            chunk.magic_end_chunk(),
        ]
    ).with_inlined_feedback()


def make_toric_color_code_circuit_round_chunk_superdense(
    *,
    width: int,
    height: int,
    noise: gen.NoiseModel | None = None,
    ablate_into_matchable_code: bool = False,
    convert_to_cz: bool,
) -> gen.Chunk:
    ancilla_qubits = [-1, -2]
    code = make_toric_color_code_layout(width=width, height=height)
    w = max(q.real for q in code.patch.used_set) + 1
    h = max(q.imag for q in code.patch.used_set) + 1

    def wrap(q: complex) -> complex:
        return (q.real % w) + (q.imag % h) * 1j

    builder = gen.Builder.for_qubits(code.patch.used_set | set(ancilla_qubits))
    x_ms = [tile.measurement_qubit for tile in code.patch.tiles if tile.basis == "X"]
    z_ms = [tile.measurement_qubit for tile in code.patch.tiles if tile.basis == "Z"]

    def do_cxs(
        centers: Iterable[complex],
        d_control: complex,
        d_target: complex,
        inv: Callable[[complex], bool] = lambda _: False,
    ) -> None:
        builder.gate2(
            "CX",
            [
                (wrap(c + d_control), wrap(c + d_target))[:: -1 if inv(c) else +1]
                for c in centers
            ],
        )

    builder.gate("RX", x_ms)
    builder.gate("RZ", z_ms)
    builder.tick()

    do_cxs(x_ms, +0, +1j)
    builder.tick()
    do_cxs(x_ms, +1, +0)
    do_cxs(z_ms, +1, +0)
    builder.tick()
    do_cxs(x_ms, -1j, +0)
    do_cxs(z_ms, +1j, +0)
    builder.tick()
    do_cxs(x_ms, -1, +0)
    do_cxs(z_ms, -1, +0)
    builder.tick()
    do_cxs(x_ms, +0, +1)
    do_cxs(z_ms, +0, +1)
    builder.tick()
    do_cxs(x_ms, +0, -1j)
    do_cxs(z_ms, +0, +1j)
    builder.tick()
    do_cxs(x_ms, +0, -1)
    do_cxs(z_ms, +0, -1)
    builder.tick()
    do_cxs(x_ms, +0, +1j)
    builder.tick()

    builder.measure(x_ms, basis="X", save_layer="solo")
    builder.measure(z_ms, basis="Z", save_layer="solo")
    builder.tick()

    def mf(*qs):
        return builder.tracker.measurement_indices(
            [gen.AtLayer(wrap(q), "solo") for q in qs]
        )

    flows = []
    for tile in code.patch.tiles:
        m = tile.measurement_qubit
        rgb = m.real % 3
        if tile.basis == "X":
            if ablate_into_matchable_code and rgb == 0:
                continue
            flows.append(
                gen.Flow(
                    end=tile.to_data_pauli_string(),
                    measurement_indices=mf(m),
                    center=m,
                    additional_coords=[rgb],
                )
            )
            flows.append(
                gen.Flow(
                    start=tile.to_data_pauli_string(),
                    measurement_indices=mf(m),
                    center=m,
                    additional_coords=[rgb],
                )
            )
        elif tile.basis == "Z":
            if ablate_into_matchable_code and rgb == 2:
                continue
            flows.append(
                gen.Flow(
                    start=tile.to_data_pauli_string(),
                    measurement_indices=mf(m),
                    center=m,
                    additional_coords=[3 + rgb],
                )
            )
            flows.append(
                gen.Flow(
                    end=tile.to_data_pauli_string(),
                    measurement_indices=mf(m - 2, m + 2),
                    center=m,
                    additional_coords=[3 + rgb],
                )
            )

    x1, x2 = code.observables_x
    z1, z2 = code.observables_z
    x1 *= gen.PauliString({ancilla_qubits[0]: "X"})
    z1 *= gen.PauliString({ancilla_qubits[0]: "Z"})
    x2 *= gen.PauliString({ancilla_qubits[1]: "X"})
    z2 *= gen.PauliString({ancilla_qubits[1]: "Z"})
    flows.append(
        gen.Flow(
            start=x1,
            end=x1,
            measurement_indices=[],
            center=-1 - 1j,
            obs_index=0,
        )
    )
    flows.append(
        gen.Flow(
            start=x2,
            end=x2,
            measurement_indices=[],
            center=-2 - 1j,
            obs_index=1,
        )
    )
    flows.append(
        gen.Flow(
            start=z1,
            end=z1,
            measurement_indices=[],
            center=-3 - 1j,
            obs_index=2,
        )
    )
    flows.append(
        gen.Flow(
            start=z2,
            end=z2,
            measurement_indices=mf(*[m for m in z_ms if m.real in [1, 2, 3]]),
            center=-4 - 1j,
            obs_index=3,
        )
    )

    circuit = builder.circuit
    if convert_to_cz:
        circuit = gen.transpile_to_z_basis_interaction_circuit(
            circuit, is_entire_circuit=False
        )
    if noise is not None:
        circuit = noise.noisy_circuit(
            circuit, immune_qubit_indices={builder.q2i[-1], builder.q2i[-2]}
        )
    return gen.Chunk(
        circuit=circuit,
        flows=flows,
        q2i=builder.q2i,
    )


def make_toric_color_code_circuit_double_round_chunk_midout(
    *,
    width: int,
    height: int,
    noise: gen.NoiseModel | None = None,
    convert_to_cz: bool,
    ablate_into_matchable_code: bool = False,
) -> gen.Chunk:
    ancilla_qubits = [-1, -2]
    code = make_toric_color_code_layout(width=width, height=height, square_coords=True)
    w = max(q.real for q in code.patch.used_set) + 1
    h = max(q.imag for q in code.patch.used_set) + 1

    def wrap(q: complex) -> complex:
        return (q.real % w) + (q.imag % h) * 1j

    builder = gen.Builder.for_qubits(code.patch.used_set | set(ancilla_qubits))

    def do_cxs(
        centers: Iterable[complex],
        d_control: complex,
        d_target: complex,
        inv: Callable[[complex], bool] = lambda _: False,
    ) -> None:
        builder.gate2(
            "CX",
            [
                (
                    wrap(c + d_control),
                    wrap(c + d_target),
                )[:: -1 if inv(c) else +1]
                for c in centers
            ],
        )

    x_ms = [
        d for d in code.patch.data_set if d.real % 2 != d.imag % 2 and d.real % 2 == 1
    ]
    z_ms = [
        d for d in code.patch.data_set if d.real % 2 != d.imag % 2 and d.real % 2 == 0
    ]
    d1s = [d for d in code.patch.data_set if d.real % 2 == 0]
    d2s = [d for d in code.patch.data_set if d.real % 2 == 1]

    do_cxs(d1s, +0, +1)
    builder.tick()
    do_cxs(d2s, +0, +1)
    builder.tick()
    do_cxs(z_ms, +1j, +0)
    do_cxs(x_ms, +0, +1j)
    builder.tick()
    builder.demolition_measure_with_feedback_passthrough(
        xs=x_ms, zs=z_ms, save_layer="a"
    )
    builder.tick()
    do_cxs(z_ms, +1j, +0)
    do_cxs(x_ms, +0, +1j)
    builder.tick()
    do_cxs(d2s, +0, +1)
    builder.tick()
    do_cxs(d1s, +0, +1)
    builder.tick()

    do_cxs(d1s, +1, +0)
    builder.tick()
    do_cxs(d2s, +1, +0)
    builder.tick()
    do_cxs(z_ms, +0, +1j)
    do_cxs(x_ms, +1j, +0)
    builder.tick()
    builder.demolition_measure_with_feedback_passthrough(
        xs=z_ms, zs=x_ms, save_layer="b"
    )
    builder.tick()
    do_cxs(z_ms, +0, +1j)
    do_cxs(x_ms, +1j, +0)
    builder.tick()
    do_cxs(d2s, +1, +0)
    builder.tick()
    do_cxs(d1s, +1, +0)
    builder.tick()

    def ma(*qs) -> list[int]:
        return builder.tracker.measurement_indices(
            [gen.AtLayer(wrap(q), "a") for q in qs]
        )

    def mb(*qs) -> list[int]:
        return builder.tracker.measurement_indices(
            [gen.AtLayer(wrap(q), "b") for q in qs]
        )

    flows = []
    for tile in code.patch.tiles:
        m = tile.measurement_qubit
        if ablate_into_matchable_code and tile.extra_coords[0] in [0, 5]:
            continue
        if tile.basis == "X":
            mids = mb(m + 1) if m.real % 2 == 1 else ma(m - 1)
        elif tile.basis == "Z":
            mids = ma(m + 1 - 1j) if m.real % 2 == 1 else mb(m - 1 - 1j)
        else:
            raise NotImplementedError(f"{tile=}")
        flows.append(
            gen.Flow(
                start=tile.to_data_pauli_string(),
                measurement_indices=mids,
                center=m,
                additional_coords=tile.extra_coords,
            )
        )
        flows.append(
            gen.Flow(
                end=tile.to_data_pauli_string(),
                measurement_indices=mids,
                center=m,
                additional_coords=tile.extra_coords,
            )
        )

    x1, x2 = code.observables_x
    z1, z2 = code.observables_z
    x1 *= gen.PauliString({ancilla_qubits[0]: "X"})
    z1 *= gen.PauliString({ancilla_qubits[0]: "Z"})
    x2 *= gen.PauliString({ancilla_qubits[1]: "X"})
    z2 *= gen.PauliString({ancilla_qubits[1]: "Z"})
    for k, obs in enumerate([x1, z1, x2, z1]):
        flows.append(
            gen.Flow(
                start=obs,
                end=obs,
                center=-1 - 1j - k * 1j,
                obs_index=k,
            )
        )

    circuit = builder.circuit
    if convert_to_cz:
        circuit = gen.transpile_to_z_basis_interaction_circuit(
            circuit, is_entire_circuit=False
        )
    if noise is not None:
        circuit = noise.noisy_circuit(
            circuit, immune_qubit_indices={builder.q2i[-1], builder.q2i[-2]}
        )
    return gen.Chunk(
        circuit=circuit,
        flows=flows,
        q2i=builder.q2i,
    )
