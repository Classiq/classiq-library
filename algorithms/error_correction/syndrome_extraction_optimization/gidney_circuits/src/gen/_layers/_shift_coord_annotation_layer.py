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
from typing import Iterable

import stim

from gen._layers._layer import Layer


@dataclasses.dataclass
class ShiftCoordAnnotationLayer(Layer):
    shift: list[float] = dataclasses.field(default_factory=list)

    def offset_by(self, args: Iterable[float]):
        for k, arg in enumerate(args):
            if k >= len(self.shift):
                self.shift.append(arg)
            else:
                self.shift[k] += arg

    def copy(self) -> "ShiftCoordAnnotationLayer":
        return ShiftCoordAnnotationLayer(shift=self.shift)

    def touched(self) -> set[int]:
        return set()

    def requires_tick_before(self) -> bool:
        return False

    def implies_eventual_tick_after(self) -> bool:
        return False

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        out.append("SHIFT_COORDS", [], self.shift)

    def locally_optimized(self, next_layer: Layer | None) -> list[Layer | None]:
        if isinstance(next_layer, ShiftCoordAnnotationLayer):
            result = self.copy()
            result.offset_by(next_layer.shift)
            return [result]
        return [self, next_layer]
