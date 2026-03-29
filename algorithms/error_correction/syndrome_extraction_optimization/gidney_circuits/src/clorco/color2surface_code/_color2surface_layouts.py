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

import gen
from clorco.color_code._superdense_planar_color_code_circuits import (
    make_color_code_layout_for_superdense,
)
from clorco.surface_code._surface_code_layouts import make_surface_code_layout


def rgb2xyz(patch: gen.Patch, basis: str) -> gen.Patch:
    return gen.Patch(
        [
            gen.Tile(
                bases="XYZXYZ"[int(tile.extra_coords[0])],
                ordered_data_qubits=tile.ordered_data_qubits,
                measurement_qubit=tile.measurement_qubit,
                extra_coords=tile.extra_coords,
            )
            for tile in patch.tiles
            if tile.basis == basis
        ]
    )


def make_color2surface_layout(
    *,
    base_data_width: int,
) -> gen.StabilizerCode:
    color_patch = make_color_code_layout_for_superdense(
        base_data_width=base_data_width,
    ).patch
    surface_patch = make_surface_code_layout(
        width=base_data_width,
        height=base_data_width,
    ).patch
    surface_patch = gen.Patch(
        tile for tile in surface_patch.tiles if tile.measurement_qubit.imag != 0.5
    )
    surface_patch = surface_patch.with_transformed_coords(
        lambda e: (e - base_data_width * 1j) * 2 + (2j - 2 if e.imag <= 0 else 0)
    )
    surface_patch = gen.Patch(
        tile for tile in surface_patch.tiles if tile.measurement_qubit.imag < -2
    )
    surface_patch = surface_patch.with_transformed_coords(
        lambda e: e + (e.real % 4 == 2 and e.imag == 0)
    )

    # Mix up the coloring a bit to keep things interesting for the decoder.
    surface_patch = gen.Patch(
        gen.Tile(
            measurement_qubit=tile.measurement_qubit,
            ordered_data_qubits=tile.ordered_data_qubits,
            bases=tile.bases,
            extra_coords=(
                tile.extra_coords
                if tile.measurement_qubit.real != 5
                else [2 + 3 * (tile.basis == "Z")]
            ),
        )
        for tile in surface_patch.tiles
    )

    dropped_tiles = [
        tile
        for tile in color_patch.tiles
        if tile.measurement_qubit.imag == 0
        if tile.basis == "X"
    ]
    color_patch = gen.Patch(set(color_patch.tiles) - set(dropped_tiles))
    patch = gen.Patch(
        [
            *color_patch.tiles,
            *surface_patch.tiles,
            *[
                gen.Tile(
                    measurement_qubit=(m := tile.measurement_qubit) - 0.5j,
                    ordered_data_qubits=[
                        m - 1 - 2j,
                        m + 1 - 2j,
                        m - 1,
                        m + 2,
                        m + 1j,
                        m + 1j + 1,
                    ],
                    bases="X",
                    extra_coords=[0],
                )
                for tile in dropped_tiles
            ],
            *[
                gen.Tile(
                    measurement_qubit=(m := tile.measurement_qubit) - 0.75j,
                    ordered_data_qubits=[
                        m + 1 - 2j,
                        m + 3 - 2j,
                        m + 2,
                        m + 3,
                    ],
                    bases="Z",
                    extra_coords=[5],
                )
                for tile in dropped_tiles
            ],
            gen.Tile(
                measurement_qubit=-1 - 1j,
                ordered_data_qubits=[0, -2j],
                bases="Z",
                extra_coords=[5],
            ),
        ]
    )

    min_y = min(q.imag for q in patch.data_set)
    max_x_per_y = {}
    for q in patch.data_set:
        if q.imag > 0 and q.imag % 3 == 1:
            continue
        cur_max = max_x_per_y.setdefault(q.imag, q.real)
        if q.real > cur_max:
            max_x_per_y[q.imag] = q.real
    code = gen.StabilizerCode(
        patch=patch,
        observables_x=[
            gen.PauliString({k * 1j + v: "X" for k, v in max_x_per_y.items()})
        ],
        observables_z=[
            gen.PauliString({q: "Z" for q in patch.data_set if q.imag == min_y})
        ],
    )
    code = code.with_transformed_coords(lambda e: e - min_y * 1j)
    return code
