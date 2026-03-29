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
from clorco.color_code._mxyz_color_codes import make_mxyz_color_code_from_stim_gen
from clorco.color_code._mxyz_color_codes import make_mxyz_phenom_color_code


@pytest.mark.parametrize(
    "d,r",
    itertools.product(
        [3, 5],
        [2, 3, 4],
    ),
)
def test_make_mxyz_phenom_color_code(d: int, r: int):
    circuit = make_mxyz_phenom_color_code(
        base_width=d,
        rounds=r,
        noise=1e-3,
    )
    assert circuit.detector_error_model() is not None
    err = circuit.search_for_undetectable_logical_errors(
        dont_explore_edges_increasing_symptom_degree=False,
        dont_explore_edges_with_degree_above=4,
        dont_explore_detection_event_sets_with_size_above=4,
        canonicalize_circuit_errors=True,
    )
    assert len(err) == d


def test_make_mxyz_phenom_color_code_exact():
    circuit = make_mxyz_phenom_color_code(
        base_width=3,
        rounds=100,
        noise=1e-3,
    )
    assert circuit == stim.Circuit(
        """
        QUBIT_COORDS(-1, -1) 0
        QUBIT_COORDS(0, 0) 1
        QUBIT_COORDS(1, 1) 2
        QUBIT_COORDS(2, 1) 3
        QUBIT_COORDS(2, 3) 4
        QUBIT_COORDS(3, 0) 5
        QUBIT_COORDS(3, 2) 6
        QUBIT_COORDS(4, 0) 7
        MPP X0*X1*X2*X3*X4*X5*X6*X7
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z1*Z5*Z7
        OBSERVABLE_INCLUDE(1) rec[-1]
        TICK
        MPP Y1*Y2*Y3*Y5 Y2*Y3*Y4*Y6 Y3*Y5*Y6*Y7
        TICK
        MPP Z1*Z2*Z3*Z5 Z2*Z3*Z4*Z6 Z3*Z5*Z6*Z7
        TICK
        REPEAT 33 {
            DEPOLARIZE1(0.001) 1 2 3 4 5 6 7
            MPP(0.001) X1*X2*X3*X5 X2*X3*X4*X6 X3*X5*X6*X7
            DETECTOR(1, 0, 0, 0) rec[-9] rec[-6] rec[-3]
            DETECTOR(1, 2, 0, 2) rec[-8] rec[-5] rec[-2]
            DETECTOR(3, 1, 0, 1) rec[-7] rec[-4] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
            DEPOLARIZE1(0.001) 1 2 3 4 5 6 7
            MPP(0.001) Y1*Y2*Y3*Y5 Y2*Y3*Y4*Y6 Y3*Y5*Y6*Y7
            DETECTOR(1, 0, 0, 1) rec[-9] rec[-6] rec[-3]
            DETECTOR(1, 2, 0, 0) rec[-8] rec[-5] rec[-2]
            DETECTOR(3, 1, 0, 2) rec[-7] rec[-4] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
            DEPOLARIZE1(0.001) 1 2 3 4 5 6 7
            MPP(0.001) Z1*Z2*Z3*Z5 Z2*Z3*Z4*Z6 Z3*Z5*Z6*Z7
            DETECTOR(1, 0, 0, 2) rec[-9] rec[-6] rec[-3]
            DETECTOR(1, 2, 0, 1) rec[-8] rec[-5] rec[-2]
            DETECTOR(3, 1, 0, 0) rec[-7] rec[-4] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
        }
        DEPOLARIZE1(0.001) 1 2 3 4 5 6 7
        MPP(0.001) X1*X2*X3*X5 X2*X3*X4*X6 X3*X5*X6*X7
        DETECTOR(1, 0, 0, 0) rec[-9] rec[-6] rec[-3]
        DETECTOR(1, 2, 0, 2) rec[-8] rec[-5] rec[-2]
        DETECTOR(3, 1, 0, 1) rec[-7] rec[-4] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Y1*Y2*Y3*Y5 Y2*Y3*Y4*Y6 Y3*Y5*Y6*Y7
        DETECTOR(1, 0, 0, 1) rec[-9] rec[-6] rec[-3]
        DETECTOR(1, 2, 0, 0) rec[-8] rec[-5] rec[-2]
        DETECTOR(3, 1, 0, 2) rec[-7] rec[-4] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP Z1*Z2*Z3*Z5 Z2*Z3*Z4*Z6 Z3*Z5*Z6*Z7
        DETECTOR(1, 0, 0, 2) rec[-9] rec[-6] rec[-3]
        DETECTOR(1, 2, 0, 1) rec[-8] rec[-5] rec[-2]
        DETECTOR(3, 1, 0, 0) rec[-7] rec[-4] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X0*X1*X2*X3*X4*X5*X6*X7
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z1*Z5*Z7
        OBSERVABLE_INCLUDE(1) rec[-1]
    """
    )


def test_make_mxyz_color_code_from_stim_gen():
    circuit = make_mxyz_color_code_from_stim_gen(
        distance=5,
        rounds=5,
        noise=gen.NoiseModel.uniform_depolarizing(1e-3),
        convert_to_cz=False,
    )
    assert (
        circuit.num_detectors + circuit.num_observables
        == circuit.count_determined_measurements()
    )
    assert circuit.detector_error_model() is not None
    err = circuit.search_for_undetectable_logical_errors(
        dont_explore_edges_increasing_symptom_degree=False,
        dont_explore_edges_with_degree_above=4,
        dont_explore_detection_event_sets_with_size_above=4,
        canonicalize_circuit_errors=True,
    )
    assert len(err) == 3

    assert circuit == stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(1, 0) 1
        QUBIT_COORDS(2, 0) 2
        QUBIT_COORDS(3, 0) 3
        QUBIT_COORDS(4, 0) 4
        QUBIT_COORDS(5, 0) 5
        QUBIT_COORDS(6, 0) 6
        QUBIT_COORDS(0.5, 1) 7
        QUBIT_COORDS(1.5, 1) 8
        QUBIT_COORDS(2.5, 1) 9
        QUBIT_COORDS(3.5, 1) 10
        QUBIT_COORDS(4.5, 1) 11
        QUBIT_COORDS(5.5, 1) 12
        QUBIT_COORDS(1, 2) 13
        QUBIT_COORDS(2, 2) 14
        QUBIT_COORDS(3, 2) 15
        QUBIT_COORDS(4, 2) 16
        QUBIT_COORDS(5, 2) 17
        QUBIT_COORDS(1.5, 3) 18
        QUBIT_COORDS(2.5, 3) 19
        QUBIT_COORDS(3.5, 3) 20
        QUBIT_COORDS(4.5, 3) 21
        QUBIT_COORDS(2, 4) 22
        QUBIT_COORDS(3, 4) 23
        QUBIT_COORDS(4, 4) 24
        QUBIT_COORDS(2.5, 5) 25
        QUBIT_COORDS(3.5, 5) 26
        QUBIT_COORDS(3, 6) 27
        R 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
        X_ERROR(0.001) 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
        TICK
        C_XYZ 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27 2 5 7 10 14 17 20 22 26
        TICK
        CX 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE2(0.001) 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE1(0.001) 0 1 4 9 12 13 16 17 18 19 24 25 26 27
        TICK
        CX 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE2(0.001) 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 11 15 17 18 21 23 26 27
        TICK
        CX 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE2(0.001) 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE1(0.001) 0 2 3 5 6 8 11 13 15 18 21 23 25 27
        TICK
        CX 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE2(0.001) 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE1(0.001) 0 3 6 7 8 11 12 15 18 21 22 23 24 27
        TICK
        CX 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE2(0.001) 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE1(0.001) 0 1 3 4 6 7 9 12 13 16 19 22 24 25
        TICK
        CX 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE2(0.001) 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE1(0.001) 1 2 4 5 6 9 12 13 16 19 21 24 25 27
        TICK
        MR(0.001) 2 5 7 10 14 17 20 22 26
        X_ERROR(0.001) 2 5 7 10 14 17 20 22 26
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        TICK
        C_XYZ 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27 2 5 7 10 14 17 20 22 26
        TICK
        CX 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE2(0.001) 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE1(0.001) 0 1 4 9 12 13 16 17 18 19 24 25 26 27
        TICK
        CX 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE2(0.001) 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 11 15 17 18 21 23 26 27
        TICK
        CX 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE2(0.001) 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE1(0.001) 0 2 3 5 6 8 11 13 15 18 21 23 25 27
        TICK
        CX 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE2(0.001) 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE1(0.001) 0 3 6 7 8 11 12 15 18 21 22 23 24 27
        TICK
        CX 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE2(0.001) 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE1(0.001) 0 1 3 4 6 7 9 12 13 16 19 22 24 25
        TICK
        CX 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE2(0.001) 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE1(0.001) 1 2 4 5 6 9 12 13 16 19 21 24 25 27
        TICK
        MR(0.001) 2 5 7 10 14 17 20 22 26
        DETECTOR(2, 0, 0, 0) rec[-9] rec[-18]
        DETECTOR(5, 0, 0, 0) rec[-8] rec[-17]
        DETECTOR(0.5, 1, 0, 1) rec[-7] rec[-16]
        DETECTOR(3.5, 1, 0, 1) rec[-6] rec[-15]
        DETECTOR(2, 2, 0, 2) rec[-5] rec[-14]
        DETECTOR(5, 2, 0, 2) rec[-4] rec[-13]
        DETECTOR(3.5, 3, 0, 0) rec[-3] rec[-12]
        DETECTOR(2, 4, 0, 1) rec[-2] rec[-11]
        DETECTOR(3.5, 5, 0, 2) rec[-1] rec[-10]
        X_ERROR(0.001) 2 5 7 10 14 17 20 22 26
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        TICK
        C_XYZ 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27 2 5 7 10 14 17 20 22 26
        TICK
        CX 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE2(0.001) 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE1(0.001) 0 1 4 9 12 13 16 17 18 19 24 25 26 27
        TICK
        CX 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE2(0.001) 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 11 15 17 18 21 23 26 27
        TICK
        CX 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE2(0.001) 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE1(0.001) 0 2 3 5 6 8 11 13 15 18 21 23 25 27
        TICK
        CX 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE2(0.001) 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE1(0.001) 0 3 6 7 8 11 12 15 18 21 22 23 24 27
        TICK
        CX 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE2(0.001) 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE1(0.001) 0 1 3 4 6 7 9 12 13 16 19 22 24 25
        TICK
        CX 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE2(0.001) 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE1(0.001) 1 2 4 5 6 9 12 13 16 19 21 24 25 27
        TICK
        MR(0.001) 2 5 7 10 14 17 20 22 26
        DETECTOR(2, 0, 1, 1) rec[-9] rec[-18] rec[-27]
        DETECTOR(5, 0, 1, 1) rec[-8] rec[-17] rec[-26]
        DETECTOR(0.5, 1, 1, 2) rec[-7] rec[-16] rec[-25]
        DETECTOR(3.5, 1, 1, 2) rec[-6] rec[-15] rec[-24]
        DETECTOR(2, 2, 1, 0) rec[-5] rec[-14] rec[-23]
        DETECTOR(5, 2, 1, 0) rec[-4] rec[-13] rec[-22]
        DETECTOR(3.5, 3, 1, 1) rec[-3] rec[-12] rec[-21]
        DETECTOR(2, 4, 1, 2) rec[-2] rec[-11] rec[-20]
        DETECTOR(3.5, 5, 1, 0) rec[-1] rec[-10] rec[-19]
        X_ERROR(0.001) 2 5 7 10 14 17 20 22 26
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        TICK
        C_XYZ 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27 2 5 7 10 14 17 20 22 26
        TICK
        CX 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE2(0.001) 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE1(0.001) 0 1 4 9 12 13 16 17 18 19 24 25 26 27
        TICK
        CX 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE2(0.001) 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 11 15 17 18 21 23 26 27
        TICK
        CX 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE2(0.001) 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE1(0.001) 0 2 3 5 6 8 11 13 15 18 21 23 25 27
        TICK
        CX 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE2(0.001) 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE1(0.001) 0 3 6 7 8 11 12 15 18 21 22 23 24 27
        TICK
        CX 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE2(0.001) 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE1(0.001) 0 1 3 4 6 7 9 12 13 16 19 22 24 25
        TICK
        CX 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE2(0.001) 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE1(0.001) 1 2 4 5 6 9 12 13 16 19 21 24 25 27
        TICK
        MR(0.001) 2 5 7 10 14 17 20 22 26
        DETECTOR(2, 0, 2, 2) rec[-9] rec[-18] rec[-27]
        DETECTOR(5, 0, 2, 2) rec[-8] rec[-17] rec[-26]
        DETECTOR(0.5, 1, 2, 0) rec[-7] rec[-16] rec[-25]
        DETECTOR(3.5, 1, 2, 0) rec[-6] rec[-15] rec[-24]
        DETECTOR(2, 2, 2, 1) rec[-5] rec[-14] rec[-23]
        DETECTOR(5, 2, 2, 1) rec[-4] rec[-13] rec[-22]
        DETECTOR(3.5, 3, 2, 2) rec[-3] rec[-12] rec[-21]
        DETECTOR(2, 4, 2, 0) rec[-2] rec[-11] rec[-20]
        DETECTOR(3.5, 5, 2, 1) rec[-1] rec[-10] rec[-19]
        X_ERROR(0.001) 2 5 7 10 14 17 20 22 26
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        TICK
        C_XYZ 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27 2 5 7 10 14 17 20 22 26
        TICK
        CX 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE2(0.001) 8 7 3 2 15 14 23 22 11 10 21 20 6 5
        DEPOLARIZE1(0.001) 0 1 4 9 12 13 16 17 18 19 24 25 26 27
        TICK
        CX 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE2(0.001) 13 7 9 2 19 14 25 22 16 10 24 20 12 5
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 11 15 17 18 21 23 26 27
        TICK
        CX 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE2(0.001) 1 7 9 14 19 22 4 10 16 20 24 26 12 17
        DEPOLARIZE1(0.001) 0 2 3 5 6 8 11 13 15 18 21 23 25 27
        TICK
        CX 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE2(0.001) 1 2 13 14 9 10 19 20 25 26 4 5 16 17
        DEPOLARIZE1(0.001) 0 3 6 7 8 11 12 15 18 21 22 23 24 27
        TICK
        CX 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE2(0.001) 8 2 18 14 15 10 23 20 27 26 11 5 21 17
        DEPOLARIZE1(0.001) 0 1 3 4 6 7 9 12 13 16 19 22 24 25
        TICK
        CX 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE2(0.001) 0 7 8 14 18 22 3 10 15 20 23 26 11 17
        DEPOLARIZE1(0.001) 1 2 4 5 6 9 12 13 16 19 21 24 25 27
        TICK
        MR(0.001) 2 5 7 10 14 17 20 22 26
        DETECTOR(2, 0, 3, 0) rec[-9] rec[-18] rec[-27]
        DETECTOR(5, 0, 3, 0) rec[-8] rec[-17] rec[-26]
        DETECTOR(0.5, 1, 3, 1) rec[-7] rec[-16] rec[-25]
        DETECTOR(3.5, 1, 3, 1) rec[-6] rec[-15] rec[-24]
        DETECTOR(2, 2, 3, 2) rec[-5] rec[-14] rec[-23]
        DETECTOR(5, 2, 3, 2) rec[-4] rec[-13] rec[-22]
        DETECTOR(3.5, 3, 3, 0) rec[-3] rec[-12] rec[-21]
        DETECTOR(2, 4, 3, 1) rec[-2] rec[-11] rec[-20]
        DETECTOR(3.5, 5, 3, 2) rec[-1] rec[-10] rec[-19]
        MY(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        DETECTOR(2, 0, 4, 1) rec[-13] rec[-14] rec[-17] rec[-18] rec[-28] rec[-37]
        DETECTOR(5, 0, 4, 1) rec[-11] rec[-12] rec[-15] rec[-16] rec[-27] rec[-36]
        DETECTOR(0.5, 1, 4, 2) rec[-10] rec[-14] rec[-18] rec[-19] rec[-26] rec[-35]
        DETECTOR(3.5, 1, 4, 2) rec[-8] rec[-9] rec[-12] rec[-13] rec[-16] rec[-17] rec[-25] rec[-34]
        DETECTOR(2, 2, 4, 0) rec[-6] rec[-7] rec[-9] rec[-10] rec[-13] rec[-14] rec[-24] rec[-33]
        DETECTOR(5, 2, 4, 0) rec[-5] rec[-8] rec[-11] rec[-12] rec[-23] rec[-32]
        DETECTOR(3.5, 3, 4, 1) rec[-3] rec[-4] rec[-5] rec[-6] rec[-8] rec[-9] rec[-22] rec[-31]
        DETECTOR(2, 4, 4, 2) rec[-2] rec[-4] rec[-6] rec[-7] rec[-21] rec[-30]
        DETECTOR(3.5, 5, 4, 0) rec[-1] rec[-2] rec[-3] rec[-4] rec[-20] rec[-29]
        OBSERVABLE_INCLUDE(0) rec[-15] rec[-16] rec[-17] rec[-18] rec[-19]
        DEPOLARIZE1(0.001) 0 1 3 4 6 8 9 11 12 13 15 16 18 19 21 23 24 25 27
        X_ERROR(0.001) 2 5 7 10 14 17 20 22 26
    """
    )
