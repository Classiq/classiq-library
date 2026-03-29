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

import gen
from clorco.color2surface_code._color2surface_layouts import make_color2surface_layout
from clorco.color2surface_code._draw_mobius_graph import code_capacity_mobius_graph_svg


@pytest.mark.parametrize("d", [3, 5, 7, 9])
def test_make_color2surface_layout(d: int):
    code = make_color2surface_layout(base_data_width=d)
    code.check_commutation_relationships()
    for tile in code.patch.tiles:
        assert (tile.extra_coords[0] >= 3) == (tile.basis == "Z")
    err = code.make_code_capacity_circuit(
        noise=1e-3
    ).search_for_undetectable_logical_errors(
        dont_explore_edges_increasing_symptom_degree=False,
        dont_explore_edges_with_degree_above=3,
        dont_explore_detection_event_sets_with_size_above=6,
    )
    assert len(err) == d


def test_draw_mobius_graph():
    code = make_color2surface_layout(base_data_width=13)
    assert code_capacity_mobius_graph_svg(code.patch) is not None
