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

from gen._layers._data import R_ZYX, R_XZY
from gen._layers._layer import Layer
from gen._layers._rotation_layer import RotationLayer


@dataclasses.dataclass
class MppLayer(Layer):
    targets: list[list[stim.GateTarget]] = dataclasses.field(default_factory=list)

    def copy(self) -> "MppLayer":
        return MppLayer(targets=[list(e) for e in self.targets])

    def touched(self) -> set[int]:
        return set(t.value for mpp in self.targets for t in mpp)

    def to_z_basis(self) -> list["Layer"]:
        assert len(self.touched()) == sum(len(e) for e in self.targets)
        rot = RotationLayer()
        new_targets: list[list[stim.GateTarget]] = []
        for groups in self.targets:
            new_group: list[stim.GateTarget] = []
            for t in groups:
                new_group.append(stim.target_z(t.value))
                if t.is_x_target:
                    rot.append_rotation(R_ZYX, t.value)
                elif t.is_y_target:
                    rot.append_rotation(R_XZY, t.value)
                elif not t.is_z_target:
                    raise NotImplementedError(f"{t=}")
            new_targets.append(new_group)

        return [
            rot,
            MppLayer(targets=new_targets),
            rot.copy(),
        ]

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        flat_targets = []
        for group in self.targets:
            for t in group:
                flat_targets.append(t)
                flat_targets.append(stim.target_combiner())
            flat_targets.pop()
        out.append("MPP", flat_targets)
