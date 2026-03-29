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

import pathlib
from typing import Iterable, Literal, Callable, TYPE_CHECKING

from gen._core._patch import Patch
from gen._surf._geo import (
    int_travel_points_on_polygon_boundary,
    int_points_on_line,
    int_points_inside_polygon_set,
    half_int_points_inside_int_polygon_set,
)
from gen._core._util import min_max_complex

if TYPE_CHECKING:
    import gen


class ClosedCurve:
    """A closed series of line segments between integer coordinates aligned at 45 degree angles.

    Each line segment has an associated basis (X or Z).
    """

    def __init__(
        self, *, points: Iterable[complex] = (), bases: Iterable[Literal["X", "Z"]] = ()
    ):
        self.points = tuple(points)
        self.bases = tuple(bases)

    def to_patch_outline(self) -> "gen.PatchOutline":
        from gen._surf._patch_outline import PatchOutline

        return PatchOutline([self])

    def to_patch(
        self,
        *,
        rel_order_func: Callable[[complex], Iterable[complex]],
    ) -> Patch:
        return self.to_patch_outline().to_patch(rel_order_func=rel_order_func)

    def write_svg(
        self,
        path: str | pathlib.Path,
    ) -> None:
        return self.to_patch_outline().write_svg(path)

    def with_basis(self, basis: Literal["X", "Z"]) -> "ClosedCurve":
        return ClosedCurve(points=self.points, bases=[basis] * len(self.bases))

    @staticmethod
    def from_cycle(point_or_basis: Iterable[Literal["X", "Z"] | complex | int | float]):
        point_or_basis = list(point_or_basis)
        cur_basis: Literal["X", "Z", "U"] = "U"
        cur_basis_used = True
        points = []
        bases: list[Literal["X", "Z", "U"]] = []
        for e in point_or_basis:
            if e == "X" or e == "Z":
                if not cur_basis_used:
                    assert cur_basis == e, "Basis disagreement"
                cur_basis = e
                cur_basis_used = False
            elif isinstance(e, (int, float, complex)):
                cur_basis_used = True
                if points and points[-1] == e:
                    continue
                points.append(e)
                bases.append(cur_basis)
            else:
                raise NotImplementedError(f"{e=}")
        assert cur_basis != "U"
        if not cur_basis_used:
            assert bases[0] == "U" or bases[0] == cur_basis

        for k in range(len(bases)):
            if bases[k] == "U":
                bases[k] = cur_basis
        while points[-1] == points[0]:
            points.pop()
            bases.pop()

        return ClosedCurve(points=points, bases=bases)

    def to_cycle(self) -> list[Literal["X", "Z"] | complex]:
        out = []
        for k in range(len(self.points)):
            out.append(self.bases[k])
            out.append(self.points[k])
        out.append(self.bases[0])
        return out

    def med(self) -> complex:
        """Returns the center of the axis-aligned bounding box of the curve."""
        a, b = min_max_complex(self.points)
        return (a.real + b.real) // 2 + (a.imag + b.imag) // 2 * 1j

    def __len__(self):
        """Returns the number of line segments making up the curve."""
        return len(self.points)

    def __getitem__(self, item: int) -> tuple[str, complex, complex]:
        assert isinstance(item, int)
        return self.bases[item], self.points[item - 1], self.points[item]

    def segment_indices_intersecting(self, points: set[complex]) -> list[int]:
        """Returns the indices of line segments intersecting the given point set."""
        hits = []
        for k in range(len(self.points)):
            a = self.points[k - 1]
            b = self.points[k]
            if any(e in points for e in int_points_on_line(a, b)):
                hits.append(k)
        return hits

    def offset_by(self, offset: complex) -> "ClosedCurve":
        """Translates the curve's location by translating all of its line segments."""
        return ClosedCurve(points=[p + offset for p in self.points], bases=self.bases)

    def interior_set(
        self, *, include_boundary: bool, half_ints: bool = False
    ) -> frozenset[complex]:
        if half_ints:
            return frozenset(
                half_int_points_inside_int_polygon_set(
                    curves=[self.points], include_boundary=include_boundary
                )
            )
        return frozenset(
            int_points_inside_polygon_set(
                [self.points], include_boundary=include_boundary
            )
        )

    def boundary_set(self) -> set[complex]:
        """Returns the set of integer coordinates along the line segments of the curve."""
        return set(int_travel_points_on_polygon_boundary(self.points))

    def boundary_travel(self) -> list[complex]:
        """Lists the integer coordinates along the line segments of the curve, in order."""
        return int_travel_points_on_polygon_boundary(self.points)

    def with_transformed_coords(
        self, coord_transform: Callable[[complex], complex]
    ) -> "ClosedCurve":
        return ClosedCurve(
            points=[coord_transform(e) for e in self.points],
            bases=self.bases,
        )

    @property
    def basis(self) -> Literal["X", "Z"] | None:
        b = set(self.bases)
        if len(b) == 1:
            return next(iter(b))
        return None

    def __eq__(self, other):
        if not isinstance(other, ClosedCurve):
            return NotImplemented
        return self.points == other.points and self.bases == other.bases

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return f"ClosedCurve.from_cycle({self.to_cycle()!r})"
