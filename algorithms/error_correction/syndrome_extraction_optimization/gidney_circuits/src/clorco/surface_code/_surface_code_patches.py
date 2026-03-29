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

import functools
from typing import Iterable, Callable

import gen

DIRS = tuple((0.5 + 0.5j) * 1j**d for d in range(4))
DR, DL, UL, UR = DIRS
ORDER_S = [UR, UL, DR, DL]
ORDER_N = [UR, DR, UL, DL]


def surface_code_patch(
    *,
    possible_data_qubits: Iterable[complex],
    basis: Callable[[complex], str],
    is_boundary_x: Callable[[complex], bool],
    is_boundary_z: Callable[[complex], bool],
    order_func: Callable[[complex], Iterable[complex | None]],
    dirs: Iterable[complex] = DIRS,
) -> gen.Patch:
    possible_data_qubits = set(possible_data_qubits)
    possible_measure_qubits = {q + d for q in possible_data_qubits for d in dirs}
    measure_qubits = {
        m
        for m in possible_measure_qubits
        if sum(m + d in possible_data_qubits for d in dirs) > 1
        if is_boundary_x(m) <= (basis(m) == "X")
        if is_boundary_z(m) <= (basis(m) == "Z")
    }
    data_qubits = {
        q
        for q in possible_data_qubits
        if sum(q + d in measure_qubits for d in dirs) > 1
    }

    tiles = []
    for m in measure_qubits:
        tiles.append(
            gen.Tile(
                bases=basis(m),
                measurement_qubit=m,
                ordered_data_qubits=[
                    m + d if d is not None and m + d in data_qubits else None
                    for d in order_func(m)
                ],
            )
        )
    return gen.Patch(tiles)


def rectangular_surface_code_patch(
    *,
    width: int,
    height: int,
    top_basis: str,
    bot_basis: str,
    left_basis: str,
    right_basis: str,
    order_func: Callable[[complex], Iterable[complex | None]],
) -> gen.Patch:
    def is_boundary(m: complex, *, b: str) -> bool:
        if top_basis == b and m.imag == -0.5:
            return True
        if left_basis == b and m.real == -0.5:
            return True
        if bot_basis == b and m.imag == height - 0.5:
            return True
        if right_basis == b and m.real == width - 0.5:
            return True
        return False

    return surface_code_patch(
        possible_data_qubits=[x + 1j * y for x in range(width) for y in range(height)],
        basis=gen.checkerboard_basis,
        is_boundary_x=functools.partial(is_boundary, b="X"),
        is_boundary_z=functools.partial(is_boundary, b="Z"),
        order_func=order_func,
    )


def rectangular_unrotated_surface_code_patch(
    *,
    width: int,
    height: int,
    order_func: Callable[[complex], Iterable[complex | None]],
) -> gen.Patch:
    return surface_code_patch(
        possible_data_qubits=[
            x + 1j * y
            for x in range(width * 2 - 1)
            for y in range(height * 2 - 1)
            if x % 2 == y % 2
        ],
        basis=lambda m: "X" if m.imag % 2 == 0 else "Z",
        is_boundary_x=lambda _: False,
        is_boundary_z=lambda _: False,
        order_func=order_func,
        dirs=[1, -1, 1j, -1j],
    )


def make_ztop_yboundary_patch(*, distance: int) -> gen.Patch:
    def order_func(m: complex) -> list[complex]:
        if m.real > m.imag and False:
            if gen.checkerboard_basis(m) == "X":
                return ORDER_N
            else:
                return ORDER_S
        else:
            if gen.checkerboard_basis(m) == "X":
                return ORDER_S
            else:
                return ORDER_N

    return rectangular_surface_code_patch(
        width=distance,
        height=distance,
        top_basis="Z",
        right_basis="X",
        bot_basis="X",
        left_basis="Z",
        order_func=order_func,
    )


def make_xtop_qubit_patch(*, diameter: int) -> gen.Patch:
    def order_func(m: complex) -> list[complex]:
        if gen.checkerboard_basis(m) == "X":
            return ORDER_S
        else:
            return ORDER_N

    return rectangular_surface_code_patch(
        width=diameter,
        height=diameter,
        top_basis="X",
        right_basis="Z",
        bot_basis="X",
        left_basis="Z",
        order_func=order_func,
    )
