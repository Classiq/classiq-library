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

import gen
from clorco.rep_code._rep_code_layouts import make_rep_code_layout


def test_make_rep_code_layout():
    v = make_rep_code_layout(distance=5, coloring="rgb")
    v.check_commutation_relationships()
    assert v == gen.StabilizerCode(
        patch=gen.Patch(
            tiles=[
                gen.Tile(
                    ordered_data_qubits=(0, 1),
                    measurement_qubit=0.5,
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(1, 2),
                    measurement_qubit=1.5,
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(2, 3),
                    measurement_qubit=2.5,
                    bases="Z",
                    extra_coords=(5,),
                ),
                gen.Tile(
                    ordered_data_qubits=(3, 4),
                    measurement_qubit=3.5,
                    bases="Z",
                    extra_coords=(3,),
                ),
            ]
        ),
        observables_x=[],
        observables_z=[
            gen.PauliString(qubits={0: "Z"}),
        ],
    )

    v = make_rep_code_layout(distance=3, coloring="rg", toric=True)
    v.check_commutation_relationships()
    assert v == gen.StabilizerCode(
        patch=gen.Patch(
            tiles=[
                gen.Tile(
                    ordered_data_qubits=(0, 1),
                    measurement_qubit=0.5,
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(1, 2),
                    measurement_qubit=1.5,
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(2, 0),
                    measurement_qubit=2.5,
                    bases="Z",
                    extra_coords=(3,),
                ),
            ]
        ),
        observables_x=[],
        observables_z=[
            gen.PauliString(qubits={0: "Z"}),
        ],
    )
