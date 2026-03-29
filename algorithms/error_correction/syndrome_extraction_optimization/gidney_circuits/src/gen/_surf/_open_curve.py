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

from typing import Iterable, Literal

from gen._surf._geo import int_points_on_line


class OpenCurve:
    """A contiguous series of line segments between integer coordinates aligned at 45 degree angles.

    Each line segment has an associated basis (X or Z).
    """

    def __init__(
        self, *, points: Iterable[complex], bases: Iterable[Literal["X", "Z"]]
    ):
        self.points = list(points)
        self.bases = list(bases)
        if len(self.points) < 2:
            raise ValueError(f"len({self.points=}) < 2")
        if len(self.points) != len(self.bases) + 1:
            raise ValueError(f"len({self.points=}) != len({self.bases=}) + 1")

    @staticmethod
    def from_sequence(
        points_and_bases: Iterable[Literal["X", "Z"] | complex | int | float]
    ):
        points_and_bases = list(points_and_bases)

        points = []
        bases: list[Literal["X", "Z"]] = []

        next_basis = None
        for e in points_and_bases:
            if e == "X" or e == "Z":
                next_basis = e
            elif isinstance(e, (int, float, complex)):
                if points:
                    if points[-1] == e:
                        continue
                    if next_basis is None:
                        raise ValueError(
                            f"Specify basis before second point in {points_and_bases=}"
                        )
                    bases.append(next_basis)
                points.append(e)
            else:
                raise NotImplementedError(f"{e=}")
        return OpenCurve(points=points, bases=bases)

    def to_sequence(self) -> list[Literal["X", "Z"] | complex]:
        out = []
        for k in range(len(self.bases)):
            out.append(self.points[k])
            out.append(self.bases[k])
        out.append(self.points[-1])
        return out

    def __len__(self):
        """Returns the number of line segments making up the curve."""
        return len(self.points)

    def __getitem__(self, item: int) -> tuple[str, complex, complex]:
        assert isinstance(item, int)
        return self.bases[item], self.points[item], self.points[item + 1]

    def offset_by(self, offset: complex) -> "OpenCurve":
        """Translates the curve's location by translating all of its line segments."""
        return OpenCurve(points=[p + offset for p in self.points], bases=self.bases)

    @property
    def basis(self) -> Literal["X", "Z"] | None:
        b = set(self.bases)
        if len(b) == 1:
            return next(iter(b))
        return None

    def int_points_set(self) -> set[complex]:
        """Returns the set of integer coordinates along the line segments of the curve."""
        return set(self.int_points_in_order())

    def int_points_in_order(self) -> list[complex]:
        """Lists the integer coordinates along the line segments of the curve, in order."""
        points = []
        for k in range(len(self.bases)):
            a = self.points[k]
            b = self.points[k + 1]
            for p in int_points_on_line(a, b):
                if len(points) == 0 or points[-1] != p:
                    points.append(p)
        return points

    def __eq__(self, other):
        if not isinstance(other, OpenCurve):
            return NotImplemented
        return self.points == other.points and self.bases == other.bases

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return f"OpenCurve.from_sequence({self.to_sequence()!r})"
