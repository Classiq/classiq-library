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

from gen._layers._data import R_YXZ
from gen._layers._interact_layer import InteractLayer
from gen._layers._iswap_layer import ISwapLayer
from gen._layers._layer import Layer
from gen._layers._rotation_layer import RotationLayer
from gen._layers._swap_layer import SwapLayer


@dataclasses.dataclass
class InteractSwapLayer(Layer):
    i_layer: InteractLayer = dataclasses.field(default_factory=InteractLayer)
    swap_layer: SwapLayer = dataclasses.field(default_factory=SwapLayer)

    def copy(self) -> "InteractSwapLayer":
        return InteractSwapLayer(
            i_layer=self.i_layer.copy(), swap_layer=self.swap_layer.copy()
        )

    def touched(self) -> set[int]:
        return self.i_layer.touched() | self.swap_layer.touched()

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        self.i_layer.append_into_stim_circuit(out)
        out.append("TICK")
        self.swap_layer.append_into_stim_circuit(out)

    def to_z_basis(self) -> list["Layer"]:
        pairs_1 = {
            frozenset([a, b])
            for a, b in zip(self.i_layer.targets1, self.i_layer.targets2)
        }
        pairs_2 = {
            frozenset([a, b])
            for a, b in zip(self.swap_layer.targets1, self.swap_layer.targets2)
        }
        assert pairs_1 == pairs_2
        pre: RotationLayer
        post: RotationLayer
        pre, _, post = self.i_layer.to_z_basis()
        for x, y in zip(self.swap_layer.targets1, self.swap_layer.targets2):
            post.rotations[x], post.rotations[y] = post.rotations[y], post.rotations[x]
            post.prepend_rotation(R_YXZ, x)
            post.prepend_rotation(R_YXZ, y)
        mid = ISwapLayer(
            targets1=self.swap_layer.targets1, targets2=self.swap_layer.targets2
        )
        return [pre, mid, post]

    def locally_optimized(self, next_layer: Layer | None) -> list[Layer | None]:
        return [self, next_layer]
