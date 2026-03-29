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

from gen._layers._interact_layer import InteractLayer
from gen._layers._layer import Layer


@dataclasses.dataclass
class SwapLayer(Layer):
    targets1: list[int] = dataclasses.field(default_factory=list)
    targets2: list[int] = dataclasses.field(default_factory=list)

    def touched(self) -> set[int]:
        return set(self.targets1 + self.targets2)

    def copy(self) -> "SwapLayer":
        return SwapLayer(targets1=list(self.targets1), targets2=list(self.targets2))

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        pairs = []
        for k in range(len(self.targets1)):
            t1 = self.targets1[k]
            t2 = self.targets2[k]
            t1, t2 = sorted([t1, t2])
            pairs.append((t1, t2))
        for pair in sorted(pairs):
            out.append("SWAP", pair)

    def locally_optimized(self, next_layer: Layer | None) -> list[Layer | None]:
        if isinstance(next_layer, InteractLayer):
            from gen._layers._interact_swap_layer import InteractSwapLayer

            i = next_layer.copy()
            i.targets1, i.targets2 = i.targets2, i.targets1
            return [InteractSwapLayer(i_layer=i, swap_layer=self.copy())]
        return [self, next_layer]
