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

import itertools

import pytest

import gen
from clorco.rep_code._rep_code_circuits import make_rep_code_circuit


@pytest.mark.parametrize(
    "d,toric,rounds",
    itertools.product(
        [3, 4, 5, 6],
        [False, True],
        [3, 4, 5],
    ),
)
def test_make_rep_code_circuit(d: int, toric: bool, rounds: int):
    c = make_rep_code_circuit(
        distance=d,
        toric=toric,
        rounds=rounds,
    )
    c = gen.NoiseModel.uniform_depolarizing(1e-3).noisy_circuit(c)
    assert c.detector_error_model(decompose_errors=True) is not None
    assert len(c.shortest_graphlike_error()) == d
    assert gen.count_measurement_layers(c) == rounds
    assert (
        c.count_determined_measurements() == c.num_observables + c.num_detectors - toric
    )
