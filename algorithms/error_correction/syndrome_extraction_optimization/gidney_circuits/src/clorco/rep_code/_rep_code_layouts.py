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


def make_rep_code_layout(
    *,
    distance: int,
    coloring: str = "r",
    toric: bool = False,
    replace_basis_with_coloring=False,
) -> gen.StabilizerCode:
    """Creates a rotated surface code.

    Data qubits are at integer coordinates. Measure qubits are at half integer coordinates.

    Args:
        distance: The number of data qubits.
        coloring: A coloring pattern to use. Must be a non-empty string made up
            of the characters 'r', 'g', and 'b'. These are the colors given to
            the color code decoder, which can affect its internal representation
            but ideally should not affect its final answer.

            If the coloring is shorter than the number of data qubits, it will
            be repeated until it is longer.

            If the coloring is longer than the number of data qubits, it will be
            truncated.
        toric: Defaults to False. When True, an additional stabilizer is added
            comparing the leftmost qubit to the rightmost qubit.
        replace_basis_with_coloring: For debugging purposes. This causes the
            stabilizer basis to be XYZ=RGB instead of always Z, so that a
            drawing of the code shows the coloring.

    Returns:
        A StabilizerCode object defining the stabilizers and X/Z observable pair of the code.
    """
    assert distance > 1

    tiles = []
    color_indices = {
        "r": 3,
        "g": 4,
        "b": 5,
        "R": 3,
        "G": 4,
        "B": 5,
    }
    for x in range(distance - (0 if toric else 1)):
        c = color_indices[coloring[x % len(coloring)]]
        tiles.append(
            gen.Tile(
                ordered_data_qubits=[x, (x + 1) % distance],
                bases="XYZ"[c % 3] if replace_basis_with_coloring else "Z",
                measurement_qubit=x + 0.5,
                extra_coords=[c],
            )
        )
    patch = gen.Patch(tiles)

    return gen.StabilizerCode(
        patch=patch,
        observables_x=[],
        observables_z=[gen.PauliString({0: "Z"})],
    )
