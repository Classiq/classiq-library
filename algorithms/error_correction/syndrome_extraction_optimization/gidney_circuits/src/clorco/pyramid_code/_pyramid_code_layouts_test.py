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

from clorco.pyramid_code._pyramid_code_layouts import make_planar_pyramid_code_layout
from clorco.pyramid_code._pyramid_code_layouts import make_toric_pyramid_code_layout


@pytest.mark.parametrize("h", [3, 6, 9])
@pytest.mark.parametrize("w", [4, 6, 8, 10])
def test_make_toric_pyramid_code_layout(w: int, h: int):
    code = make_toric_pyramid_code_layout(
        width=w,
        height=h,
    )
    code.check_commutation_relationships()
    assert (
        len(code.patch.data_set)
        == len(code.patch.tiles)
        + max(len(code.observables_x), len(code.observables_z))
        - 2
    )
    c = code.make_code_capacity_circuit(noise=1e-3)
    err = c.search_for_undetectable_logical_errors(
        dont_explore_edges_with_degree_above=3,
        dont_explore_detection_event_sets_with_size_above=6,
        dont_explore_edges_increasing_symptom_degree=False,
    )
    assert len(err) == min((w + 1) // 2, h * 2 // 3)


@pytest.mark.parametrize("h", [3, 4, 5, 6, 7, 8, 9, 10])
@pytest.mark.parametrize("w", [3, 4, 5, 6, 7, 8, 9, 10])
def test_make_planar_pyramid_code_layout(w: int, h: int):
    code = make_planar_pyramid_code_layout(
        width=w,
        height=h,
    )
    code.check_commutation_relationships()
    c = code.make_code_capacity_circuit(noise=1e-3)
    assert len(code.patch.data_set) == len(code.patch.tiles) + max(
        len(code.observables_x), len(code.observables_z)
    )
    err = c.search_for_undetectable_logical_errors(
        dont_explore_edges_with_degree_above=3,
        dont_explore_detection_event_sets_with_size_above=6,
        dont_explore_edges_increasing_symptom_degree=False,
    )
    assert len(err) == min((w + 1) // 2, h * 2 // 3)
