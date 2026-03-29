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

import pytest

from gen._surf._geo import (
    int_points_on_line,
    int_points_inside_polygon,
    half_int_points_inside_int_polygon,
    int_point_disjoint_regions_inside_polygon_set,
)
from gen._core._util import sorted_complex


def test_int_points_on_line():
    with pytest.raises(NotImplementedError):
        int_points_on_line(0, 1 + 2j)

    assert int_points_on_line(0, 0) == [0]
    assert int_points_on_line(0, 5) == [0, 1, 2, 3, 4, 5]
    assert int_points_on_line(1, -3) == [1, 0, -1, -2, -3]
    assert int_points_on_line(1j, 3j) == [1j, 2j, 3j]
    assert int_points_on_line(0, -2j) == [0, -1j, -2j]
    assert int_points_on_line(5, 8 + 3j) == [5, 6 + 1j, 7 + 2j, 8 + 3j]
    assert int_points_on_line(5, 8 - 3j) == [5, 6 - 1j, 7 - 2j, 8 - 3j]
    assert int_points_on_line(5, 2 + 3j) == [5, 4 + 1j, 3 + 2j, 2 + 3j]
    assert int_points_on_line(5, 2 - 3j) == [5, 4 - 1j, 3 - 2j, 2 - 3j]


def test_int_points_inside_polygon():
    assert sorted_complex(
        int_points_inside_polygon([0, 3, 3 + 2j, 5j], include_boundary=True)
    ) == [
        0 + 0j,
        0 + 1j,
        0 + 2j,
        0 + 3j,
        0 + 4j,
        0 + 5j,
        1 + 0j,
        1 + 1j,
        1 + 2j,
        1 + 3j,
        1 + 4j,
        2 + 0j,
        2 + 1j,
        2 + 2j,
        2 + 3j,
        3 + 0j,
        3 + 1j,
        3 + 2j,
    ]
    assert sorted_complex(
        int_points_inside_polygon([0, 3, 3 + 2j, 5j], include_boundary=False)
    ) == [
        1 + 1j,
        1 + 2j,
        1 + 3j,
        2 + 1j,
        2 + 2j,
    ]


def test_half_int_points_inside_int_polygon():
    assert sorted_complex(
        half_int_points_inside_int_polygon([0, 3, 3 + 2j, 5j], include_boundary=True)
    ) == [
        0.5 + 0.5j,
        0.5 + 1.5j,
        0.5 + 2.5j,
        0.5 + 3.5j,
        0.5 + 4.5j,
        1.5 + 0.5j,
        1.5 + 1.5j,
        1.5 + 2.5j,
        1.5 + 3.5j,
        2.5 + 0.5j,
        2.5 + 1.5j,
        2.5 + 2.5j,
    ]
    assert sorted_complex(
        half_int_points_inside_int_polygon([0, 3, 3 + 2j, 5j], include_boundary=False)
    ) == [
        0.5 + 0.5j,
        0.5 + 1.5j,
        0.5 + 2.5j,
        0.5 + 3.5j,
        1.5 + 0.5j,
        1.5 + 1.5j,
        1.5 + 2.5j,
        2.5 + 0.5j,
        2.5 + 1.5j,
    ]


def test_int_point_disjoint_regions_inside_polygon_set():
    a = int_point_disjoint_regions_inside_polygon_set(
        [
            [0, 3, 3 + 2j, 2j],
            [3j, 3 + 3j, 3 + 5j, 5j],
        ],
        include_boundary=False,
    )
    assert len(a) == 2
    assert a[1] == {1 + 1j, 2 + 1j}
    assert a[2] == {1 + 4j, 2 + 4j}

    a = int_point_disjoint_regions_inside_polygon_set(
        [
            [0, 3, 3 + 2j, 2j],
            [3j, 3 + 3j, 3 + 5j, 5j],
        ],
        include_boundary=True,
    )
    assert len(a) == 2
    assert a[1] == {
        0,
        1,
        2,
        3,
        0 + 1j,
        1 + 1j,
        2 + 1j,
        3 + 1j,
        0 + 2j,
        1 + 2j,
        2 + 2j,
        3 + 2j,
    }
    assert a[2] == {
        0 + 3j,
        1 + 3j,
        2 + 3j,
        3 + 3j,
        0 + 4j,
        1 + 4j,
        2 + 4j,
        3 + 4j,
        0 + 5j,
        1 + 5j,
        2 + 5j,
        3 + 5j,
    }
