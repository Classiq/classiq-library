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

from gen._layers._data import R_XZY, R_ZYX, R_YXZ
from gen._layers._interact_layer import InteractLayer
from gen._layers._layer import Layer
from gen._layers._rotation_layer import RotationLayer


@dataclasses.dataclass
class SqrtPPLayer(Layer):
    targets1: list[int] = dataclasses.field(default_factory=list)
    targets2: list[int] = dataclasses.field(default_factory=list)
    bases: list[str] = dataclasses.field(default_factory=list)

    def touched(self) -> set[int]:
        return set(self.targets1 + self.targets2)

    def copy(self) -> "SqrtPPLayer":
        return SqrtPPLayer(
            targets1=list(self.targets1),
            targets2=list(self.targets2),
            bases=list(self.bases),
        )

    def to_z_basis(self) -> list["Layer"]:
        interact = InteractLayer()
        rot = RotationLayer()
        for q1, q2, b in zip(self.targets1, self.targets2, self.bases):
            interact.targets1.append(q1)
            interact.targets2.append(q2)
            interact.bases1.append(b)
            interact.bases1.append(b)
            if b == "X":
                r = R_XZY
            elif b == "Y":
                r = R_ZYX
            elif b == "Z":
                r = R_YXZ
            else:
                raise NotImplementedError(f"{b=}")
            rot.append_rotation(r, q1)
            rot.append_rotation(r, q2)

        return [
            rot,
            *interact.to_z_basis(),
        ]

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        groups = collections.defaultdict(list)
        for q1, q2, b in zip(self.targets1, self.targets2, self.bases):
            gate = f"SQRT_{b}{b}"
            if q2 < q1:
                q1, q2 = q2, q1
            groups[gate].append((q1, q2))
        for gate in sorted(groups.keys()):
            for pair in sorted(groups[gate]):
                out.append(gate, pair)
