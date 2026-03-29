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

import sinter
import stim

from gen._layers._data import (
    R_ZXY,
    R_YZX,
    ORIENTATIONS,
    R_XYZ,
    ORIENTATION_MULTIPLICATION_TABLE,
)
from gen._layers._layer import Layer


@dataclasses.dataclass
class RotationLayer(Layer):
    rotations: dict[int, int] = dataclasses.field(default_factory=dict)

    def touched(self) -> set[int]:
        return {k for k, v in self.rotations.items() if v}

    def copy(self) -> "RotationLayer":
        return RotationLayer(dict(self.rotations))

    def inverse(self) -> "RotationLayer":
        return RotationLayer(
            rotations={
                q: R_YZX if r == R_ZXY else R_ZXY if r == R_YZX else r
                for q, r in self.rotations.items()
            }
        )

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        v = sinter.group_by(self.rotations.items(), key=lambda e: e[1])
        for r, items in sorted(v.items(), key=lambda e: ORIENTATIONS[e[0]]):
            if r:
                out.append(ORIENTATIONS[r], sorted(q for q, _ in items))

    def prepend_rotation(self, rotation_index: int, target: int):
        r1 = self.rotations.setdefault(target, R_XYZ)
        self.rotations[target] = ORIENTATION_MULTIPLICATION_TABLE[r1][rotation_index]

    def append_rotation(self, rotation_index: int, target: int):
        r1 = self.rotations.setdefault(target, R_XYZ)
        self.rotations[target] = ORIENTATION_MULTIPLICATION_TABLE[rotation_index][r1]

    def is_vacuous(self) -> bool:
        return not any(self.rotations.values())

    def locally_optimized(self, next_layer: Layer | None) -> list[Layer | None]:
        from gen._layers._det_obs_annotation_layer import DetObsAnnotationLayer
        from gen._layers._feedback_layer import FeedbackLayer
        from gen._layers._reset_layer import ResetLayer
        from gen._layers._shift_coord_annotation_layer import ShiftCoordAnnotationLayer

        if isinstance(next_layer, (DetObsAnnotationLayer, ShiftCoordAnnotationLayer)):
            return [next_layer, self]
        if isinstance(next_layer, FeedbackLayer):
            return [next_layer.before(self), self]
        if isinstance(next_layer, ResetLayer):
            trimmed = self.copy()
            for t in next_layer.targets.keys():
                if t in trimmed.rotations:
                    del trimmed.rotations[t]
            if trimmed.rotations:
                return [trimmed, next_layer]
            else:
                return [next_layer]
        if isinstance(next_layer, RotationLayer):
            result = RotationLayer(rotations=dict(self.rotations))
            for q, r in next_layer.rotations.items():
                result.append_rotation(r, q)
            return [result]
        return [self, next_layer]
