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

UL, UR, DL, DR = [e * 0.5 for e in [-1 - 1j, +1 - 1j, -1 + 1j, +1 + 1j]]
Order_Z = [UL, UR, DL, DR]
Order_ᴎ = [UL, DL, UR, DR]
Order_N = [DL, UL, DR, UR]
Order_S = [DL, DR, UL, UR]


def checkerboard_basis(q: complex) -> str:
    """Classifies a coordinate as X type or Z type according to a checkerboard."""
    is_x = int(q.real + q.imag) & 1 == 0
    return "X" if is_x else "Z"
