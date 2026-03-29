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
from clorco.surface_code._surface_code_layouts import (
    make_surface_code_layout,
    make_toric_surface_code_layout,
)


def test_make_surface_code_layout():
    code = make_surface_code_layout(
        width=3,
        height=4,
    )
    assert len(code.observables_x) == len(code.observables_z) == 1
    code.check_commutation_relationships()
    assert (
        len(code.make_code_capacity_circuit(noise=1e-3).shortest_graphlike_error()) == 3
    )
    assert code.patch.tiles == (
        gen.Tile(
            ordered_data_qubits=(None, None, 0j, 1j),
            measurement_qubit=(-0.5 + 0.5j),
            bases="Z",
            extra_coords=(5,),
        ),
        gen.Tile(
            ordered_data_qubits=(None, None, 2j, 3j),
            measurement_qubit=(-0.5 + 2.5j),
            bases="Z",
            extra_coords=(5,),
        ),
        gen.Tile(
            ordered_data_qubits=(0j, (1 + 0j), 1j, (1 + 1j)),
            measurement_qubit=(0.5 + 0.5j),
            bases="X",
            extra_coords=(0,),
        ),
        gen.Tile(
            ordered_data_qubits=(1j, 2j, (1 + 1j), (1 + 2j)),
            measurement_qubit=(0.5 + 1.5j),
            bases="Z",
            extra_coords=(3,),
        ),
        gen.Tile(
            ordered_data_qubits=(2j, (1 + 2j), 3j, (1 + 3j)),
            measurement_qubit=(0.5 + 2.5j),
            bases="X",
            extra_coords=(0,),
        ),
        gen.Tile(
            ordered_data_qubits=(None, None, (1 + 0j), (2 + 0j)),
            measurement_qubit=(1.5 - 0.5j),
            bases="X",
            extra_coords=(2,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 0j), (1 + 1j), (2 + 0j), (2 + 1j)),
            measurement_qubit=(1.5 + 0.5j),
            bases="Z",
            extra_coords=(5,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 1j), (2 + 1j), (1 + 2j), (2 + 2j)),
            measurement_qubit=(1.5 + 1.5j),
            bases="X",
            extra_coords=(2,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 2j), (1 + 3j), (2 + 2j), (2 + 3j)),
            measurement_qubit=(1.5 + 2.5j),
            bases="Z",
            extra_coords=(5,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 3j), (2 + 3j), None, None),
            measurement_qubit=(1.5 + 3.5j),
            bases="X",
            extra_coords=(2,),
        ),
        gen.Tile(
            ordered_data_qubits=((2 + 1j), (2 + 2j), None, None),
            measurement_qubit=(2.5 + 1.5j),
            bases="Z",
            extra_coords=(3,),
        ),
    )


def test_make_toric_surface_code_layout():
    code = make_toric_surface_code_layout(
        width=4,
        height=6,
    )
    assert len(code.observables_x) == len(code.observables_z) == 2
    code.check_commutation_relationships()
    assert (
        len(code.make_code_capacity_circuit(noise=1e-3).shortest_graphlike_error()) == 4
    )
    assert code.patch.tiles == (
        gen.Tile(
            ordered_data_qubits=(0j, 1j, (1 + 0j), (1 + 1j)),
            measurement_qubit=(0.5 + 0.5j),
            bases="X",
            extra_coords=(0,),
        ),
        gen.Tile(
            ordered_data_qubits=(1j, (1 + 1j), 2j, (1 + 2j)),
            measurement_qubit=(0.5 + 1.5j),
            bases="Z",
            extra_coords=(3,),
        ),
        gen.Tile(
            ordered_data_qubits=(2j, 3j, (1 + 2j), (1 + 3j)),
            measurement_qubit=(0.5 + 2.5j),
            bases="X",
            extra_coords=(0,),
        ),
        gen.Tile(
            ordered_data_qubits=(3j, (1 + 3j), 4j, (1 + 4j)),
            measurement_qubit=(0.5 + 3.5j),
            bases="Z",
            extra_coords=(3,),
        ),
        gen.Tile(
            ordered_data_qubits=(4j, 5j, (1 + 4j), (1 + 5j)),
            measurement_qubit=(0.5 + 4.5j),
            bases="X",
            extra_coords=(0,),
        ),
        gen.Tile(
            ordered_data_qubits=(5j, (1 + 5j), 0j, (1 + 0j)),
            measurement_qubit=(0.5 + 5.5j),
            bases="Z",
            extra_coords=(3,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 0j), (2 + 0j), (1 + 1j), (2 + 1j)),
            measurement_qubit=(1.5 + 0.5j),
            bases="Z",
            extra_coords=(4,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 1j), (1 + 2j), (2 + 1j), (2 + 2j)),
            measurement_qubit=(1.5 + 1.5j),
            bases="X",
            extra_coords=(1,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 2j), (2 + 2j), (1 + 3j), (2 + 3j)),
            measurement_qubit=(1.5 + 2.5j),
            bases="Z",
            extra_coords=(4,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 3j), (1 + 4j), (2 + 3j), (2 + 4j)),
            measurement_qubit=(1.5 + 3.5j),
            bases="X",
            extra_coords=(1,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 4j), (2 + 4j), (1 + 5j), (2 + 5j)),
            measurement_qubit=(1.5 + 4.5j),
            bases="Z",
            extra_coords=(4,),
        ),
        gen.Tile(
            ordered_data_qubits=((1 + 5j), (1 + 0j), (2 + 5j), (2 + 0j)),
            measurement_qubit=(1.5 + 5.5j),
            bases="X",
            extra_coords=(1,),
        ),
        gen.Tile(
            ordered_data_qubits=((2 + 0j), (2 + 1j), (3 + 0j), (3 + 1j)),
            measurement_qubit=(2.5 + 0.5j),
            bases="X",
            extra_coords=(0,),
        ),
        gen.Tile(
            ordered_data_qubits=((2 + 1j), (3 + 1j), (2 + 2j), (3 + 2j)),
            measurement_qubit=(2.5 + 1.5j),
            bases="Z",
            extra_coords=(3,),
        ),
        gen.Tile(
            ordered_data_qubits=((2 + 2j), (2 + 3j), (3 + 2j), (3 + 3j)),
            measurement_qubit=(2.5 + 2.5j),
            bases="X",
            extra_coords=(0,),
        ),
        gen.Tile(
            ordered_data_qubits=((2 + 3j), (3 + 3j), (2 + 4j), (3 + 4j)),
            measurement_qubit=(2.5 + 3.5j),
            bases="Z",
            extra_coords=(3,),
        ),
        gen.Tile(
            ordered_data_qubits=((2 + 4j), (2 + 5j), (3 + 4j), (3 + 5j)),
            measurement_qubit=(2.5 + 4.5j),
            bases="X",
            extra_coords=(0,),
        ),
        gen.Tile(
            ordered_data_qubits=((2 + 5j), (3 + 5j), (2 + 0j), (3 + 0j)),
            measurement_qubit=(2.5 + 5.5j),
            bases="Z",
            extra_coords=(3,),
        ),
        gen.Tile(
            ordered_data_qubits=((3 + 0j), 0j, (3 + 1j), 1j),
            measurement_qubit=(3.5 + 0.5j),
            bases="Z",
            extra_coords=(4,),
        ),
        gen.Tile(
            ordered_data_qubits=((3 + 1j), (3 + 2j), 1j, 2j),
            measurement_qubit=(3.5 + 1.5j),
            bases="X",
            extra_coords=(1,),
        ),
        gen.Tile(
            ordered_data_qubits=((3 + 2j), 2j, (3 + 3j), 3j),
            measurement_qubit=(3.5 + 2.5j),
            bases="Z",
            extra_coords=(4,),
        ),
        gen.Tile(
            ordered_data_qubits=((3 + 3j), (3 + 4j), 3j, 4j),
            measurement_qubit=(3.5 + 3.5j),
            bases="X",
            extra_coords=(1,),
        ),
        gen.Tile(
            ordered_data_qubits=((3 + 4j), 4j, (3 + 5j), 5j),
            measurement_qubit=(3.5 + 4.5j),
            bases="Z",
            extra_coords=(4,),
        ),
        gen.Tile(
            ordered_data_qubits=((3 + 5j), (3 + 0j), 5j, 0j),
            measurement_qubit=(3.5 + 5.5j),
            bases="X",
            extra_coords=(1,),
        ),
    )
