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
import stim

import chromobius


def test_errors():
    with pytest.raises(ValueError, match="must be a stim.DetectorErrorModel"):
        chromobius.compile_decoder_for_dem(object())
    with pytest.raises(ValueError, match="4th coordinate"):
        chromobius.compile_decoder_for_dem(
            stim.DetectorErrorModel(
                """
            error(0.1) D0
        """
            )
        )


def test_decoding():
    color_rep_code = stim.Circuit(
        """
        X_ERROR(0.1) 0 1 2 3 4 5 6 7 8
        M 0 1 2 3 4 5 6 7 8
        DETECTOR(0, 0, 0, 0) rec[-9] rec[-8] rec[-7]
        DETECTOR(1, 0, 0, 1) rec[-8] rec[-7] rec[-6]
        DETECTOR(2, 0, 0, 2) rec[-7] rec[-6] rec[-5]
        DETECTOR(3, 0, 0, 0) rec[-6] rec[-5] rec[-4]
        DETECTOR(4, 0, 0, 1) rec[-5] rec[-4] rec[-3]
        DETECTOR(5, 0, 0, 2) rec[-4] rec[-3] rec[-2]
        DETECTOR(6, 0, 0, 0) rec[-3] rec[-2] rec[-1]
        DETECTOR(7, 0, 0, 1) rec[-2] rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
        OBSERVABLE_INCLUDE(1) rec[-2]
        OBSERVABLE_INCLUDE(2) rec[-3]
        OBSERVABLE_INCLUDE(3) rec[-4]
        OBSERVABLE_INCLUDE(4) rec[-5]
        OBSERVABLE_INCLUDE(5) rec[-6]
        OBSERVABLE_INCLUDE(6) rec[-7]
        OBSERVABLE_INCLUDE(7) rec[-8]
        OBSERVABLE_INCLUDE(8) rec[-9]
    """
    )

    err = color_rep_code.search_for_undetectable_logical_errors(
        dont_explore_detection_event_sets_with_size_above=7,
        dont_explore_edges_increasing_symptom_degree=False,
        dont_explore_edges_with_degree_above=10,
        canonicalize_circuit_errors=True,
    )
    assert len(err) == 6

    decoder = chromobius.compile_decoder_for_dem(color_rep_code.detector_error_model())
    decoder2 = chromobius.CompiledDecoder.from_dem(
        color_rep_code.detector_error_model()
    )
    shots = 1024
    dets, obs = color_rep_code.compile_detector_sampler().sample(
        shots=shots, separate_observables=True, bit_packed=True
    )
    predictions = decoder.predict_obs_flips_from_dets_bit_packed(dets)
    predictions2 = decoder2.predict_obs_flips_from_dets_bit_packed(dets)
    assert np.array_equal(predictions, predictions2)
    mistakes = np.count_nonzero(np.any(predictions != obs, axis=1))
    assert mistakes < 100
