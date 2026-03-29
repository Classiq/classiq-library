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

import dataclasses
from typing import Literal

import stim

from gen._layers._data import R_XYZ, R_ZYX, R_XZY
from gen._layers._layer import Layer
from gen._layers._rotation_layer import RotationLayer


@dataclasses.dataclass
class ResetLayer(Layer):
    targets: dict[int, Literal["X", "Y", "Z"]] = dataclasses.field(default_factory=dict)

    def copy(self) -> "ResetLayer":
        return ResetLayer(targets=dict(self.targets))

    def touched(self) -> set[int]:
        return set(self.targets.keys())

    def to_z_basis(self) -> list["Layer"]:
        return [
            ResetLayer(targets={q: "Z" for q in self.targets.keys()}),
            RotationLayer(
                {
                    q: R_XYZ if b == "Z" else R_ZYX if b == "X" else R_XZY
                    for q, b in self.targets.items()
                }
            ),
        ]

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        outs = {"X": [], "Y": [], "Z": []}
        for t, b in self.targets.items():
            outs[b].append(t)
        for b, vs in outs.items():
            if vs:
                out.append("R" + b, vs)

    def locally_optimized(self, next_layer: Layer | None) -> list[Layer | None]:
        if isinstance(next_layer, ResetLayer):
            return [
                ResetLayer(
                    targets={
                        t: b
                        for layer in [self, next_layer]
                        for t, b in layer.targets.items()
                    }
                )
            ]
        return [self, next_layer]
