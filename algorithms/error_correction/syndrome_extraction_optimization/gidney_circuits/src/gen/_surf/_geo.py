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
from typing import Iterable, Sequence

from gen._core._util import min_max_complex


def int_points_on_line(a: complex, b: complex) -> list[complex]:
    """Lists the integer points along a given line segment.

    The delta `a-b` must be horizontal (imaginary part is 0), vertical
    (real part is 0), or diagonal (real and imaginary parts have same
    absolute magnitude).

    Args:
        a: A complex number with integer real part and integer imaginary part.
        b: A complex number with integer real part and integer imaginary part.

    Returns:
        The list of integer points.
    """
    dr = b.real - a.real
    di = b.imag - a.imag
    if a == b:
        return [a]
    if len({0, abs(di), abs(dr)}) != 2:
        raise NotImplementedError(
            f"{a=} to {b=} isn't horizontal, vertical, or 1:1 diagonal."
        )
    steps = int(max(abs(dr), abs(di)))
    result = []
    dr /= steps
    di /= steps
    assert int(dr) == dr
    assert int(di) == di
    dr = int(dr)
    di = int(di)
    for k in range(steps + 1):
        result.append(a + dr * k + di * k * 1j)
    return result


def int_travel_points_on_polygon_boundary(corners: Sequence[complex]) -> list[complex]:
    boundary = []
    for k in range(len(corners)):
        a = corners[k - 1]
        b = corners[k]
        for p in int_points_on_line(a, b):
            if len(boundary) == 0 or boundary[-1] != p:
                boundary.append(p)
    assert boundary[-1] == boundary[0]
    boundary.pop()
    return boundary


def half_int_points_inside_int_polygon_set(
    *,
    curves: Sequence[Sequence[complex]],
    include_boundary: bool,
    match_mask: int | None = None,
) -> set[complex]:
    curves2 = [[pt * 2 for pt in curve] for curve in curves]
    interior2 = int_points_inside_polygon_set(
        curves2, include_boundary=include_boundary, match_mask=match_mask
    )
    return {p / 2 for p in interior2 if p.real % 2 == 1 and p.imag % 2 == 1}


def half_int_points_inside_int_polygon(
    corners: Sequence[complex], *, include_boundary: bool
) -> set[complex]:
    return half_int_points_inside_int_polygon_set(
        curves=[corners], include_boundary=include_boundary
    )


def int_points_inside_polygon(
    corners: Sequence[complex], *, include_boundary: bool
) -> set[complex]:
    return int_points_inside_polygon_set([corners], include_boundary=include_boundary)


def int_points_inside_polygon_set(
    curves: Iterable[Sequence[complex]],
    *,
    include_boundary: bool,
    match_mask: int | None = None,
) -> set[complex]:
    curves = tuple(curves)
    min_c, max_c = min_max_complex((pt for curve in curves for pt in curve), default=0)

    boundary = set()
    half_boundary = collections.defaultdict(int)
    for k, curve in enumerate(curves):
        boundary |= set(int_travel_points_on_polygon_boundary(curve))
        for p in set(int_travel_points_on_polygon_boundary([p * 2 for p in curve])):
            half_boundary[p / 2] ^= 1 << k

    result = set()
    for r in range(int(min_c.real), int(max_c.real) + 1):
        r0 = r - 0.5
        r1 = r + 0.5
        mask0 = 0
        inside0 = 0
        mask1 = 0
        inside1 = 0
        i = int(min_c.imag)
        while i <= max_c.imag:
            c0 = r0 + i * 1j
            c1 = r1 + i * 1j
            inside0 ^= half_boundary[c0] != 0
            inside1 ^= half_boundary[c1] != 0
            mask0 ^= half_boundary[c0]
            mask1 ^= half_boundary[c1]
            m0 = mask0 if inside0 else 0
            m1 = mask1 if inside1 else 0
            if (
                i == int(i)
                and m0 == m1
                and (m0 != 0 if match_mask is None else m0 == match_mask)
            ):
                result.add(r + i * 1j)
            i += 0.5

    if include_boundary:
        result |= boundary
    else:
        result -= boundary

    return result


def int_point_disjoint_regions_inside_polygon_set(
    curves: Iterable[Sequence[complex]], *, include_boundary: bool
) -> dict[int, set[complex]]:
    curves = tuple(curves)
    min_real = int(min(pt.real for curve in curves for pt in curve))
    min_imag = int(min(pt.imag for curve in curves for pt in curve))
    max_real = int(max(pt.real for curve in curves for pt in curve))
    max_imag = int(max(pt.imag for curve in curves for pt in curve))

    half_boundary = collections.defaultdict(int)
    for k, curve in enumerate(curves):
        for p in set(int_travel_points_on_polygon_boundary([p * 2 for p in curve])):
            half_boundary[p / 2] ^= 1 << k

    result = collections.defaultdict(set)
    for r in range(min_real, max_real + 1):
        r0 = r - 0.5
        r1 = r + 0.5

        mask0 = 0
        mask1 = 0
        inside0 = 0
        inside1 = 0
        i = min_imag
        while i <= max_imag:
            c0 = r0 + i * 1j
            c1 = r1 + i * 1j
            c = r + i * 1j
            b0 = half_boundary[c0]
            b1 = half_boundary[c1]
            new_inside0 = inside0 ^ (b0 != 0)
            new_inside1 = inside1 ^ (b1 != 0)
            new_mask0 = mask0 ^ b0
            new_mask1 = mask1 ^ b1
            if i == int(i):
                if include_boundary:
                    # On horizontal segment?
                    if inside0 and not new_inside0:
                        result[mask0].add(c)
                    if not inside0 and new_inside0:
                        result[new_mask0].add(c)
                    if inside1 and not new_inside1:
                        result[mask1].add(c)
                    if not inside1 and new_inside1:
                        result[new_mask1].add(c)

                    # On vertical segment?
                    if inside0 and not inside1:
                        result[mask0].add(c)
                    if new_inside0 and not new_inside1:
                        result[new_mask0].add(c)
                    if inside1 and not inside0:
                        result[mask1].add(c)
                    if new_inside1 and not new_inside0:
                        result[new_mask1].add(c)
                if (
                    inside0
                    and inside1
                    and new_inside0
                    and new_inside1
                    and mask0 == mask1 == new_mask0 == new_mask1
                ):
                    # Interior.
                    result[mask0].add(c)
            mask0 = new_mask0
            mask1 = new_mask1
            inside0 = new_inside0
            inside1 = new_inside1
            i += 0.5

    if 0 in result:
        del result[0]

    return dict(result)
