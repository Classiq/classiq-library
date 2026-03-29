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

from typing import Iterator, AbstractSet, Any

import collections

import stim


ANNOTATION_OPS = {
    "DETECTOR",
    "OBSERVABLE_INCLUDE",
    "QUBIT_COORDS",
    "SHIFT_COORDS",
    "TICK",
}
OP_TO_MEASURE_BASES = {
    "M": "Z",
    "MX": "X",
    "MY": "Y",
    "MZ": "Z",
    "MXX": "XX",
    "MYY": "YY",
    "MZZ": "ZZ",
    "MPP": "*",
}


class NoiseRule:
    """Describes how to add noise to an operation."""

    def __init__(
        self,
        *,
        after: dict[str, float],
        flip_result: float = 0,
    ):
        """
        Args:
            after: A dictionary mapping noise rule names to their probability argument.
                For example, {"DEPOLARIZE2": 0.01, "X_ERROR": 0.02} will add two qubit
                depolarization with parameter 0.01 and also add 2% bit flip noise. These
                noise channels occur after all other operations in the moment and are applied
                to the same targets as the relevant operation.
            flip_result: The probability that a measurement result should be reported incorrectly.
                Only valid when applied to operations that produce measurement results.
        """
        if not (0 <= flip_result <= 1):
            raise ValueError(f"not (0 <= {flip_result=} <= 1)")
        for k, p in after.items():
            gate_data = stim.gate_data(k)
            if gate_data.produces_measurements or not gate_data.is_noisy_gate:
                raise ValueError(f"not a pure noise channel: {k} from {after=}")
            if not (0 <= p <= 1):
                raise ValueError(f"not (0 <= {p} <= 1) from {after=}")
        self.after = after
        self.flip_result = flip_result

    def append_noisy_version_of(
        self,
        *,
        split_op: stim.CircuitInstruction,
        out_during_moment: stim.Circuit,
        after_moments: collections.defaultdict[Any, stim.Circuit],
        immune_qubit_indices: AbstractSet[int],
    ) -> None:
        targets = split_op.targets_copy()
        if immune_qubit_indices and any(
            (t.is_qubit_target or t.is_x_target or t.is_y_target or t.is_z_target)
            and t.value in immune_qubit_indices
            for t in targets
        ):
            out_during_moment.append(split_op)
            return

        args = split_op.gate_args_copy()
        if self.flip_result:
            gate_data = stim.gate_data(split_op.name)
            assert gate_data.produces_measurements
            assert gate_data.is_noisy_gate
            assert gate_data.num_parens_arguments_range == range(0, 2)
            assert len(args) == 0
            args = [self.flip_result]

        out_during_moment.append(split_op.name, targets, args)
        raw_targets = [t.value for t in targets if not t.is_combiner]
        for op_name, arg in self.after.items():
            after_moments[(op_name, arg)].append(op_name, raw_targets, arg)


class NoiseModel:
    def __init__(
        self,
        idle_noise: float | NoiseRule | None = None,
        tick_noise: NoiseRule | None = None,
        additional_depolarization_waiting_for_m_or_r: float = 0,
        gate_rules: dict[str, NoiseRule] | None = None,
        measure_rules: dict[str, NoiseRule] | None = None,
        any_measurement_rule: NoiseRule | None = None,
        any_clifford_1q_rule: NoiseRule | None = None,
        any_clifford_2q_rule: NoiseRule | None = None,
        allow_multiple_uses_of_a_qubit_in_one_tick: bool = False,
    ):
        if isinstance(idle_noise, float):
            if idle_noise == 0:
                idle_noise = None
            else:
                idle_noise = NoiseRule(after={"DEPOLARIZE1": idle_noise})
        self.idle_noise: NoiseRule | None = idle_noise
        self.tick_noise = tick_noise
        self.additional_depolarization_waiting_for_m_or_r = (
            additional_depolarization_waiting_for_m_or_r
        )
        self.gate_rules = {} if gate_rules is None else gate_rules
        self.measure_rules = measure_rules
        self.any_measurement_rule = any_measurement_rule
        self.any_clifford_1q_rule = any_clifford_1q_rule
        self.any_clifford_2q_rule = any_clifford_2q_rule
        self.allow_multiple_uses_of_a_qubit_in_one_tick = (
            allow_multiple_uses_of_a_qubit_in_one_tick
        )
        assert self.tick_noise is None or not self.tick_noise.flip_result

    @staticmethod
    def si1000(p: float) -> "NoiseModel":
        """Superconducting inspired noise.

        As defined in "A Fault-Tolerant Honeycomb Memory" https://arxiv.org/abs/2108.10457

        Small tweak when measurements aren't immediately followed by a reset: the measurement result
        is probabilistically flipped instead of the input qubit. The input qubit is depolarized after
        the measurement.
        """
        return NoiseModel(
            idle_noise=p / 10,
            additional_depolarization_waiting_for_m_or_r=2 * p,
            any_clifford_1q_rule=NoiseRule(after={"DEPOLARIZE1": p / 10}),
            any_clifford_2q_rule=NoiseRule(after={"DEPOLARIZE2": p}),
            measure_rules={
                "Z": NoiseRule(after={"DEPOLARIZE1": p}, flip_result=p * 5),
                "ZZ": NoiseRule(after={"DEPOLARIZE2": p}, flip_result=p * 5),
            },
            gate_rules={
                "R": NoiseRule(after={"X_ERROR": p * 2}),
            },
        )

    @staticmethod
    def uniform_depolarizing(p: float) -> "NoiseModel":
        """Near-standard circuit depolarizing noise.

        Everything has the same parameter p.
        Single qubit clifford gates get single qubit depolarization.
        Two qubit clifford gates get single qubit depolarization.
        Dissipative gates have their result probabilistically bit flipped (or phase flipped if appropriate).

        Non-demolition measurement is treated a bit unusually in that it is the result that is flipped instead of
        the input qubit. The input qubit is depolarized.
        """
        return NoiseModel(
            idle_noise=p,
            any_clifford_1q_rule=NoiseRule(after={"DEPOLARIZE1": p}),
            any_clifford_2q_rule=NoiseRule(after={"DEPOLARIZE2": p}),
            measure_rules={
                "X": NoiseRule(after={"DEPOLARIZE1": p}, flip_result=p),
                "Y": NoiseRule(after={"DEPOLARIZE1": p}, flip_result=p),
                "Z": NoiseRule(after={"DEPOLARIZE1": p}, flip_result=p),
                "XX": NoiseRule(after={"DEPOLARIZE2": p}, flip_result=p),
                "YY": NoiseRule(after={"DEPOLARIZE2": p}, flip_result=p),
                "ZZ": NoiseRule(after={"DEPOLARIZE2": p}, flip_result=p),
            },
            gate_rules={
                "RX": NoiseRule(after={"Z_ERROR": p}),
                "RY": NoiseRule(after={"X_ERROR": p}),
                "R": NoiseRule(after={"X_ERROR": p}),
            },
        )

    def _noise_rule_for_split_operation(
        self,
        *,
        split_op: stim.CircuitInstruction,
    ) -> NoiseRule | None:
        if occurs_in_classical_control_system(split_op):
            return None

        rule = self.gate_rules.get(split_op.name)
        if rule is not None:
            return rule

        gate_data = stim.gate_data(split_op.name)

        if (
            self.any_clifford_1q_rule is not None
            and gate_data.is_unitary
            and gate_data.is_single_qubit_gate
        ):
            return self.any_clifford_1q_rule
        if (
            self.any_clifford_2q_rule is not None
            and gate_data.is_unitary
            and gate_data.is_two_qubit_gate
        ):
            return self.any_clifford_2q_rule
        if self.measure_rules is not None:
            rule = self.measure_rules.get(_measure_basis(split_op=split_op))
            if rule is not None:
                return rule
        if self.any_measurement_rule is not None and gate_data.produces_measurements:
            return self.any_measurement_rule
        if gate_data.is_reset and gate_data.produces_measurements:
            m_name, r_name = {
                "MRX": ("MX", "RX"),
                "MRY": ("MY", "RY"),
                "MR": ("M", "R"),
            }[gate_data.name]
            r_noise = self._noise_rule_for_split_operation(
                split_op=stim.CircuitInstruction(r_name, split_op.targets_copy())
            )
            m_noise = self._noise_rule_for_split_operation(
                split_op=stim.CircuitInstruction(m_name, split_op.targets_copy())
            )
            return NoiseRule(
                after=r_noise.after if r_noise is not None else {},
                flip_result=m_noise.flip_result if m_noise is not None else 0,
            )

        raise ValueError(f"No noise (or lack of noise) specified for {split_op=}.")

    def _append_idle_error(
        self,
        *,
        moment_split_ops: list[stim.CircuitInstruction],
        out: stim.Circuit,
        system_qubit_indices: AbstractSet[int],
        immune_qubit_indices: AbstractSet[int],
    ) -> None:
        collapse_qubits = []
        clifford_qubits = []
        for split_op in moment_split_ops:
            if occurs_in_classical_control_system(split_op):
                continue
            gate_data = stim.gate_data(split_op.name)
            if gate_data.is_reset or gate_data.produces_measurements:
                qubits_out = collapse_qubits
            else:
                qubits_out = clifford_qubits
            for target in split_op.targets_copy():
                if not target.is_combiner:
                    qubits_out.append(target.value)

        # Safety check for operation collisions.
        usage_counts = collections.Counter(collapse_qubits + clifford_qubits)
        qubits_used_multiple_times = {q for q, c in usage_counts.items() if c != 1}
        if (
            qubits_used_multiple_times
            and not self.allow_multiple_uses_of_a_qubit_in_one_tick
        ):
            moment = stim.Circuit()
            for op in moment_split_ops:
                moment.append(op)
            raise ValueError(
                f"Qubits were operated on multiple times without a TICK in between:\n"
                f"multiple uses: {sorted(qubits_used_multiple_times)}\n"
                f"moment:\n"
                f"{moment}"
            )

        collapse_qubits_set = set(collapse_qubits)
        clifford_qubits_set = set(clifford_qubits)
        idle = sorted(
            system_qubit_indices
            - collapse_qubits_set
            - clifford_qubits_set
            - immune_qubit_indices
        )
        if idle and self.idle_noise is not None:
            for k, v in self.idle_noise.after.items():
                out.append(k, idle, v)

        waiting_for_mr = sorted(
            system_qubit_indices - collapse_qubits_set - immune_qubit_indices
        )
        if (
            collapse_qubits_set
            and waiting_for_mr
            and self.additional_depolarization_waiting_for_m_or_r
        ):
            out.append(
                "DEPOLARIZE1", idle, self.additional_depolarization_waiting_for_m_or_r
            )

        if self.tick_noise is not None:
            for k, p in self.tick_noise.after.items():
                out.append(k, system_qubit_indices - immune_qubit_indices, p)

    def _append_noisy_moment(
        self,
        *,
        moment_split_ops: list[stim.CircuitInstruction],
        out: stim.Circuit,
        system_qubits_indices: AbstractSet[int],
        immune_qubit_indices: AbstractSet[int],
    ) -> None:
        after = collections.defaultdict(stim.Circuit)
        for split_op in moment_split_ops:
            rule = self._noise_rule_for_split_operation(split_op=split_op)
            if rule is None:
                out.append(split_op)
            else:
                rule.append_noisy_version_of(
                    split_op=split_op,
                    out_during_moment=out,
                    after_moments=after,
                    immune_qubit_indices=immune_qubit_indices,
                )
        for k in sorted(after.keys()):
            out += after[k]

        self._append_idle_error(
            moment_split_ops=moment_split_ops,
            out=out,
            system_qubit_indices=system_qubits_indices,
            immune_qubit_indices=immune_qubit_indices,
        )

    def noisy_circuit(
        self,
        circuit: stim.Circuit,
        *,
        system_qubit_indices: AbstractSet[int] | None = None,
        immune_qubit_indices: AbstractSet[int] | None = None,
    ) -> stim.Circuit:
        """Returns a noisy version of the given circuit, by applying the receiving noise model.

        Args:
            circuit: The circuit to layer noise over.
            system_qubit_indices: All qubits used by the circuit. These are the qubits eligible for idling noise.
            immune_qubit_indices: Qubits to not apply noise to, even if they are operated on.

        Returns:
            The noisy version of the circuit.
        """
        if system_qubit_indices is None:
            system_qubit_indices = set(range(circuit.num_qubits))
        if immune_qubit_indices is None:
            immune_qubit_indices = set()

        result = stim.Circuit()

        first = True
        for moment_split_ops in _iter_split_op_moments(
            circuit, immune_qubit_indices=immune_qubit_indices
        ):
            if first:
                first = False
            elif result and isinstance(result[-1], stim.CircuitRepeatBlock):
                pass
            else:
                result.append("TICK")
            if isinstance(moment_split_ops, stim.CircuitRepeatBlock):
                noisy_body = self.noisy_circuit(
                    moment_split_ops.body_copy(),
                    system_qubit_indices=system_qubit_indices,
                    immune_qubit_indices=immune_qubit_indices,
                )
                noisy_body.append("TICK")
                result.append(
                    stim.CircuitRepeatBlock(
                        repeat_count=moment_split_ops.repeat_count, body=noisy_body
                    )
                )
            else:
                self._append_noisy_moment(
                    moment_split_ops=moment_split_ops,
                    out=result,
                    system_qubits_indices=system_qubit_indices,
                    immune_qubit_indices=immune_qubit_indices,
                )

        return result


def occurs_in_classical_control_system(op: stim.CircuitInstruction) -> bool:
    """Determines if an operation is an annotation or a classical control system update."""
    if op.name in ANNOTATION_OPS:
        return True

    gate_data = stim.gate_data(op.name)
    if gate_data.is_unitary and gate_data.is_two_qubit_gate:
        targets = op.targets_copy()
        for k in range(0, len(targets), 2):
            a = targets[k]
            b = targets[k + 1]
            classical_0 = a.is_measurement_record_target or a.is_sweep_bit_target
            classical_1 = b.is_measurement_record_target or b.is_sweep_bit_target
            if not (classical_0 or classical_1):
                return False
        return True
    return False


def _split_targets_if_needed(
    op: stim.CircuitInstruction,
    immune_qubit_indices: AbstractSet[int],
) -> list[stim.CircuitInstruction]:
    """Splits operations into pieces as needed (e.g. MPP into each product, classical control away from quantum ops)."""
    gate_data = stim.gate_data(op.name)
    if gate_data.is_unitary and gate_data.is_two_qubit_gate:
        yield from _split_targets_if_needed_clifford_2q(op, immune_qubit_indices)
    elif op.name == "MPP":
        yield from _split_targets_if_needed_m_basis(op)
    elif op.name in ANNOTATION_OPS:
        yield op
    elif gate_data.is_noisy_gate and not gate_data.produces_measurements:
        yield op
    elif gate_data.is_single_qubit_gate:
        yield from _split_out_immune_targets_assuming_single_qubit_gate(
            op, immune_qubit_indices
        )
    else:
        raise NotImplementedError(f"{op=}")


def _split_out_immune_targets_assuming_single_qubit_gate(
    op: stim.CircuitInstruction,
    immune_qubit_indices: AbstractSet[int],
) -> list[stim.CircuitInstruction]:
    if immune_qubit_indices:
        args = op.gate_args_copy()
        for t in op.targets_copy():
            yield stim.CircuitInstruction(op.name, [t], args)
    else:
        yield op


def _split_targets_if_needed_clifford_2q(
    op: stim.CircuitInstruction,
    immune_qubit_indices: AbstractSet[int],
) -> list[stim.CircuitInstruction]:
    """Splits classical control system operations away from things actually happening on the quantum computer."""
    gate_data = stim.gate_data(op.name)
    assert gate_data.is_unitary and gate_data.is_two_qubit_gate
    targets = op.targets_copy()
    if immune_qubit_indices or any(t.is_measurement_record_target for t in targets):
        args = op.gate_args_copy()
        for k in range(0, len(targets), 2):
            yield stim.CircuitInstruction(op.name, targets[k : k + 2], args)
    else:
        yield op


def _split_targets_if_needed_m_basis(
    op: stim.CircuitInstruction,
) -> list[stim.CircuitInstruction]:
    """Splits an MPP operation into one operation for each Pauli product it measures."""
    targets = op.targets_copy()
    args = op.gate_args_copy()
    k = 0
    start = k
    while k < len(targets):
        if k + 1 == len(targets) or not targets[k + 1].is_combiner:
            yield stim.CircuitInstruction(op.name, targets[start : k + 1], args)
            k += 1
            start = k
        else:
            k += 2
    assert k == len(targets)


def _iter_split_op_moments(
    circuit: stim.Circuit,
    *,
    immune_qubit_indices: AbstractSet[int],
) -> Iterator[stim.CircuitRepeatBlock | list[stim.CircuitInstruction]]:
    """Splits a circuit into moments and some operations into pieces.

    Classical control system operations like CX rec[-1] 0 are split from quantum operations like CX 1 0.

    MPP operations are split into one operation per Pauli product.

    Yields:
        Lists of operations corresponding to one moment in the circuit, with any problematic operations
        like MPPs split into pieces.

        (A moment is the time between two TICKs.)
    """
    cur_moment = []

    for op in circuit:
        if isinstance(op, stim.CircuitRepeatBlock):
            if cur_moment:
                yield cur_moment
                cur_moment = []
            yield op
        elif isinstance(op, stim.CircuitInstruction):
            if op.name == "TICK":
                yield cur_moment
                cur_moment = []
            else:
                cur_moment.extend(
                    _split_targets_if_needed(
                        op, immune_qubit_indices=immune_qubit_indices
                    )
                )
    if cur_moment:
        yield cur_moment


def _measure_basis(*, split_op: stim.CircuitInstruction) -> str | None:
    """Converts an operation into a string describing the Pauli product basis it measures.

    Returns:
        None: This is not a measurement (or not *just* a measurement).
        str: Pauli product string that the operation measures (e.g. "XX" or "Y").
    """
    result = OP_TO_MEASURE_BASES.get(split_op.name)
    if result == "*":
        result = ""
        targets = split_op.targets_copy()
        for k in range(0, len(targets), 2):
            t = targets[k]
            if t.is_x_target:
                result += "X"
            elif t.is_y_target:
                result += "Y"
            elif t.is_z_target:
                result += "Z"
            else:
                raise NotImplementedError(f"{targets=}")
    return result
