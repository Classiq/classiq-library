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
from typing import Iterable, Sequence, Literal

import gen
from gen._surf._geo import int_points_on_line
from gen._core._util import complex_key


class PathOutline:
    """A series of line segments between integer coordinates."""

    def __init__(self, segments: Iterable[tuple[complex, complex, Literal["X", "Z"]]]):
        canon_segments = []
        for a, c, b in segments:
            a, c = sorted([a, c], key=complex_key)
            canon_segments.append((a, c, b))
        self.segments = frozenset(canon_segments)

    @staticmethod
    def from_stops(
        basis: Literal["X", "Z"],
        stops: Sequence[complex],
        *,
        extra: Iterable[complex] = (),
    ) -> "PathOutline":
        assert len(stops) > 1
        segments = []
        for k in range(len(stops) - 1):
            segments.append((stops[k], stops[k + 1], basis))
        for e in extra:
            segments.append((e, e, basis))
        return PathOutline(segments)

    def offset_by(self, offset: complex) -> "PathOutline":
        return PathOutline((a + offset, b + offset, c) for a, b, c in self.segments)

    def basis(self) -> str | None:
        bases = {c for _, _, c in self.segments}
        if len(bases) != 1:
            return None
        return next(iter(bases))

    def to_pauli_string(self) -> gen.PauliString:
        b = self.basis()
        assert b is not None
        return gen.PauliString({q: b for q in self.int_point_set})

    @functools.cached_property
    def int_point_set(self) -> set[complex]:
        return {p for a, b, _ in self.segments for p in int_points_on_line(a, b)}

    @property
    def end_point_set(self) -> frozenset[complex]:
        end_points = set()
        for a, b, _ in self.segments:
            end_points ^= {a, b}
        return frozenset(end_points)

    @property
    def end_point_set_including_elbows(self) -> frozenset[complex]:
        end_points = set()
        for a, b, _ in self.segments:
            end_points.add(a)
            end_points.add(b)
        return frozenset(end_points)

    def __eq__(self, other):
        if not isinstance(other, PathOutline):
            return NotImplemented
        return self.segments == other.segments

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return f"SegmentSet({self.segments!r})"
