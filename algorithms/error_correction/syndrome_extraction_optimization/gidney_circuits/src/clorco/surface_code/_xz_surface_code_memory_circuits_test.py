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
import stim

import gen
from clorco._make_circuit import make_circuit


@pytest.mark.parametrize("basis,diameter", itertools.product(["X", "Z"], [2, 3, 4, 5]))
def test_make_xz_memory_experiment(basis: str, diameter: int):
    circuit = make_circuit(
        style=f"surface_code_{basis}",
        diameter=diameter,
        rounds=5,
        noise_model=gen.NoiseModel.uniform_depolarizing(1e-3),
        noise_strength=1e-3,
        convert_to_cz=True,
        editable_extras={},
    )

    dem = circuit.detector_error_model(
        decompose_errors=True, block_decomposition_from_introducing_remnant_edges=True
    )
    assert dem is not None

    actual_distance = len(circuit.shortest_graphlike_error())
    expected_distance = diameter
    assert actual_distance == expected_distance


@pytest.mark.parametrize(
    "basis,diameter,rounds", itertools.product(["X", "Z"], [3, 4, 5], [0, 5])
)
def test_have_all_detectors(basis: str, diameter: int, rounds: int):
    c = make_circuit(
        style=f"surface_code_{basis}",
        diameter=diameter,
        noise_model=gen.NoiseModel.uniform_depolarizing(1e-3),
        noise_strength=1e-3,
        convert_to_cz=True,
        editable_extras={},
        rounds=3,
    )
    assert c.detector_error_model() is not None
    assert c.count_determined_measurements() == c.num_observables + c.num_detectors


def test_exact_circuit_x():
    assert make_circuit(
        style="surface_code_X",
        diameter=3,
        noise_model=gen.NoiseModel.uniform_depolarizing(1e-3),
        noise_strength=1e-3,
        convert_to_cz=True,
        editable_extras={},
        rounds=100,
    ) == stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(0, 2) 2
        QUBIT_COORDS(1, 0) 3
        QUBIT_COORDS(1, 1) 4
        QUBIT_COORDS(1, 2) 5
        QUBIT_COORDS(2, 0) 6
        QUBIT_COORDS(2, 1) 7
        QUBIT_COORDS(2, 2) 8
        QUBIT_COORDS(-0.5, 1.5) 9
        QUBIT_COORDS(0.5, -0.5) 10
        QUBIT_COORDS(0.5, 0.5) 11
        QUBIT_COORDS(0.5, 1.5) 12
        QUBIT_COORDS(1.5, 0.5) 13
        QUBIT_COORDS(1.5, 1.5) 14
        QUBIT_COORDS(1.5, 2.5) 15
        QUBIT_COORDS(2.5, 0.5) 16
        R 10 12 13 15 0 1 2 3 4 5 6 7 8 9 11 14 16
        X_ERROR(0.001) 10 12 13 15 0 1 2 3 4 5 6 7 8 9 11 14 16
        TICK
        H 0 1 2 3 7 9 10 11 12 13 14 15 16
        DEPOLARIZE1(0.001) 0 1 2 3 7 9 10 11 12 13 14 15 16 4 5 6 8
        TICK
        CZ 1 9 3 11 4 12 6 13 7 14 8 15
        DEPOLARIZE2(0.001) 1 9 3 11 4 12 6 13 7 14 8 15
        DEPOLARIZE1(0.001) 0 2 5 10 16
        TICK
        H 1 3 4 6 7 8
        DEPOLARIZE1(0.001) 1 3 4 6 7 8 0 2 5 9 10 11 12 13 14 15 16
        TICK
        CZ 1 12 2 9 3 13 4 11 5 15 8 14
        DEPOLARIZE2(0.001) 1 12 2 9 3 13 4 11 5 15 8 14
        DEPOLARIZE1(0.001) 0 6 7 10 16
        TICK
        CZ 0 11 3 10 4 14 5 12 6 16 7 13
        DEPOLARIZE2(0.001) 0 11 3 10 4 14 5 12 6 16 7 13
        DEPOLARIZE1(0.001) 1 2 8 9 15
        TICK
        H 0 1 2 3 4 5 7 9
        DEPOLARIZE1(0.001) 0 1 2 3 4 5 7 9 6 8 10 11 12 13 14 15 16
        TICK
        CZ 0 10 1 11 2 12 4 13 5 14 7 16
        DEPOLARIZE2(0.001) 0 10 1 11 2 12 4 13 5 14 7 16
        DEPOLARIZE1(0.001) 3 6 8 9 15
        TICK
        H 0 2 4 10 11 12 13 14 15 16
        DEPOLARIZE1(0.001) 0 2 4 10 11 12 13 14 15 16 1 3 5 6 7 8 9
        TICK
        M(0.001) 10 12 13 15 9 11 14 16
        DETECTOR(0.5, -0.5, 0, 1) rec[-8]
        DETECTOR(0.5, 1.5, 0, 1) rec[-7]
        DETECTOR(1.5, 0.5, 0, 0) rec[-6]
        DETECTOR(1.5, 2.5, 0, 0) rec[-5]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE1(0.001) 10 12 13 15 9 11 14 16 0 1 2 3 4 5 6 7 8
        TICK
        REPEAT 98 {
            R 10 12 13 15 9 11 14 16
            X_ERROR(0.001) 10 12 13 15 9 11 14 16
            DEPOLARIZE1(0.001) 0 1 2 3 4 5 6 7 8
            TICK
            H 4 6 8 9 10 11 12 13 14 15 16
            DEPOLARIZE1(0.001) 4 6 8 9 10 11 12 13 14 15 16 0 1 2 3 5 7
            TICK
            CZ 1 9 3 11 4 12 6 13 7 14 8 15
            DEPOLARIZE2(0.001) 1 9 3 11 4 12 6 13 7 14 8 15
            DEPOLARIZE1(0.001) 0 2 5 10 16
            TICK
            H 1 3 4 5 6 7 8
            DEPOLARIZE1(0.001) 1 3 4 5 6 7 8 0 2 9 10 11 12 13 14 15 16
            TICK
            CZ 1 12 2 9 3 13 4 11 5 15 8 14
            DEPOLARIZE2(0.001) 1 12 2 9 3 13 4 11 5 15 8 14
            DEPOLARIZE1(0.001) 0 6 7 10 16
            TICK
            CZ 0 11 3 10 4 14 5 12 6 16 7 13
            DEPOLARIZE2(0.001) 0 11 3 10 4 14 5 12 6 16 7 13
            DEPOLARIZE1(0.001) 1 2 8 9 15
            TICK
            H 0 1 2 3 4 5 7 9
            DEPOLARIZE1(0.001) 0 1 2 3 4 5 7 9 6 8 10 11 12 13 14 15 16
            TICK
            CZ 0 10 1 11 2 12 4 13 5 14 7 16
            DEPOLARIZE2(0.001) 0 10 1 11 2 12 4 13 5 14 7 16
            DEPOLARIZE1(0.001) 3 6 8 9 15
            TICK
            H 0 2 4 10 11 12 13 14 15 16
            DEPOLARIZE1(0.001) 0 2 4 10 11 12 13 14 15 16 1 3 5 6 7 8 9
            TICK
            M(0.001) 10 12 13 15 9 11 14 16
            DETECTOR(-0.5, 1.5, 0, 3) rec[-12] rec[-4]
            DETECTOR(0.5, -0.5, 0, 1) rec[-16] rec[-8]
            DETECTOR(0.5, 0.5, 0, 4) rec[-11] rec[-3]
            DETECTOR(0.5, 1.5, 0, 1) rec[-15] rec[-7]
            DETECTOR(1.5, 0.5, 0, 0) rec[-14] rec[-6]
            DETECTOR(1.5, 1.5, 0, 3) rec[-10] rec[-2]
            DETECTOR(1.5, 2.5, 0, 0) rec[-13] rec[-5]
            DETECTOR(2.5, 0.5, 0, 4) rec[-9] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE1(0.001) 10 12 13 15 9 11 14 16 0 1 2 3 4 5 6 7 8
            TICK
        }
        R 10 12 13 15 9 11 14 16
        X_ERROR(0.001) 10 12 13 15 9 11 14 16
        DEPOLARIZE1(0.001) 0 1 2 3 4 5 6 7 8
        TICK
        H 4 6 8 9 10 11 12 13 14 15 16
        DEPOLARIZE1(0.001) 4 6 8 9 10 11 12 13 14 15 16 0 1 2 3 5 7
        TICK
        CZ 1 9 3 11 4 12 6 13 7 14 8 15
        DEPOLARIZE2(0.001) 1 9 3 11 4 12 6 13 7 14 8 15
        DEPOLARIZE1(0.001) 0 2 5 10 16
        TICK
        H 1 3 4 5 6 7 8
        DEPOLARIZE1(0.001) 1 3 4 5 6 7 8 0 2 9 10 11 12 13 14 15 16
        TICK
        CZ 1 12 2 9 3 13 4 11 5 15 8 14
        DEPOLARIZE2(0.001) 1 12 2 9 3 13 4 11 5 15 8 14
        DEPOLARIZE1(0.001) 0 6 7 10 16
        TICK
        CZ 0 11 3 10 4 14 5 12 6 16 7 13
        DEPOLARIZE2(0.001) 0 11 3 10 4 14 5 12 6 16 7 13
        DEPOLARIZE1(0.001) 1 2 8 9 15
        TICK
        H 0 1 2 4 5 6 7 9
        DEPOLARIZE1(0.001) 0 1 2 4 5 6 7 9 3 8 10 11 12 13 14 15 16
        TICK
        CZ 0 10 1 11 2 12 4 13 5 14 7 16
        DEPOLARIZE2(0.001) 0 10 1 11 2 12 4 13 5 14 7 16
        DEPOLARIZE1(0.001) 3 6 8 9 15
        TICK
        H 1 5 7 8 10 11 12 13 14 15 16
        DEPOLARIZE1(0.001) 1 5 7 8 10 11 12 13 14 15 16 0 2 3 4 6 9
        TICK
        M(0.001) 10 12 13 15 0 1 2 3 4 5 6 7 8 9 11 14 16
        DETECTOR(-0.5, 1.5, 0, 3) rec[-21] rec[-4]
        DETECTOR(0.5, -0.5, 0, 1) rec[-25] rec[-17]
        DETECTOR(0.5, 0.5, 0, 4) rec[-20] rec[-3]
        DETECTOR(0.5, 1.5, 0, 1) rec[-24] rec[-16]
        DETECTOR(1.5, 0.5, 0, 0) rec[-23] rec[-15]
        DETECTOR(1.5, 1.5, 0, 3) rec[-19] rec[-2]
        DETECTOR(1.5, 2.5, 0, 0) rec[-22] rec[-14]
        DETECTOR(2.5, 0.5, 0, 4) rec[-18] rec[-1]
        DETECTOR(0.5, -0.5, 0, 1) rec[-17] rec[-13] rec[-10]
        DETECTOR(0.5, 1.5, 0, 1) rec[-16] rec[-12] rec[-11] rec[-9] rec[-8]
        DETECTOR(1.5, 0.5, 0, 0) rec[-15] rec[-10] rec[-9] rec[-7] rec[-6]
        DETECTOR(1.5, 2.5, 0, 0) rec[-14] rec[-8] rec[-5]
        OBSERVABLE_INCLUDE(0) rec[-13] rec[-12] rec[-11]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE1(0.001) 10 12 13 15 0 1 2 3 4 5 6 7 8 9 11 14 16
    """
    )
