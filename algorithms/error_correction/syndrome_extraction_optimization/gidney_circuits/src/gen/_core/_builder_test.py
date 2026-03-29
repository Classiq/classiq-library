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


def test_builder_init():
    builder = gen.Builder.for_qubits([0, 1j, 3 + 2j])
    assert builder.circuit == stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(3, 2) 2
    """
    )


def test_measure_code():
    perfect_code = gen.StabilizerCode(
        patch=gen.Patch(
            [
                gen.Tile(
                    bases="XZZX",
                    measurement_qubit=k + 1j,
                    ordered_data_qubits=[(k + j) % 5 for j in range(4)],
                )
                for k in range(4)
            ]
        ),
        observables_x=[gen.PauliString.from_xyzs(xs=range(5))],
        observables_z=[gen.PauliString.from_xyzs(zs=range(5))],
    )

    builder = gen.Builder.for_qubits([1j, 0, 1, 2, 3, 4])
    builder.measure_stabilizer_code(
        perfect_code,
        save_layer="init",
        observables_first=True,
        ancilla_qubits_for_xz_observable_pairs=[1j],
    )
    assert builder.circuit == stim.Circuit(
        """
        QUBIT_COORDS(0, 0) 0
        QUBIT_COORDS(0, 1) 1
        QUBIT_COORDS(1, 0) 2
        QUBIT_COORDS(2, 0) 3
        QUBIT_COORDS(3, 0) 4
        QUBIT_COORDS(4, 0) 5
        MPP X0*X1*X2*X3*X4*X5
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z1*Z2*Z3*Z4*Z5
        OBSERVABLE_INCLUDE(1) rec[-1]
        MPP X0*Z2*Z3*X4 X2*Z3*Z4*X5 X0*X3*Z4*Z5 Z0*X2*X4*Z5
    """
    )

    builder.circuit.clear()
    builder.measure_stabilizer_code(
        perfect_code,
        save_layer="end",
        det_cmp_layer="init",
        observables_first=False,
        ancilla_qubits_for_xz_observable_pairs=[1j],
    )
    assert builder.circuit == stim.Circuit(
        """
        MPP X0*Z2*Z3*X4 X2*Z3*Z4*X5 X0*X3*Z4*Z5 Z0*X2*X4*Z5
        DETECTOR(0, 1, 0) rec[-8] rec[-4]
        DETECTOR(1, 1, 0) rec[-7] rec[-3]
        DETECTOR(2, 1, 0) rec[-6] rec[-2]
        DETECTOR(3, 1, 0) rec[-5] rec[-1]
        MPP X0*X1*X2*X3*X4*X5
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP Z0*Z1*Z2*Z3*Z4*Z5
        OBSERVABLE_INCLUDE(1) rec[-1]
    """
    )
