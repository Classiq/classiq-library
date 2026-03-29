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

import gen


def _rect_to_hex_transform(c: complex) -> complex:
    r = c.real
    i = c.imag
    f = 0.6
    if (c.real + c.imag + 1) % 2 == 0:
        r += 0.5 * f
    i *= f
    return r + 1j * i


def make_color_code_layout(
    *,
    base_width: int,
    spurs: Literal["smooth", "midout", "midout_readout_line_constraint"],
    coord_style: Literal["rect", "hex"],
    single_rgb_layer_instead_of_actual_code: bool,
) -> gen.StabilizerCode:
    """Creates a color code over a truncated hexagonal tiling.

    Args:
        base_width: The width of the base of the triangle.
        spurs: Determines if there are jagged bits sticking out the sides of the code.
            'smooth': No spurs. The normal color code.
            'midout': Include the spurs needed for the midout circuit to run cleanly.
            'midout_readout_line_constraint': Extend the midout spurs so that there is
                a subgrid of qubits that can all be simultaneously measured, This is
                relevant if hardware has the constraint that qubits share a readout
                line and measuring one qubit on the line hurts the coherence of the
                others.
        coord_style: Determines the qubit layout.
            'rect': Lay qubits onto a square grid, with stabilizers forming rectangles.
            'hex': Lay qubits onto a (nearly) hexagonal grid, with stabilizers forming hexagons.
        single_rgb_layer_instead_of_actual_code: When False, this method returns an actual color
            code. When True, the method will instead return a single layer of stabilizers with
            bases XYZ corresponding to the RGB coloring. This is not the actual code because it's
            only one layer instead of two layers, but it draws a lot better.

    Returns:
        A StabilizerCode object defining the stabilizers and X/Z observable pair of the code.
    """

    half = base_width // 2 - 1
    w = 2 * half + 1
    h = 3 * half + 2

    tiles = []
    for x in range(w + 1):
        if x > half:
            start_y = (x - half) * 3 - 2
        else:
            start_y = h - x * 3 - 2
        assert start_y >= 0
        if x % 2 or spurs == "smooth":
            start_y += 2
        for y in range(start_y, h, 2):
            q = x + 1j * y
            order = [0, 1j, 2j, 1 + 2j, 1 + 1j, 1]
            if q.real % 2 == 0:
                order = [e.conjugate() + 2j for e in order]
                m = q + 1
            else:
                m = q + 2j
            tiles.append(
                gen.Tile(
                    bases="XYZ"[int(q.imag % 3)],
                    measurement_qubit=m,
                    ordered_data_qubits=[q + d for d in order],
                    extra_coords=[q.imag % 3],
                )
            )
        if x % 2 == 0:
            q = x + 1j * h
            tiles.append(
                gen.Tile(
                    bases="Z",
                    measurement_qubit=q + 1,
                    ordered_data_qubits=[q + d for d in [1j, 0, 1, 1 + 1j]],
                    extra_coords=[2],
                )
            )
            q = x + 1j * start_y
            if x <= half:
                if spurs == "midout_readout_line_constraint":
                    tiles.append(
                        gen.Tile(
                            bases="Y",
                            measurement_qubit=q + 1j - 1,
                            ordered_data_qubits=[q + d for d in [0, 1j - 1, 1j, -1]],
                            extra_coords=[1],
                        )
                    )
                    tiles.append(
                        gen.Tile(
                            bases="X",
                            measurement_qubit=q - 1,
                            ordered_data_qubits=[q + d for d in [-1, 1j - 1]],
                            extra_coords=[0],
                        )
                    )
                else:
                    if spurs == "midout":
                        tiles.append(
                            gen.Tile(
                                bases="Z",
                                measurement_qubit=q + 1j,
                                ordered_data_qubits=[q + d for d in [1j, 0]],
                                extra_coords=[2],
                            )
                        )
            else:
                q += 1
                if spurs == "midout":
                    tiles.append(
                        gen.Tile(
                            bases="X",
                            measurement_qubit=q + 1j,
                            ordered_data_qubits=[q + d for d in [0, 1j]],
                            extra_coords=[0],
                        )
                    )
        if x % 2 == 1 or spurs == "smooth":
            q = x + 1j * start_y - 2j
            if x <= half:
                tiles.append(
                    gen.Tile(
                        bases="X",
                        measurement_qubit=q + 2j,
                        ordered_data_qubits=[q + d for d in [2j, 1 + 2j, 1 + 1j, 1]],
                        extra_coords=[0],
                    )
                )
            else:
                tiles.append(
                    gen.Tile(
                        bases="Y",
                        measurement_qubit=q + 2j,
                        ordered_data_qubits=[q + d for d in [0, 1j, 2j, 1 + 2j]],
                        extra_coords=[1],
                    )
                )
    patch = gen.Patch(tiles).with_transformed_coords(lambda e: h * 1j + w - e + 1 + 2j)
    if coord_style == "hex":
        patch = patch.with_transformed_coords(_rect_to_hex_transform)
    for tile in patch.tiles:
        assert "XYZ".index(tile.basis) == tile.extra_coords[0]
    if not single_rgb_layer_instead_of_actual_code:
        patch = gen.Patch(
            gen.Tile(
                bases=basis,
                measurement_qubit=tile.measurement_qubit
                + (0.125 if basis == "Z" else 0),
                ordered_data_qubits=tile.ordered_data_qubits,
                extra_coords=[tile.extra_coords[0] + (3 if basis == "Z" else 0)],
            )
            for tile in patch.tiles
            for basis in "XZ"
        )

    return gen.StabilizerCode(
        patch=patch,
        observables_x=[gen.PauliString({q: "X" for q in patch.data_set})],
        observables_z=[gen.PauliString({q: "Z" for q in patch.data_set})],
    )


def make_toric_color_code_layout(
    *,
    width: int,
    height: int,
    ablate_into_matchable_code: bool = False,
    square_coords: bool = False,
) -> gen.StabilizerCode:
    """Makes a toric color code layout with two ancilla qubits per hex on a square grid."""
    assert width % 6 == 0, (width, height)
    assert height % 4 == 0, (width, height)
    assert width > 0 and height > 0, (width, height)

    def wrap(q: complex) -> complex:
        return (q.real % width) + (q.imag % height) * 1j

    tiles = []
    for y in range(0, height, 2):
        for x in range((y // 2) % 2, width, 2):
            q = x + 1j * y
            order = [-1j, +1, +1 + 1j, +2j, -1 + 1j, -1]
            rgb = x % 3
            if rgb != 0 or not ablate_into_matchable_code:
                tiles.append(
                    gen.Tile(
                        bases="X",
                        measurement_qubit=wrap(q + 0),
                        ordered_data_qubits=[wrap(q + d) for d in order],
                        extra_coords=[rgb],
                    )
                )
            if rgb != 2 or not ablate_into_matchable_code:
                tiles.append(
                    gen.Tile(
                        bases="Z",
                        measurement_qubit=wrap(q + 1j),
                        ordered_data_qubits=[wrap(q + d) for d in order],
                        extra_coords=[rgb + 3],
                    )
                )

    patch = gen.Patch(tiles)
    obs_x1 = gen.PauliString({q: "X" for q in patch.data_set if q.real == 0})
    obs_z1 = gen.PauliString(
        {q: "Z" for q in patch.data_set if q.imag in [1, 2] and q.real % 3 != 2}
    )
    obs_x2 = gen.PauliString(
        {
            q: "X"
            for q in patch.data_set
            if q.imag in [3, 4 % height] and q.real % 3 != 0
        }
    )
    obs_z2 = gen.PauliString({q: "Z" for q in patch.data_set if q.real == 2})

    result = gen.StabilizerCode(
        patch=patch,
        observables_x=[obs_x1, obs_x2],
        observables_z=[obs_z1, obs_z2],
    )
    if square_coords:

        def hex_to_rect(c: complex):
            r = c.real
            i = c.imag
            if i == height - 1:
                i = 0
            else:
                if i % 4 == 0:
                    i -= 1
                elif i % 4 == 1:
                    i += 1
                i -= i // 4 * 2
                i -= 1
            return r + 1j * i

        result = result.with_transformed_coords(hex_to_rect)

    return result


def _rect_to_oct_transform(c: complex) -> complex:
    r = c.real
    i = c.imag
    r *= 2
    if (i + 1) // 2 % 2 == 0:
        r -= 1
        r += (r // 2) % 2
        r += 1
    else:
        r += (r // 2) % 2

    f = 0.1
    ib = f * (+1 if i % 2 == 0 else -1)
    rb = f * (+1 if r % 2 == 0 else -1)
    i += ib
    r += rb
    return r + 1j * i


def make_color_code_layout_488(
    *,
    base_width: int,
    spurs: Literal["smooth", "midout", "midout_readout_line_constraint"],
    coord_style: Literal["rect", "oct"],
    single_rgb_layer_instead_of_actual_code: bool,
) -> gen.StabilizerCode:
    """Makes a bounded oct/square patch with some spandrels to allow the inline cycle to work.

    Args:
        base_width: The width of the base of the triangle. Must be odd.
        spurs: Determines if there are jagged bits sticking out the sides of the code.
            'smooth': No spurs. The normal color code.
            'midout': Include the spurs needed for the midout circuit to run cleanly.
            'midout_readout_line_constraint': Extend the midout spurs so that there is
                a subgrid of qubits that can all be simultaneously measured, This is
                relevant if hardware has the constraint that qubits share a readout
                line and measuring one qubit on the line hurts the coherence of the
                others.
        coord_style: Determines the qubit layout.
            'rect': Lay qubits onto a square grid, with stabilizers forming rectangles
                and squares.
            'oct': Lay qubits onto a (nearly) 488 tiling, with stabilizers forming
                octagons and squares.
        single_rgb_layer_instead_of_actual_code: When False, this returns an actual color code.
            When True, this returns a single layer of stabilizers with bases XYZ corresponding
            to the RGB coloring. This is not the actual code because it's only one layer instead
            of two layers, but it draws better.

    Returns:
        A StabilizerCode object defining the stabilizers and X/Z observable pair of the code.
    """

    assert base_width % 2 == 1
    w = base_width
    half = w // 2

    tiles = []
    for x in range(1, w, 2):
        q = x
        tiles.append(
            gen.Tile(
                bases="Z",
                measurement_qubit=q + 0.5,
                ordered_data_qubits=[q + d for d in [1j, 0, 1, 1 + 1j]],
                extra_coords=[2],
            )
        )
    for x in range(0, half, 2):
        q = x + 2j * x
        if spurs == "midout_readout_line_constraint":
            tiles.append(
                gen.Tile(
                    bases="X",
                    measurement_qubit=q + 2j - 0.5,
                    ordered_data_qubits=[q + d for d in [1j, 2j, -1 + 2j, -1 + 1j]],
                    extra_coords=[0],
                )
            )
            tiles.append(
                gen.Tile(
                    bases="Y",
                    measurement_qubit=q + 1j - 1.5,
                    ordered_data_qubits=[q + d for d in [-1 + 2j, -1 + 1j]],
                    extra_coords=[1],
                )
            )
        else:
            if spurs != "smooth":
                tiles.append(
                    gen.Tile(
                        bases="X",
                        measurement_qubit=q + 2j - 0.5,
                        ordered_data_qubits=[q + d for d in [1j, 2j]],
                        extra_coords=[0],
                    )
                )
        tiles.append(
            gen.Tile(
                bases="Y",
                measurement_qubit=q + 0.5 + 1j,
                ordered_data_qubits=[
                    q + d
                    for d in (
                        [0, 1 + 1j, 1, 1 + 1j, 1 + 2j]
                        if spurs == "smooth"
                        else [2j, 1j, 0, 1j, 1 + 1j, 1, 1 + 1j, 1 + 2j]
                    )
                ],
                extra_coords=[1],
            )
        )
    for x in range(0, half - 1, 2):
        q = w - x + 2j * x + 2j - 1
        if spurs == "midout_readout_line_constraint":
            tiles.append(
                gen.Tile(
                    bases="X",
                    measurement_qubit=q + 0.5 + 1j,
                    ordered_data_qubits=[q + d for d in [2j, 1j, 1 + 1j, 1 + 2j]],
                    extra_coords=[0],
                )
            )
            tiles.append(
                gen.Tile(
                    bases="Z",
                    measurement_qubit=q + 1.5 + 2j,
                    ordered_data_qubits=[q + d for d in [1 + 1j, 1 + 2j]],
                    extra_coords=[2],
                )
            )
        elif spurs != "smooth":
            tiles.append(
                gen.Tile(
                    bases="X",
                    measurement_qubit=q + 1j + 0.5,
                    ordered_data_qubits=[q + d for d in [1j, 2j]],
                    extra_coords=[0],
                )
            )
        q -= 1
        tiles.append(
            gen.Tile(
                bases="Z",
                measurement_qubit=q + 2j + 0.5,
                ordered_data_qubits=[
                    q + d
                    for d in (
                        [0, 1j, 2j, 1]
                        if spurs == "smooth"
                        else [0, 1j, 2j, 1 + 2j, 1 + 1j, 1]
                    )
                ],
                extra_coords=[2],
            )
        )

    for offset in range(0, w, 2):
        for x in range(0, half - offset // 2, 1):
            q = x + 2j * x + 1 + 1j + offset
            tiles.append(
                gen.Tile(
                    bases="X",
                    measurement_qubit=q + 0.5 + ((x + 1) % 2) * 1j,
                    ordered_data_qubits=[
                        q + d
                        for d in (
                            [0, 1j, 1 + 1j, 1] if x % 2 == 0 else [1j, 0, 1, 1 + 1j]
                        )
                    ],
                    extra_coords=[0],
                )
            )
    for offset in range(0, w, 2):
        for x in range(0, half - offset // 2 - 1, 2):
            q = x + 2j * x + 2 + offset
            tiles.append(
                gen.Tile(
                    bases="Y",
                    measurement_qubit=q + 0.5 + 1j,
                    ordered_data_qubits=[
                        q + d
                        for d in [3j, 2j, 1j, 0, 1j, 1 + 1j, 1, 1 + 1j, 1 + 2j, 1 + 3j]
                    ],
                    extra_coords=[1],
                )
            )
    for offset in range(0, w, 2):
        for x in range(0, half - offset // 2 - 2, 2):
            q = x + 2j * x + 3 + 2j + offset
            tiles.append(
                gen.Tile(
                    bases="Z",
                    measurement_qubit=q + 2j + 0.5,
                    ordered_data_qubits=[
                        q + d
                        for d in [
                            3j,
                            2j,
                            1j,
                            0,
                            1j,
                            2j,
                            1 + 2j,
                            1 + 1j,
                            1,
                            1 + 1j,
                            1 + 2j,
                            1 + 3j,
                        ]
                    ],
                    extra_coords=[2],
                )
            )

    patch = gen.Patch(
        [
            gen.Tile(
                bases=tile.bases,
                measurement_qubit=tile.measurement_qubit
                + -0.5
                * (
                    1
                    if (tile.measurement_qubit.real % 2 == 0.5)
                    ^ (spurs == "midout_readout_line_constraint")
                    else -1
                ),
                ordered_data_qubits=tile.ordered_data_qubits,
                extra_coords=tile.extra_coords,
            )
            for tile in tiles
        ]
    )
    if coord_style == "oct":
        patch = patch.with_transformed_coords(_rect_to_oct_transform)
    for tile in patch.tiles:
        assert "XYZ".index(tile.basis) == tile.extra_coords[0]
    if not single_rgb_layer_instead_of_actual_code:
        patch = gen.Patch(
            gen.Tile(
                bases=basis,
                measurement_qubit=tile.measurement_qubit
                + (0.125 if basis == "Z" else 0),
                ordered_data_qubits=tile.ordered_data_qubits,
                extra_coords=[tile.extra_coords[0] + (3 if basis == "Z" else 0)],
            )
            for tile in patch.tiles
            for basis in "XZ"
        )
    return gen.StabilizerCode(
        patch=patch,
        observables_x=[gen.PauliString({q: "X" for q in patch.data_set})],
        observables_z=[gen.PauliString({q: "Z" for q in patch.data_set})],
    )
