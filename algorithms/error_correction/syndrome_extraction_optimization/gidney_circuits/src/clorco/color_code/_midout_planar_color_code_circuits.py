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

from typing import Iterable, Callable

import gen
from clorco.color_code._color_code_layouts import (
    make_color_code_layout,
    make_color_code_layout_488,
)


def _color_code_round_chunk(
    *,
    base_width: int,
    use_488: bool,
    basis: str,
    layer_parity: bool,
    first_round: bool,
) -> gen.Chunk:
    if use_488:
        code = make_color_code_layout_488(
            base_width=base_width,
            spurs="midout",
            coord_style="rect",
            single_rgb_layer_instead_of_actual_code=True,
        )
    else:
        code = make_color_code_layout(
            base_width=base_width,
            spurs="midout",
            coord_style="rect",
            single_rgb_layer_instead_of_actual_code=True,
        )
    patch = code.patch

    rail_b = {
        (q, q + 1j)
        for q in patch.data_set
        if q.imag % 2 == 0
        if q + 1j in patch.data_set
    }
    rail_a = {
        (q, q + 1j)
        for q in patch.data_set
        if q.imag % 2 == 1
        if q + 1j in patch.data_set
    }
    rung_m = {
        (other, q)
        for q in patch.data_set
        if (q.imag + q.real) % 2 == 1
        if (other := q + 1) in patch.data_set
    }
    if use_488:
        rung_m = rev_pairs(rung_m)
        rail_b = rev_pairs(rail_b, pred=lambda a, _: a.imag % 4 == 0)

    mx = {q for q in patch.measure_set if q.imag % 2 == 1}
    mz = {q for q in patch.measure_set if q.imag % 2 == 0}
    m2t = {tile.measurement_qubit: tile for tile in patch.tiles}
    assert len(m2t) == len(patch.tiles)
    if not layer_parity:
        mx, mz = mz, mx
        rung_m = rev_pairs(rung_m)
        rail_b = rev_pairs(rail_b)
        rail_a = rev_pairs(rail_a)

    builder = gen.Builder.for_qubits(patch.data_set)

    # Fold color code state towards next measurement.
    if not first_round:
        builder.gate2("CX", rail_b)
        builder.tick()
        builder.gate2("CX", rail_a)
        builder.tick()
        builder.gate2("CX", rung_m)
        builder.tick()

        # Measure stabilizers.
        builder.measure(mx, basis="X", save_layer="solo")
        builder.measure(mz, basis="Z", save_layer="solo")
        builder.shift_coords(dt=1)
        builder.tick()

    # Physically do a demolition measurement, but use feedback to present it as non-demolition to the control system.
    builder.gate("RX", mx)
    if first_round:
        builder.gate(f"R{basis}", patch.data_set - mx - mz)
    builder.gate("R", mz)
    if not first_round:
        for ms, mb in ((mx, "Z"), (mz, "X")):
            for m in gen.sorted_complex(ms):
                builder.classical_paulis(
                    control_keys=[gen.AtLayer(m, "solo")], targets=[m], basis=mb
                )
    builder.tick()

    # Unfold from previous measurement to color code state.
    builder.gate2("CX", rung_m)
    builder.tick()
    builder.gate2("CX", rail_a)
    builder.tick()
    builder.gate2("CX", rail_b)

    flows = []
    discarded_outputs = []
    for tile in patch.tiles:
        measured_tile_basis = "X" if tile.measurement_qubit in mx else "Z"
        for check_basis in "XZ":
            ps = gen.PauliString({q: check_basis for q in tile.data_set})
            additional_coords = [tile.extra_coords[0] + "XZ".index(check_basis) * 3]
            if first_round:
                if check_basis in [basis, measured_tile_basis]:
                    flows.append(
                        gen.Flow(
                            end=ps,
                            center=tile.measurement_qubit,
                            additional_coords=additional_coords,
                        )
                    )
                else:
                    discarded_outputs.append(ps)
            else:
                if check_basis == measured_tile_basis:
                    ms = builder.tracker.measurement_indices(
                        [gen.AtLayer(tile.measurement_qubit, "solo")]
                    )
                    flows.append(
                        gen.Flow(
                            start=ps,
                            measurement_indices=ms,
                            center=tile.measurement_qubit,
                            additional_coords=additional_coords,
                        )
                    )
                    flows.append(
                        gen.Flow(
                            end=ps,
                            measurement_indices=ms,
                            center=tile.measurement_qubit,
                            additional_coords=additional_coords,
                        )
                    )
                else:
                    flows.append(
                        gen.Flow(
                            start=ps,
                            end=ps,
                            center=tile.measurement_qubit,
                            additional_coords=additional_coords,
                        )
                    )

    obs = gen.PauliString({q: basis for q in patch.data_set})
    flows.append(
        gen.Flow(
            start=None if first_round else obs,
            end=obs,
            center=0,
            obs_index=0,
            additional_coords=(),
        )
    )

    return gen.Chunk(
        circuit=builder.circuit,
        q2i=builder.q2i,
        flows=flows,
        discarded_outputs=discarded_outputs,
    )


def make_midout_color_code_circuit_chunks(
    *,
    base_width: int,
    basis: str,
    rounds: int,
    use_488: bool,
) -> list[gen.Chunk]:
    assert rounds >= 2
    start_not_a_round = _color_code_round_chunk(
        base_width=base_width,
        use_488=use_488,
        basis=basis,
        layer_parity=False,
        first_round=True,
    )
    body_0, body_1 = [
        _color_code_round_chunk(
            base_width=base_width,
            use_488=use_488,
            basis=basis,
            layer_parity=b,
            first_round=False,
        )
        for b in [False, True]
    ]
    end = _color_code_round_chunk(
        base_width=base_width,
        use_488=use_488,
        basis=basis,
        layer_parity=rounds % 2 == 1,
        first_round=True,
    ).inverted()

    if rounds % 2 == 0:
        tail = [body_1, end]
    else:
        tail = [end]

    return [
        start_not_a_round,
        gen.ChunkLoop([body_1, body_0], repetitions=(rounds - 1) // 2),
        *tail,
    ]


def rev_pairs(
    pairs: Iterable[tuple[complex, complex]],
    *,
    pred: Callable[[complex, complex], bool] = lambda _a, _b: True,
) -> list[tuple[complex, complex]]:
    return [e[:: -1 if pred(*e) else +1] for e in pairs]
