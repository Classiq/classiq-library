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

from gen._layers._layer import Layer


@dataclasses.dataclass
class EmptyLayer(Layer):
    def copy(self) -> "EmptyLayer":
        return EmptyLayer()

    def touched(self) -> set[int]:
        return set()

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        pass

    def locally_optimized(self, next_layer: None | Layer) -> list[Layer | None]:
        return [next_layer]

    def is_vacuous(self) -> bool:
        return True
