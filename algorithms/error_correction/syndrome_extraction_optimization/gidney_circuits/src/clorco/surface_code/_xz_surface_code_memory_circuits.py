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

import gen
from clorco.surface_code._surface_code_chunks import standard_surface_code_chunk
from clorco.surface_code._surface_code_patches import make_xtop_qubit_patch


def make_xz_memory_experiment_chunks(
    *,
    diameter: int,
    basis: str,
    rounds: int,
) -> list[gen.Chunk]:
    qubit_patch = make_xtop_qubit_patch(diameter=diameter)
    xs = {q for q in qubit_patch.data_set if q.real == 0}
    zs = {q for q in qubit_patch.data_set if q.imag == 0}
    assert len(xs & zs) % 2 == 1
    obs = gen.PauliString({q: basis for q in (xs if basis == "X" else zs)})
    assert rounds > 0
    if rounds == 1:
        return [
            standard_surface_code_chunk(
                qubit_patch, init_data_basis=basis, measure_data_basis=basis, obs=obs
            )
        ]

    return [
        standard_surface_code_chunk(
            qubit_patch,
            init_data_basis=basis,
            obs=obs,
        ),
        standard_surface_code_chunk(
            qubit_patch,
            obs=obs,
        ).with_repetitions(rounds - 2),
        standard_surface_code_chunk(
            qubit_patch,
            measure_data_basis=basis,
            obs=obs,
        ),
    ]
