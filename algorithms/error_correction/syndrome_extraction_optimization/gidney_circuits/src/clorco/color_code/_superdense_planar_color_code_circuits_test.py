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
from clorco.color_code._superdense_planar_color_code_circuits import (
    make_superdense_color_code_circuit,
)
from clorco.color_code._superdense_planar_color_code_circuits import (
    make_superdense_color_code_circuit_round_chunk,
)


@pytest.mark.parametrize(
    "d,b,i",
    itertools.product(
        [3, 5, 7],
        ["X", "Z"],
        [False, True],
    ),
)
def test_make_superdense_color_code_circuit_round_chunk(d: int, b: Any, i: bool):
    chunk = make_superdense_color_code_circuit_round_chunk(
        base_data_width=d,
        initialize=i,
        basis=b,
    )
    chunk.verify()
    if d == 5:
        if i:
            assert len(chunk.flows) == 3 * 9 + 1
        else:
            assert len(chunk.flows) == 4 * 9 + 1


@pytest.mark.parametrize(
    "d,b,r",
    itertools.product(
        [3, 5],
        ["X", "Z"],
        [2, 3, 5],
    ),
)
def test_make_superdense_color_code_circuit(d: int, b: Any, r: int):
    circuit = make_superdense_color_code_circuit(
        base_data_width=d,
        basis=b,
        rounds=r,
    )
    circuit = gen.NoiseModel.uniform_depolarizing(1e-3).noisy_circuit(circuit)
    assert (
        len(
            circuit.search_for_undetectable_logical_errors(
                dont_explore_detection_event_sets_with_size_above=4,
                dont_explore_edges_with_degree_above=3,
                dont_explore_edges_increasing_symptom_degree=False,
            )
        )
        == d
    )


def test_make_superdense_color_code_circuit_exact():
    circuit = make_superdense_color_code_circuit(
        base_data_width=5,
        basis="X",
        rounds=100,
    )
    assert circuit == stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(1, 0) 1
        QUBIT_COORDS(1, 1) 2
        QUBIT_COORDS(1, 2) 3
        QUBIT_COORDS(2, 0) 4
        QUBIT_COORDS(2, 1) 5
        QUBIT_COORDS(2, 2) 6
        QUBIT_COORDS(2, 3) 7
        QUBIT_COORDS(3, 0) 8
        QUBIT_COORDS(3, 1) 9
        QUBIT_COORDS(3, 2) 10
        QUBIT_COORDS(3, 3) 11
        QUBIT_COORDS(3, 4) 12
        QUBIT_COORDS(3, 5) 13
        QUBIT_COORDS(4, 0) 14
        QUBIT_COORDS(4, 1) 15
        QUBIT_COORDS(4, 2) 16
        QUBIT_COORDS(4, 3) 17
        QUBIT_COORDS(4, 4) 18
        QUBIT_COORDS(4, 5) 19
        QUBIT_COORDS(4, 6) 20
        QUBIT_COORDS(5, 0) 21
        QUBIT_COORDS(5, 1) 22
        QUBIT_COORDS(5, 2) 23
        QUBIT_COORDS(5, 3) 24
        QUBIT_COORDS(5, 4) 25
        QUBIT_COORDS(5, 5) 26
        QUBIT_COORDS(6, 0) 27
        QUBIT_COORDS(6, 1) 28
        QUBIT_COORDS(6, 2) 29
        QUBIT_COORDS(6, 3) 30
        QUBIT_COORDS(6, 4) 31
        QUBIT_COORDS(7, 0) 32
        QUBIT_COORDS(7, 1) 33
        QUBIT_COORDS(7, 2) 34
        QUBIT_COORDS(8, 0) 35
        QUBIT_COORDS(8, 1) 36
        RX 1 3 9 11 13 21 23 25 33 0 2 5 7 8 10 12 14 16 18 20 22 24 26 28 30 32 34 35
        R 4 6 15 17 19 27 29 31 36
        TICK
        CX 1 4 3 6 9 15 11 17 13 19 21 27 23 29 25 31 33 36
        TICK
        CX 2 1 10 9 12 11 22 21 24 23 26 25 34 33 5 4 7 6 16 15 18 17 20 19 28 27 30 29
        TICK
        CX 0 1 5 9 7 11 14 21 16 23 18 25 28 33 8 4 10 6 22 15 24 17 26 19 32 27 34 29
        TICK
        CX 2 3 8 9 10 11 12 13 22 23 24 25 32 33 5 6 14 15 16 17 18 19 28 29 30 31 35 36
        TICK
        CX 1 2 9 10 11 12 21 22 23 24 25 26 33 34 4 5 6 7 15 16 17 18 19 20 27 28 29 30
        TICK
        CX 1 0 9 5 11 7 21 14 23 16 25 18 33 28 4 8 6 10 15 22 17 24 19 26 27 32 29 34
        TICK
        CX 3 2 9 8 11 10 13 12 23 22 25 24 33 32 6 5 15 14 17 16 19 18 29 28 31 30 36 35
        TICK
        CX 1 4 3 6 9 15 11 17 13 19 21 27 23 29 25 31 33 36
        TICK
        MX 1 3 9 11 13 21 23 25 33
        M 4 6 15 17 19 27 29 31 36
        DETECTOR(1, 0, 0, 0) rec[-18]
        DETECTOR(1, 2, 0, 2) rec[-17]
        DETECTOR(3, 1, 0, 1) rec[-16]
        DETECTOR(3, 3, 0, 0) rec[-15]
        DETECTOR(3, 5, 0, 2) rec[-14]
        DETECTOR(5, 0, 0, 0) rec[-13]
        DETECTOR(5, 2, 0, 2) rec[-12]
        DETECTOR(5, 4, 0, 1) rec[-11]
        DETECTOR(7, 1, 0, 1) rec[-10]
        SHIFT_COORDS(0, 0, 1)
        TICK
        REPEAT 98 {
            RX 1 3 9 11 13 21 23 25 33
            R 4 6 15 17 19 27 29 31 36
            TICK
            CX 1 4 3 6 9 15 11 17 13 19 21 27 23 29 25 31 33 36
            TICK
            CX 2 1 10 9 12 11 22 21 24 23 26 25 34 33 5 4 7 6 16 15 18 17 20 19 28 27 30 29
            TICK
            CX 0 1 5 9 7 11 14 21 16 23 18 25 28 33 8 4 10 6 22 15 24 17 26 19 32 27 34 29
            TICK
            CX 2 3 8 9 10 11 12 13 22 23 24 25 32 33 5 6 14 15 16 17 18 19 28 29 30 31 35 36
            TICK
            CX 1 2 9 10 11 12 21 22 23 24 25 26 33 34 4 5 6 7 15 16 17 18 19 20 27 28 29 30
            TICK
            CX 1 0 9 5 11 7 21 14 23 16 25 18 33 28 4 8 6 10 15 22 17 24 19 26 27 32 29 34
            TICK
            CX 3 2 9 8 11 10 13 12 23 22 25 24 33 32 6 5 15 14 17 16 19 18 29 28 31 30 36 35
            TICK
            CX 1 4 3 6 9 15 11 17 13 19 21 27 23 29 25 31 33 36
            TICK
            MX 1 3 9 11 13 21 23 25 33
            M 4 6 15 17 19 27 29 31 36
            DETECTOR(1, 0, 0, 0) rec[-36] rec[-18]
            DETECTOR(1, 2, 0, 2) rec[-35] rec[-17]
            DETECTOR(2, 0, 0, 3) rec[-27] rec[-26] rec[-9]
            DETECTOR(2, 2, 0, 5) rec[-27] rec[-8]
            DETECTOR(3, 1, 0, 1) rec[-34] rec[-16]
            DETECTOR(3, 3, 0, 0) rec[-33] rec[-15]
            DETECTOR(3, 5, 0, 2) rec[-32] rec[-14]
            DETECTOR(4, 1, 0, 4) rec[-24] rec[-7]
            DETECTOR(4, 3, 0, 3) rec[-25] rec[-23] rec[-6]
            DETECTOR(4, 5, 0, 5) rec[-24] rec[-5]
            DETECTOR(5, 0, 0, 0) rec[-31] rec[-13]
            DETECTOR(5, 2, 0, 2) rec[-30] rec[-12]
            DETECTOR(5, 4, 0, 1) rec[-29] rec[-11]
            DETECTOR(6, 0, 0, 3) rec[-22] rec[-21] rec[-4]
            DETECTOR(6, 2, 0, 5) rec[-22] rec[-20] rec[-3]
            DETECTOR(6, 4, 0, 4) rec[-21] rec[-2]
            DETECTOR(7, 1, 0, 1) rec[-28] rec[-10]
            DETECTOR(8, 1, 0, 4) rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
        }
        R 36 31 29 27 19 17 15 6 4
        RX 33 25 23 21 13 11 9 3 1
        TICK
        CX 33 36 25 31 23 29 21 27 13 19 11 17 9 15 3 6 1 4
        TICK
        CX 36 35 31 30 29 28 19 18 17 16 15 14 6 5 33 32 25 24 23 22 13 12 11 10 9 8 3 2
        TICK
        CX 29 34 27 32 19 26 17 24 15 22 6 10 4 8 33 28 25 18 23 16 21 14 11 7 9 5 1 0
        TICK
        CX 29 30 27 28 19 20 17 18 15 16 6 7 4 5 33 34 25 26 23 24 21 22 11 12 9 10 1 2
        TICK
        CX 35 36 30 31 28 29 18 19 16 17 14 15 5 6 32 33 24 25 22 23 12 13 10 11 8 9 2 3
        TICK
        CX 34 29 32 27 26 19 24 17 22 15 10 6 8 4 28 33 18 25 16 23 14 21 7 11 5 9 0 1
        TICK
        CX 30 29 28 27 20 19 18 17 16 15 7 6 5 4 34 33 26 25 24 23 22 21 12 11 10 9 2 1
        TICK
        CX 33 36 25 31 23 29 21 27 13 19 11 17 9 15 3 6 1 4
        TICK
        M 36 31 29 27 19 17 15 6 4
        MX 35 34 32 30 28 26 24 22 20 18 16 14 12 10 8 7 5 2 0 33 25 23 21 13 11 9 3 1
        DETECTOR(1, 0, 0, 0) rec[-14] rec[-12] rec[-11] rec[-10] rec[-2] rec[-1]
        DETECTOR(1, 0, 0, 0) rec[-55] rec[-1]
        DETECTOR(1, 2, 0, 2) rec[-15] rec[-13] rec[-12] rec[-11] rec[-1]
        DETECTOR(1, 2, 0, 2) rec[-54] rec[-2]
        DETECTOR(2, 0, 0, 3) rec[-46] rec[-45] rec[-29]
        DETECTOR(2, 2, 0, 5) rec[-46] rec[-30]
        DETECTOR(3, 1, 0, 1) rec[-21] rec[-18] rec[-17] rec[-15] rec[-14] rec[-12] rec[-4]
        DETECTOR(3, 1, 0, 1) rec[-53] rec[-3]
        DETECTOR(3, 3, 0, 0) rec[-22] rec[-19] rec[-18] rec[-16] rec[-15] rec[-13] rec[-5] rec[-3]
        DETECTOR(3, 3, 0, 0) rec[-52] rec[-4]
        DETECTOR(3, 5, 0, 2) rec[-23] rec[-20] rec[-19] rec[-16] rec[-4]
        DETECTOR(3, 5, 0, 2) rec[-51] rec[-5]
        DETECTOR(4, 1, 0, 4) rec[-43] rec[-31]
        DETECTOR(4, 3, 0, 3) rec[-44] rec[-42] rec[-32]
        DETECTOR(4, 5, 0, 5) rec[-43] rec[-33]
        DETECTOR(5, 0, 0, 0) rec[-26] rec[-24] rec[-21] rec[-17] rec[-7] rec[-6]
        DETECTOR(5, 0, 0, 0) rec[-50] rec[-6]
        DETECTOR(5, 2, 0, 2) rec[-27] rec[-25] rec[-24] rec[-22] rec[-21] rec[-18] rec[-8] rec[-6]
        DETECTOR(5, 2, 0, 2) rec[-49] rec[-7]
        DETECTOR(5, 4, 0, 1) rec[-25] rec[-23] rec[-22] rec[-19] rec[-7]
        DETECTOR(5, 4, 0, 1) rec[-48] rec[-8]
        DETECTOR(6, 0, 0, 3) rec[-41] rec[-40] rec[-34]
        DETECTOR(6, 2, 0, 5) rec[-41] rec[-39] rec[-35]
        DETECTOR(6, 4, 0, 4) rec[-40] rec[-36]
        DETECTOR(7, 1, 0, 1) rec[-28] rec[-27] rec[-26] rec[-24]
        DETECTOR(7, 1, 0, 1) rec[-47] rec[-9]
        DETECTOR(8, 1, 0, 4) rec[-37]
        OBSERVABLE_INCLUDE(0) rec[-28] rec[-27] rec[-26] rec[-25] rec[-24] rec[-23] rec[-22] rec[-21] rec[-20] rec[-19] rec[-18] rec[-17] rec[-16] rec[-15] rec[-14] rec[-13] rec[-12] rec[-11] rec[-10] rec[-9] rec[-8] rec[-7] rec[-5] rec[-4] rec[-3] rec[-2]
        SHIFT_COORDS(0, 0, 1)
        TICK
    """
    )
