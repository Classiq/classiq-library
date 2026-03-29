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

import gen
from clorco._make_circuit import make_circuit


def test_make_circuit():
    c = make_circuit(
        style="phenom_color_code",
        noise_model=gen.NoiseModel.uniform_depolarizing(1e-3),
        noise_strength=1e-3,
        diameter=5,
        editable_extras={},
        rounds=7,
    )
    err = c.search_for_undetectable_logical_errors(
        dont_explore_edges_increasing_symptom_degree=False,
        dont_explore_edges_with_degree_above=3,
        dont_explore_detection_event_sets_with_size_above=3,
    )
    assert len(err) == 5
