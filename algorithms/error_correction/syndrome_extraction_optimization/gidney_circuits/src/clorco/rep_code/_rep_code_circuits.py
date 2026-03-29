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

from typing import Sequence

import stim

import gen
from clorco.rep_code._rep_code_layouts import make_rep_code_layout


def make_rep_code_circuit(
    *,
    distance: int,
    toric: bool = False,
    rounds: int,
    round_colorings: Sequence[str] = ("r",),
) -> stim.Circuit:
    assert rounds > 1
    code = make_rep_code_layout(
        distance=distance,
        toric=toric,
    )
    color_indices = {
        "r": [3],
        "g": [4],
        "b": [5],
        "R": [3],
        "G": [4],
        "B": [5],
    }

    builder = gen.Builder.for_qubits(code.patch.used_set)

    for cur_round in range(rounds):
        if cur_round > 0:
            builder.tick()
        builder.gate(
            "R", code.patch.used_set if cur_round == 0 else code.patch.measure_set
        )
        builder.tick()
        builder.gate2("CX", [(m - 0.5, m) for m in code.patch.measure_set])
        builder.tick()
        builder.gate2(
            "CX", [((m.real + 0.5) % distance, m) for m in code.patch.measure_set]
        )
        builder.tick()
        builder.measure(
            code.patch.used_set if cur_round == rounds - 1 else code.patch.measure_set,
            save_layer=cur_round,
        )
        for m in gen.sorted_complex(code.patch.measure_set):
            m_key = gen.AtLayer(m, cur_round)
            other_key = [] if cur_round == 0 else [gen.AtLayer(m, cur_round - 1)]
            rc = round_colorings[cur_round % len(round_colorings)]
            c = color_indices[rc[int(m.real % len(rc) - 0.5)]]
            builder.detector([m_key] + other_key, pos=m, extra_coords=c)
        builder.shift_coords(dt=1)
    for m in gen.sorted_complex(code.patch.measure_set):
        rc = round_colorings[rounds % len(round_colorings)]
        c = color_indices[rc[int(m.real % len(rc) - 0.5)]]
        builder.detector(
            [
                gen.AtLayer(m, rounds - 1),
                gen.AtLayer((m.real + 0.5) % distance, rounds - 1),
                gen.AtLayer(m - 0.5, rounds - 1),
            ],
            pos=m,
            extra_coords=c,
        )
    builder.obs_include([gen.AtLayer(0, rounds - 1)], obs_index=0)
    return builder.circuit
