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

from typing import Callable
from typing import Iterable
from typing import Literal

import stim

import gen


def make_color_code_layout_for_superdense(
    *,
    base_data_width: int,
    single_rgb_layer_instead_of_actual_code: (
        bool | Literal["double_measure_qubit"]
    ) = False,
) -> gen.StabilizerCode:
    assert base_data_width > 2 and base_data_width % 2 == 1
    base_width = base_data_width * 2 - 1

    tiles = []
    for x in range(-1, base_width, 2):
        for y in range((x // 2) % 2, base_width, 2):
            q = x + 1j * y
            order = [-1, +1j, +1j + 1, +2, -1j + 1, -1j]
            rgb = y % 3
            bases = "XYZ"[rgb] if single_rgb_layer_instead_of_actual_code else "XZ"
            if single_rgb_layer_instead_of_actual_code == "double_measure_qubit":
                bases *= 2
            for k in range(len(bases)):
                tiles.append(
                    gen.Tile(
                        bases=bases[k],
                        measurement_qubit=q + k,
                        ordered_data_qubits=[q + d for d in order],
                        extra_coords=[rgb + k * 3],
                    )
                )

    def is_in_bounds(q: complex) -> bool:
        if q.real < 0 or q.imag < 0 or q.real >= base_width or q.imag >= base_width:
            return False
        if q.imag * 2 > q.real * 3:
            return False
        if q.imag * 2 > (base_width - q.real) * 3:
            return False
        return True

    filtered_tiles = []
    for tile in tiles:
        new_tile = gen.Tile(
            bases=tile.bases,
            measurement_qubit=tile.measurement_qubit,
            ordered_data_qubits=[
                (q if is_in_bounds(q) else None) for q in tile.ordered_data_qubits
            ],
            extra_coords=tile.extra_coords,
        )
        if len(new_tile.data_set) >= 4:
            filtered_tiles.append(new_tile)

    patch = gen.Patch(filtered_tiles)
    obs_x = gen.PauliString({q: "X" for q in patch.data_set})
    obs_z = gen.PauliString({q: "Z" for q in patch.data_set if q.imag == 0})

    result = gen.StabilizerCode(
        patch=patch,
        observables_x=[obs_x],
        observables_z=[obs_z],
    )

    return result


def make_superdense_color_code_circuit_round_chunk(
    *,
    initialize: bool,
    basis: Literal["X", "Z"],
    base_data_width: int,
    cnot_schedule: Literal["original", "modified"] = "original",
) -> gen.Chunk:
    code = make_color_code_layout_for_superdense(
        base_data_width=base_data_width,
    )

    builder = gen.Builder.for_qubits(code.patch.used_set)
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
                (c + d_control, c + d_target)[:: -1 if inv(c) else +1]
                for c in centers
                if c + d_control in code.patch.used_set
                if c + d_target in code.patch.used_set
            ],
        )

    builder.gate("RX", x_ms)
    if initialize:
        builder.gate(f"R{basis}", code.patch.data_set)
    builder.gate("RZ", z_ms)
    builder.tick()

    if cnot_schedule == "original":
        do_cxs(x_ms, +0, +1)
        builder.tick()
        do_cxs(x_ms, +1j, +0)
        do_cxs(z_ms, +1j, +0)
        builder.tick()
        do_cxs(x_ms, -1, +0)
        do_cxs(z_ms, +1, +0)
        builder.tick()
        do_cxs(x_ms, -1j, +0)
        do_cxs(z_ms, -1j, +0)
        builder.tick()
        do_cxs(x_ms, +0, +1j)
        do_cxs(z_ms, +0, +1j)
        builder.tick()
        do_cxs(x_ms, +0, -1)
        do_cxs(z_ms, +0, +1)
        builder.tick()
        do_cxs(x_ms, +0, -1j)
        do_cxs(z_ms, +0, -1j)
        builder.tick()
        do_cxs(x_ms, +0, +1)
        builder.tick()
    else:
        # modified: swap 2nd and 3rd tick blocks (-1 before +1j)
        do_cxs(x_ms, +0, +1)
        builder.tick()
        do_cxs(x_ms, -1, +0)
        do_cxs(z_ms, +1, +0)
        builder.tick()
        do_cxs(x_ms, +1j, +0)
        do_cxs(z_ms, +1j, +0)
        builder.tick()
        do_cxs(x_ms, -1j, +0)
        do_cxs(z_ms, -1j, +0)
        builder.tick()
        do_cxs(x_ms, +0, -1)
        do_cxs(z_ms, +0, +1)
        builder.tick()
        do_cxs(x_ms, +0, +1j)
        do_cxs(z_ms, +0, +1j)
        builder.tick()
        do_cxs(x_ms, +0, -1j)
        do_cxs(z_ms, +0, -1j)
        builder.tick()
        do_cxs(x_ms, +0, +1)
        builder.tick()

    builder.measure(x_ms, basis="X", save_layer="solo")
    builder.measure(z_ms, basis="Z", save_layer="solo")

    def mf(*qs):
        return builder.tracker.measurement_indices(
            [gen.AtLayer(q, "solo") for q in qs if q in code.patch.measure_set]
        )

    flows = []
    for tile in code.patch.tiles:
        m = tile.measurement_qubit
        if tile.basis == "X":
            if not initialize:
                flows.append(
                    gen.Flow(
                        start=tile.to_data_pauli_string(),
                        measurement_indices=mf(m),
                        center=m,
                        additional_coords=tile.extra_coords,
                    )
                )
            elif basis == "X":
                flows.append(
                    gen.Flow(
                        measurement_indices=mf(m),
                        center=m,
                        additional_coords=tile.extra_coords,
                    )
                )
            flows.append(
                gen.Flow(
                    end=tile.to_data_pauli_string(),
                    measurement_indices=mf(m),
                    center=m,
                    additional_coords=tile.extra_coords,
                )
            )
        elif tile.basis == "Z":
            if not initialize:
                flows.append(
                    gen.Flow(
                        start=tile.to_data_pauli_string(),
                        measurement_indices=mf(m),
                        center=m,
                        additional_coords=tile.extra_coords,
                    )
                )
            elif basis == "Z":
                flows.append(
                    gen.Flow(
                        measurement_indices=mf(m),
                        center=m,
                        additional_coords=tile.extra_coords,
                    )
                )
            flows.append(
                gen.Flow(
                    end=tile.to_data_pauli_string(),
                    measurement_indices=mf(m - 2j if m.imag > 0 else m, m + 2j),
                    center=m,
                    additional_coords=tile.extra_coords,
                )
            )

    (obs_x,) = code.observables_x
    (obs_z,) = code.observables_z
    if basis == "X":
        flows.append(
            gen.Flow(
                start=None if initialize else obs_x,
                end=obs_x,
                measurement_indices=[],
                center=-1 - 1j,
                obs_index=0,
            )
        )
    elif basis == "Z":
        flows.append(
            gen.Flow(
                start=None if initialize else obs_z,
                end=obs_z,
                measurement_indices=mf(
                    *[
                        tile.measurement_qubit
                        for tile in code.patch.tiles
                        if tile.basis == "Z" and tile.measurement_qubit.imag <= 1
                    ]
                ),
                center=-1 - 1j,
                obs_index=0,
            )
        )

    return gen.Chunk(
        circuit=builder.circuit,
        flows=flows,
        q2i=builder.q2i,
    )


def make_superdense_color_code_circuit(
    *,
    base_data_width: int,
    basis: Literal["X", "Z"],
    rounds: int,
    cnot_schedule: Literal["original", "modified"] = "original",
) -> stim.Circuit:
    assert rounds >= 2

    first_round = make_superdense_color_code_circuit_round_chunk(
        initialize=True,
        basis=basis,
        base_data_width=base_data_width,
        cnot_schedule=cnot_schedule,
    )
    mid_round = make_superdense_color_code_circuit_round_chunk(
        initialize=False,
        basis=basis,
        base_data_width=base_data_width,
        cnot_schedule=cnot_schedule,
    )
    end_round = first_round.inverted()

    return gen.compile_chunks_into_circuit(
        [
            first_round,
            gen.ChunkLoop([mid_round], repetitions=rounds - 2),
            end_round,
        ]
    )
