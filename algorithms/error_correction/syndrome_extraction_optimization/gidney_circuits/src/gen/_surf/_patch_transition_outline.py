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
from typing import Iterable

import gen
from gen._surf._closed_curve import ClosedCurve
from gen._surf._geo import int_points_inside_polygon_set
from gen._surf._path_outline import PathOutline


class PatchTransitionOutline:
    """An outline of what's happening during a transition between two patches.

    This class stores data encoding a floor or ceiling in a 3d topological
    spacetime diagram. It encodes the details of time boundaries.
    """

    def __init__(
        self,
        *,
        observable_deltas: dict[str, PathOutline],
        data_boundary_planes: Iterable[ClosedCurve],
    ):
        self.observable_deltas = observable_deltas
        self.data_boundary_planes = tuple(data_boundary_planes)
        for data_boundary_plane in self.data_boundary_planes:
            if data_boundary_plane.basis is None:
                raise ValueError(f"Not a uniform basis: {data_boundary_plane=}")

    @staticmethod
    def empty() -> "PatchTransitionOutline":
        return PatchTransitionOutline(observable_deltas={}, data_boundary_planes=[])

    def __bool__(self) -> bool:
        return bool(self.observable_deltas) or bool(self.data_boundary_planes)

    @functools.cached_property
    def patch(self) -> gen.Patch:
        tiles = []
        for b, qs in [
            ("X", self.data_x_set),
            ("Y", self.data_y_set),
            ("Z", self.data_z_set),
        ]:
            for q in qs:
                tiles.append(
                    gen.Tile(bases=b, measurement_qubit=q, ordered_data_qubits=[q])
                )
        return gen.Patch(tiles)

    def iter_control_points(self) -> Iterable[complex]:
        for curve in self.data_boundary_planes:
            yield from curve.points
        for segment_sets in self.observable_deltas.values():
            for a, b, _ in segment_sets.segments:
                yield a
                yield b

    @functools.cached_property
    def data_basis_map(self) -> dict[complex, str]:
        result = {}
        for q in self.data_x_set:
            result[q] = "X"
        for q in self.data_y_set:
            result[q] = "Y"
        for q in self.data_z_set:
            result[q] = "Z"
        return result

    @functools.cached_property
    def data_set(self) -> frozenset[complex]:
        curves = []
        for plane in self.data_boundary_planes:
            curves.append(plane.points)
        return frozenset(int_points_inside_polygon_set(curves, include_boundary=True))

    @functools.cached_property
    def data_x_set(self) -> frozenset[complex]:
        curves = []
        for plane in self.data_boundary_planes:
            if plane.basis == "X":
                curves.append(plane.points)
        return frozenset(int_points_inside_polygon_set(curves, include_boundary=True))

    @functools.cached_property
    def data_y_set(self) -> frozenset[complex]:
        curves = []
        for plane in self.data_boundary_planes:
            if plane.basis == "Y":
                curves.append(plane.points)
        return frozenset(int_points_inside_polygon_set(curves, include_boundary=True))

    @functools.cached_property
    def data_z_set(self) -> frozenset[complex]:
        curves = []
        for plane in self.data_boundary_planes:
            if plane.basis == "Z":
                curves.append(plane.points)
        return frozenset(int_points_inside_polygon_set(curves, include_boundary=True))
