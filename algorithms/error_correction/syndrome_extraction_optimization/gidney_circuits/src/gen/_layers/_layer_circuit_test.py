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

from gen._layers._layer_circuit import LayerCircuit


def test_with_squashed_rotations():
    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        S 0 1 2 3
        TICK
        CZ 1 2
        TICK
        H 0 3
        TICK
        CZ 1 2
        TICK
        S 0 1 2 3
    """
            )
        )
        .with_clearable_rotation_layers_cleared()
        .to_stim_circuit()
        == stim.Circuit(
            """
        C_XYZ 0 3
        S 1 2
        TICK
        CZ 1 2
        TICK
        CZ 1 2
        TICK
        S 0 1 2 3
    """
        )
    )

    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        S 0 1 2 3
        TICK
        CZ 0 2
        TICK
        H 0 3
        TICK
        CZ 1 2
        TICK
        S 0 1 2 3
    """
            )
        )
        .with_clearable_rotation_layers_cleared()
        .to_stim_circuit()
        == stim.Circuit(
            """
        C_XYZ 3
        S 0 1 2
        TICK
        CZ 0 2
        TICK
        CZ 1 2
        TICK
        C_ZYX 0
        S 1 2 3
    """
        )
    )


def test_with_rotations_before_resets_removed():
    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        H 0 1 2 3
        TICK
        R 0 1
    """
            )
        )
        .with_rotations_before_resets_removed()
        .to_stim_circuit()
        == stim.Circuit(
            """
        H 2 3
        TICK
        R 0 1
    """
        )
    )

    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        H 0 1 2 3
        TICK
        REPEAT 100 {
            R 0 1
            TICK
            H 0 1 2 3
            TICK
        }
        R 1 2
        TICK
    """
            )
        )
        .with_rotations_before_resets_removed()
        .to_stim_circuit()
        == stim.Circuit(
            """
        H 2 3
        TICK
        REPEAT 100 {
            R 0 1
            TICK
            H 0 2 3
            TICK
        }
        R 1 2
    """
        )
    )


def test_with_rotations_merged_earlier():
    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        S 0 1 2 3
        TICK
        CZ 1 2 3 4
        TICK
        H 0 1 2 3
        TICK
        CZ 1 2
        TICK
        S 0 1 2 3
    """
            )
        )
        .with_rotations_merged_earlier()
        .to_stim_circuit()
        == stim.Circuit(
            """
        S 1 2 3
        SQRT_X 0
        TICK
        CZ 1 2 3 4
        TICK
        C_ZYX 3
        H 1 2
        TICK
        CZ 1 2
        TICK
        S 1 2
    """
        )
    )


def test_with_qubit_coords_at_start():
    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        QUBIT_COORDS(2, 3) 0
        SHIFT_COORDS(0, 0, 100)
        QUBIT_COORDS(5, 7) 1
        SHIFT_COORDS(0, 200)
        QUBIT_COORDS(11, 13) 2
        SHIFT_COORDS(300)
        R 0 1
        TICK
        QUBIT_COORDS(17) 3
        H 3
        TICK
        QUBIT_COORDS(19, 23, 29) 4
        REPEAT 10 {
            M 0 1 2 3
            DETECTOR rec[-1]
        }
    """
            )
        )
        .with_qubit_coords_at_start()
        .to_stim_circuit()
        == stim.Circuit(
            """
        QUBIT_COORDS(2, 3) 0
        QUBIT_COORDS(5, 7) 1
        QUBIT_COORDS(11, 213) 2
        QUBIT_COORDS(317) 3
        QUBIT_COORDS(319, 223, 129) 4
        SHIFT_COORDS(0, 0, 100)
        SHIFT_COORDS(0, 200)
        SHIFT_COORDS(300)
        R 0 1
        TICK
        H 3
        TICK
        REPEAT 10 {
            M 0 1 2 3
            DETECTOR rec[-1]
            TICK
        }
    """
        )
    )


def test_merge_shift_coords():
    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        SHIFT_COORDS(300)
        SHIFT_COORDS(0, 0, 100)
        SHIFT_COORDS(0, 200)
    """
            )
        )
        .with_locally_optimized_layers()
        .to_stim_circuit()
        == stim.Circuit(
            """
        SHIFT_COORDS(300, 200, 100)
    """
        )
    )

    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        SHIFT_COORDS(300)
        TICK
        SHIFT_COORDS(0, 0, 100)
        TICK
        SHIFT_COORDS(0, 200)
        TICK
    """
            )
        )
        .with_locally_optimized_layers()
        .to_stim_circuit()
        == stim.Circuit(
            """
        SHIFT_COORDS(300, 200, 100)
    """
        )
    )


def test_merge_resets_and_measurements():
    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        RX 0 1
        TICK
        RY 2 3
    """
            )
        )
        .with_locally_optimized_layers()
        .to_stim_circuit()
        == stim.Circuit(
            """
        RX 0 1
        RY 2 3
    """
        )
    )

    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        RX 0 1
        TICK
        RY 1 2 3
    """
            )
        )
        .with_locally_optimized_layers()
        .to_stim_circuit()
        == stim.Circuit(
            """
        RX 0
        RY 1 2 3
    """
        )
    )

    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        MX 0 1
        TICK
        MY 2 3
    """
            )
        )
        .with_locally_optimized_layers()
        .to_stim_circuit()
        == stim.Circuit(
            """
        MX 0 1
        MY 2 3
    """
        )
    )

    assert (
        LayerCircuit.from_stim_circuit(
            stim.Circuit(
                """
        MX 0 1
        TICK
        MY 1 2 3
    """
            )
        )
        .with_locally_optimized_layers()
        .to_stim_circuit()
        == stim.Circuit(
            """
        MX 0 1
        TICK
        MY 1 2 3
    """
        )
    )
