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


def test_step_outline_simple():
    rel_order_func = lambda m: (
        gen.Order_Z if gen.checkerboard_basis(m) == "Z" else gen.Order_ᴎ
    )
    step = gen.StepOutline(
        start=gen.PatchTransitionOutline(
            observable_deltas={},
            data_boundary_planes=[
                gen.ClosedCurve.from_cycle(
                    [
                        "Z",
                        0,
                        2,
                        2 + 2j,
                        2j,
                    ]
                )
            ],
        ),
        body=gen.PatchOutline(
            [
                gen.ClosedCurve.from_cycle(
                    [
                        0,
                        "X",
                        2,
                        "Z",
                        2 + 2j,
                        "X",
                        2j,
                        "Z",
                    ]
                )
            ]
        ),
        end=gen.PatchTransitionOutline(
            observable_deltas={},
            data_boundary_planes=[
                gen.ClosedCurve.from_cycle(
                    [
                        "X",
                        0,
                        2,
                        2 + 2j,
                        2j,
                    ]
                )
            ],
        ),
        rounds=25,
    )
    builder = gen.Builder.for_qubits(
        step.body.to_patch(rel_order_func=rel_order_func).used_set
    )
    step.build_rounds(
        builder=builder,
        rel_order_func=rel_order_func,
        alternate_ordering_with_round_parity=False,
        start_round_index=5,
        cmp_layer=None,
        save_layer="test",
        edit_cur_obs={},
        o2i={},
    )
    assert builder.circuit == stim.Circuit(
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
        RX 10 12 13 15
        R 0 1 2 3 4 5 6 7 8 9 11 14 16
        TICK
        CX 0 11 4 14 6 16 12 1 13 3 15 5
        TICK
        CX 1 9 3 11 7 14 10 0 12 2 13 4
        TICK
        CX 1 11 5 14 7 16 12 4 13 6 15 8
        TICK
        CX 2 9 4 11 8 14 10 3 12 5 13 7
        TICK
        MX 10 12 13 15
        M 9 11 14 16
        DETECTOR(-0.5, 1.5, 0) rec[-4]
        DETECTOR(0.5, 0.5, 0) rec[-3]
        DETECTOR(1.5, 1.5, 0) rec[-2]
        DETECTOR(2.5, 0.5, 0) rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        REPEAT 23 {
            RX 10 12 13 15
            R 9 11 14 16
            TICK
            CX 0 11 4 14 6 16 12 1 13 3 15 5
            TICK
            CX 1 9 3 11 7 14 10 0 12 2 13 4
            TICK
            CX 1 11 5 14 7 16 12 4 13 6 15 8
            TICK
            CX 2 9 4 11 8 14 10 3 12 5 13 7
            TICK
            MX 10 12 13 15
            M 9 11 14 16
            DETECTOR(-0.5, 1.5, 0) rec[-12] rec[-4]
            DETECTOR(0.5, -0.5, 0) rec[-16] rec[-8]
            DETECTOR(0.5, 0.5, 0) rec[-11] rec[-3]
            DETECTOR(0.5, 1.5, 0) rec[-15] rec[-7]
            DETECTOR(1.5, 0.5, 0) rec[-14] rec[-6]
            DETECTOR(1.5, 1.5, 0) rec[-10] rec[-2]
            DETECTOR(1.5, 2.5, 0) rec[-13] rec[-5]
            DETECTOR(2.5, 0.5, 0) rec[-9] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
        }
        RX 10 12 13 15
        R 9 11 14 16
        TICK
        CX 0 11 4 14 6 16 12 1 13 3 15 5
        TICK
        CX 1 9 3 11 7 14 10 0 12 2 13 4
        TICK
        CX 1 11 5 14 7 16 12 4 13 6 15 8
        TICK
        CX 2 9 4 11 8 14 10 3 12 5 13 7
        TICK
        MX 0 1 2 3 4 5 6 7 8 10 12 13 15
        M 9 11 14 16
        DETECTOR(-0.5, 1.5, 0) rec[-21] rec[-4]
        DETECTOR(0.5, -0.5, 0) rec[-25] rec[-8]
        DETECTOR(0.5, 0.5, 0) rec[-20] rec[-3]
        DETECTOR(0.5, 1.5, 0) rec[-24] rec[-7]
        DETECTOR(1.5, 0.5, 0) rec[-23] rec[-6]
        DETECTOR(1.5, 1.5, 0) rec[-19] rec[-2]
        DETECTOR(1.5, 2.5, 0) rec[-22] rec[-5]
        DETECTOR(2.5, 0.5, 0) rec[-18] rec[-1]
        DETECTOR(0.5, -0.5, 0.5) rec[-17] rec[-14] rec[-8]
        DETECTOR(0.5, 1.5, 0.5) rec[-16] rec[-15] rec[-13] rec[-12] rec[-7]
        DETECTOR(1.5, 0.5, 0.5) rec[-14] rec[-13] rec[-11] rec[-10] rec[-6]
        DETECTOR(1.5, 2.5, 0.5) rec[-12] rec[-9] rec[-5]
        SHIFT_COORDS(0, 0, 1)
        TICK
    """
    )


def test_step_outline_alternating():
    rel_order_func = lambda m: (
        gen.Order_Z if gen.checkerboard_basis(m) == "Z" else gen.Order_ᴎ
    )
    step = gen.StepOutline(
        start=gen.PatchTransitionOutline(
            observable_deltas={},
            data_boundary_planes=[
                gen.ClosedCurve.from_cycle(
                    [
                        "Z",
                        0,
                        2,
                        2 + 2j,
                        2j,
                    ]
                )
            ],
        ),
        body=gen.PatchOutline(
            [
                gen.ClosedCurve.from_cycle(
                    [
                        0,
                        "X",
                        2,
                        "Z",
                        2 + 2j,
                        "X",
                        2j,
                        "Z",
                    ]
                )
            ]
        ),
        end=gen.PatchTransitionOutline(
            observable_deltas={},
            data_boundary_planes=[
                gen.ClosedCurve.from_cycle(
                    [
                        "X",
                        0,
                        2,
                        2 + 2j,
                        2j,
                    ]
                )
            ],
        ),
        rounds=25,
    )
    builder = gen.Builder.for_qubits(
        step.body.to_patch(rel_order_func=rel_order_func).used_set
    )
    step.build_rounds(
        builder=builder,
        rel_order_func=rel_order_func,
        alternate_ordering_with_round_parity=True,
        start_round_index=5,
        cmp_layer=None,
        save_layer="test",
        edit_cur_obs={},
        o2i={},
    )
    assert builder.circuit == stim.Circuit(
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
        RX 10 12 13 15
        R 0 1 2 3 4 5 6 7 8 9 11 14 16
        TICK
        CX 2 9 4 11 8 14 10 3 12 5 13 7
        TICK
        CX 1 11 5 14 7 16 12 4 13 6 15 8
        TICK
        CX 1 9 3 11 7 14 10 0 12 2 13 4
        TICK
        CX 0 11 4 14 6 16 12 1 13 3 15 5
        TICK
        MX 10 12 13 15
        M 9 11 14 16
        DETECTOR(-0.5, 1.5, 0) rec[-4]
        DETECTOR(0.5, 0.5, 0) rec[-3]
        DETECTOR(1.5, 1.5, 0) rec[-2]
        DETECTOR(2.5, 0.5, 0) rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        RX 10 12 13 15
        R 9 11 14 16
        TICK
        CX 0 11 4 14 6 16 12 1 13 3 15 5
        TICK
        CX 1 9 3 11 7 14 10 0 12 2 13 4
        TICK
        CX 1 11 5 14 7 16 12 4 13 6 15 8
        TICK
        CX 2 9 4 11 8 14 10 3 12 5 13 7
        TICK
        MX 10 12 13 15
        M 9 11 14 16
        DETECTOR(-0.5, 1.5, 0) rec[-12] rec[-4]
        DETECTOR(0.5, -0.5, 0) rec[-16] rec[-8]
        DETECTOR(0.5, 0.5, 0) rec[-11] rec[-3]
        DETECTOR(0.5, 1.5, 0) rec[-15] rec[-7]
        DETECTOR(1.5, 0.5, 0) rec[-14] rec[-6]
        DETECTOR(1.5, 1.5, 0) rec[-10] rec[-2]
        DETECTOR(1.5, 2.5, 0) rec[-13] rec[-5]
        DETECTOR(2.5, 0.5, 0) rec[-9] rec[-1]
        SHIFT_COORDS(0, 0, 1)
        TICK
        REPEAT 11 {
            RX 10 12 13 15
            R 9 11 14 16
            TICK
            CX 2 9 4 11 8 14 10 3 12 5 13 7
            TICK
            CX 1 11 5 14 7 16 12 4 13 6 15 8
            TICK
            CX 1 9 3 11 7 14 10 0 12 2 13 4
            TICK
            CX 0 11 4 14 6 16 12 1 13 3 15 5
            TICK
            MX 10 12 13 15
            M 9 11 14 16
            DETECTOR(-0.5, 1.5, 0) rec[-12] rec[-4]
            DETECTOR(0.5, -0.5, 0) rec[-16] rec[-8]
            DETECTOR(0.5, 0.5, 0) rec[-11] rec[-3]
            DETECTOR(0.5, 1.5, 0) rec[-15] rec[-7]
            DETECTOR(1.5, 0.5, 0) rec[-14] rec[-6]
            DETECTOR(1.5, 1.5, 0) rec[-10] rec[-2]
            DETECTOR(1.5, 2.5, 0) rec[-13] rec[-5]
            DETECTOR(2.5, 0.5, 0) rec[-9] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
            RX 10 12 13 15
            R 9 11 14 16
            TICK
            CX 0 11 4 14 6 16 12 1 13 3 15 5
            TICK
            CX 1 9 3 11 7 14 10 0 12 2 13 4
            TICK
            CX 1 11 5 14 7 16 12 4 13 6 15 8
            TICK
            CX 2 9 4 11 8 14 10 3 12 5 13 7
            TICK
            MX 10 12 13 15
            M 9 11 14 16
            DETECTOR(-0.5, 1.5, 0) rec[-12] rec[-4]
            DETECTOR(0.5, -0.5, 0) rec[-16] rec[-8]
            DETECTOR(0.5, 0.5, 0) rec[-11] rec[-3]
            DETECTOR(0.5, 1.5, 0) rec[-15] rec[-7]
            DETECTOR(1.5, 0.5, 0) rec[-14] rec[-6]
            DETECTOR(1.5, 1.5, 0) rec[-10] rec[-2]
            DETECTOR(1.5, 2.5, 0) rec[-13] rec[-5]
            DETECTOR(2.5, 0.5, 0) rec[-9] rec[-1]
            SHIFT_COORDS(0, 0, 1)
            TICK
        }
        RX 10 12 13 15
        R 9 11 14 16
        TICK
        CX 2 9 4 11 8 14 10 3 12 5 13 7
        TICK
        CX 1 11 5 14 7 16 12 4 13 6 15 8
        TICK
        CX 1 9 3 11 7 14 10 0 12 2 13 4
        TICK
        CX 0 11 4 14 6 16 12 1 13 3 15 5
        TICK
        MX 0 1 2 3 4 5 6 7 8 10 12 13 15
        M 9 11 14 16
        DETECTOR(-0.5, 1.5, 0) rec[-21] rec[-4]
        DETECTOR(0.5, -0.5, 0) rec[-25] rec[-8]
        DETECTOR(0.5, 0.5, 0) rec[-20] rec[-3]
        DETECTOR(0.5, 1.5, 0) rec[-24] rec[-7]
        DETECTOR(1.5, 0.5, 0) rec[-23] rec[-6]
        DETECTOR(1.5, 1.5, 0) rec[-19] rec[-2]
        DETECTOR(1.5, 2.5, 0) rec[-22] rec[-5]
        DETECTOR(2.5, 0.5, 0) rec[-18] rec[-1]
        DETECTOR(0.5, -0.5, 0.5) rec[-17] rec[-14] rec[-8]
        DETECTOR(0.5, 1.5, 0.5) rec[-16] rec[-15] rec[-13] rec[-12] rec[-7]
        DETECTOR(1.5, 0.5, 0.5) rec[-14] rec[-13] rec[-11] rec[-10] rec[-6]
        DETECTOR(1.5, 2.5, 0.5) rec[-12] rec[-9] rec[-5]
        SHIFT_COORDS(0, 0, 1)
        TICK
    """
    )
