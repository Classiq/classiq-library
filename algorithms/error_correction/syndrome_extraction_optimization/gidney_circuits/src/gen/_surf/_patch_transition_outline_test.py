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

from gen._surf._closed_curve import ClosedCurve
from gen._surf._patch_transition_outline import PatchTransitionOutline
from gen._surf._path_outline import PathOutline


def test_data_set():
    trans = PatchTransitionOutline(
        observable_deltas={1: PathOutline([(0 + 1j, 2 + 1j, "X")])},
        data_boundary_planes=[ClosedCurve.from_cycle(["X", 0, 2, 2 + 2j, 2j])],
    )
    assert trans.data_set == {0, 1, 2, 1j, 1j + 1, 1j + 2, 2j, 2j + 1, 2j + 2}
