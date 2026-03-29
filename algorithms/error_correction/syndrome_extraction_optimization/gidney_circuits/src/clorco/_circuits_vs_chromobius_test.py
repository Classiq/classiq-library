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

import numpy as np
import pytest
import sinter

import gen
from clorco._make_circuit import CONSTRUCTIONS
from clorco._make_circuit import make_circuit
import chromobius


@pytest.mark.parametrize(
    "style", [style for style in CONSTRUCTIONS.keys() if "mxyz_" not in style]
)
def test_constructions_are_decoded(style: str):
    r = 1 if style.startswith("transit") else 6
    d = 12 if "toric_" in style else 11
    circuit = make_circuit(
        style=style,
        noise_model=gen.NoiseModel.uniform_depolarizing(1e-3),
        noise_strength=1e-3,
        rounds=r,
        diameter=d,
        convert_to_cz=True,
        editable_extras={},
    )
    decoder = chromobius.compile_decoder_for_dem(circuit.detector_error_model())

    shots = 2048
    assert 0 < circuit.num_observables <= 8
    dets, obs = circuit.compile_detector_sampler().sample(
        shots=shots, separate_observables=True, bit_packed=True
    )
    predictions = decoder.predict_obs_flips_from_dets_bit_packed(dets)
    mistakes = np.count_nonzero(np.any(predictions != obs, axis=1))
    assert mistakes / shots < 0.42, (mistakes, shots)
