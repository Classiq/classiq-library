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

from typing import Literal

import numpy as np

R_XYZ = 0
R_XZY = 1
R_YXZ = 2
R_YZX = 3
R_ZXY = 4
R_ZYX = 5
PERMUTATIONS: list[dict[Literal["X", "Y", "Z"], Literal["X", "Y", "Z"]]] = [
    {"X": "X", "Y": "Y", "Z": "Z"},
    {"X": "X", "Y": "Z", "Z": "Y"},
    {"X": "Y", "Y": "X", "Z": "Z"},
    {"X": "Y", "Y": "Z", "Z": "X"},
    {"X": "Z", "Y": "X", "Z": "Y"},
    {"X": "Z", "Y": "Y", "Z": "X"},
]
INVERSE_PERMUTATIONS: list[dict[Literal["X", "Y", "Z"], Literal["X", "Y", "Z"]]] = [
    {"X": "X", "Y": "Y", "Z": "Z"},
    {"X": "X", "Y": "Z", "Z": "Y"},
    {"X": "Y", "Y": "X", "Z": "Z"},
    {"X": "Z", "Y": "X", "Z": "Y"},
    {"X": "Y", "Y": "Z", "Z": "X"},
    {"X": "Z", "Y": "Y", "Z": "X"},
]
ORIENTATIONS = [
    "I",
    "SQRT_X",
    "S",
    "C_XYZ",
    "C_ZYX",
    "H",
]
ORIENTATION_MULTIPLICATION_TABLE = np.array(
    [
        [0, 1, 2, 3, 4, 5],
        [1, 0, 4, 5, 2, 3],
        [2, 3, 0, 1, 5, 4],
        [3, 2, 5, 4, 0, 1],
        [4, 5, 1, 0, 3, 2],
        [5, 4, 3, 2, 1, 0],
    ],
    dtype=np.uint8,
)
