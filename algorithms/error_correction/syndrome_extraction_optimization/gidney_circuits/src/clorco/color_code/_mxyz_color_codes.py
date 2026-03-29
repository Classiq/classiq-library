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
from typing import cast

import stim

import gen
from clorco.color_code._superdense_planar_color_code_circuits import (
    make_color_code_layout_for_superdense,
)


def make_mxyz_phenom_color_code(
    *,
    base_width: int,
    rounds: int,
    noise: float | gen.NoiseRule,
) -> stim.Circuit:
    """Creates a color code that cycles between measuring X, then Y, then Z stabilizers.

     (As opposed to alternating between X and Z, as is more common.)

     Uses a phenomomenological noise model.

     Args:
         base_width: Base width of the triangular patch of the color code.
         rounds: Number of times each shape is measured. An XYZ cycle is
            three rounds. This differs from rounds in the usual phenom
            circuit which measure both X and Z in one round.
        noise: Noise to apply. If this is a float, then the float is both
            the between-ronud depolarization strength and the
            measurement flip probability. If this is a gen.NoiseRule then
            its `after` is the between-round noise and its `flip_result` is
            the measurement noise.

    Returns:
        Stim circuit specifying the XYZ phenom color code.
    """
    if isinstance(noise, (int, float)):
        noise = gen.NoiseRule(after={"DEPOLARIZE1": noise}, flip_result=noise)

    code = make_color_code_layout_for_superdense(
        base_data_width=base_width,
    )
    ancilla = -1 - 1j
    builder = gen.Builder.for_qubits(code.patch.data_set | {ancilla})

    builder.measure_observables_and_include(
        code.entangled_observables([ancilla])[0],
    )
    builder.tick()
    x_tiles = gen.Patch(tile for tile in code.patch.tiles if tile.basis == "X")
    y_tiles = x_tiles.after_basis_transform(lambda _: cast(Literal["X", "Y", "Z"], "Y"))
    z_tiles = x_tiles.after_basis_transform(lambda _: cast(Literal["X", "Y", "Z"], "Z"))
    builder.measure_patch(
        y_tiles,
        save_layer=-2,
    )
    builder.tick()
    builder.measure_patch(
        z_tiles,
        save_layer=-1,
    )
    builder.tick()

    round_index = 0

    def append_round(out: gen.Builder, round_noise: bool) -> None:
        nonlocal round_index
        tiles = [x_tiles, y_tiles, z_tiles][round_index % 3]
        if round_noise:
            for k, p in noise.after.items():
                out.circuit.append(
                    k, [builder.q2i[q] for q in gen.sorted_complex(tiles.data_set)], p
                )
        out.measure_patch(
            tiles,
            save_layer=round_index,
            noise=noise.flip_result if round_noise else None,
        )
        for tile in tiles.tiles:
            rgb = int(tile.extra_coords[0]) % 3
            m = tile.measurement_qubit
            out.detector(
                [gen.AtLayer(m, round_index + offset) for offset in [-2, -1, 0]],
                pos=m,
                extra_coords=[(rgb + round_index) % 3],
            )
        out.shift_coords(dt=1)
        out.tick()
        round_index += 1

    loop = builder.fork()
    append_round(loop, True)
    append_round(loop, True)
    append_round(loop, True)
    builder.circuit += loop.circuit * (rounds // 3)
    for _ in range(rounds % 3):
        append_round(builder, True)

    append_round(builder, False)
    append_round(builder, False)
    builder.measure_observables_and_include(
        code.entangled_observables([ancilla])[0],
    )
    return builder.circuit


def make_mxyz_color_code_from_stim_gen(
    *,
    distance: int,
    rounds: int,
    noise: gen.NoiseModel | None,
    convert_to_cz: bool,
) -> stim.Circuit:
    """Tweaks stim's memory_xyz color code circuits.

    Overwrites the noise model.

    Adds Chromobius basis and color annotations to each detector.
    """

    circuit = stim.Circuit.generated(
        code_task="color_code:memory_xyz",
        distance=distance,
        rounds=rounds,
    ).flattened()

    colored_circuit = stim.Circuit()
    for instruction in circuit:
        if instruction.name == "DETECTOR":
            x, y, t = instruction.gate_args_copy()
            colored_circuit.append(
                "DETECTOR", instruction.targets_copy(), [x, y, t, (y + t) % 3]
            )
        else:
            colored_circuit.append(instruction)

    if convert_to_cz:
        colored_circuit = gen.transpile_to_z_basis_interaction_circuit(colored_circuit)

    if noise is not None:
        colored_circuit = noise.noisy_circuit(colored_circuit)

    return colored_circuit
