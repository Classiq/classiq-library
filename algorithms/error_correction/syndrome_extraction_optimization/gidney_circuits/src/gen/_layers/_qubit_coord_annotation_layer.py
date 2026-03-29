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
class QubitCoordAnnotationLayer(Layer):
    coords: dict[int, list[float]] = dataclasses.field(default_factory=dict)

    def offset_by(self, args: Iterable[float]):
        for index, offset in enumerate(args):
            if offset:
                for q, qubit_coords in self.coords.items():
                    if index < len(qubit_coords):
                        qubit_coords[index] += offset

    def copy(self) -> "Layer":
        return QubitCoordAnnotationLayer(coords=dict(self.coords))

    def touched(self) -> set[int]:
        return set()

    def requires_tick_before(self) -> bool:
        return False

    def implies_eventual_tick_after(self) -> bool:
        return False

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        for q in sorted(self.coords.keys()):
            out.append("QUBIT_COORDS", [q], self.coords[q])
