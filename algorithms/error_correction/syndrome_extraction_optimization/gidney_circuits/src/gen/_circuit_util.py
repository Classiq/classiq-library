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

import collections
from typing import Counter

import stim

from gen._core._noise import ANNOTATION_OPS


def count_measurement_layers(circuit: stim.Circuit) -> int:
    saw_measurement = False
    result = 0
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            result += (
                count_measurement_layers(instruction.body_copy())
                * instruction.repeat_count
            )
        elif isinstance(instruction, stim.CircuitInstruction):
            saw_measurement |= stim.gate_data(instruction.name).produces_measurements
            if instruction.name == "TICK":
                result += saw_measurement
                saw_measurement = False
        else:
            raise NotImplementedError(f"{instruction=}")
    result += saw_measurement
    return result


def gate_counts_for_circuit(circuit: stim.Circuit) -> Counter[str]:
    """Determines gates used by a circuit, disambiguating MPP/feedback cases.

    MPP instructions are expanded into what they actually measure, such as
    "MXX" for MPP X1*X2 and "MXYZ" for MPP X4*Y5*Z7.

    Feedback instructions like `CX rec[-1] 0` become the gate "feedback".

    Sweep instructions like `CX sweep[2] 0` become the gate "sweep".
    """
    out = collections.Counter()
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            for k, v in gate_counts_for_circuit(instruction.body_copy()).items():
                out[k] += v * instruction.repeat_count

        elif instruction.name in ["CX", "CY", "CZ", "XCZ", "YCZ"]:
            targets = instruction.targets_copy()
            for k in range(0, len(targets), 2):
                if (
                    targets[k].is_measurement_record_target
                    or targets[k + 1].is_measurement_record_target
                ):
                    out["feedback"] += 1
                elif (
                    targets[k].is_sweep_bit_target or targets[k + 1].is_sweep_bit_target
                ):
                    out["sweep"] += 1
                else:
                    out[instruction.name] += 1

        elif instruction.name == "MPP":
            op = "M"
            targets = instruction.targets_copy()
            is_continuing = True
            for t in targets:
                if t.is_combiner:
                    is_continuing = True
                    continue
                p = (
                    "X"
                    if t.is_x_target
                    else "Y"
                    if t.is_y_target
                    else "Z"
                    if t.is_z_target
                    else "?"
                )
                if is_continuing:
                    op += p
                    is_continuing = False
                else:
                    if op == "MZ":
                        op = "M"
                    out[op] += 1
                    op = "M" + p
            if op:
                if op == "MZ":
                    op = "M"
                out[op] += 1

        elif stim.gate_data(instruction.name).is_two_qubit_gate:
            out[instruction.name] += len(instruction.targets_copy()) // 2
        elif (
            instruction.name in ANNOTATION_OPS
            or instruction.name == "E"
            or instruction.name == "ELSE_CORRELATED_ERROR"
        ):
            out[instruction.name] += 1
        else:
            out[instruction.name] += len(instruction.targets_copy())

    return out


def gates_used_by_circuit(circuit: stim.Circuit) -> set[str]:
    """Determines gates used by a circuit, disambiguating MPP/feedback cases.

    MPP instructions are expanded into what they actually measure, such as
    "MXX" for MPP X1*X2 and "MXYZ" for MPP X4*Y5*Z7.

    Feedback instructions like `CX rec[-1] 0` become the gate "feedback".

    Sweep instructions like `CX sweep[2] 0` become the gate "sweep".
    """
    out = set()
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            out |= gates_used_by_circuit(instruction.body_copy())

        elif instruction.name in ["CX", "CY", "CZ", "XCZ", "YCZ"]:
            targets = instruction.targets_copy()
            for k in range(0, len(targets), 2):
                if (
                    targets[k].is_measurement_record_target
                    or targets[k + 1].is_measurement_record_target
                ):
                    out.add("feedback")
                elif (
                    targets[k].is_sweep_bit_target or targets[k + 1].is_sweep_bit_target
                ):
                    out.add("sweep")
                else:
                    out.add(instruction.name)

        elif instruction.name == "MPP":
            op = "M"
            targets = instruction.targets_copy()
            is_continuing = True
            for t in targets:
                if t.is_combiner:
                    is_continuing = True
                    continue
                p = (
                    "X"
                    if t.is_x_target
                    else "Y"
                    if t.is_y_target
                    else "Z"
                    if t.is_z_target
                    else "?"
                )
                if is_continuing:
                    op += p
                    is_continuing = False
                else:
                    if op == "MZ":
                        op = "M"
                    out.add(op)
                    op = "M" + p
            if op:
                if op == "MZ":
                    op = "M"
                out.add(op)

        else:
            out.add(instruction.name)

    return out
