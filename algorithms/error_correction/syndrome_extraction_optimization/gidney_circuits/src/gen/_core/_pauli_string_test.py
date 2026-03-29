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

from gen._core._pauli_string import PauliString


def test_mul():
    a = "IIIIXXXXYYYYZZZZ"
    b = "IXYZ" * 4
    c = "IXYZXIZYYZIXZYXI"
    a = PauliString({q: p for q, p in enumerate(a) if p != "I"})
    b = PauliString({q: p for q, p in enumerate(b) if p != "I"})
    c = PauliString({q: p for q, p in enumerate(c) if p != "I"})
    assert a * b == c
