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
from gen._circuit_util import (
    gates_used_by_circuit,
    gate_counts_for_circuit,
    count_measurement_layers,
)


def test_gates_used_by_circuit():
    assert (
        gates_used_by_circuit(
            stim.Circuit(
                """
        H 0
        TICK
        CX 0 1
    """
            )
        )
        == {"H", "TICK", "CX"}
    )

    assert (
        gates_used_by_circuit(
            stim.Circuit(
                """
        S 0
        XCZ 0 1
    """
            )
        )
        == {"S", "XCZ"}
    )

    assert (
        gates_used_by_circuit(
            stim.Circuit(
                """
        MPP X0*X1 Z2*Z3*Z4 Y0*Z1
    """
            )
        )
        == {"MXX", "MZZZ", "MYZ"}
    )

    assert (
        gates_used_by_circuit(
            stim.Circuit(
                """
        CX rec[-1] 1
    """
            )
        )
        == {"feedback"}
    )

    assert (
        gates_used_by_circuit(
            stim.Circuit(
                """
        CX sweep[1] 1
    """
            )
        )
        == {"sweep"}
    )

    assert (
        gates_used_by_circuit(
            stim.Circuit(
                """
        CX rec[-1] 1 0 1
    """
            )
        )
        == {"feedback", "CX"}
    )


def test_gate_counts_for_circuit():
    assert (
        gate_counts_for_circuit(
            stim.Circuit(
                """
        H 0
        TICK
        CX 0 1
    """
            )
        )
        == {"H": 1, "TICK": 1, "CX": 1}
    )

    assert (
        gate_counts_for_circuit(
            stim.Circuit(
                """
        S 0
        XCZ 0 1
    """
            )
        )
        == {"S": 1, "XCZ": 1}
    )

    assert (
        gate_counts_for_circuit(
            stim.Circuit(
                """
        MPP X0*X1 Z2*Z3*Z4 Y0*Z1
    """
            )
        )
        == {"MXX": 1, "MZZZ": 1, "MYZ": 1}
    )

    assert (
        gate_counts_for_circuit(
            stim.Circuit(
                """
        CX rec[-1] 1
    """
            )
        )
        == {"feedback": 1}
    )

    assert (
        gate_counts_for_circuit(
            stim.Circuit(
                """
        CX sweep[1] 1
    """
            )
        )
        == {"sweep": 1}
    )

    assert (
        gate_counts_for_circuit(
            stim.Circuit(
                """
        CX rec[-1] 1 0 1
    """
            )
        )
        == {"feedback": 1, "CX": 1}
    )

    assert (
        gate_counts_for_circuit(
            stim.Circuit(
                """
        H 0 1
        REPEAT 100 {
            S 0 1 2
            CX 0 1 2 3
        }
    """
            )
        )
        == {"H": 2, "S": 300, "CX": 200}
    )


def test_count_measurement_layers():
    assert count_measurement_layers(stim.Circuit()) == 0
    assert (
        count_measurement_layers(
            stim.Circuit(
                """
        M 0 1 2
    """
            )
        )
        == 1
    )
    assert (
        count_measurement_layers(
            stim.Circuit(
                """
        M 0 1
        MX 2
        MR 3
    """
            )
        )
        == 1
    )
    assert (
        count_measurement_layers(
            stim.Circuit(
                """
        M 0 1
        MX 2
        TICK
        MR 3
    """
            )
        )
        == 2
    )
    assert (
        count_measurement_layers(
            stim.Circuit(
                """
        R 0
        CX 0 1
        TICK
        M 0
    """
            )
        )
        == 1
    )
    assert (
        count_measurement_layers(
            stim.Circuit(
                """
        R 0
        CX 0 1
        TICK
        M 0
        DETECTOR rec[-1]
        M 1
        DETECTOR rec[-1]
        OBSERVABLE_INCLUDE(0) rec[-1]
        MPP X0*X1
        DETECTOR rec[-1]
    """
            )
        )
        == 1
    )
    assert (
        count_measurement_layers(
            stim.Circuit.generated(
                "repetition_code:memory",
                distance=3,
                rounds=4,
            )
        )
        == 4
    )
    assert (
        count_measurement_layers(
            stim.Circuit.generated(
                "surface_code:rotated_memory_x",
                distance=3,
                rounds=1000,
            )
        )
        == 1000
    )
