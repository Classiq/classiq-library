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

import stim

from gen._layers._data import R_ZXY
from gen._layers._feedback_layer import _basis_before_rotation


def test_basis_before_rotation():
    assert _basis_before_rotation("X", R_ZXY) == "Y"
    assert _basis_before_rotation("Y", R_ZXY) == "Z"
    assert _basis_before_rotation("Z", R_ZXY) == "X"
