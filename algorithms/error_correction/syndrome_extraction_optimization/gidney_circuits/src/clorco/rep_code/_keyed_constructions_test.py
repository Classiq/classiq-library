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

from typing import Any
from typing import Callable

import pytest
import stim

import gen
from clorco._make_circuit_params import Params
from clorco.rep_code._keyed_constructions import make_named_rep_code_constructions


@pytest.mark.parametrize("name,maker", make_named_rep_code_constructions().items())
def test_rep_code_constructions(name: str, maker: Callable[[Params], stim.Circuit]):
    params = Params(
        style=name,
        rounds=1 if "transit" in name else 5,
        diameter=4,
        noise_strength=1e-3,
        noise_model=gen.NoiseModel.uniform_depolarizing(1e-3),
        convert_to_cz=False,
        editable_extras={},
        debug_out_dir=None,
    )
    circuit: stim.Circuit = maker(params)
    assert circuit.detector_error_model(decompose_errors=True) is not None
    assert len(circuit.shortest_graphlike_error()) == 4


def test_exact_construction():
    style = "rep_code_rbrrr"
    params = Params(
        style=style,
        rounds=3,
        diameter=4,
        noise_strength=1e-3,
        noise_model=gen.NoiseModel.uniform_depolarizing(1e-3),
        convert_to_cz=False,
        editable_extras={},
        debug_out_dir=None,
    )
    circuit = make_named_rep_code_constructions()[style](params)
    assert circuit == stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(1, 0) 1
        QUBIT_COORDS(2, 0) 2
        QUBIT_COORDS(3, 0) 3
        QUBIT_COORDS(0.5, 0) 4
        QUBIT_COORDS(1.5, 0) 5
        QUBIT_COORDS(2.5, 0) 6
        R 0 1 2 3 4 5 6
        X_ERROR(0.001) 0 1 2 3 4 5 6
        TICK
        CX 0 4 1 5 2 6
        DEPOLARIZE2(0.001) 0 4 1 5 2 6
        DEPOLARIZE1(0.001) 3
        TICK
        CX 1 4 2 5 3 6
        DEPOLARIZE2(0.001) 1 4 2 5 3 6
        DEPOLARIZE1(0.001) 0
        TICK
        M(0.001) 4 5 6
        DETECTOR(0.5, 0, 0, 3) rec[-3]
        DETECTOR(1.5, 0, 0, 5) rec[-2]
        DETECTOR(2.5, 0, 0, 3) rec[-1]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE1(0.001) 4 5 6 0 1 2 3
        TICK
        R 4 5 6
        X_ERROR(0.001) 4 5 6
        DEPOLARIZE1(0.001) 0 1 2 3
        TICK
        CX 0 4 1 5 2 6
        DEPOLARIZE2(0.001) 0 4 1 5 2 6
        DEPOLARIZE1(0.001) 3
        TICK
        CX 1 4 2 5 3 6
        DEPOLARIZE2(0.001) 1 4 2 5 3 6
        DEPOLARIZE1(0.001) 0
        TICK
        M(0.001) 4 5 6
        DETECTOR(0.5, 0, 0, 5) rec[-6] rec[-3]
        DETECTOR(1.5, 0, 0, 3) rec[-5] rec[-2]
        DETECTOR(2.5, 0, 0, 3) rec[-4] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE1(0.001) 4 5 6 0 1 2 3
        TICK
        R 4 5 6
        X_ERROR(0.001) 4 5 6
        DEPOLARIZE1(0.001) 0 1 2 3
        TICK
        CX 0 4 1 5 2 6
        DEPOLARIZE2(0.001) 0 4 1 5 2 6
        DEPOLARIZE1(0.001) 3
        TICK
        CX 1 4 2 5 3 6
        DEPOLARIZE2(0.001) 1 4 2 5 3 6
        DEPOLARIZE1(0.001) 0
        TICK
        M(0.001) 0 1 2 3 4 5 6
        DETECTOR(0.5, 0, 0, 3) rec[-10] rec[-3]
        DETECTOR(1.5, 0, 0, 3) rec[-9] rec[-2]
        DETECTOR(2.5, 0, 0, 3) rec[-8] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        DETECTOR(0.5, 0, 0, 3) rec[-7] rec[-6] rec[-3]
        DETECTOR(1.5, 0, 0, 3) rec[-6] rec[-5] rec[-2]
        DETECTOR(2.5, 0, 0, 3) rec[-5] rec[-4] rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-7]
        DEPOLARIZE1(0.001) 0 1 2 3 4 5 6
    """
    )
