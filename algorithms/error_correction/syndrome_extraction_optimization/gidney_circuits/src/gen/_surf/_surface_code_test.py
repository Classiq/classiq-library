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
from gen._surf._patch_outline import PatchOutline
from gen._surf._closed_curve import ClosedCurve
from gen._surf._order import Order_Z, Order_ᴎ, checkerboard_basis
from gen._surf._surface_code import layer_transition, surface_code_patch
from gen._core._builder import Builder
from gen._core._pauli_string import PauliString


def test_surface_code_patch():
    patch = surface_code_patch(
        width=5,
        height=5,
        top_basis="Z",
        bot_basis="Z",
        left_basis="X",
        right_basis="X",
        rel_order_func=lambda _: Order_Z,
    )
    assert len(patch.data_set) == 25
    assert len(patch.tiles) == 24


def test_layer_transition_notched_shift():
    c0 = ClosedCurve.from_cycle(
        [
            "Z",
            6 + 0j,
            "X",
            6 + 6j,
            "Z",
            0 + 6j,
            "X",
            0 + 0j,
        ]
    )
    p0 = PatchOutline([c0]).to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )
    p2 = PatchOutline([c0.offset_by(2)]).to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )
    p3 = PatchOutline([c0.offset_by(3)]).to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )

    builder = Builder.for_qubits(p0.used_set | p3.used_set | {-1})

    builder.measure_pauli_string(
        PauliString.from_xyzs(zs=[q for q in p0.data_set if q.real == 4] + [-1]),
        key="H_INIT",
    )
    builder.obs_include(["H_INIT"], obs_index=2)
    builder.tick()
    builder.measure_pauli_string(
        PauliString.from_xyzs(xs=[q for q in p0.data_set if q.imag == 0] + [-1]),
        key="V_INIT",
    )
    builder.obs_include(["V_INIT"], obs_index=5)
    builder.tick()

    builder.measure_patch(patch=p0, save_layer=4)

    builder.tick()
    layer_transition(
        builder=builder,
        past_patch=p0,
        future_patch=p2,
        kept_data_qubits=p0.data_set & p2.data_set & p3.data_set,
        style="mpp",
        past_compare_layer=4,
        past_save_layer=5,
        future_save_layer=6,
        past_layer_lost_data_obs_qubit_sets={
            2: {q for q in p0.data_set | p3.data_set if q.real == 4},
            5: {q for q in p0.data_set | p3.data_set if q.imag == 0},
        },
        future_layer_gain_data_reset_basis="X",
        past_layer_lost_data_measure_basis="X",
    )

    builder.measure_pauli_string(
        PauliString.from_xyzs(zs=[q for q in p2.data_set if q.real == 4] + [-1]),
        key="H_OUT",
    )
    builder.obs_include(["H_OUT"], obs_index=2)
    builder.tick()
    builder.measure_pauli_string(
        PauliString.from_xyzs(xs=[q for q in p2.data_set if q.imag == 0] + [-1]),
        key="V_OUT",
    )
    builder.obs_include(["V_OUT"], obs_index=5)
    builder.tick()

    # Verify that all detectors and observables are deterministic.
    builder.circuit.detector_error_model(decompose_errors=True)


def test_layer_transition_shrink():
    c_shrunk = ClosedCurve.from_cycle(
        [
            "X",
            3 + 0j,
            "Z",
            3 + 6j,
            "X",
            0 + 6j,
            "Z",
            0 + 0j,
        ]
    )

    c_full = ClosedCurve.from_cycle(
        [
            "X",
            6 + 0j,
            "Z",
            6 + 6j,
            "X",
            0 + 6j,
            "Z",
            0 + 0j,
        ]
    )

    p_shrunk = PatchOutline([c_shrunk]).to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )
    p_full = PatchOutline([c_full]).to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )

    builder = Builder.for_qubits(p_full.used_set | {-1})

    builder.measure_pauli_string(
        gen.PauliString.from_xyzs(
            xs=[q for q in p_full.data_set if q.real == 0] + [-1]
        ),
        key="H_INIT",
    )
    builder.obs_include(["H_INIT"], obs_index=2)
    builder.tick()
    builder.measure_pauli_string(
        gen.PauliString.from_xyzs(
            zs=[q for q in p_full.data_set if q.imag == 0] + [-1]
        ),
        key="V_INIT",
    )
    builder.obs_include(["V_INIT"], obs_index=5)
    builder.tick()

    builder.measure_patch(patch=p_full, save_layer=4)

    builder.tick()
    layer_transition(
        builder=builder,
        past_patch=p_full,
        future_patch=p_shrunk,
        kept_data_qubits=p_shrunk.data_set,
        style="mpp",
        past_compare_layer=4,
        past_save_layer=5,
        future_save_layer=6,
        past_layer_lost_data_obs_qubit_sets={
            2: {q for q in p_full.data_set if q.real == 0},
            5: {q for q in p_full.data_set if q.imag == 0},
        },
        past_layer_lost_data_measure_basis="Z",
        future_layer_gain_data_reset_basis="Z",
    )

    builder.measure_pauli_string(
        PauliString.from_xyzs(xs=[q for q in p_shrunk.data_set if q.real == 0] + [-1]),
        key="H_OUT",
    )
    builder.obs_include(["H_OUT"], obs_index=2)
    builder.tick()
    builder.measure_pauli_string(
        PauliString.from_xyzs(zs=[q for q in p_shrunk.data_set if q.imag == 0] + [-1]),
        key="V_OUT",
    )
    builder.obs_include(["V_OUT"], obs_index=5)
    builder.tick()

    # Verify that all detectors and observables are deterministic.
    builder.circuit.detector_error_model(decompose_errors=True)


def test_layer_transition_full_notch():
    c = ClosedCurve.from_cycle(
        [
            "X",
            3 + 0j,
            "Z",
            3 + 3j,
            "X",
            0 + 3j,
            "Z",
            0 + 0j,
        ]
    )

    p = PatchOutline([c]).to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )
    builder = Builder.for_qubits(p.used_set)
    builder.measure_patch(patch=p, save_layer=4)
    builder.tick()
    layer_transition(
        builder=builder,
        past_patch=p,
        future_patch=p,
        kept_data_qubits=set(),
        style="mpp",
        past_compare_layer=4,
        past_save_layer=5,
        future_save_layer=6,
        past_layer_lost_data_obs_qubit_sets={},
        past_layer_lost_data_measure_basis="Z",
        future_layer_gain_data_reset_basis="Z",
    )

    # Verify that all detectors and observables are deterministic.
    builder.circuit.detector_error_model(decompose_errors=True)
    assert builder.circuit.num_detectors == 7 * 3 + 8


def test_fused_inner():
    b1 = PatchOutline(
        [
            ClosedCurve(
                points=[
                    0 + 16j,
                    6 + 16j,
                    8 + 16j,
                    14 + 16j,
                    16 + 16j,
                    22 + 16j,
                    22 + 18j,
                    22 + 20j,
                    22 + 22j,
                    22 + 24j,
                    22 + 26j,
                    22 + 28j,
                    22 + 30j,
                    16 + 30j,
                    16 + 28j,
                    16 + 26j,
                    14 + 26j,
                    8 + 26j,
                    8 + 24j,
                    14 + 24j,
                    16 + 24j,
                    16 + 22j,
                    16 + 20j,
                    16 + 18j,
                    14 + 18j,
                    8 + 18j,
                    6 + 18j,
                    6 + 20j,
                    8 + 20j,
                    14 + 20j,
                    14 + 22j,
                    8 + 22j,
                    6 + 22j,
                    6 + 24j,
                    6 + 26j,
                    6 + 28j,
                    8 + 28j,
                    14 + 28j,
                    14 + 30j,
                    8 + 30j,
                    6 + 30j,
                    30j,
                    28j,
                    26j,
                    24j,
                    22j,
                    20j,
                    18j,
                ],
                bases="XXXXXXXXXXXXXXXXXXZXXXXXXXXXXXZXXXXXXXZXXXXXXXXX",
            )
        ]
    )
    b2 = b1.fused(19 + 29j, 11 + 29j)

    assert len(b2.region_curves) == 2
    assert all(e == "X" for e in b2.region_curves[0].bases)
    assert b2.region_curves[1] == ClosedCurve(
        points=[
            (16 + 28j),
            (16 + 26j),
            (14 + 26j),
            (8 + 26j),
            (8 + 24j),
            (14 + 24j),
            (16 + 24j),
            (16 + 22j),
            (16 + 20j),
            (16 + 18j),
            (14 + 18j),
            (8 + 18j),
            (6 + 18j),
            (6 + 20j),
            (8 + 20j),
            (14 + 20j),
            (14 + 22j),
            (8 + 22j),
            (6 + 22j),
            (6 + 24j),
            (6 + 26j),
            (6 + 28j),
            (8 + 28j),
            (14 + 28j),
        ],
        bases="XXXXZXXXXXXXXXXXZXXXXXXX",
    )


def test_distance_2():
    curve = ClosedCurve(points=[1, (1 + 1j), 1j, 0], bases="ZXZX")
    plan = PatchOutline([curve]).to_patch(rel_order_func=lambda _: Order_Z)
    assert len(plan.tiles) == 3
