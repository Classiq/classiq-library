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
import math
from typing import Literal

import pytest
import stim

import gen

from clorco.color_code._color_code_layouts import (
    make_color_code_layout_488,
    make_color_code_layout,
    make_toric_color_code_layout,
)


def test_make_color_code_patch_3_6():
    patch = make_color_code_layout(
        base_width=9,
        spurs="midout",
        coord_style="rect",
        single_rgb_layer_instead_of_actual_code=True,
    ).patch
    assert len(patch.tiles) == 34
    patch = make_color_code_layout(
        base_width=11,
        spurs="midout",
        coord_style="rect",
        single_rgb_layer_instead_of_actual_code=True,
    ).patch
    assert len(patch.tiles) == 50

    patch = make_color_code_layout(
        base_width=3,
        spurs="midout",
        coord_style="rect",
        single_rgb_layer_instead_of_actual_code=True,
    ).patch
    assert patch == gen.Patch(
        tiles=[
            gen.Tile(
                ordered_data_qubits=((1 + 3j), (1 + 2j), (1 + 1j), 1j),
                measurement_qubit=(1 + 1j),
                bases="Y",
                extra_coords=(1,),
            ),
            gen.Tile(
                ordered_data_qubits=((2 + 1j), (2 + 2j), (1 + 2j), (1 + 1j)),
                measurement_qubit=(1 + 2j),
                bases="Z",
                extra_coords=(2,),
            ),
            gen.Tile(
                ordered_data_qubits=(
                    (2 + 2j),
                    (2 + 3j),
                    (2 + 4j),
                    (1 + 4j),
                    (1 + 3j),
                    (1 + 2j),
                ),
                measurement_qubit=(1 + 4j),
                bases="X",
                extra_coords=(0.0,),
            ),
            gen.Tile(
                ordered_data_qubits=((2 + 3j), (2 + 4j)),
                measurement_qubit=(2 + 3j),
                bases="Z",
                extra_coords=(2,),
            ),
        ]
    )


def test_make_color_code_patch_4_8_8():
    patch = make_color_code_layout_488(
        base_width=11,
        spurs="midout",
        single_rgb_layer_instead_of_actual_code=True,
        coord_style="rect",
    ).patch
    assert len(patch.tiles) == 40
    patch = make_color_code_layout_488(
        base_width=11,
        spurs="midout_readout_line_constraint",
        single_rgb_layer_instead_of_actual_code=True,
        coord_style="rect",
    ).patch
    assert len(patch.tiles) == 45
    patch = make_color_code_layout_488(
        base_width=13,
        spurs="midout",
        single_rgb_layer_instead_of_actual_code=True,
        coord_style="rect",
    ).patch
    assert len(patch.tiles) == 54
    patch = make_color_code_layout_488(
        base_width=13,
        spurs="midout_readout_line_constraint",
        single_rgb_layer_instead_of_actual_code=True,
        coord_style="rect",
    ).patch
    assert len(patch.tiles) == 60

    patch = make_color_code_layout_488(
        base_width=5,
        spurs="midout",
        single_rgb_layer_instead_of_actual_code=True,
        coord_style="rect",
    ).patch
    assert patch == gen.Patch(
        tiles=[
            gen.Tile(
                ordered_data_qubits=(
                    2j,
                    1j,
                    0j,
                    1j,
                    (1 + 1j),
                    (1 + 0j),
                    (1 + 1j),
                    (1 + 2j),
                ),
                measurement_qubit=1j,
                bases="Y",
                extra_coords=[1],
            ),
            gen.Tile(
                ordered_data_qubits=(1j, 2j),
                measurement_qubit=2j,
                bases="X",
                extra_coords=[0],
            ),
            gen.Tile(
                ordered_data_qubits=((1 + 1j), 1, 2, (2 + 1j)),
                measurement_qubit=2.0,
                bases="Z",
                extra_coords=[2],
            ),
            gen.Tile(
                ordered_data_qubits=(
                    (2 + 3j),
                    (2 + 2j),
                    (2 + 1j),
                    (2 + 0j),
                    (2 + 1j),
                    (3 + 1j),
                    (3 + 0j),
                    (3 + 1j),
                    (3 + 2j),
                    (3 + 3j),
                ),
                measurement_qubit=(2 + 1j),
                bases="Y",
                extra_coords=[1],
            ),
            gen.Tile(
                ordered_data_qubits=((1 + 1j), (1 + 2j), (2 + 2j), (2 + 1j)),
                measurement_qubit=(2 + 2j),
                bases="X",
                extra_coords=[0],
            ),
            gen.Tile(
                ordered_data_qubits=((2 + 4j), (2 + 3j), (3 + 3j), (3 + 4j)),
                measurement_qubit=(2 + 3j),
                bases="X",
                extra_coords=[0],
            ),
            gen.Tile(
                ordered_data_qubits=((3 + 1j), 3, 4, (4 + 1j)),
                measurement_qubit=4.0,
                bases="Z",
                extra_coords=[2],
            ),
            gen.Tile(
                ordered_data_qubits=((3 + 1j), (3 + 2j), (4 + 2j), (4 + 1j)),
                measurement_qubit=(4 + 2j),
                bases="X",
                extra_coords=[0],
            ),
            gen.Tile(
                ordered_data_qubits=((4 + 3j), (4 + 4j)),
                measurement_qubit=(4 + 3j),
                bases="X",
                extra_coords=[0],
            ),
            gen.Tile(
                ordered_data_qubits=(
                    (3 + 2j),
                    (3 + 3j),
                    (3 + 4j),
                    (4 + 4j),
                    (4 + 3j),
                    (4 + 2j),
                ),
                measurement_qubit=(4 + 4j),
                bases="Z",
                extra_coords=[2],
            ),
        ]
    )


@pytest.mark.parametrize(
    "base_width,spurs",
    itertools.product(
        [3, 5, 7, 9, 11, 13],
        ["smooth", "midout", "midout_readout_line_constraint"],
    ),
)
def test_make_color_code_patch_4_8_8_stripped_measurements(
    base_width: int,
    spurs: Literal["smooth", "midout", "midout_readout_line_constraint"],
):
    code = make_color_code_layout_488(
        base_width=base_width,
        spurs=spurs,
        single_rgb_layer_instead_of_actual_code=True,
        coord_style="rect",
    )
    code.check_commutation_relationships()

    patch = code.patch
    all_columns = {c.real for c in patch.data_set}
    assert len(all_columns) == base_width + (
        0 if spurs != "midout_readout_line_constraint" else 1 if base_width == 3 else 2
    )
    measure_columns = {tile.measurement_qubit.real for tile in patch.tiles}
    data_columns = {c.real for c in patch.data_set - patch.measure_set}
    if spurs == "midout_readout_line_constraint":
        assert data_columns.isdisjoint(measure_columns)
    assert len(measure_columns) == math.ceil(len(all_columns) / 2)


@pytest.mark.parametrize(
    "width,height,ablate_into_matchable_code",
    itertools.product(
        [6, 12, 18],
        [4, 8, 12, 16],
        [False, True],
    ),
)
def test_make_toric_color_code_layout(
    width: int, height: int, ablate_into_matchable_code: bool
):
    code = make_toric_color_code_layout(
        width=width,
        height=height,
        ablate_into_matchable_code=ablate_into_matchable_code,
    )
    code.check_commutation_relationships()
    circuit = code.make_code_capacity_circuit(
        noise=gen.NoiseRule(after={"DEPOLARIZE1": 1e-3})
    )
    if ablate_into_matchable_code:
        err = circuit.shortest_graphlike_error(
            canonicalize_circuit_errors=True,
        )
    else:
        err = circuit.search_for_undetectable_logical_errors(
            dont_explore_edges_with_degree_above=4,
            dont_explore_edges_increasing_symptom_degree=False,
            canonicalize_circuit_errors=True,
            dont_explore_detection_event_sets_with_size_above=4,
        )

    expected_distance = min(width // 3 * 2, height // 2)
    assert len(err) == expected_distance


def test_make_toric_color_code_exact():
    assert make_toric_color_code_layout(
        width=6,
        height=8,
        ablate_into_matchable_code=True,
    ) == gen.StabilizerCode(
        patch=gen.Patch(
            tiles=[
                gen.Tile(
                    ordered_data_qubits=(
                        7j,
                        (1 + 0j),
                        (1 + 1j),
                        2j,
                        (5 + 1j),
                        (5 + 0j),
                    ),
                    measurement_qubit=1j,
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        3j,
                        (1 + 4j),
                        (1 + 5j),
                        6j,
                        (5 + 5j),
                        (5 + 4j),
                    ),
                    measurement_qubit=5j,
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (1 + 1j),
                        (2 + 2j),
                        (2 + 3j),
                        (1 + 4j),
                        3j,
                        2j,
                    ),
                    measurement_qubit=(1 + 2j),
                    bases="X",
                    extra_coords=(1,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (1 + 1j),
                        (2 + 2j),
                        (2 + 3j),
                        (1 + 4j),
                        3j,
                        2j,
                    ),
                    measurement_qubit=(1 + 3j),
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (1 + 5j),
                        (2 + 6j),
                        (2 + 7j),
                        (1 + 0j),
                        7j,
                        6j,
                    ),
                    measurement_qubit=(1 + 6j),
                    bases="X",
                    extra_coords=(1,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (1 + 5j),
                        (2 + 6j),
                        (2 + 7j),
                        (1 + 0j),
                        7j,
                        6j,
                    ),
                    measurement_qubit=(1 + 7j),
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (2 + 7j),
                        (3 + 0j),
                        (3 + 1j),
                        (2 + 2j),
                        (1 + 1j),
                        (1 + 0j),
                    ),
                    measurement_qubit=(2 + 0j),
                    bases="X",
                    extra_coords=(2,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (2 + 3j),
                        (3 + 4j),
                        (3 + 5j),
                        (2 + 6j),
                        (1 + 5j),
                        (1 + 4j),
                    ),
                    measurement_qubit=(2 + 4j),
                    bases="X",
                    extra_coords=(2,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (3 + 1j),
                        (4 + 2j),
                        (4 + 3j),
                        (3 + 4j),
                        (2 + 3j),
                        (2 + 2j),
                    ),
                    measurement_qubit=(3 + 3j),
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (3 + 5j),
                        (4 + 6j),
                        (4 + 7j),
                        (3 + 0j),
                        (2 + 7j),
                        (2 + 6j),
                    ),
                    measurement_qubit=(3 + 7j),
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (4 + 7j),
                        (5 + 0j),
                        (5 + 1j),
                        (4 + 2j),
                        (3 + 1j),
                        (3 + 0j),
                    ),
                    measurement_qubit=(4 + 0j),
                    bases="X",
                    extra_coords=(1,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (4 + 7j),
                        (5 + 0j),
                        (5 + 1j),
                        (4 + 2j),
                        (3 + 1j),
                        (3 + 0j),
                    ),
                    measurement_qubit=(4 + 1j),
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (4 + 3j),
                        (5 + 4j),
                        (5 + 5j),
                        (4 + 6j),
                        (3 + 5j),
                        (3 + 4j),
                    ),
                    measurement_qubit=(4 + 4j),
                    bases="X",
                    extra_coords=(1,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (4 + 3j),
                        (5 + 4j),
                        (5 + 5j),
                        (4 + 6j),
                        (3 + 5j),
                        (3 + 4j),
                    ),
                    measurement_qubit=(4 + 5j),
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (5 + 1j),
                        2j,
                        3j,
                        (5 + 4j),
                        (4 + 3j),
                        (4 + 2j),
                    ),
                    measurement_qubit=(5 + 2j),
                    bases="X",
                    extra_coords=(2,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (5 + 5j),
                        6j,
                        7j,
                        (5 + 0j),
                        (4 + 7j),
                        (4 + 6j),
                    ),
                    measurement_qubit=(5 + 6j),
                    bases="X",
                    extra_coords=(2,),
                ),
            ]
        ),
        observables_x=[
            gen.PauliString(qubits={2j: "X", 3j: "X", 6j: "X", 7j: "X"}),
            gen.PauliString(
                qubits={(1 + 4j): "X", (2 + 3j): "X", (4 + 3j): "X", (5 + 4j): "X"}
            ),
        ],
        observables_z=[
            gen.PauliString(
                qubits={2j: "Z", (1 + 1j): "Z", (3 + 1j): "Z", (4 + 2j): "Z"}
            ),
            gen.PauliString(
                qubits={(2 + 2j): "Z", (2 + 3j): "Z", (2 + 6j): "Z", (2 + 7j): "Z"}
            ),
        ],
    )


def test_make_toric_color_code_phenom_circuit_exact():
    code = make_toric_color_code_layout(
        width=6,
        height=8,
        ablate_into_matchable_code=True,
    )
    assert code.make_code_capacity_circuit(noise=0.125) == stim.Circuit(
        """
        QUBIT_COORDS(0, -1) 0
        QUBIT_COORDS(0, 2) 1
        QUBIT_COORDS(0, 3) 2
        QUBIT_COORDS(0, 6) 3
        QUBIT_COORDS(0, 7) 4
        QUBIT_COORDS(1, -1) 5
        QUBIT_COORDS(1, 0) 6
        QUBIT_COORDS(1, 1) 7
        QUBIT_COORDS(1, 4) 8
        QUBIT_COORDS(1, 5) 9
        QUBIT_COORDS(2, 2) 10
        QUBIT_COORDS(2, 3) 11
        QUBIT_COORDS(2, 6) 12
        QUBIT_COORDS(2, 7) 13
        QUBIT_COORDS(3, 0) 14
        QUBIT_COORDS(3, 1) 15
        QUBIT_COORDS(3, 4) 16
        QUBIT_COORDS(3, 5) 17
        QUBIT_COORDS(4, 2) 18
        QUBIT_COORDS(4, 3) 19
        QUBIT_COORDS(4, 6) 20
        QUBIT_COORDS(4, 7) 21
        QUBIT_COORDS(5, 0) 22
        QUBIT_COORDS(5, 1) 23
        QUBIT_COORDS(5, 4) 24
        QUBIT_COORDS(5, 5) 25
        MPP X0*X1*X2*X3*X4
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP X5*X8*X11*X19*X24
        OBSERVABLE_INCLUDE(1) rec[-1]
        MPP Z0*Z1*Z7*Z15*Z18
        OBSERVABLE_INCLUDE(2) rec[-1]
        MPP Z5*Z10*Z11*Z12*Z13
        OBSERVABLE_INCLUDE(3) rec[-1]
        MPP Z1*Z4*Z6*Z7*Z22*Z23 Z2*Z3*Z8*Z9*Z24*Z25 X1*X2*X7*X8*X10*X11 Z1*Z2*Z7*Z8*Z10*Z11 X3*X4*X6*X9*X12*X13 Z3*Z4*Z6*Z9*Z12*Z13 X6*X7*X10*X13*X14*X15 X8*X9*X11*X12*X16*X17 Z10*Z11*Z15*Z16*Z18*Z19 Z12*Z13*Z14*Z17*Z20*Z21 X14*X15*X18*X21*X22*X23 Z14*Z15*Z18*Z21*Z22*Z23 X16*X17*X19*X20*X24*X25 Z16*Z17*Z19*Z20*Z24*Z25 X1*X2*X18*X19*X23*X24 X3*X4*X20*X21*X22*X25
        TICK
        DEPOLARIZE1(0.125) 1 2 3 4 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
        TICK
        MPP Z1*Z4*Z6*Z7*Z22*Z23 Z2*Z3*Z8*Z9*Z24*Z25 X1*X2*X7*X8*X10*X11 Z1*Z2*Z7*Z8*Z10*Z11 X3*X4*X6*X9*X12*X13 Z3*Z4*Z6*Z9*Z12*Z13 X6*X7*X10*X13*X14*X15 X8*X9*X11*X12*X16*X17 Z10*Z11*Z15*Z16*Z18*Z19 Z12*Z13*Z14*Z17*Z20*Z21 X14*X15*X18*X21*X22*X23 Z14*Z15*Z18*Z21*Z22*Z23 X16*X17*X19*X20*X24*X25 Z16*Z17*Z19*Z20*Z24*Z25 X1*X2*X18*X19*X23*X24 X3*X4*X20*X21*X22*X25
        DETECTOR(0, 1, 0, 3) rec[-32] rec[-16]
        DETECTOR(0, 5, 0, 3) rec[-31] rec[-15]
        DETECTOR(1, 2, 0, 1) rec[-30] rec[-14]
        DETECTOR(1, 3, 0, 4) rec[-29] rec[-13]
        DETECTOR(1, 6, 0, 1) rec[-28] rec[-12]
        DETECTOR(1, 7, 0, 4) rec[-27] rec[-11]
        DETECTOR(2, 0, 0, 2) rec[-26] rec[-10]
        DETECTOR(2, 4, 0, 2) rec[-25] rec[-9]
        DETECTOR(3, 3, 0, 3) rec[-24] rec[-8]
        DETECTOR(3, 7, 0, 3) rec[-23] rec[-7]
        DETECTOR(4, 0, 0, 1) rec[-22] rec[-6]
        DETECTOR(4, 1, 0, 4) rec[-21] rec[-5]
        DETECTOR(4, 4, 0, 1) rec[-20] rec[-4]
        DETECTOR(4, 5, 0, 4) rec[-19] rec[-3]
        DETECTOR(5, 2, 0, 2) rec[-18] rec[-2]
        DETECTOR(5, 6, 0, 2) rec[-17] rec[-1]
        MPP X0*X1*X2*X3*X4
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP X5*X8*X11*X19*X24
        OBSERVABLE_INCLUDE(1) rec[-1]
        MPP Z0*Z1*Z7*Z15*Z18
        OBSERVABLE_INCLUDE(2) rec[-1]
        MPP Z5*Z10*Z11*Z12*Z13
        OBSERVABLE_INCLUDE(3) rec[-1]
    """
    )


def test_make_toric_color_code_exact_square_coords():
    assert make_toric_color_code_layout(
        width=6,
        height=8,
        ablate_into_matchable_code=True,
        square_coords=True,
    ) == gen.StabilizerCode(
        patch=gen.Patch(
            tiles=[
                gen.Tile(
                    ordered_data_qubits=(
                        0j,
                        (1 + 0j),
                        (1 + 1j),
                        1j,
                        (5 + 1j),
                        (5 + 0j),
                    ),
                    measurement_qubit=1j,
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        2j,
                        (1 + 2j),
                        (1 + 3j),
                        3j,
                        (5 + 3j),
                        (5 + 2j),
                    ),
                    measurement_qubit=3j,
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (1 + 3j),
                        (2 + 3j),
                        (2 + 0j),
                        (1 + 0j),
                        0j,
                        3j,
                    ),
                    measurement_qubit=(1 + 0j),
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (1 + 1j),
                        (2 + 1j),
                        (2 + 2j),
                        (1 + 2j),
                        2j,
                        1j,
                    ),
                    measurement_qubit=(1 + 1j),
                    bases="X",
                    extra_coords=(1,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (1 + 1j),
                        (2 + 1j),
                        (2 + 2j),
                        (1 + 2j),
                        2j,
                        1j,
                    ),
                    measurement_qubit=(1 + 2j),
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (1 + 3j),
                        (2 + 3j),
                        (2 + 0j),
                        (1 + 0j),
                        0j,
                        3j,
                    ),
                    measurement_qubit=(1 + 3j),
                    bases="X",
                    extra_coords=(1,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (2 + 0j),
                        (3 + 0j),
                        (3 + 1j),
                        (2 + 1j),
                        (1 + 1j),
                        (1 + 0j),
                    ),
                    measurement_qubit=(2 + 0j),
                    bases="X",
                    extra_coords=(2,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (2 + 2j),
                        (3 + 2j),
                        (3 + 3j),
                        (2 + 3j),
                        (1 + 3j),
                        (1 + 2j),
                    ),
                    measurement_qubit=(2 + 2j),
                    bases="X",
                    extra_coords=(2,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (3 + 3j),
                        (4 + 3j),
                        (4 + 0j),
                        (3 + 0j),
                        (2 + 0j),
                        (2 + 3j),
                    ),
                    measurement_qubit=(3 + 0j),
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (3 + 1j),
                        (4 + 1j),
                        (4 + 2j),
                        (3 + 2j),
                        (2 + 2j),
                        (2 + 1j),
                    ),
                    measurement_qubit=(3 + 2j),
                    bases="Z",
                    extra_coords=(3,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (4 + 0j),
                        (5 + 0j),
                        (5 + 1j),
                        (4 + 1j),
                        (3 + 1j),
                        (3 + 0j),
                    ),
                    measurement_qubit=(4 + 0j),
                    bases="X",
                    extra_coords=(1,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (4 + 0j),
                        (5 + 0j),
                        (5 + 1j),
                        (4 + 1j),
                        (3 + 1j),
                        (3 + 0j),
                    ),
                    measurement_qubit=(4 + 1j),
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (4 + 2j),
                        (5 + 2j),
                        (5 + 3j),
                        (4 + 3j),
                        (3 + 3j),
                        (3 + 2j),
                    ),
                    measurement_qubit=(4 + 2j),
                    bases="X",
                    extra_coords=(1,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (4 + 2j),
                        (5 + 2j),
                        (5 + 3j),
                        (4 + 3j),
                        (3 + 3j),
                        (3 + 2j),
                    ),
                    measurement_qubit=(4 + 3j),
                    bases="Z",
                    extra_coords=(4,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (5 + 1j),
                        1j,
                        2j,
                        (5 + 2j),
                        (4 + 2j),
                        (4 + 1j),
                    ),
                    measurement_qubit=(5 + 1j),
                    bases="X",
                    extra_coords=(2,),
                ),
                gen.Tile(
                    ordered_data_qubits=(
                        (5 + 3j),
                        3j,
                        0j,
                        (5 + 0j),
                        (4 + 0j),
                        (4 + 3j),
                    ),
                    measurement_qubit=(5 + 3j),
                    bases="X",
                    extra_coords=(2,),
                ),
            ]
        ),
        observables_x=[
            gen.PauliString(qubits={0j: "X", 1j: "X", 2j: "X", 3j: "X"}),
            gen.PauliString(
                qubits={(1 + 2j): "X", (2 + 2j): "X", (4 + 2j): "X", (5 + 2j): "X"}
            ),
        ],
        observables_z=[
            gen.PauliString(
                qubits={1j: "Z", (1 + 1j): "Z", (3 + 1j): "Z", (4 + 1j): "Z"}
            ),
            gen.PauliString(
                qubits={(2 + 0j): "Z", (2 + 1j): "Z", (2 + 2j): "Z", (2 + 3j): "Z"}
            ),
        ],
    )
