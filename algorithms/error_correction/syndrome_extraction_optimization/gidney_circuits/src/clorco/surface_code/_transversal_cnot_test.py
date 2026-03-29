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
from typing import Any

import pytest
import stim

import gen
from clorco.surface_code._transversal_cnot import (
    make_transversal_cnot_surface_code_circuit,
)


@pytest.mark.parametrize(
    "d,b",
    itertools.product(
        [3, 4, 5],
        ["X", "Z", "MagicEPR"],
    ),
)
def test_make_transversal_cnot_surface_code_circuit(d: int, b: Any):
    c = make_transversal_cnot_surface_code_circuit(
        diameter=d,
        basis=b,
        pad_rounds=2,
        noise=gen.NoiseModel.uniform_depolarizing(1e-3),
        convert_to_z=True,
    )
    err = c.search_for_undetectable_logical_errors(
        dont_explore_edges_with_degree_above=3,
        dont_explore_detection_event_sets_with_size_above=5,
        dont_explore_edges_increasing_symptom_degree=False,
        canonicalize_circuit_errors=True,
    )
    assert len(err) == d
    if b == "MagicEPR":
        assert gen.count_measurement_layers(c) == 6
        assert c.num_observables == 4
        assert (
            c.count_determined_measurements()
            == c.num_detectors + c.num_observables + 6 * (d % 2 == 0)
        )
    else:
        assert gen.count_measurement_layers(c) == 4
        assert c.num_observables == 2
        assert c.count_determined_measurements() == c.num_detectors + c.num_observables


def test_make_transversal_cnot_surface_code_circuit_exact():
    assert make_transversal_cnot_surface_code_circuit(
        diameter=3,
        basis="MagicEPR",
        pad_rounds=2,
        noise=None,
        convert_to_z=False,
    ) == stim.Circuit(
        """
        QUBIT_COORDS(-2, 0) 0
        QUBIT_COORDS(-1, 0) 1
        QUBIT_COORDS(0, 0) 2
        QUBIT_COORDS(0, 1) 3
        QUBIT_COORDS(0, 2) 4
        QUBIT_COORDS(1, 0) 5
        QUBIT_COORDS(1, 1) 6
        QUBIT_COORDS(1, 2) 7
        QUBIT_COORDS(2, 0) 8
        QUBIT_COORDS(2, 1) 9
        QUBIT_COORDS(2, 2) 10
        QUBIT_COORDS(5, 0) 11
        QUBIT_COORDS(5, 1) 12
        QUBIT_COORDS(5, 2) 13
        QUBIT_COORDS(6, 0) 14
        QUBIT_COORDS(6, 1) 15
        QUBIT_COORDS(6, 2) 16
        QUBIT_COORDS(7, 0) 17
        QUBIT_COORDS(7, 1) 18
        QUBIT_COORDS(7, 2) 19
        QUBIT_COORDS(-0.5, 0.5) 20
        QUBIT_COORDS(0.5, 0.5) 21
        QUBIT_COORDS(0.5, 1.5) 22
        QUBIT_COORDS(0.5, 2.5) 23
        QUBIT_COORDS(1.5, -0.5) 24
        QUBIT_COORDS(1.5, 0.5) 25
        QUBIT_COORDS(1.5, 1.5) 26
        QUBIT_COORDS(2.5, 1.5) 27
        QUBIT_COORDS(4.5, 0.5) 28
        QUBIT_COORDS(5.5, 0.5) 29
        QUBIT_COORDS(5.5, 1.5) 30
        QUBIT_COORDS(5.5, 2.5) 31
        QUBIT_COORDS(6.5, -0.5) 32
        QUBIT_COORDS(6.5, 0.5) 33
        QUBIT_COORDS(6.5, 1.5) 34
        QUBIT_COORDS(7.5, 1.5) 35
        RY 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
        MPP X1*X2*X3*X4 Z1*Z2*Z5*Z8 X0*X11*X12*X13 Z0*Z11*Z14*Z17
        OBSERVABLE_INCLUDE(0) rec[-4]
        OBSERVABLE_INCLUDE(1) rec[-3]
        OBSERVABLE_INCLUDE(2) rec[-2]
        OBSERVABLE_INCLUDE(3) rec[-1]
        MPP X2*X3*X5*X6 X4*X7 X5*X8 X6*X7*X9*X10 X11*X12*X14*X15 X13*X16 X14*X17 X15*X16*X18*X19 Z2*Z3 Z3*Z4*Z6*Z7 Z5*Z6*Z8*Z9 Z9*Z10 Z11*Z12 Z12*Z13*Z15*Z16 Z14*Z15*Z17*Z18 Z18*Z19
        SHIFT_COORDS(0, 0, 1)
        TICK
        REPEAT 2 {
            RX 21 23 24 26 29 31 32 34
            R 20 22 25 27 28 30 33 35
            TICK
            CX 3 22 5 25 9 27 12 30 14 33 18 35 21 2 23 4 26 6 29 11 31 13 34 15
            TICK
            CX 4 22 6 25 10 27 13 30 15 33 19 35 21 5 23 7 26 9 29 14 31 16 34 18
            TICK
            CX 2 20 6 22 8 25 11 28 15 30 17 33 21 3 24 5 26 7 29 12 32 14 34 16
            TICK
            CX 3 20 7 22 9 25 12 28 16 30 18 33 21 6 24 8 26 10 29 15 32 17 34 19
            TICK
            MX 21 23 24 26 29 31 32 34
            M 20 22 25 27 28 30 33 35
            DETECTOR(-0.5, 0.5, 0, 3) rec[-24] rec[-8]
            DETECTOR(0.5, 0.5, 0, 0) rec[-32] rec[-16]
            DETECTOR(0.5, 1.5, 0, 3) rec[-23] rec[-7]
            DETECTOR(0.5, 2.5, 0, 0) rec[-31] rec[-15]
            DETECTOR(1.5, -0.5, 0, 0) rec[-30] rec[-14]
            DETECTOR(1.5, 0.5, 0, 3) rec[-22] rec[-6]
            DETECTOR(1.5, 1.5, 0, 0) rec[-29] rec[-13]
            DETECTOR(2.5, 1.5, 0, 3) rec[-21] rec[-5]
            DETECTOR(4.5, 0.5, 0, 3) rec[-20] rec[-4]
            DETECTOR(5.5, 0.5, 0, 0) rec[-28] rec[-12]
            DETECTOR(5.5, 1.5, 0, 3) rec[-19] rec[-3]
            DETECTOR(5.5, 2.5, 0, 0) rec[-27] rec[-11]
            DETECTOR(6.5, -0.5, 0, 0) rec[-26] rec[-10]
            DETECTOR(6.5, 0.5, 0, 3) rec[-18] rec[-2]
            DETECTOR(6.5, 1.5, 0, 0) rec[-25] rec[-9]
            DETECTOR(7.5, 1.5, 0, 3) rec[-17] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
        }
        CX 2 11 3 12 4 13 5 14 6 15 7 16 8 17 9 18 10 19
        TICK
        RX 21 23 24 26 29 31 32 34
        R 20 22 25 27 28 30 33 35
        TICK
        CX 3 22 5 25 9 27 12 30 14 33 18 35 21 2 23 4 26 6 29 11 31 13 34 15
        TICK
        CX 4 22 6 25 10 27 13 30 15 33 19 35 21 5 23 7 26 9 29 14 31 16 34 18
        TICK
        CX 2 20 6 22 8 25 11 28 15 30 17 33 21 3 24 5 26 7 29 12 32 14 34 16
        TICK
        CX 3 20 7 22 9 25 12 28 16 30 18 33 21 6 24 8 26 10 29 15 32 17 34 19
        TICK
        MX 21 23 24 26 29 31 32 34
        M 20 22 25 27 28 30 33 35
        DETECTOR(-0.5, 0.5, 0, 5) rec[-24] rec[-8]
        DETECTOR(0.5, 0.5, 0, 2) rec[-32] rec[-16] rec[-12]
        DETECTOR(0.5, 1.5, 0, 5) rec[-23] rec[-7]
        DETECTOR(0.5, 2.5, 0, 2) rec[-31] rec[-15] rec[-11]
        DETECTOR(1.5, -0.5, 0, 2) rec[-30] rec[-14] rec[-10]
        DETECTOR(1.5, 0.5, 0, 5) rec[-22] rec[-6]
        DETECTOR(1.5, 1.5, 0, 2) rec[-29] rec[-13] rec[-9]
        DETECTOR(2.5, 1.5, 0, 5) rec[-21] rec[-5]
        DETECTOR(4.5, 0.5, 0, 4) rec[-20] rec[-8] rec[-4]
        DETECTOR(5.5, 0.5, 0, 1) rec[-28] rec[-12]
        DETECTOR(5.5, 1.5, 0, 4) rec[-19] rec[-7] rec[-3]
        DETECTOR(5.5, 2.5, 0, 1) rec[-27] rec[-11]
        DETECTOR(6.5, -0.5, 0, 1) rec[-26] rec[-10]
        DETECTOR(6.5, 0.5, 0, 4) rec[-18] rec[-6] rec[-2]
        DETECTOR(6.5, 1.5, 0, 1) rec[-25] rec[-9]
        DETECTOR(7.5, 1.5, 0, 4) rec[-17] rec[-5] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        RX 21 23 24 26 29 31 32 34
        R 20 22 25 27 28 30 33 35
        TICK
        CX 3 22 5 25 9 27 12 30 14 33 18 35 21 2 23 4 26 6 29 11 31 13 34 15
        TICK
        CX 4 22 6 25 10 27 13 30 15 33 19 35 21 5 23 7 26 9 29 14 31 16 34 18
        TICK
        CX 2 20 6 22 8 25 11 28 15 30 17 33 21 3 24 5 26 7 29 12 32 14 34 16
        TICK
        CX 3 20 7 22 9 25 12 28 16 30 18 33 21 6 24 8 26 10 29 15 32 17 34 19
        TICK
        MX 21 23 24 26 29 31 32 34
        M 20 22 25 27 28 30 33 35
        DETECTOR(-0.5, 0.5, 0, 3) rec[-24] rec[-8]
        DETECTOR(0.5, 0.5, 0, 0) rec[-32] rec[-16]
        DETECTOR(0.5, 1.5, 0, 3) rec[-23] rec[-7]
        DETECTOR(0.5, 2.5, 0, 0) rec[-31] rec[-15]
        DETECTOR(1.5, -0.5, 0, 0) rec[-30] rec[-14]
        DETECTOR(1.5, 0.5, 0, 3) rec[-22] rec[-6]
        DETECTOR(1.5, 1.5, 0, 0) rec[-29] rec[-13]
        DETECTOR(2.5, 1.5, 0, 3) rec[-21] rec[-5]
        DETECTOR(4.5, 0.5, 0, 3) rec[-20] rec[-4]
        DETECTOR(5.5, 0.5, 0, 0) rec[-28] rec[-12]
        DETECTOR(5.5, 1.5, 0, 3) rec[-19] rec[-3]
        DETECTOR(5.5, 2.5, 0, 0) rec[-27] rec[-11]
        DETECTOR(6.5, -0.5, 0, 0) rec[-26] rec[-10]
        DETECTOR(6.5, 0.5, 0, 3) rec[-18] rec[-2]
        DETECTOR(6.5, 1.5, 0, 0) rec[-25] rec[-9]
        DETECTOR(7.5, 1.5, 0, 3) rec[-17] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        MPP X2*X3*X5*X6 X4*X7 X5*X8 X6*X7*X9*X10 X11*X12*X14*X15 X13*X16 X14*X17 X15*X16*X18*X19 Z2*Z3 Z3*Z4*Z6*Z7 Z5*Z6*Z8*Z9 Z9*Z10 Z11*Z12 Z12*Z13*Z15*Z16 Z14*Z15*Z17*Z18 Z18*Z19
        DETECTOR(-0.5, 0.5, 0, 3) rec[-24] rec[-8]
        DETECTOR(0.5, 0.5, 0, 0) rec[-32] rec[-16]
        DETECTOR(0.5, 1.5, 0, 3) rec[-23] rec[-7]
        DETECTOR(0.5, 2.5, 0, 0) rec[-31] rec[-15]
        DETECTOR(1.5, -0.5, 0, 0) rec[-30] rec[-14]
        DETECTOR(1.5, 0.5, 0, 3) rec[-22] rec[-6]
        DETECTOR(1.5, 1.5, 0, 0) rec[-29] rec[-13]
        DETECTOR(2.5, 1.5, 0, 3) rec[-21] rec[-5]
        DETECTOR(4.5, 0.5, 0, 3) rec[-20] rec[-4]
        DETECTOR(5.5, 0.5, 0, 0) rec[-28] rec[-12]
        DETECTOR(5.5, 1.5, 0, 3) rec[-19] rec[-3]
        DETECTOR(5.5, 2.5, 0, 0) rec[-27] rec[-11]
        DETECTOR(6.5, -0.5, 0, 0) rec[-26] rec[-10]
        DETECTOR(6.5, 0.5, 0, 3) rec[-18] rec[-2]
        DETECTOR(6.5, 1.5, 0, 0) rec[-25] rec[-9]
        DETECTOR(7.5, 1.5, 0, 3) rec[-17] rec[-1]
        MPP X1*X2*X3*X4*X11*X12*X13 Z1*Z2*Z5*Z8 X0*X11*X12*X13 Z0*Z2*Z5*Z8*Z11*Z14*Z17
        OBSERVABLE_INCLUDE(0) rec[-4]
        OBSERVABLE_INCLUDE(1) rec[-3]
        OBSERVABLE_INCLUDE(2) rec[-2]
        OBSERVABLE_INCLUDE(3) rec[-1]
    """
    )
