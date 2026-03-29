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

from typing import Literal

import stim

import gen
from clorco.surface_code._surface_code_chunks import build_surface_code_round_circuit
from clorco.surface_code._surface_code_layouts import make_surface_code_layout


def make_transversal_cnot_surface_code_circuit(
    *,
    diameter: int,
    basis: Literal["X", "Z", "MagicEPR"],
    pad_rounds: int,
    noise: gen.NoiseModel | None,
    convert_to_z: bool,
) -> stim.Circuit:
    assert pad_rounds >= 1
    offset = diameter + 2
    left = make_surface_code_layout(width=diameter, height=diameter)
    right = left.with_transformed_coords(lambda e: e + offset)
    combo = gen.Patch(left.patch.tiles + right.patch.tiles)
    ancillas = {-1, -2} if basis == "MagicEPR" else set()
    xl = left.observables_x[0]
    zl = left.observables_z[0]
    xr = right.observables_x[0]
    zr = right.observables_z[0]

    # Initial round.
    head = gen.Builder.for_qubits(combo.used_set | ancillas)
    builder = head.fork()
    tail = head.fork()
    if basis == "MagicEPR":
        head.gate("RY", combo.used_set)
        head.measure_pauli_string(xl * gen.PauliString({-1: "X"}), key="OBS_INIT1")
        head.measure_pauli_string(zl * gen.PauliString({-1: "Z"}), key="OBS_INIT2")
        head.measure_pauli_string(xr * gen.PauliString({-2: "X"}), key="OBS_INIT3")
        head.measure_pauli_string(zr * gen.PauliString({-2: "Z"}), key="OBS_INIT4")
        head.obs_include(["OBS_INIT1"], obs_index=0)
        head.obs_include(["OBS_INIT2"], obs_index=1)
        head.obs_include(["OBS_INIT3"], obs_index=2)
        head.obs_include(["OBS_INIT4"], obs_index=3)
        head.measure_patch(combo, sorted_by_basis=True, save_layer="init")
        pad_rounds += 1
    else:
        build_surface_code_round_circuit(
            patch=combo,
            init_data_basis=basis,
            save_layer="init",
            out=builder,
        )
        for tile in combo.tiles:
            m = tile.measurement_qubit
            if tile.basis == basis:
                builder.detector(
                    [gen.AtLayer(m, "init")],
                    pos=m,
                    extra_coords=[0 + 3 * (tile.basis == "Z")],
                )
    builder.shift_coords(dt=1)
    builder.tick()

    # Padding rounds until transition.
    loop = builder.fork()
    build_surface_code_round_circuit(
        patch=combo,
        save_layer="before",
        out=loop,
    )
    for tile in combo.tiles:
        m = tile.measurement_qubit
        loop.detector(
            [gen.AtLayer(m, "init"), gen.AtLayer(m, "before")],
            pos=m,
            extra_coords=[0 + 3 * (tile.basis == "Z")],
        )
    loop.shift_coords(dt=1)
    loop.tick()
    builder.circuit += loop.circuit * (pad_rounds - 1)

    # Transition round.
    builder.gate2("CX", [(q, q + offset) for q in left.patch.data_set])
    builder.tick()
    build_surface_code_round_circuit(
        patch=combo,
        save_layer="transition",
        out=builder,
    )
    for tile in combo.tiles:
        m = tile.measurement_qubit
        if tile.basis == "X" and m in left.patch.measure_set:
            tile_offsets = [(0, "before"), (0, "transition"), (offset, "transition")]
        elif tile.basis == "Z" and m in right.patch.measure_set:
            tile_offsets = [(0, "before"), (0, "transition"), (-offset, "transition")]
        else:
            tile_offsets = [(0, "before"), (0, "transition")]
        builder.detector(
            [gen.AtLayer(m + d, layer) for d, layer in tile_offsets],
            pos=m,
            extra_coords=[1 + (m in left.patch.measure_set) + 3 * (tile.basis == "Z")],
        )
    builder.shift_coords(dt=1)
    builder.tick()

    # Padding rounds until measurement round.
    loop = builder.fork()
    build_surface_code_round_circuit(
        patch=combo,
        save_layer="after",
        out=loop,
    )
    for tile in combo.tiles:
        m = tile.measurement_qubit
        loop.detector(
            [gen.AtLayer(m, "transition"), gen.AtLayer(m, "after")],
            pos=m,
            extra_coords=[0 + 3 * (tile.basis == "Z")],
        )
    loop.shift_coords(dt=1)
    loop.tick()
    builder.circuit += loop.circuit * (pad_rounds - 2)

    # Final measurement round.
    if basis == "MagicEPR":
        tail.measure_patch(combo, sorted_by_basis=True, save_layer="end")
        for tile in combo.tiles:
            m = tile.measurement_qubit
            tail.detector(
                [gen.AtLayer(m, "after"), gen.AtLayer(m, "end")],
                pos=m,
                extra_coords=[0 + 3 * (tile.basis == "Z")],
            )
        tail.measure_pauli_string(xl * xr * gen.PauliString({-1: "X"}), key="OBS_END1")
        tail.measure_pauli_string(zl * gen.PauliString({-1: "Z"}), key="OBS_END2")
        tail.measure_pauli_string(xr * gen.PauliString({-2: "X"}), key="OBS_END3")
        tail.measure_pauli_string(zl * zr * gen.PauliString({-2: "Z"}), key="OBS_END4")
        tail.obs_include(["OBS_END1"], obs_index=0)
        tail.obs_include(["OBS_END2"], obs_index=1)
        tail.obs_include(["OBS_END3"], obs_index=2)
        tail.obs_include(["OBS_END4"], obs_index=3)
    else:
        build_surface_code_round_circuit(
            patch=combo,
            measure_data_basis=basis,
            save_layer="end",
            out=builder,
        )
        for tile in combo.tiles:
            m = tile.measurement_qubit
            builder.detector(
                [gen.AtLayer(m, "after"), gen.AtLayer(m, "end")],
                pos=m,
                extra_coords=[0 + 3 * (tile.basis == "Z")],
            )
        builder.shift_coords(dt=1)
        for tile in combo.tiles:
            m = tile.measurement_qubit
            if tile.basis == basis:
                builder.detector(
                    [gen.AtLayer(q, "end") for q in tile.used_set],
                    pos=m,
                    extra_coords=[0 + 3 * (tile.basis == "Z")],
                )
        if basis == "X":
            builder.obs_include([gen.AtLayer(q, "end") for q in xl.qubits], obs_index=0)
            builder.obs_include([gen.AtLayer(q, "end") for q in xr.qubits], obs_index=1)
        elif basis == "Z":
            builder.obs_include([gen.AtLayer(q, "end") for q in zl.qubits], obs_index=0)
            builder.obs_include([gen.AtLayer(q, "end") for q in zr.qubits], obs_index=1)
        else:
            raise NotImplementedError(f"{basis=}")

    body = builder.circuit
    if convert_to_z:
        body = gen.transpile_to_z_basis_interaction_circuit(
            body, is_entire_circuit=False
        )
    if noise is not None:
        body = noise.noisy_circuit(
            body, immune_qubit_indices={builder.q2i[a] for a in ancillas}
        )

    return head.circuit + body + tail.circuit
