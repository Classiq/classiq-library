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
from clorco.color_code._toric_color_code_circuits import (
    make_toric_color_code_circuit_with_magic_time_boundaries,
    make_toric_color_code_circuit_double_round_chunk_midout,
    make_toric_color_code_circuit_round_chunk_superdense,
)


@pytest.mark.parametrize("style", ["superdense"])
def test_make_toric_color_code_circuit_round_chunk(style: Any):
    make_toric_color_code_circuit_round_chunk_superdense(
        width=6,
        height=8,
        ablate_into_matchable_code=False,
        convert_to_cz=False,
    ).verify()
    make_toric_color_code_circuit_round_chunk_superdense(
        width=6,
        height=8,
        ablate_into_matchable_code=True,
        convert_to_cz=False,
    ).verify()


def test_make_toric_color_code_circuit_round_chunk_inplace():
    make_toric_color_code_circuit_double_round_chunk_midout(
        width=6,
        height=8,
        ablate_into_matchable_code=False,
        convert_to_cz=False,
    ).verify()
    make_toric_color_code_circuit_double_round_chunk_midout(
        width=6,
        height=8,
        ablate_into_matchable_code=True,
        convert_to_cz=False,
    ).verify()


@pytest.mark.parametrize(
    "width,height,style,ablate_into_matchable_code",
    itertools.product(
        [6, 12],
        [4, 8],
        ["superdense", "midout"],
        [False, True],
    ),
)
def test_make_toric_color_code_circuit_with_magic_time_boundaries(
    width: int, height: int, style: Any, ablate_into_matchable_code: bool
):
    circuit = make_toric_color_code_circuit_with_magic_time_boundaries(
        width=width,
        height=height,
        rounds=4,
        noise=gen.NoiseModel.uniform_depolarizing(1e-3),
        style=style,
        ablate_into_matchable_code=ablate_into_matchable_code,
        convert_to_cz=False,
    )
    assert gen.count_measurement_layers(circuit) == 4 + 2
    if ablate_into_matchable_code:
        err = circuit.shortest_graphlike_error(
            canonicalize_circuit_errors=True,
        )
    else:
        err = circuit.search_for_undetectable_logical_errors(
            dont_explore_edges_increasing_symptom_degree=False,
            dont_explore_edges_with_degree_above=3,
            dont_explore_detection_event_sets_with_size_above=4,
            canonicalize_circuit_errors=True,
        )
    if style == "midout":
        expected_distance = min(width // 3 * 2, height // 2) // 2
    elif style == "superdense":
        if ablate_into_matchable_code:
            expected_distance = min(width // 3, height // 2)
        else:
            expected_distance = min(width // 3 * 2, height // 2)
    else:
        raise NotImplementedError(f"{style=}")
    assert len(err) == expected_distance


def test_make_toric_color_code_circuit_with_magic_time_boundaries_exact_circuit():
    assert make_toric_color_code_circuit_with_magic_time_boundaries(
        width=6,
        height=8,
        rounds=5,
        noise=gen.NoiseModel.uniform_depolarizing(1e-3),
        style="superdense",
        convert_to_cz=False,
    ) == stim.Circuit(
        """
        QUBIT_COORDS(-2, 0) 0
        QUBIT_COORDS(-1, 0) 1
        QUBIT_COORDS(0, 0) 2
        QUBIT_COORDS(0, 1) 3
        QUBIT_COORDS(0, 2) 4
        QUBIT_COORDS(0, 3) 5
        QUBIT_COORDS(0, 4) 6
        QUBIT_COORDS(0, 5) 7
        QUBIT_COORDS(0, 6) 8
        QUBIT_COORDS(0, 7) 9
        QUBIT_COORDS(1, 0) 10
        QUBIT_COORDS(1, 1) 11
        QUBIT_COORDS(1, 2) 12
        QUBIT_COORDS(1, 3) 13
        QUBIT_COORDS(1, 4) 14
        QUBIT_COORDS(1, 5) 15
        QUBIT_COORDS(1, 6) 16
        QUBIT_COORDS(1, 7) 17
        QUBIT_COORDS(2, 0) 18
        QUBIT_COORDS(2, 1) 19
        QUBIT_COORDS(2, 2) 20
        QUBIT_COORDS(2, 3) 21
        QUBIT_COORDS(2, 4) 22
        QUBIT_COORDS(2, 5) 23
        QUBIT_COORDS(2, 6) 24
        QUBIT_COORDS(2, 7) 25
        QUBIT_COORDS(3, 0) 26
        QUBIT_COORDS(3, 1) 27
        QUBIT_COORDS(3, 2) 28
        QUBIT_COORDS(3, 3) 29
        QUBIT_COORDS(3, 4) 30
        QUBIT_COORDS(3, 5) 31
        QUBIT_COORDS(3, 6) 32
        QUBIT_COORDS(3, 7) 33
        QUBIT_COORDS(4, 0) 34
        QUBIT_COORDS(4, 1) 35
        QUBIT_COORDS(4, 2) 36
        QUBIT_COORDS(4, 3) 37
        QUBIT_COORDS(4, 4) 38
        QUBIT_COORDS(4, 5) 39
        QUBIT_COORDS(4, 6) 40
        QUBIT_COORDS(4, 7) 41
        QUBIT_COORDS(5, 0) 42
        QUBIT_COORDS(5, 1) 43
        QUBIT_COORDS(5, 2) 44
        QUBIT_COORDS(5, 3) 45
        QUBIT_COORDS(5, 4) 46
        QUBIT_COORDS(5, 5) 47
        QUBIT_COORDS(5, 6) 48
        QUBIT_COORDS(5, 7) 49
        MPP X4*X9*X10*X11*X42*X43 Z4*Z9*Z10*Z11*Z42*Z43 X5*X8*X14*X15*X46*X47 Z5*Z8*Z14*Z15*Z46*Z47 X4*X5*X11*X14*X20*X21 Z4*Z5*Z11*Z14*Z20*Z21 X8*X9*X10*X15*X24*X25 Z8*Z9*Z10*Z15*Z24*Z25 X10*X11*X20*X25*X26*X27 Z10*Z11*Z20*Z25*Z26*Z27 X14*X15*X21*X24*X30*X31 Z14*Z15*Z21*Z24*Z30*Z31 X20*X21*X27*X30*X36*X37 Z20*Z21*Z27*Z30*Z36*Z37 X24*X25*X26*X31*X40*X41 Z24*Z25*Z26*Z31*Z40*Z41 X26*X27*X36*X41*X42*X43 Z26*Z27*Z36*Z41*Z42*Z43 X30*X31*X37*X40*X46*X47 Z30*Z31*Z37*Z40*Z46*Z47 X4*X5*X36*X37*X43*X46 Z4*Z5*Z36*Z37*Z43*Z46 X8*X9*X40*X41*X42*X47 Z8*Z9*Z40*Z41*Z42*Z47 X1*X4*X5*X8*X9 X0*X14*X21*X37*X46 Z1*Z4*Z11*Z27*Z36 Z0*Z20*Z21*Z24*Z25
        OBSERVABLE_INCLUDE(0) rec[-4]
        OBSERVABLE_INCLUDE(1) rec[-3]
        OBSERVABLE_INCLUDE(2) rec[-2]
        OBSERVABLE_INCLUDE(3) rec[-1]
        TICK
        RX 2 6 12 16 18 22 28 32 34 38 44 48
        R 3 7 13 17 19 23 29 33 35 39 45 49
        X_ERROR(0.001) 3 7 13 17 19 23 29 33 35 39 45 49
        Z_ERROR(0.001) 2 6 12 16 18 22 28 32 34 38 44 48
        DEPOLARIZE1(0.001) 4 5 8 9 10 11 14 15 20 21 24 25 26 27 30 31 36 37 40 41 42 43 46 47
        TICK
        CX 2 3 6 7 12 13 16 17 18 19 22 23 28 29 32 33 34 35 38 39 44 45 48 49
        DEPOLARIZE2(0.001) 2 3 6 7 12 13 16 17 18 19 22 23 28 29 32 33 34 35 38 39 44 45 48 49
        DEPOLARIZE1(0.001) 4 5 8 9 10 11 14 15 20 21 24 25 26 27 30 31 36 37 40 41 42 43 46 47
        TICK
        CX 4 44 8 48 10 2 14 6 20 12 24 16 26 18 30 22 36 28 40 32 42 34 46 38 5 45 9 49 11 3 15 7 21 13 25 17 27 19 31 23 37 29 41 33 43 35 47 39
        DEPOLARIZE2(0.001) 4 44 8 48 10 2 14 6 20 12 24 16 26 18 30 22 36 28 40 32 42 34 46 38 5 45 9 49 11 3 15 7 21 13 25 17 27 19 31 23 37 29 41 33 43 35 47 39
        TICK
        CX 5 6 9 2 11 12 15 16 21 22 25 18 27 28 31 32 37 38 41 34 43 44 47 48 4 3 8 7 10 17 14 13 20 19 24 23 26 33 30 29 36 35 40 39 42 49 46 45
        DEPOLARIZE2(0.001) 5 6 9 2 11 12 15 16 21 22 25 18 27 28 31 32 37 38 41 34 43 44 47 48 4 3 8 7 10 17 14 13 20 19 24 23 26 33 30 29 36 35 40 39 42 49 46 45
        TICK
        CX 4 12 8 16 10 18 14 22 20 28 24 32 26 34 30 38 36 44 40 48 42 2 46 6 5 13 9 17 11 19 15 23 21 29 25 33 27 35 31 39 37 45 41 49 43 3 47 7
        DEPOLARIZE2(0.001) 4 12 8 16 10 18 14 22 20 28 24 32 26 34 30 38 36 44 40 48 42 2 46 6 5 13 9 17 11 19 15 23 21 29 25 33 27 35 31 39 37 45 41 49 43 3 47 7
        TICK
        CX 2 10 6 14 12 20 16 24 18 26 22 30 28 36 32 40 34 42 38 46 44 4 48 8 3 11 7 15 13 21 17 25 19 27 23 31 29 37 33 41 35 43 39 47 45 5 49 9
        DEPOLARIZE2(0.001) 2 10 6 14 12 20 16 24 18 26 22 30 28 36 32 40 34 42 38 46 44 4 48 8 3 11 7 15 13 21 17 25 19 27 23 31 29 37 33 41 35 43 39 47 45 5 49 9
        TICK
        CX 2 9 6 5 12 11 16 15 18 25 22 21 28 27 32 31 34 41 38 37 44 43 48 47 3 4 7 8 13 14 17 10 19 20 23 24 29 30 33 26 35 36 39 40 45 46 49 42
        DEPOLARIZE2(0.001) 2 9 6 5 12 11 16 15 18 25 22 21 28 27 32 31 34 41 38 37 44 43 48 47 3 4 7 8 13 14 17 10 19 20 23 24 29 30 33 26 35 36 39 40 45 46 49 42
        TICK
        CX 2 42 6 46 12 4 16 8 18 10 22 14 28 20 32 24 34 26 38 30 44 36 48 40 3 43 7 47 13 5 17 9 19 11 23 15 29 21 33 25 35 27 39 31 45 37 49 41
        DEPOLARIZE2(0.001) 2 42 6 46 12 4 16 8 18 10 22 14 28 20 32 24 34 26 38 30 44 36 48 40 3 43 7 47 13 5 17 9 19 11 23 15 29 21 33 25 35 27 39 31 45 37 49 41
        TICK
        CX 2 3 6 7 12 13 16 17 18 19 22 23 28 29 32 33 34 35 38 39 44 45 48 49
        DEPOLARIZE2(0.001) 2 3 6 7 12 13 16 17 18 19 22 23 28 29 32 33 34 35 38 39 44 45 48 49
        DEPOLARIZE1(0.001) 4 5 8 9 10 11 14 15 20 21 24 25 26 27 30 31 36 37 40 41 42 43 46 47
        TICK
        MX(0.001) 2 6 12 16 18 22 28 32 34 38 44 48
        M(0.001) 3 7 13 17 19 23 29 33 35 39 45 49
        DEPOLARIZE1(0.001) 2 6 12 16 18 22 28 32 34 38 44 48 3 7 13 17 19 23 29 33 35 39 45 49 4 5 8 9 10 11 14 15 20 21 24 25 26 27 30 31 36 37 40 41 42 43 46 47
        DETECTOR(0, 0, 0, 0) rec[-52] rec[-24]
        DETECTOR(0, 1, 0, 3) rec[-51] rec[-12]
        DETECTOR(0, 4, 0, 0) rec[-50] rec[-23]
        DETECTOR(0, 5, 0, 3) rec[-49] rec[-11]
        DETECTOR(1, 2, 0, 1) rec[-48] rec[-22]
        DETECTOR(1, 3, 0, 4) rec[-47] rec[-10]
        DETECTOR(1, 6, 0, 1) rec[-46] rec[-21]
        DETECTOR(1, 7, 0, 4) rec[-45] rec[-9]
        DETECTOR(2, 0, 0, 2) rec[-44] rec[-20]
        DETECTOR(2, 1, 0, 5) rec[-43] rec[-8]
        DETECTOR(2, 4, 0, 2) rec[-42] rec[-19]
        DETECTOR(2, 5, 0, 5) rec[-41] rec[-7]
        DETECTOR(3, 2, 0, 0) rec[-40] rec[-18]
        DETECTOR(3, 3, 0, 3) rec[-39] rec[-6]
        DETECTOR(3, 6, 0, 0) rec[-38] rec[-17]
        DETECTOR(3, 7, 0, 3) rec[-37] rec[-5]
        DETECTOR(4, 0, 0, 1) rec[-36] rec[-16]
        DETECTOR(4, 1, 0, 4) rec[-35] rec[-4]
        DETECTOR(4, 4, 0, 1) rec[-34] rec[-15]
        DETECTOR(4, 5, 0, 4) rec[-33] rec[-3]
        DETECTOR(5, 2, 0, 2) rec[-32] rec[-14]
        DETECTOR(5, 3, 0, 5) rec[-31] rec[-2]
        DETECTOR(5, 6, 0, 2) rec[-30] rec[-13]
        DETECTOR(5, 7, 0, 5) rec[-29] rec[-1]
        OBSERVABLE_INCLUDE(3) rec[-10] rec[-9] rec[-8] rec[-7] rec[-6] rec[-5]
        SHIFT_COORDS(0, 0, 1)
        TICK
        REPEAT 4 {
            RX 2 6 12 16 18 22 28 32 34 38 44 48
            R 3 7 13 17 19 23 29 33 35 39 45 49
            X_ERROR(0.001) 3 7 13 17 19 23 29 33 35 39 45 49
            Z_ERROR(0.001) 2 6 12 16 18 22 28 32 34 38 44 48
            DEPOLARIZE1(0.001) 4 5 8 9 10 11 14 15 20 21 24 25 26 27 30 31 36 37 40 41 42 43 46 47
            TICK
            CX 2 3 6 7 12 13 16 17 18 19 22 23 28 29 32 33 34 35 38 39 44 45 48 49
            DEPOLARIZE2(0.001) 2 3 6 7 12 13 16 17 18 19 22 23 28 29 32 33 34 35 38 39 44 45 48 49
            DEPOLARIZE1(0.001) 4 5 8 9 10 11 14 15 20 21 24 25 26 27 30 31 36 37 40 41 42 43 46 47
            TICK
            CX 4 44 8 48 10 2 14 6 20 12 24 16 26 18 30 22 36 28 40 32 42 34 46 38 5 45 9 49 11 3 15 7 21 13 25 17 27 19 31 23 37 29 41 33 43 35 47 39
            DEPOLARIZE2(0.001) 4 44 8 48 10 2 14 6 20 12 24 16 26 18 30 22 36 28 40 32 42 34 46 38 5 45 9 49 11 3 15 7 21 13 25 17 27 19 31 23 37 29 41 33 43 35 47 39
            TICK
            CX 5 6 9 2 11 12 15 16 21 22 25 18 27 28 31 32 37 38 41 34 43 44 47 48 4 3 8 7 10 17 14 13 20 19 24 23 26 33 30 29 36 35 40 39 42 49 46 45
            DEPOLARIZE2(0.001) 5 6 9 2 11 12 15 16 21 22 25 18 27 28 31 32 37 38 41 34 43 44 47 48 4 3 8 7 10 17 14 13 20 19 24 23 26 33 30 29 36 35 40 39 42 49 46 45
            TICK
            CX 4 12 8 16 10 18 14 22 20 28 24 32 26 34 30 38 36 44 40 48 42 2 46 6 5 13 9 17 11 19 15 23 21 29 25 33 27 35 31 39 37 45 41 49 43 3 47 7
            DEPOLARIZE2(0.001) 4 12 8 16 10 18 14 22 20 28 24 32 26 34 30 38 36 44 40 48 42 2 46 6 5 13 9 17 11 19 15 23 21 29 25 33 27 35 31 39 37 45 41 49 43 3 47 7
            TICK
            CX 2 10 6 14 12 20 16 24 18 26 22 30 28 36 32 40 34 42 38 46 44 4 48 8 3 11 7 15 13 21 17 25 19 27 23 31 29 37 33 41 35 43 39 47 45 5 49 9
            DEPOLARIZE2(0.001) 2 10 6 14 12 20 16 24 18 26 22 30 28 36 32 40 34 42 38 46 44 4 48 8 3 11 7 15 13 21 17 25 19 27 23 31 29 37 33 41 35 43 39 47 45 5 49 9
            TICK
            CX 2 9 6 5 12 11 16 15 18 25 22 21 28 27 32 31 34 41 38 37 44 43 48 47 3 4 7 8 13 14 17 10 19 20 23 24 29 30 33 26 35 36 39 40 45 46 49 42
            DEPOLARIZE2(0.001) 2 9 6 5 12 11 16 15 18 25 22 21 28 27 32 31 34 41 38 37 44 43 48 47 3 4 7 8 13 14 17 10 19 20 23 24 29 30 33 26 35 36 39 40 45 46 49 42
            TICK
            CX 2 42 6 46 12 4 16 8 18 10 22 14 28 20 32 24 34 26 38 30 44 36 48 40 3 43 7 47 13 5 17 9 19 11 23 15 29 21 33 25 35 27 39 31 45 37 49 41
            DEPOLARIZE2(0.001) 2 42 6 46 12 4 16 8 18 10 22 14 28 20 32 24 34 26 38 30 44 36 48 40 3 43 7 47 13 5 17 9 19 11 23 15 29 21 33 25 35 27 39 31 45 37 49 41
            TICK
            CX 2 3 6 7 12 13 16 17 18 19 22 23 28 29 32 33 34 35 38 39 44 45 48 49
            DEPOLARIZE2(0.001) 2 3 6 7 12 13 16 17 18 19 22 23 28 29 32 33 34 35 38 39 44 45 48 49
            DEPOLARIZE1(0.001) 4 5 8 9 10 11 14 15 20 21 24 25 26 27 30 31 36 37 40 41 42 43 46 47
            TICK
            MX(0.001) 2 6 12 16 18 22 28 32 34 38 44 48
            M(0.001) 3 7 13 17 19 23 29 33 35 39 45 49
            DEPOLARIZE1(0.001) 2 6 12 16 18 22 28 32 34 38 44 48 3 7 13 17 19 23 29 33 35 39 45 49 4 5 8 9 10 11 14 15 20 21 24 25 26 27 30 31 36 37 40 41 42 43 46 47
            DETECTOR(0, 0, 0, 0) rec[-48] rec[-24]
            DETECTOR(0, 1, 0, 3) rec[-32] rec[-28] rec[-12]
            DETECTOR(0, 4, 0, 0) rec[-47] rec[-23]
            DETECTOR(0, 5, 0, 3) rec[-31] rec[-27] rec[-11]
            DETECTOR(1, 2, 0, 1) rec[-46] rec[-22]
            DETECTOR(1, 3, 0, 4) rec[-30] rec[-26] rec[-10]
            DETECTOR(1, 6, 0, 1) rec[-45] rec[-21]
            DETECTOR(1, 7, 0, 4) rec[-29] rec[-25] rec[-9]
            DETECTOR(2, 0, 0, 2) rec[-44] rec[-20]
            DETECTOR(2, 1, 0, 5) rec[-36] rec[-28] rec[-8]
            DETECTOR(2, 4, 0, 2) rec[-43] rec[-19]
            DETECTOR(2, 5, 0, 5) rec[-35] rec[-27] rec[-7]
            DETECTOR(3, 2, 0, 0) rec[-42] rec[-18]
            DETECTOR(3, 3, 0, 3) rec[-34] rec[-26] rec[-6]
            DETECTOR(3, 6, 0, 0) rec[-41] rec[-17]
            DETECTOR(3, 7, 0, 3) rec[-33] rec[-25] rec[-5]
            DETECTOR(4, 0, 0, 1) rec[-40] rec[-16]
            DETECTOR(4, 1, 0, 4) rec[-36] rec[-32] rec[-4]
            DETECTOR(4, 4, 0, 1) rec[-39] rec[-15]
            DETECTOR(4, 5, 0, 4) rec[-35] rec[-31] rec[-3]
            DETECTOR(5, 2, 0, 2) rec[-38] rec[-14]
            DETECTOR(5, 3, 0, 5) rec[-34] rec[-30] rec[-2]
            DETECTOR(5, 6, 0, 2) rec[-37] rec[-13]
            DETECTOR(5, 7, 0, 5) rec[-33] rec[-29] rec[-1]
            OBSERVABLE_INCLUDE(3) rec[-10] rec[-9] rec[-8] rec[-7] rec[-6] rec[-5]
            SHIFT_COORDS(0, 0, 1)
            TICK
        }
        MPP X4*X9*X10*X11*X42*X43 Z4*Z9*Z10*Z11*Z42*Z43 X5*X8*X14*X15*X46*X47 Z5*Z8*Z14*Z15*Z46*Z47 X4*X5*X11*X14*X20*X21 Z4*Z5*Z11*Z14*Z20*Z21 X8*X9*X10*X15*X24*X25 Z8*Z9*Z10*Z15*Z24*Z25 X10*X11*X20*X25*X26*X27 Z10*Z11*Z20*Z25*Z26*Z27 X14*X15*X21*X24*X30*X31 Z14*Z15*Z21*Z24*Z30*Z31 X20*X21*X27*X30*X36*X37 Z20*Z21*Z27*Z30*Z36*Z37 X24*X25*X26*X31*X40*X41 Z24*Z25*Z26*Z31*Z40*Z41 X26*X27*X36*X41*X42*X43 Z26*Z27*Z36*Z41*Z42*Z43 X30*X31*X37*X40*X46*X47 Z30*Z31*Z37*Z40*Z46*Z47 X4*X5*X36*X37*X43*X46 Z4*Z5*Z36*Z37*Z43*Z46 X8*X9*X40*X41*X42*X47 Z8*Z9*Z40*Z41*Z42*Z47 X1*X4*X5*X8*X9 X0*X14*X21*X37*X46 Z1*Z4*Z11*Z27*Z36 Z0*Z20*Z21*Z24*Z25
        DETECTOR(0, 0, 0, 0) rec[-52] rec[-28]
        DETECTOR(0, 1, 0, 3) rec[-36] rec[-32] rec[-27]
        DETECTOR(0, 4, 0, 0) rec[-51] rec[-26]
        DETECTOR(0, 5, 0, 3) rec[-35] rec[-31] rec[-25]
        DETECTOR(1, 2, 0, 1) rec[-50] rec[-24]
        DETECTOR(1, 3, 0, 4) rec[-34] rec[-30] rec[-23]
        DETECTOR(1, 6, 0, 1) rec[-49] rec[-22]
        DETECTOR(1, 7, 0, 4) rec[-33] rec[-29] rec[-21]
        DETECTOR(2, 0, 0, 2) rec[-48] rec[-20]
        DETECTOR(2, 1, 0, 5) rec[-40] rec[-32] rec[-19]
        DETECTOR(2, 4, 0, 2) rec[-47] rec[-18]
        DETECTOR(2, 5, 0, 5) rec[-39] rec[-31] rec[-17]
        DETECTOR(3, 2, 0, 0) rec[-46] rec[-16]
        DETECTOR(3, 3, 0, 3) rec[-38] rec[-30] rec[-15]
        DETECTOR(3, 6, 0, 0) rec[-45] rec[-14]
        DETECTOR(3, 7, 0, 3) rec[-37] rec[-29] rec[-13]
        DETECTOR(4, 0, 0, 1) rec[-44] rec[-12]
        DETECTOR(4, 1, 0, 4) rec[-40] rec[-36] rec[-11]
        DETECTOR(4, 4, 0, 1) rec[-43] rec[-10]
        DETECTOR(4, 5, 0, 4) rec[-39] rec[-35] rec[-9]
        DETECTOR(5, 2, 0, 2) rec[-42] rec[-8]
        DETECTOR(5, 3, 0, 5) rec[-38] rec[-34] rec[-7]
        DETECTOR(5, 6, 0, 2) rec[-41] rec[-6]
        DETECTOR(5, 7, 0, 5) rec[-37] rec[-33] rec[-5]
        OBSERVABLE_INCLUDE(0) rec[-4]
        OBSERVABLE_INCLUDE(1) rec[-3]
        OBSERVABLE_INCLUDE(2) rec[-2]
        OBSERVABLE_INCLUDE(3) rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
    """
    )
