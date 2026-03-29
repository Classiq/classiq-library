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
from clorco.color_code._midout_planar_color_code_circuits import (
    _color_code_round_chunk,
    make_midout_color_code_circuit_chunks,
)


@pytest.mark.parametrize(
    "basis,base_width,use_488,layer_parity,first_round",
    itertools.product(
        "XZ",
        [3, 5, 7, 9, 11],
        [False, True],
        [False, True],
        [False, True],
    ),
)
def test_color_code_round_chunk(
    basis: str, base_width: int, use_488: bool, layer_parity: bool, first_round: bool
):
    _color_code_round_chunk(
        base_width=base_width,
        use_488=use_488,
        basis=basis,
        layer_parity=layer_parity,
        first_round=first_round,
    ).verify()


@pytest.mark.parametrize(
    "basis,base_width,use_488,rounds",
    itertools.product(
        "XZ",
        [3, 5, 7, 9],
        [False, True],
        [2, 3, 4, 5, 6, 7],
    ),
)
def test_make_color_code_circuit_chunks(
    basis: str, base_width: int, use_488: bool, rounds: int
):
    chunks = make_midout_color_code_circuit_chunks(
        basis=basis,
        base_width=base_width,
        rounds=rounds,
        use_488=use_488,
    )

    circuit = gen.compile_chunks_into_circuit(chunks)
    circuit.detector_error_model()
    assert (
        circuit.count_determined_measurements()
        == circuit.num_observables + circuit.num_detectors
    )

    noisy = gen.NoiseModel.uniform_depolarizing(1e-3).noisy_circuit(
        circuit.with_inlined_feedback()
    )
    if use_488:
        expected_distance = base_width // 4 + 1
    else:
        expected_distance = base_width // 2 + 1 - (basis == "Y" and base_width > 3)
    actual_distance = len(noisy.shortest_graphlike_error())
    assert actual_distance == expected_distance


def test_exact_color_code_circuit():
    circuit = make_circuit(
        style="midout_color_code_X",
        noise_model=gen.NoiseModel.uniform_depolarizing(1e-3),
        noise_strength=1e-3,
        rounds=11,
        diameter=3,
        convert_to_cz=False,
        editable_extras={},
    )
    assert circuit == stim.Circuit(
        """
        QUBIT_COORDS(0, 1) 0
        QUBIT_COORDS(1, 1) 1
        QUBIT_COORDS(1, 2) 2
        QUBIT_COORDS(1, 3) 3
        QUBIT_COORDS(1, 4) 4
        QUBIT_COORDS(2, 1) 5
        QUBIT_COORDS(2, 2) 6
        QUBIT_COORDS(2, 3) 7
        QUBIT_COORDS(2, 4) 8
        RX 2 4 0 3 5 6 8
        R 1 7
        X_ERROR(0.001) 1 7
        Z_ERROR(0.001) 2 4 0 3 5 6 8
        TICK
        CX 0 1 2 6 4 8
        DEPOLARIZE2(0.001) 0 1 2 6 4 8
        DEPOLARIZE1(0.001) 3 5 7
        TICK
        CX 2 1 4 3 6 5 8 7
        DEPOLARIZE2(0.001) 2 1 4 3 6 5 8 7
        DEPOLARIZE1(0.001) 0
        TICK
        CX 3 2 7 6
        DEPOLARIZE2(0.001) 3 2 7 6
        DEPOLARIZE1(0.001) 0 1 4 5 8
        TICK
        CX 2 3 6 7
        DEPOLARIZE2(0.001) 2 3 6 7
        DEPOLARIZE1(0.001) 0 1 4 5 8
        TICK
        CX 1 2 3 4 5 6 7 8
        DEPOLARIZE2(0.001) 1 2 3 4 5 6 7 8
        DEPOLARIZE1(0.001) 0
        TICK
        CX 1 0 6 2 8 4
        DEPOLARIZE2(0.001) 1 0 6 2 8 4
        DEPOLARIZE1(0.001) 3 5 7
        TICK
        MX(0.001) 1 7
        M(0.001) 2 4
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE1(0.001) 1 7 2 4 0 3 5 6 8
        TICK
        RX 1 7
        R 2 4
        OBSERVABLE_INCLUDE(0) rec[-4]
        X_ERROR(0.001) 2 4
        Z_ERROR(0.001) 1 7
        DEPOLARIZE1(0.001) 0 3 5 6 8
        TICK
        CX 1 0 6 2 8 4
        DEPOLARIZE2(0.001) 1 0 6 2 8 4
        DEPOLARIZE1(0.001) 3 5 7
        TICK
        CX 1 2 3 4 5 6 7 8
        DEPOLARIZE2(0.001) 1 2 3 4 5 6 7 8
        DEPOLARIZE1(0.001) 0
        TICK
        CX 2 3 6 7
        DETECTOR(1, 1, 0, 1) rec[-4]
        DETECTOR(2, 3, 0, 2) rec[-3]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE2(0.001) 2 3 6 7
        DEPOLARIZE1(0.001) 0 1 4 5 8
        TICK
        CX 3 2 7 6
        DEPOLARIZE2(0.001) 3 2 7 6
        DEPOLARIZE1(0.001) 0 1 4 5 8
        TICK
        CX 2 1 4 3 6 5 8 7
        DEPOLARIZE2(0.001) 2 1 4 3 6 5 8 7
        DEPOLARIZE1(0.001) 0
        TICK
        CX 0 1 2 6 4 8
        DEPOLARIZE2(0.001) 0 1 2 6 4 8
        DEPOLARIZE1(0.001) 3 5 7
        TICK
        MX(0.001) 2 4
        M(0.001) 1 7
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE1(0.001) 2 4 1 7 0 3 5 6 8
        TICK
        RX 2 4
        R 1 7
        OBSERVABLE_INCLUDE(0) rec[-3]
        X_ERROR(0.001) 1 7
        Z_ERROR(0.001) 2 4
        DEPOLARIZE1(0.001) 0 3 5 6 8
        TICK
        CX 0 1 2 6 4 8
        DEPOLARIZE2(0.001) 0 1 2 6 4 8
        DEPOLARIZE1(0.001) 3 5 7
        TICK
        CX 2 1 4 3 6 5 8 7
        DEPOLARIZE2(0.001) 2 1 4 3 6 5 8 7
        DEPOLARIZE1(0.001) 0
        TICK
        CX 3 2 7 6
        DETECTOR(1, 1, 0, 4) rec[-2]
        DETECTOR(1, 2, 0, 2) rec[-8] rec[-7] rec[-4]
        DETECTOR(1, 4, 0, 0) rec[-3]
        DETECTOR(2, 3, 0, 5) rec[-1]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE2(0.001) 3 2 7 6
        DEPOLARIZE1(0.001) 0 1 4 5 8
        TICK
        REPEAT 4 {
            CX 2 3 6 7
            DEPOLARIZE2(0.001) 2 3 6 7
            DEPOLARIZE1(0.001) 0 1 4 5 8
            TICK
            CX 1 2 3 4 5 6 7 8
            DEPOLARIZE2(0.001) 1 2 3 4 5 6 7 8
            DEPOLARIZE1(0.001) 0
            TICK
            CX 1 0 6 2 8 4
            DEPOLARIZE2(0.001) 1 0 6 2 8 4
            DEPOLARIZE1(0.001) 3 5 7
            TICK
            MX(0.001) 1 7
            M(0.001) 2 4
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE1(0.001) 1 7 2 4 0 3 5 6 8
            TICK
            RX 1 7
            R 2 4
            OBSERVABLE_INCLUDE(0) rec[-4]
            X_ERROR(0.001) 2 4
            Z_ERROR(0.001) 1 7
            DEPOLARIZE1(0.001) 0 3 5 6 8
            TICK
            CX 1 0 6 2 8 4
            DEPOLARIZE2(0.001) 1 0 6 2 8 4
            DEPOLARIZE1(0.001) 3 5 7
            TICK
            CX 1 2 3 4 5 6 7 8
            DEPOLARIZE2(0.001) 1 2 3 4 5 6 7 8
            DEPOLARIZE1(0.001) 0
            TICK
            CX 2 3 6 7
            DETECTOR(1, 1, 0, 1) rec[-4]
            DETECTOR(1, 2, 0, 5) rec[-6] rec[-5] rec[-2]
            DETECTOR(1, 4, 0, 3) rec[-1]
            DETECTOR(2, 3, 0, 2) rec[-3]
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE2(0.001) 2 3 6 7
            DEPOLARIZE1(0.001) 0 1 4 5 8
            TICK
            CX 3 2 7 6
            DEPOLARIZE2(0.001) 3 2 7 6
            DEPOLARIZE1(0.001) 0 1 4 5 8
            TICK
            CX 2 1 4 3 6 5 8 7
            DEPOLARIZE2(0.001) 2 1 4 3 6 5 8 7
            DEPOLARIZE1(0.001) 0
            TICK
            CX 0 1 2 6 4 8
            DEPOLARIZE2(0.001) 0 1 2 6 4 8
            DEPOLARIZE1(0.001) 3 5 7
            TICK
            MX(0.001) 2 4
            M(0.001) 1 7
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE1(0.001) 2 4 1 7 0 3 5 6 8
            TICK
            RX 2 4
            R 1 7
            OBSERVABLE_INCLUDE(0) rec[-3]
            X_ERROR(0.001) 1 7
            Z_ERROR(0.001) 2 4
            DEPOLARIZE1(0.001) 0 3 5 6 8
            TICK
            CX 0 1 2 6 4 8
            DEPOLARIZE2(0.001) 0 1 2 6 4 8
            DEPOLARIZE1(0.001) 3 5 7
            TICK
            CX 2 1 4 3 6 5 8 7
            DEPOLARIZE2(0.001) 2 1 4 3 6 5 8 7
            DEPOLARIZE1(0.001) 0
            TICK
            CX 3 2 7 6
            DETECTOR(1, 1, 0, 4) rec[-2]
            DETECTOR(1, 2, 0, 2) rec[-8] rec[-7] rec[-4]
            DETECTOR(1, 4, 0, 0) rec[-3]
            DETECTOR(2, 3, 0, 5) rec[-1]
            SHIFT_COORDS(0, 0, 1)
            DEPOLARIZE2(0.001) 3 2 7 6
            DEPOLARIZE1(0.001) 0 1 4 5 8
            TICK
        }
        CX 6 7 2 3
        DEPOLARIZE2(0.001) 6 7 2 3
        DEPOLARIZE1(0.001) 0 1 4 5 8
        TICK
        CX 7 8 5 6 3 4 1 2
        DEPOLARIZE2(0.001) 7 8 5 6 3 4 1 2
        DEPOLARIZE1(0.001) 0
        TICK
        CX 8 4 6 2 1 0
        DEPOLARIZE2(0.001) 8 4 6 2 1 0
        DEPOLARIZE1(0.001) 3 5 7
        TICK
        M(0.001) 4 2
        MX(0.001) 8 6 5 3 0 7 1
        DETECTOR(1, 1, 0, 1) rec[-1]
        DETECTOR(1, 2, 0, 2) rec[-7] rec[-5] rec[-4] rec[-3] rec[-2] rec[-1]
        DETECTOR(1, 2, 0, 5) rec[-11] rec[-10] rec[-8]
        DETECTOR(1, 4, 0, 0) rec[-7] rec[-6]
        DETECTOR(1, 4, 0, 3) rec[-9]
        DETECTOR(2, 3, 0, 2) rec[-2]
        OBSERVABLE_INCLUDE(0) rec[-7] rec[-5] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        DEPOLARIZE1(0.001) 4 2 8 6 5 3 0 7 1
    """
    )
