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


def make_toric_pyramid_code_layout(
    *,
    width: int,
    height: int,
) -> gen.StabilizerCode:
    assert width % 2 == 0
    assert height % 3 == 0

    def wrap(v: complex) -> complex:
        return (v.real % width) + 1j * (v.imag % height)

    tiles = []
    for x in range(width):
        for y in range(height):
            c = x + 1j * y
            b = "X" if x % 2 == 1 else "Z"
            tiles.append(
                gen.Tile(
                    bases=b,
                    ordered_data_qubits=[wrap(c + d) for d in [1, -1, 1j, -1j, 0]],
                    measurement_qubit=c,
                    extra_coords=[y % 3 + 3 * (b == "Z")],
                )
            )
    patch = gen.Patch(tiles)

    return gen.StabilizerCode(
        patch=patch,
        observables_x=[
            gen.PauliString(
                {q: "X" for q in patch.data_set if q.imag % 3 != 2 and q.real == 0}
            ),
            gen.PauliString(
                {q: "X" for q in patch.data_set if q.real % 2 == 1 and q.imag == 0}
            ),
        ],
        observables_z=[
            gen.PauliString(
                {q: "Z" for q in patch.data_set if q.real % 2 == 0 and q.imag == 0}
            ),
            gen.PauliString(
                {q: "Z" for q in patch.data_set if q.imag % 3 != 2 and q.real == 1}
            ),
        ],
    )


def make_planar_pyramid_code_layout(
    *,
    width: int,
    height: int,
) -> gen.StabilizerCode:
    tiles = []
    for x in range(-1, width + 1):
        for y in range(-1, height + 1):
            c = x + 1j * y
            b = "X" if x % 2 == 1 else "Z"
            qs: list[complex | None] = [c + d for d in [1, -1, 1j, -1j, 0]]
            drop_tile = False
            for k in range(len(qs)):
                q = qs[k]
                if not (0 <= q.real < width):
                    drop_tile |= b == "X"
                    qs[k] = None
                if not (0 <= q.imag < height):
                    drop_tile |= b == "Z"
                    qs[k] = None
            if drop_tile:
                continue

            tiles.append(
                gen.Tile(
                    bases=b,
                    ordered_data_qubits=qs,
                    measurement_qubit=c,
                    extra_coords=[y % 3 + 3 * (b == "Z")],
                )
            )
    patch = gen.Patch(tiles)

    return gen.StabilizerCode(
        patch=patch,
        observables_x=[
            gen.PauliString(
                {q: "X" for q in patch.data_set if q.imag % 3 != 2 and q.real == 0}
            ),
            gen.PauliString(
                {q: "X" for q in patch.data_set if q.imag % 3 != 0 and q.real == 0}
            ),
        ],
        observables_z=[
            gen.PauliString(
                {q: "Z" for q in patch.data_set if q.real % 2 == 0 and q.imag == 0}
            ),
            gen.PauliString(
                {q: "Z" for q in patch.data_set if q.real % 2 == 0 and q.imag == 2}
            ),
        ],
    )
