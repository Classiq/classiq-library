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
from typing import Iterable

import numpy as np
import stim

from gen._flows._flow import Flow
from gen._flows._chunk import Chunk


FLIP_REV_SET = {
    "CX",
    "CY",
    "CZ",
    "XCY",
}
REV_DICT = {
    "I": "I",
    "X": "X",
    "Y": "Y",
    "Z": "Z",
    "C_XYZ": "C_ZYX",
    "C_ZYX": "C_XYZ",
    "H": "H",
    "H_XY": "H_XY",
    "H_XZ": "H_XZ",
    "H_YZ": "H_YZ",
    "S": "S",
    "SQRT_X": "SQRT_X",
    "SQRT_X_DAG": "SQRT_X",
    "SQRT_Y": "SQRT_Y",
    "SQRT_Y_DAG": "SQRT_Y",
    "S_DAG": "S",
    "CX": "XCZ",
    "CY": "YCZ",
    "CZ": "CZ",
    "ISWAP": "ISWAP",
    "ISWAP_DAG": "ISWAP",
    "SQRT_XX": "SQRT_XX",
    "SQRT_XX_DAG": "SQRT_XX",
    "SQRT_YY": "SQRT_YY",
    "SQRT_YY_DAG": "SQRT_YY",
    "SQRT_ZZ": "SQRT_ZZ",
    "SQRT_ZZ_DAG": "SQRT_ZZ",
    "SWAP": "SWAP",
    "XCX": "XCX",
    "CXSWAP": "CXSWAP",
    "SWAPCX": "SWAPCX",
    "XCY": "YCX",
    "XCZ": "CX",
    "YCX": "XCY",
    "YCY": "YCY",
    "YCZ": "CY",
    "SHIFT_COORDS": "SHIFT_COORDS",
    "TICK": "TICK",
}


class FlowStabilizerVerifier:
    def __init__(
        self, next_measurement: int, q2i: dict[complex, int], flows: Iterable[Flow]
    ):
        self.flows: tuple[Flow, ...] = tuple(flows)
        self.q2i = q2i
        self.i2m = collections.defaultdict(list)
        self.measurement_to_can_be_destructive: set[int] = set()
        self.reset_index = 0
        self.next_measurement = next_measurement
        self.reset_to_flow_indices: collections.defaultdict[int, list[int]] = (
            collections.defaultdict(list)
        )
        num_qubits = max(q2i.values()) + 1
        self.xs = np.zeros(shape=(num_qubits, len(self.flows)), dtype=np.bool_)
        self.zs = np.zeros(shape=(num_qubits, len(self.flows)), dtype=np.bool_)
        for k in range(len(self.flows)):
            flow: Flow = self.flows[k]
            for m in flow.measurement_indices:
                self.i2m[m].append(k)
            for q, p in flow.end.qubits.items():
                assert p == "X" or p == "Y" or p == "Z"
                self.xs[q2i[q], k] = p == "X" or p == "Y"
                self.zs[q2i[q], k] = p == "Z" or p == "Y"

    def fail_if(self, mask: np.ndarray, msg: str):
        if np.any(mask):
            for k in range(len(mask)):
                if mask[k]:
                    self.fail(k, msg)

    def pauli_terms(self, k: int) -> str:
        i2q = {i: q for q, i in self.q2i.items()}
        terms = []
        for q in range(self.xs.shape[0]):
            x = self.xs[q, k]
            z = self.zs[q, k]
            if x or z:
                terms.append("_XZY"[x + z * 2] + repr(i2q[q]))
        return "*".join(terms)

    def fail(self, k: int, msg: str):
        raise ValueError(
            f"{msg} for flow {self.flows[k]} with current value {self.pauli_terms(k)}"
        )

    def finish(self):
        for k in range(len(self.flows)):
            for q, p in self.flows[k].start.qubits.items():
                assert p == "X" or p == "Y" or p == "Z"
                self.xs[self.q2i[q], k] ^= p == "X" or p == "Y"
                self.zs[self.q2i[q], k] ^= p == "Z" or p == "Y"
        if np.any(self.xs) or np.any(self.zs):
            for k in range(len(self.flows)):
                if np.any(self.xs[:, k]) or np.any(self.zs[:, k]):
                    self.fail(k, "Mismatch at start")

    @staticmethod
    def verify(chunk: "Chunk") -> "FlowStabilizerVerifier":
        verifier = FlowStabilizerVerifier(
            q2i=chunk.q2i,
            flows=chunk.flows,
            next_measurement=chunk.circuit.num_measurements - 1,
        )
        for inst in chunk.circuit.flattened()[::-1]:
            verifier.rev_apply(inst)
        verifier.finish()
        return verifier

    @staticmethod
    def invert(chunk: "Chunk") -> Chunk:
        v = FlowStabilizerVerifier.verify(chunk)
        measurement_to_flow_indices: collections.defaultdict[int, list[int]] = (
            collections.defaultdict(list)
        )
        for k, flow in enumerate(chunk.flows):
            for m in flow.measurement_indices:
                measurement_to_flow_indices[m].append(k)

        header = stim.Circuit()
        rev_circuit = stim.Circuit()
        new_flow_measurements: list[list[int]] = [[] for _ in range(len(v.flows))]
        reset_index = 0
        new_measure_index = 0
        old_measure_index = chunk.circuit.num_measurements
        for inst in chunk.circuit.flattened()[::-1]:
            if inst.name in FLIP_REV_SET:
                old_targets = inst.targets_copy()
                new_targets = [
                    old_targets[k + i]
                    for k in range(0, len(old_targets), 2)[::-1]
                    for i in range(2)
                ]
                rev_circuit.append(inst.name, new_targets, inst.gate_args_copy())
            elif inst.name in REV_DICT:
                rev_circuit.append(
                    REV_DICT[inst.name],
                    inst.targets_copy()[::-1],
                    inst.gate_args_copy(),
                )
            elif inst.name in ["R", "RX", "RY"]:
                ts = inst.targets_copy()[::-1]
                rev_circuit.append(
                    inst.name.replace("R", "M"), ts, inst.gate_args_copy()
                )
                for k in range(len(ts)):
                    for f in v.reset_to_flow_indices[reset_index]:
                        new_flow_measurements[f].append(new_measure_index)
                    new_measure_index += 1
                    reset_index += 1
            elif inst.name in ["M", "MX", "MY"]:
                ts = inst.targets_copy()[::-1]
                if all(
                    old_measure_index - k - 1 in v.measurement_to_can_be_destructive
                    for k in range(len(ts))
                ):
                    rev_circuit.append(
                        inst.name.replace("M", "R"), ts, inst.gate_args_copy()
                    )
                    old_measure_index -= len(ts)
                else:
                    rev_circuit.append(inst.name, ts, inst.gate_args_copy())
                    for k in range(len(ts)):
                        for f in measurement_to_flow_indices[old_measure_index]:
                            new_flow_measurements[f].append(new_measure_index)
                        old_measure_index -= 1
                        new_measure_index += 1
            elif inst.name == "QUBIT_COORDS":
                header.append(inst)
            else:
                raise NotImplementedError(f"{inst=}")

        return Chunk(
            circuit=header + rev_circuit,
            q2i=chunk.q2i,
            flows=[
                Flow(
                    center=flow.center,
                    start=flow.end,
                    end=flow.start,
                    measurement_indices=new_flow_measurements[k],
                    additional_coords=flow.additional_coords,
                    obs_index=flow.obs_index,
                    allow_vacuous=True,
                )
                for k, flow in enumerate(chunk.flows)
            ],
            discarded_inputs=chunk.discarded_outputs,
            discarded_outputs=chunk.discarded_inputs,
        )

    def rev_apply(self, inst: stim.CircuitInstruction):
        if inst.name == "H" or inst.name == "SQRT_Y" or inst.name == "SQRT_Y_DAG":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                tmp = self.xs[q].copy()
                self.xs[q, :] = self.zs[q]
                self.zs[q, :] = tmp
        elif (
            inst.name == "I" or inst.name == "Z" or inst.name == "X" or inst.name == "Y"
        ):
            pass
        elif inst.name == "S" or inst.name == "S_DAG" or inst.name == "H_XY":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                self.zs[q, :] ^= self.xs[q]
        elif inst.name == "SQRT_X" or inst.name == "SQRT_X_DAG" or inst.name == "H_YZ":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                self.xs[q, :] ^= self.zs[q]
        elif inst.name == "C_XYZ":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                self.zs[q, :] ^= self.xs[q]
                self.xs[q, :] ^= self.zs[q]
        elif inst.name == "C_ZYX":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                self.xs[q, :] ^= self.zs[q]
                self.zs[q, :] ^= self.xs[q]
        elif inst.name == "RY":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                self.fail_if(self.xs[q] ^ self.zs[q], "Anticommuted with RY")
                for k in range(len(self.flows)):
                    if self.xs[q, k] and self.zs[q, k]:
                        self.reset_to_flow_indices[self.reset_index].append(k)
                self.reset_index += 1
                self.xs[q, :] = 0
                self.zs[q, :] = 0
        elif inst.name == "RX":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                self.fail_if(self.zs[q], "Anticommuted with RX")
                for k in range(len(self.flows)):
                    if self.xs[q, k]:
                        self.reset_to_flow_indices[self.reset_index].append(k)
                self.reset_index += 1
                self.xs[q, :] = 0
        elif inst.name == "R":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                self.fail_if(self.xs[q], "Anticommuted with R")
                for k in range(len(self.flows)):
                    if self.zs[q, k]:
                        self.reset_to_flow_indices[self.reset_index].append(k)
                self.reset_index += 1
                self.zs[q, :] = 0
        elif inst.name == "M":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                m = self.next_measurement
                self.next_measurement -= 1
                self.fail_if(self.xs[q], "Anticommuted with M")
                if not np.any(self.xs[q, :]) and not np.any(self.zs[q, :]):
                    self.measurement_to_can_be_destructive.add(m)
                for s in self.i2m[m]:
                    self.zs[q, s] ^= True
        elif inst.name == "MR":
            for gate in "RM":
                self.rev_apply(
                    stim.CircuitInstruction(
                        name=gate,
                        targets=inst.targets_copy(),
                        gate_args=inst.gate_args_copy(),
                    )
                )
        elif inst.name == "CXSWAP":
            for gate in ["SWAP", "CX"]:
                self.rev_apply(
                    stim.CircuitInstruction(
                        name=gate,
                        targets=inst.targets_copy(),
                        gate_args=inst.gate_args_copy(),
                    )
                )
        elif inst.name == "SWAPCX":
            for gate in ["CX", "SWAP"]:
                self.rev_apply(
                    stim.CircuitInstruction(
                        name=gate,
                        targets=inst.targets_copy(),
                        gate_args=inst.gate_args_copy(),
                    )
                )
        elif inst.name == "MRX":
            for gate in ["RX", "MX"]:
                self.rev_apply(
                    stim.CircuitInstruction(
                        name=gate,
                        targets=inst.targets_copy(),
                        gate_args=inst.gate_args_copy(),
                    )
                )
        elif inst.name == "MRY":
            for gate in ["RY", "MY"]:
                self.rev_apply(
                    stim.CircuitInstruction(
                        name=gate,
                        targets=inst.targets_copy(),
                        gate_args=inst.gate_args_copy(),
                    )
                )
        elif inst.name == "MY":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                m = self.next_measurement
                self.next_measurement -= 1
                self.fail_if(self.xs[q] ^ self.zs[q], "Anticommuted with M")
                if not np.any(self.xs[q, :]) and not np.any(self.zs[q, :]):
                    self.measurement_to_can_be_destructive.add(m)
                for s in self.i2m[m]:
                    self.xs[q, s] ^= True
                    self.zs[q, s] ^= True
        elif inst.name == "MX":
            for t in inst.targets_copy()[::-1]:
                assert t.is_qubit_target
                q = t.value
                m = self.next_measurement
                self.next_measurement -= 1
                self.fail_if(self.zs[q], "Anticommuted with MX")
                if not np.any(self.xs[q, :]) and not np.any(self.zs[q, :]):
                    self.measurement_to_can_be_destructive.add(m)
                for s in self.i2m[m]:
                    self.xs[q, s] ^= True
        elif inst.name == "XCZ":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                self.xs[q1] ^= self.xs[q2]
                self.zs[q2] ^= self.zs[q1]
        elif inst.name == "CX":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t2.is_qubit_target
                q2 = t2.value
                if t1.is_measurement_record_target:
                    m = self.next_measurement + t1.value + 1
                    for s in np.flatnonzero(self.zs[q2, :]):
                        self.i2m[m].append(s)
                else:
                    assert t1.is_qubit_target
                    q1 = t1.value
                    self.xs[q2] ^= self.xs[q1]
                    self.zs[q1] ^= self.zs[q2]
        elif inst.name == "CZ":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t2.is_qubit_target
                q2 = t2.value
                if t1.is_measurement_record_target:
                    m = self.next_measurement + t1.value + 1
                    for s in np.flatnonzero(self.xs[q2, :]):
                        self.i2m[m].append(s)
                else:
                    assert t1.is_qubit_target
                    q1 = t1.value
                    self.zs[q2] ^= self.xs[q1]
                    self.zs[q1] ^= self.xs[q2]
        elif inst.name == "CY" or inst.name == "YCZ":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                if inst.name == "YCZ":
                    t1, t2 = t2, t1
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                yt = self.xs[q2] ^ self.zs[q2]
                self.zs[q1] ^= yt
                self.zs[q2] ^= self.xs[q1]
                self.xs[q2] ^= self.xs[q1]
        elif inst.name == "ISWAP" or inst.name == "ISWAP_DAG":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                # swap
                for bs in [self.xs, self.zs]:
                    bs[q1] ^= bs[q2]
                    bs[q2] ^= bs[q1]
                    bs[q1] ^= bs[q2]
                # cz
                self.zs[q2] ^= self.xs[q1]
                self.zs[q1] ^= self.xs[q2]
                # s s
                self.zs[q1, :] ^= self.xs[q1]
                self.zs[q2, :] ^= self.xs[q2]
        elif inst.name == "SQRT_ZZ" or inst.name == "SQRT_ZZ_DAG":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                # cz
                self.zs[q2] ^= self.xs[q1]
                self.zs[q1] ^= self.xs[q2]
                # s s
                self.zs[q1, :] ^= self.xs[q1]
                self.zs[q2, :] ^= self.xs[q2]
        elif inst.name == "XCX":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                self.xs[q2] ^= self.zs[q1]
                self.xs[q1] ^= self.zs[q2]
        elif inst.name == "YCY":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                # s s
                self.zs[q1, :] ^= self.xs[q1]
                self.zs[q2, :] ^= self.xs[q2]
                # xcx
                self.xs[q2] ^= self.zs[q1]
                self.xs[q1] ^= self.zs[q2]
                # s s
                self.zs[q1, :] ^= self.xs[q1]
                self.zs[q2, :] ^= self.xs[q2]
        elif inst.name == "SQRT_YY" or inst.name == "SQRT_YY_DAG":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                # s s
                self.zs[q1, :] ^= self.xs[q1]
                self.zs[q2, :] ^= self.xs[q2]
                # xcx
                self.xs[q2] ^= self.zs[q1]
                self.xs[q1] ^= self.zs[q2]
                # sqrt_x sqrt_x
                self.xs[q1, :] ^= self.zs[q1]
                self.xs[q2, :] ^= self.zs[q2]
                # s s
                self.zs[q1, :] ^= self.xs[q1]
                self.zs[q2, :] ^= self.xs[q2]
        elif inst.name == "SQRT_XX" or inst.name == "SQRT_XX_DAG":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                # xcx
                self.xs[q2] ^= self.zs[q1]
                self.xs[q1] ^= self.zs[q2]
                # sqrt_x sqrt_x
                self.xs[q1, :] ^= self.zs[q1]
                self.xs[q2, :] ^= self.zs[q2]
        elif inst.name == "SWAP":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                for bs in [self.xs, self.zs]:
                    bs[q1] ^= bs[q2]
                    bs[q2] ^= bs[q1]
                    bs[q1] ^= bs[q2]
        elif inst.name == "XCY" or inst.name == "YCX":
            ts = inst.targets_copy()
            for k in range(0, len(ts), 2)[::-1]:
                t1 = ts[k]
                t2 = ts[k + 1]
                if inst.name == "YCX":
                    t1, t2 = t2, t1
                assert t1.is_qubit_target
                assert t2.is_qubit_target
                q1 = t1.value
                q2 = t2.value
                yt = self.xs[q2] ^ self.zs[q2]
                self.xs[q1] ^= yt
                self.zs[q2] ^= self.zs[q1]
                self.xs[q2] ^= self.zs[q1]
        elif inst.name == "MPP":
            targets = inst.targets_copy()[::-1]
            start = 0
            while start < len(targets):
                end = start + 1
                while end < len(targets) and targets[end].is_combiner:
                    end += 2

                x_mask = np.zeros(shape=self.xs.shape[0], dtype=np.bool_)
                z_mask = np.zeros(shape=self.xs.shape[0], dtype=np.bool_)
                for t in targets[start:end:2]:
                    if t.is_x_target:
                        x_mask[t.value] ^= True
                    elif t.is_y_target:
                        x_mask[t.value] ^= True
                        z_mask[t.value] ^= True
                    elif t.is_z_target:
                        z_mask[t.value] ^= True
                    else:
                        raise NotImplementedError(f"{inst=}")

                for k in range(self.xs.shape[1]):
                    x_combos = np.sum(np.bitwise_and(self.xs[:, k], z_mask), axis=0)
                    z_combos = np.sum(np.bitwise_and(self.zs[:, k], x_mask), axis=0)
                    if np.any((x_combos + z_combos) & 1):
                        raise ValueError("Anticommuted with MPP")
                m = self.next_measurement
                self.next_measurement -= 1
                for s in self.i2m[m]:
                    self.zs[:, s] ^= z_mask
                    self.xs[:, s] ^= x_mask

                start = end

        elif inst.name == "TICK":
            pass
        elif inst.name == "QUBIT_COORDS":
            pass
        else:
            raise NotImplementedError(f"{inst=}")
