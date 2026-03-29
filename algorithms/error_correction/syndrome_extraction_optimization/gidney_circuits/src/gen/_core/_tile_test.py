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

from gen._core._tile import Tile


def test_basis():
    tile = Tile(bases="XYZX", measurement_qubit=0, ordered_data_qubits=(1, 2, None, 3))
    assert tile.basis is None

    tile = Tile(bases="XXZX", measurement_qubit=0, ordered_data_qubits=(1, 2, None, 3))
    assert tile.basis == "X"

    tile = Tile(bases="XXX", measurement_qubit=0, ordered_data_qubits=(1, 2, 3))
    assert tile.basis == "X"

    tile = Tile(bases="ZZZ", measurement_qubit=0, ordered_data_qubits=(1, 2, 3))
    assert tile.basis == "Z"

    tile = Tile(bases="ZXZ", measurement_qubit=0, ordered_data_qubits=(1, 2, 3))
    assert tile.basis == None
