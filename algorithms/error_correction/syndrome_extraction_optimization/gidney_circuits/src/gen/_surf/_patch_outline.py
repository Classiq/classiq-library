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

import collections
import functools
import pathlib
from typing import Iterable, Callable, Union, Literal, TYPE_CHECKING

from gen._core import Patch, Tile, sorted_complex
from gen._surf._closed_curve import ClosedCurve
from gen._surf._css_observable_boundary_pair import CssObservableBoundaryPair
from gen._surf._geo import (
    int_points_on_line,
    int_points_inside_polygon_set,
    half_int_points_inside_int_polygon_set,
    int_point_disjoint_regions_inside_polygon_set,
)
from gen._surf._order import Order_Z, checkerboard_basis
from gen._util import write_file

if TYPE_CHECKING:
    from gen._surf._patch_transition_outline import PatchTransitionOutline


class PatchOutline:
    """Defines a surface code stabilizer configuration in terms of its boundaries."""

    def __init__(
        self,
        region_curves: Iterable[ClosedCurve],
        *,
        observables: Iterable[CssObservableBoundaryPair] = (),
    ):
        """
        Args:
            region_curves: The curves defining the boundaries of the patch.
                These curves should not intersect each other, but may be inside
                each other, creating interior voids or nested islands.
        """
        self.region_curves = tuple(region_curves)
        self.observables = tuple(observables)

    def iter_control_points(self) -> Iterable[complex]:
        for curve in self.region_curves:
            yield from curve.points

    def validate(self):
        if not self.observables:
            return
        boundary_xs = self.x_boundary_set
        boundary_zs = self.z_boundary_set

        for i in range(len(self.observables)):
            for j in range(len(self.observables)):
                pts_x = self.observables[i].x_obs.int_point_set
                pts_z = self.observables[j].z_obs.int_point_set
                does_commute = len(pts_x & pts_z) % 2 == 0
                should_commute = i != j
                if does_commute != should_commute:
                    raise ValueError(
                        f"Bad commutation relationship between X{i} and Z{j}: {pts_x=} vs {pts_z=}"
                    )

        for obs_pair in self.observables:
            for basis, obs in obs_pair:
                same_boundary_points = boundary_xs if basis == "X" else boundary_zs
                if obs.end_point_set - same_boundary_points:
                    raise ValueError(
                        f"Observable doesn't terminate on same-basis boundaries:  {basis=} {obs=}."
                    )
                if not (obs.int_point_set - same_boundary_points):
                    raise ValueError(
                        f"Observable is a stabilizer (only runs along same-basis boundaries): {basis=} {obs=}."
                    )

    @functools.cached_property
    def used_set(self) -> frozenset[complex]:
        return frozenset(self.interior_set(include_boundary=True))

    @functools.cached_property
    def x_boundary_set(self) -> frozenset[complex]:
        result = set()
        for curve in self.region_curves:
            for basis, a, b in curve:
                if basis == "X":
                    result |= set(int_points_on_line(a, b))
        return frozenset(result)

    @functools.cached_property
    def z_boundary_set(self) -> frozenset[complex]:
        result = set()
        for curve in self.region_curves:
            for basis, a, b in curve:
                if basis == "Z":
                    result |= set(int_points_on_line(a, b))
        return frozenset(result)

    @functools.cached_property
    def boundary_set(self) -> frozenset[complex]:
        """Returns the set of integer coordinates that are on any of the boundary curves."""
        result = set()
        for c in self.region_curves:
            result |= c.boundary_set()
        return frozenset(result)

    def interior_set(self, *, include_boundary: bool) -> set[complex]:
        """Returns the set of integer coordinates inside the bounded area.

        Args:
            include_boundary: Whether or not boundary points are considered part
                of the interior or not.
        """
        return int_points_inside_polygon_set(
            [c.points for c in self.region_curves], include_boundary=include_boundary
        )

    def disjoint_interiors(self, *, include_boundary: bool) -> dict[int, set[complex]]:
        """Groups the interior by connected component.

        Args:
            include_boundary: Whether or not boundary points are considered part
                of the interior or not.

        Returns:
            A (mask -> interior) dictionary where the mask is the set of curves
            the interior is within and the interior is a set of integer
            coordinates.
        """
        return int_point_disjoint_regions_inside_polygon_set(
            [c.points for c in self.region_curves], include_boundary=include_boundary
        )

    def fused(self, a: complex, b: complex) -> "PatchOutline":
        """Performs lattice surgery between the two segments intersected by the line from a to b.

        It is assumed that there are exactly two segments along the line from a to b.
        It is assumed that these two segments' endpoints are equal when perp-projecting
        onto the a-to-b vector.

        Returns:
            A boundary list containing the stitched result.
        """
        hits = []
        pts = set(int_points_on_line(a, b))
        for k in range(len(self.region_curves)):
            for e in self.region_curves[k].segment_indices_intersecting(pts):
                hits.append((k, e))
        if len(hits) != 2:
            raise NotImplementedError(f"len({hits=}) != 2")

        (c0, s0), (c1, s1) = sorted(hits)
        if c0 == c1:
            # creating an interior space
            c = c0
            v = self.region_curves[c]
            new_points = []
            new_bases = []
            fb = v.bases[s0 - 1]

            new_bases.extend(v.bases[:s0])
            new_points.extend(v.points[:s0])
            new_points.extend(v.points[s1:])
            new_bases.append(fb)
            new_bases.extend(v.bases[s1 + 1 :])

            interior_points = v.points[s0:s1]
            interior_bases = v.bases[s0:s1]

            return PatchOutline(
                [
                    *self.region_curves[:c],
                    ClosedCurve(points=new_points, bases=new_bases),
                    *self.region_curves[c + 1 :],
                    ClosedCurve(points=interior_points, bases=interior_bases),
                ]
            )
        else:
            # stitching two regions
            v0 = self.region_curves[c0]
            v1 = self.region_curves[c1]
            new_points = []
            new_bases = []
            fb = v0.bases[s0 - 1]

            new_bases.extend(v0.bases[:s0])
            new_points.extend(v0.points[:s0])

            new_points.extend(v1.points[s1:])
            new_bases.append(fb)
            new_bases.extend(v1.bases[s1 + 1 :])

            new_points.extend(v1.points[:s1])
            new_bases.extend(v1.bases[:s1])

            new_points.extend(v0.points[s0:])
            new_bases.append(fb)
            new_bases.extend(v0.bases[s0 + 1 :])

            return PatchOutline(
                [
                    *self.region_curves[:c0],
                    ClosedCurve(points=new_points, bases=new_bases),
                    *self.region_curves[c0 + 1 : c1],
                    *self.region_curves[c1 + 1 :],
                ]
            )

    def __eq__(self, other):
        if not isinstance(other, PatchOutline):
            return NotImplemented
        return self.region_curves == other.region_curves

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return f"PatchOutline(curves={self.region_curves!r})"

    def write_svg(
        self,
        path: str | pathlib.Path,
        *,
        other_segments: Iterable[tuple[complex, Literal["X", "Y", "Z"], complex]] = (),
        other: Union[
            "PatchOutline",
            "PatchTransitionOutline",
            Iterable[Union["PatchOutline", "PatchTransitionOutline"]],
        ] = (),
    ) -> None:
        from gen._surf._viz_patch_outline_svg import patch_outline_svg_viewer
        from gen._surf._patch_transition_outline import PatchTransitionOutline

        if isinstance(other, (PatchOutline, PatchTransitionOutline)):
            other = [other]
        viewer = patch_outline_svg_viewer(
            values=[self, *other],
            other_segments=other_segments,
        )
        write_file(path, viewer)

    def to_patch(
        self,
        *,
        rel_order_func: Callable[[complex], Iterable[complex]] | None = None,
    ) -> Patch:
        """Converts the boundary list into an explicit surface code stabilizer configuration."""

        if rel_order_func is None:
            rel_order_func = lambda _: Order_Z
        data_qubits = self.interior_set(include_boundary=True)
        contiguous_x_data_qubit_sets = []
        contiguous_z_data_qubit_sets = []
        for c in self.region_curves:
            cur_set = None
            for k in range(len(c.points)):
                if k == 0 or c.bases[k] != c.bases[k - 1]:
                    cur_set = set()
                    if c.bases[k] == "X":
                        contiguous_x_data_qubit_sets.append(cur_set)
                    else:
                        contiguous_z_data_qubit_sets.append(cur_set)
                a = c.points[k - 1]
                b = c.points[k]
                for p in int_points_on_line(a, b):
                    cur_set.add(p)

        internal_measure_qubits = half_int_points_inside_int_polygon_set(
            curves=[curve.points for curve in self.region_curves],
            include_boundary=True,
        )

        plaqs = []
        external_measure_qubits = set()
        for c in self.region_curves:
            b = c.boundary_travel()
            b3 = b * 3
            n = len(b)
            for k in range(n):
                nearby_measurement_qubits = {b[k] + d for d in Order_Z}
                for m in nearby_measurement_qubits:
                    if m in internal_measure_qubits:
                        continue
                    if m in external_measure_qubits:
                        continue
                    relevant_contiguous_sets = (
                        contiguous_z_data_qubit_sets
                        if checkerboard_basis(m) == "Z"
                        else contiguous_x_data_qubit_sets
                    )
                    nearby_boundary_data = b3[n + k - 2 : n + k + 3]
                    ds = set()
                    for contiguous_candidate in relevant_contiguous_sets:
                        kept_ds = {
                            m + d
                            for d in Order_Z
                            if m + d in nearby_boundary_data
                            and m + d in contiguous_candidate
                        }
                        if len(kept_ds) > len(ds):
                            ds = kept_ds
                    if len(ds) < 2:
                        continue
                    plaqs.append(
                        Tile(
                            bases=checkerboard_basis(m),
                            measurement_qubit=m,
                            ordered_data_qubits=[
                                m + d if d is not None and m + d in ds else None
                                for d in rel_order_func(m)
                            ],
                        )
                    )
                    external_measure_qubits.add(m)

        d_count = collections.Counter()
        for m in internal_measure_qubits:
            for d in Order_Z:
                d_count[m + d] += 1
        for p in plaqs:
            # Don't trim data qubits used by boundary measurements.
            for d in p.data_set:
                d_count[d] += 100

        used_data_qubits = set()
        for d in sorted_complex(data_qubits):
            if d_count[d] > 1:
                used_data_qubits.add(d)

        for m in internal_measure_qubits:
            b = checkerboard_basis(m)
            plaqs.append(
                Tile(
                    bases=b,
                    measurement_qubit=m,
                    ordered_data_qubits=[
                        m + d if d is not None and m + d in used_data_qubits else None
                        for d in rel_order_func(m)
                    ],
                )
            )

        return Patch(plaqs)
