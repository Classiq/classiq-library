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

import stim

from gen._layers._data import R_ZYX, R_XYZ, R_XZY
from gen._layers._layer import Layer
from gen._layers._rotation_layer import RotationLayer


@dataclasses.dataclass
class MeasureLayer(Layer):
    targets: list[int] = dataclasses.field(default_factory=list)
    bases: list[str] = dataclasses.field(default_factory=list)

    def copy(self) -> "MeasureLayer":
        return MeasureLayer(targets=list(self.targets), bases=list(self.bases))

    def touched(self) -> set[int]:
        return set(self.targets)

    def to_z_basis(self) -> list["Layer"]:
        rot = RotationLayer(
            {
                q: R_XYZ if b == "Z" else R_ZYX if b == "X" else R_XZY
                for q, b in zip(self.targets, self.bases)
            }
        )
        return [
            rot,
            MeasureLayer(targets=list(self.targets), bases=["Z"] * len(self.targets)),
            rot.copy(),
        ]

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        for t, b in zip(self.targets, self.bases):
            out.append("M" + b, [t])

    def locally_optimized(self, next_layer: Layer | None) -> list[Layer | None]:
        if isinstance(next_layer, MeasureLayer) and set(self.targets).isdisjoint(
            next_layer.targets
        ):
            return [
                MeasureLayer(
                    targets=self.targets + next_layer.targets,
                    bases=self.bases + next_layer.bases,
                )
            ]
        return [self, next_layer]
