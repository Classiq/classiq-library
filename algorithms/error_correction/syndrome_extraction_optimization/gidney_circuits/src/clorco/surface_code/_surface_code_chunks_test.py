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

import stim

import gen
from clorco.surface_code._surface_code_chunks import standard_surface_code_chunk
from clorco.surface_code._surface_code_patches import make_xtop_qubit_patch


def test_magic_init_surface_code_chunk():
    p = make_xtop_qubit_patch(diameter=3)
    obs = gen.PauliString({0: "X", 1j: "X", 2j: "X"})
    c = standard_surface_code_chunk(p, obs=obs)
    c2 = c.magic_init_chunk()
    c2.verify()
    c3 = c.magic_end_chunk()
    c3.verify()
    assert gen.compile_chunks_into_circuit([c2, c3]) == stim.Circuit(
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
        MPP Z1*Z2 X0*X3 Z0*Z1*Z3*Z4 X1*X2*X4*X5 X3*X4*X6*X7 Z4*Z5*Z7*Z8 X5*X8 Z6*Z7 X0*X1*X2
        OBSERVABLE_INCLUDE(0) rec[-1]
        TICK
        MPP Z1*Z2 X0*X3 Z0*Z1*Z3*Z4 X1*X2*X4*X5 X3*X4*X6*X7 Z4*Z5*Z7*Z8 X5*X8 Z6*Z7 X0*X1*X2
        DETECTOR(-0.5, 1.5, 0, 3) rec[-18] rec[-9]
        DETECTOR(0.5, -0.5, 0, 1) rec[-17] rec[-8]
        DETECTOR(0.5, 0.5, 0, 4) rec[-16] rec[-7]
        DETECTOR(0.5, 1.5, 0, 1) rec[-15] rec[-6]
        DETECTOR(1.5, 0.5, 0, 0) rec[-14] rec[-5]
        DETECTOR(1.5, 1.5, 0, 3) rec[-13] rec[-4]
        DETECTOR(1.5, 2.5, 0, 0) rec[-12] rec[-3]
        DETECTOR(2.5, 0.5, 0, 4) rec[-11] rec[-2]
        OBSERVABLE_INCLUDE(0) rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
    """
    )


def test_verify_normal_surface_code_chunk():
    p = make_xtop_qubit_patch(diameter=3)
    obs = gen.PauliString({0: "X", 1j: "X", 2j: "X"})
    c1 = standard_surface_code_chunk(p, init_data_basis="X", obs=obs)
    c2 = standard_surface_code_chunk(p, obs=obs)
    c3 = standard_surface_code_chunk(p, measure_data_basis="X", obs=obs)
    c4 = standard_surface_code_chunk(p, init_data_basis="X", measure_data_basis="X")
    c1.verify()
    c2.verify()
    c3.verify()
    c4.verify()
    circuit = gen.compile_chunks_into_circuit([c1, c2, c3])
    circuit.detector_error_model(decompose_errors=True)
    assert (
        len(
            gen.NoiseModel.uniform_depolarizing(1e-3)
            .noisy_circuit(circuit)
            .shortest_graphlike_error()
        )
        == 3
    )

    assert circuit == stim.Circuit(
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
        RX 10 12 13 15 0 1 2 3 4 5 6 7 8
        R 9 11 14 16
        TICK
        CX 1 9 3 11 7 14 12 4 13 6 15 8
        TICK
        CX 2 9 4 11 8 14 12 1 13 3 15 5
        TICK
        CX 0 11 4 14 6 16 10 3 12 5 13 7
        TICK
        CX 1 11 5 14 7 16 10 0 12 2 13 4
        TICK
        MX 10 12 13 15
        M 9 11 14 16
        DETECTOR(0.5, -0.5, 0, 1) rec[-8]
        DETECTOR(0.5, 1.5, 0, 1) rec[-7]
        DETECTOR(1.5, 0.5, 0, 0) rec[-6]
        DETECTOR(1.5, 2.5, 0, 0) rec[-5]
        SHIFT_COORDS(0, 0, 1)
        TICK
        RX 10 12 13 15
        R 9 11 14 16
        TICK
        CX 1 9 3 11 7 14 12 4 13 6 15 8
        TICK
        CX 2 9 4 11 8 14 12 1 13 3 15 5
        TICK
        CX 0 11 4 14 6 16 10 3 12 5 13 7
        TICK
        CX 1 11 5 14 7 16 10 0 12 2 13 4
        TICK
        MX 10 12 13 15
        M 9 11 14 16
        DETECTOR(-0.5, 1.5, 0, 3) rec[-12] rec[-4]
        DETECTOR(0.5, -0.5, 0, 1) rec[-16] rec[-8]
        DETECTOR(0.5, 0.5, 0, 4) rec[-11] rec[-3]
        DETECTOR(0.5, 1.5, 0, 1) rec[-15] rec[-7]
        DETECTOR(1.5, 0.5, 0, 0) rec[-14] rec[-6]
        DETECTOR(1.5, 1.5, 0, 3) rec[-10] rec[-2]
        DETECTOR(1.5, 2.5, 0, 0) rec[-13] rec[-5]
        DETECTOR(2.5, 0.5, 0, 4) rec[-9] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        RX 10 12 13 15
        R 9 11 14 16
        TICK
        CX 1 9 3 11 7 14 12 4 13 6 15 8
        TICK
        CX 2 9 4 11 8 14 12 1 13 3 15 5
        TICK
        CX 0 11 4 14 6 16 10 3 12 5 13 7
        TICK
        CX 1 11 5 14 7 16 10 0 12 2 13 4
        TICK
        MX 10 12 13 15 0 1 2 3 4 5 6 7 8
        M 9 11 14 16
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
        TICK
    """
    )
