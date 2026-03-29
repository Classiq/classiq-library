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


def test_make_phenom_circuit_for_stabilizer_code():
    patch = gen.Patch(
        [
            gen.Tile(
                bases="Z",
                ordered_data_qubits=[0, 1, 1j, 1 + 1j],
                measurement_qubit=0.5 + 0.5j,
            ),
            gen.Tile(
                bases="X",
                ordered_data_qubits=[0, 1],
                measurement_qubit=0.5,
            ),
            gen.Tile(
                bases="X",
                ordered_data_qubits=[0 + 1j, 1 + 1j],
                measurement_qubit=0.5 + 1j,
            ),
        ]
    )
    obs_x = gen.PauliString({0: "X", 1j: "X"})
    obs_z = gen.PauliString({0: "Z", 1: "Z"})

    assert gen.StabilizerCode(
        patch=patch,
        observables_x=[obs_x],
        observables_z=[obs_z],
    ).make_phenom_circuit(
        noise=gen.NoiseRule(flip_result=0.125, after={"DEPOLARIZE1": 0.25}),
        rounds=100,
    ) == stim.Circuit(
        """
        QUBIT_COORDS(0, -1) 0
        QUBIT_COORDS(0, 0) 1
        QUBIT_COORDS(0, 1) 2
        QUBIT_COORDS(1, 0) 3
        QUBIT_COORDS(1, 1) 4
        MPP X0*X1*X2
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z1*Z3
        OBSERVABLE_INCLUDE(1) rec[-1]
        MPP X1*X3 Z1*Z2*Z3*Z4 X2*X4
        TICK
        REPEAT 100 {
            DEPOLARIZE1(0.25) 1 2 3 4
            MPP(0.125) X1*X3 Z1*Z2*Z3*Z4 X2*X4
            DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
            DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
            DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
        }
        MPP X1*X3 Z1*Z2*Z3*Z4 X2*X4
        DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
        DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
        DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
        MPP X0*X1*X2
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z1*Z3
        OBSERVABLE_INCLUDE(1) rec[-1]
    """
    )


def test_make_code_capacity_circuit_for_stabilizer_code():
    patch = gen.Patch(
        [
            gen.Tile(
                bases="Z",
                ordered_data_qubits=[0, 1, 1j, 1 + 1j],
                measurement_qubit=0.5 + 0.5j,
            ),
            gen.Tile(
                bases="X",
                ordered_data_qubits=[0, 1],
                measurement_qubit=0.5,
            ),
            gen.Tile(
                bases="X",
                ordered_data_qubits=[0 + 1j, 1 + 1j],
                measurement_qubit=0.5 + 1j,
            ),
        ]
    )
    obs_x = gen.PauliString({0: "X", 1j: "X"})
    obs_z = gen.PauliString({0: "Z", 1: "Z"})

    assert gen.StabilizerCode(
        patch=patch,
        observables_x=[obs_x],
        observables_z=[obs_z],
    ).make_code_capacity_circuit(
        noise=gen.NoiseRule(after={"DEPOLARIZE1": 0.25}),
    ) == stim.Circuit(
        """
        QUBIT_COORDS(0, -1) 0
        QUBIT_COORDS(0, 0) 1
        QUBIT_COORDS(0, 1) 2
        QUBIT_COORDS(1, 0) 3
        QUBIT_COORDS(1, 1) 4
        MPP X0*X1*X2
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z1*Z3
        OBSERVABLE_INCLUDE(1) rec[-1]
        MPP X1*X3 Z1*Z2*Z3*Z4 X2*X4
        TICK
        DEPOLARIZE1(0.25) 1 2 3 4
        TICK
        MPP X1*X3 Z1*Z2*Z3*Z4 X2*X4
        DETECTOR(0.5, 0, 0) rec[-6] rec[-3]
        DETECTOR(0.5, 0.5, 0) rec[-5] rec[-2]
        DETECTOR(0.5, 1, 0) rec[-4] rec[-1]
        MPP X0*X1*X2
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z1*Z3
        OBSERVABLE_INCLUDE(1) rec[-1]
    """
    )


def test_from_patch_with_inferred_observables():
    code = gen.StabilizerCode.from_patch_with_inferred_observables(
        gen.Patch(
            [
                gen.Tile(
                    bases="XZZX", ordered_data_qubits=[0, 1, 2, 3], measurement_qubit=0
                ),
                gen.Tile(
                    bases="XZZX", ordered_data_qubits=[1, 2, 3, 4], measurement_qubit=1
                ),
                gen.Tile(
                    bases="XZZX", ordered_data_qubits=[2, 3, 4, 0], measurement_qubit=2
                ),
                gen.Tile(
                    bases="XZZX", ordered_data_qubits=[3, 4, 0, 1], measurement_qubit=3
                ),
            ]
        )
    )
    code.check_commutation_relationships()
    assert len(code.observables_x) == len(code.observables_z) == 1
