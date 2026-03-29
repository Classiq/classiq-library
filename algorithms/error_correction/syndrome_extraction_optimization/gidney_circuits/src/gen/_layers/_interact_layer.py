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

import collections
import dataclasses

import stim

from gen._layers._data import R_XYZ, R_ZYX, R_XZY
from gen._layers._layer import Layer


@dataclasses.dataclass
class InteractLayer(Layer):
    targets1: list[int] = dataclasses.field(default_factory=list)
    targets2: list[int] = dataclasses.field(default_factory=list)
    bases1: list[str] = dataclasses.field(default_factory=list)
    bases2: list[str] = dataclasses.field(default_factory=list)

    def touched(self) -> set[int]:
        return set(self.targets1 + self.targets2)

    def copy(self) -> "InteractLayer":
        return InteractLayer(
            targets1=list(self.targets1),
            targets2=list(self.targets2),
            bases1=list(self.bases1),
            bases2=list(self.bases2),
        )

    def _rot_layer(self):
        from gen._layers._rotation_layer import RotationLayer

        result = RotationLayer()
        for targets, bases in [
            (self.targets1, self.bases1),
            (self.targets2, self.bases2),
        ]:
            for q, b in zip(targets, bases):
                result.rotations[q] = (
                    R_XYZ if b == "Z" else R_ZYX if b == "X" else R_XZY
                )
        return result

    def to_z_basis(self) -> list["Layer"]:
        rot = self._rot_layer()
        return [
            rot,
            InteractLayer(
                targets1=list(self.targets1),
                targets2=list(self.targets2),
                bases1=["Z"] * len(self.targets1),
                bases2=["Z"] * len(self.targets2),
            ),
            rot.copy(),
        ]

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        groups = collections.defaultdict(list)
        for k in range(len(self.targets1)):
            gate = self.bases1[k] + "C" + self.bases2[k]
            t1 = self.targets1[k]
            t2 = self.targets2[k]
            if gate in ["XCZ", "YCZ", "YCX"]:
                t1, t2 = t2, t1
                gate = gate[::-1]
            if gate in ["XCX", "YCY", "ZCZ"]:
                t1, t2 = sorted([t1, t2])
            groups[gate].append((t1, t2))
        for gate in sorted(groups.keys()):
            for pair in sorted(groups[gate]):
                out.append(gate, pair)

    def locally_optimized(self, next_layer: Layer | None) -> list[Layer | None]:
        from gen._layers._swap_layer import SwapLayer
        from gen._layers._interact_swap_layer import InteractSwapLayer

        if isinstance(next_layer, SwapLayer):
            return [
                InteractSwapLayer(i_layer=self.copy(), swap_layer=next_layer.copy())
            ]
        return [self, next_layer]
