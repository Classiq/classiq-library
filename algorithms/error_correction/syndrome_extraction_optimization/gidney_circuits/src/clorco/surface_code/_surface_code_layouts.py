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


def make_surface_code_layout(
    *,
    width: int,
    height: int,
) -> gen.StabilizerCode:
    """Creates a rotated surface code.

    Data qubits are at integer coordinates. Measure qubits are at half integer coordinates.

    Args:
        width: width of the patch measured in data qubits.
        height: height of the patch measured in data qubits.

    Returns:
        A StabilizerCode object defining the stabilizers and X/Z observable pair of the code.
    """
    tiles = []
    for x in range(-1, width + 1):
        for y in range(-1, height + 1):
            m = x + 1j * y + 0.5 + 0.5j
            b = "XZ"[(x + y) % 2]
            if not (0 < m.real < width - 1) and b == "X":
                continue
            if not (0 < m.imag < height - 1) and b == "Z":
                continue
            order = gen.Order_Z if b == "X" else gen.Order_ᴎ
            data_qubits = [m + d for d in order]
            tile = gen.Tile(
                ordered_data_qubits=[
                    (d if 0 <= d.real < width and 0 <= d.imag < height else None)
                    for d in data_qubits
                ],
                bases=b,
                measurement_qubit=m,
                extra_coords=["XZ".index(b) * 3 + (x % 2) * 2],
            )
            if sum(e is not None for e in tile.ordered_data_qubits) > 0:
                tiles.append(tile)
    patch = gen.Patch(tiles)

    return gen.StabilizerCode(
        patch=patch,
        observables_x=[
            gen.PauliString({q: "X" for q in patch.data_set if q.real == 0})
        ],
        observables_z=[
            gen.PauliString({q: "Z" for q in patch.data_set if q.imag == 0})
        ],
    )


def make_toric_surface_code_layout(
    *,
    width: int,
    height: int,
) -> gen.StabilizerCode:
    """Creates a rotated toric surface code.

    Data qubits are at integer coordinates. Measure qubits are at half integer coordinates.

    Args:
        width: width of the patch measured in data qubits.
        height: height of the patch measured in data qubits.

    Returns:
        A StabilizerCode object defining the stabilizers and X/Z observable pair of the code.
    """
    if width % 2 != 0 or height % 2 != 0:
        raise ValueError(f"{width=} and {height=} must be even")

    def wrap(c: complex) -> complex:
        return (c.real % width) + 1j * (c.imag % height)

    tiles = []
    for x in range(width):
        for y in range(height):
            m = wrap(x + 1j * y + 0.5 + 0.5j)
            b = "XZ"[(x + y) % 2]
            order = gen.Order_ᴎ if b == "X" else gen.Order_Z
            tiles.append(
                gen.Tile(
                    ordered_data_qubits=[wrap(m + d) for d in order],
                    bases=b,
                    measurement_qubit=m,
                    extra_coords=["XZ".index(b) * 3 + x % 2],
                )
            )
    patch = gen.Patch(tiles)
    return gen.StabilizerCode(
        patch=patch,
        observables_x=[
            gen.PauliString({q: "X" for q in patch.data_set if q.real == 0}),
            gen.PauliString({q: "X" for q in patch.data_set if q.imag == 0}),
        ],
        observables_z=[
            gen.PauliString({q: "Z" for q in patch.data_set if q.imag == 0}),
            gen.PauliString({q: "Z" for q in patch.data_set if q.real == 0}),
        ],
    )
