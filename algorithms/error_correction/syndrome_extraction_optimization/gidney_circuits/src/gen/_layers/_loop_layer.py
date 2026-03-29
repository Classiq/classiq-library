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
from typing import TYPE_CHECKING

import stim

from gen._layers._layer import Layer

if TYPE_CHECKING:
    from gen._layers._layer_circuit import LayerCircuit


@dataclasses.dataclass
class LoopLayer(Layer):
    body: "LayerCircuit"
    repetitions: int

    def copy(self) -> "LoopLayer":
        return LoopLayer(body=self.body.copy(), repetitions=self.repetitions)

    def touched(self) -> set[int]:
        return self.body.touched()

    def to_z_basis(self) -> list["Layer"]:
        return [
            LoopLayer(
                body=self.body.to_z_basis(),
                repetitions=self.repetitions,
            )
        ]

    def locally_optimized(self, next_layer: Layer | None) -> list[Layer | None]:
        optimized = LoopLayer(
            body=self.body.with_locally_optimized_layers(),
            repetitions=self.repetitions,
        )
        return [optimized, next_layer]

    def implies_eventual_tick_after(self) -> bool:
        return False

    def append_into_stim_circuit(self, out: stim.Circuit) -> None:
        body = self.body.to_stim_circuit()
        body.append("TICK")
        out.append(stim.CircuitRepeatBlock(repeat_count=self.repetitions, body=body))
