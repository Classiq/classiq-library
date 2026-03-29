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
from typing import Any

import gen


def build_surface_code_round_circuit(
    patch: gen.Patch,
    *,
    init_data_basis: (
        None | Literal["X", "Y", "Z"] | dict[complex, Literal["X", "Y", "Z"]]
    ) = None,
    measure_data_basis: (
        None | Literal["X", "Y", "Z"] | dict[complex, Literal["X", "Y", "Z"]]
    ) = None,
    save_layer: Any,
    out: gen.Builder,
):
    measure_xs = gen.Patch([tile for tile in patch.tiles if tile.basis == "X"])
    measure_zs = gen.Patch([tile for tile in patch.tiles if tile.basis == "Z"])
    if init_data_basis is None:
        init_data_basis = {}
    elif isinstance(init_data_basis, str):
        init_data_basis = {q: init_data_basis for q in patch.data_set}
    if measure_data_basis is None:
        measure_data_basis = {}
    elif isinstance(measure_data_basis, str):
        measure_data_basis = {q: measure_data_basis for q in patch.data_set}

    out.gate("RX", measure_xs.measure_set)
    for basis in "XYZ":
        qs = [q for q in init_data_basis if init_data_basis[q] == basis]
        if qs:
            out.gate(f"R{basis}", qs)
    out.gate("R", measure_zs.measure_set)
    out.tick()

    (num_layers,) = {len(tile.ordered_data_qubits) for tile in patch.tiles}
    for k in range(num_layers):
        out.gate2(
            "CX",
            [
                (tile.measurement_qubit, tile.ordered_data_qubits[k])[
                    :: -1 if tile.basis == "Z" else +1
                ]
                for tile in patch.tiles
                if tile.ordered_data_qubits[k] is not None
            ],
        )
        out.tick()

    out.measure(measure_xs.measure_set, basis="X", save_layer=save_layer)
    for basis in "XYZ":
        qs = [q for q in measure_data_basis if measure_data_basis[q] == basis]
        if qs:
            out.measure(qs, basis=basis, save_layer=save_layer)
    out.measure(measure_zs.measure_set, basis="Z", save_layer=save_layer)


def standard_surface_code_chunk(
    patch: gen.Patch,
    *,
    init_data_basis: None | str | dict[complex, str] = None,
    measure_data_basis: None | str | dict[complex, str] = None,
    obs: gen.PauliString | None = None,
) -> gen.Chunk:
    if init_data_basis is None:
        init_data_basis = {}
    elif isinstance(init_data_basis, str):
        init_data_basis = {q: init_data_basis for q in patch.data_set}
    if measure_data_basis is None:
        measure_data_basis = {}
    elif isinstance(measure_data_basis, str):
        measure_data_basis = {q: measure_data_basis for q in patch.data_set}

    out = gen.Builder.for_qubits(patch.used_set)
    save_layer = "solo"
    build_surface_code_round_circuit(
        patch=patch,
        init_data_basis=init_data_basis,
        measure_data_basis=measure_data_basis,
        save_layer=save_layer,
        out=out,
    )

    discarded_inputs = []
    discarded_outputs = []
    flows = []
    for tile in patch.tiles:
        from_prev = gen.PauliString(
            {
                q: b
                for q, b in zip(tile.ordered_data_qubits, tile.bases)
                if q is not None and q not in init_data_basis
            }
        )
        if any(
            init_data_basis.get(q, b) != b
            for q, b in zip(tile.ordered_data_qubits, tile.bases)
        ):
            # Stabilizer anticommutes with a reset. Not prepared.
            if from_prev:
                discarded_inputs.append(from_prev)
            continue
        flows.append(
            gen.Flow(
                center=tile.measurement_qubit,
                start=from_prev,
                measurement_indices=out.tracker.measurement_indices(
                    [gen.AtLayer(tile.measurement_qubit, save_layer)]
                ),
                additional_coords=[
                    (tile.measurement_qubit.real % 2 == 0.5) + 3 * (tile.basis == "Z")
                ],
            )
        )

    for tile in patch.tiles:
        to_next = gen.PauliString(
            {
                q: b
                for q, b in zip(tile.ordered_data_qubits, tile.bases)
                if q is not None and q not in measure_data_basis
            }
        )
        if any(
            measure_data_basis.get(q, b) != b
            for q, b in zip(tile.ordered_data_qubits, tile.bases)
        ):
            # Stabilizer anticommutes with a reset. Not prepared.
            if to_next:
                discarded_outputs.append(to_next)
            continue
        flows.append(
            gen.Flow(
                center=tile.measurement_qubit,
                end=to_next,
                measurement_indices=out.tracker.measurement_indices(
                    [
                        gen.AtLayer(q, save_layer)
                        for q in tile.used_set
                        if q in measure_data_basis or q == tile.measurement_qubit
                    ]
                ),
                additional_coords=[
                    (tile.measurement_qubit.real % 2 == 0.5) + 3 * (tile.basis == "Z")
                ],
            )
        )

    if obs is not None:
        start_obs = dict(obs.qubits)
        end_obs = dict(obs.qubits)
        for q in init_data_basis:
            if q in start_obs:
                if start_obs.pop(q) != init_data_basis[q]:
                    raise ValueError("wrong init basis for obs")
        measure_indices = []
        for q in measure_data_basis:
            if q in end_obs:
                if end_obs.pop(q) != measure_data_basis[q]:
                    raise ValueError("wrong measure basis for obs")
                measure_indices.extend(
                    out.tracker.measurement_indices([gen.AtLayer(q, save_layer)])
                )

        flows.append(
            gen.Flow(
                center=0,
                start=gen.PauliString(start_obs),
                end=gen.PauliString(end_obs),
                obs_index=0,
                measurement_indices=measure_indices,
            )
        )

    return gen.Chunk(
        circuit=out.circuit,
        q2i=out.q2i,
        flows=flows,
        discarded_inputs=discarded_inputs,
        discarded_outputs=discarded_outputs,
    )
