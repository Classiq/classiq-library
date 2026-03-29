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

import functools
from typing import Callable, Any, Iterable

from gen._core import Builder, AtLayer
from gen._surf._closed_curve import ClosedCurve
from gen._surf._patch_outline import PatchOutline
from gen._surf._patch_transition_outline import PatchTransitionOutline


class StepOutline:
    def __init__(
        self,
        *,
        start: PatchTransitionOutline | None = None,
        body: PatchOutline,
        end: PatchTransitionOutline | None = None,
        obs_delta_body_start: dict[str, ClosedCurve] | None = None,
        obs_delta_body_end: dict[str, ClosedCurve] | None = None,
        rounds: int,
    ):
        self.start: PatchTransitionOutline = (
            start if start is not None else PatchTransitionOutline.empty()
        )
        self.body: PatchOutline = body
        self.obs_delta_body_start = (
            {} if obs_delta_body_start is None else obs_delta_body_start
        )
        self.obs_delta_body_end = (
            {} if obs_delta_body_end is None else obs_delta_body_end
        )
        self.end: PatchTransitionOutline = (
            end if end is not None else PatchTransitionOutline.empty()
        )
        self.rounds = rounds
        assert self.rounds > 0

    def without_start_transition(self):
        return StepOutline(
            start=None,
            body=self.body,
            end=self.end,
            obs_delta_body_start=self.obs_delta_body_end,
            obs_delta_body_end=self.obs_delta_body_start,
            rounds=self.rounds,
        )

    def without_end_transition(self):
        return StepOutline(
            start=self.start,
            body=self.body,
            end=None,
            obs_delta_body_start=self.obs_delta_body_end,
            obs_delta_body_end=self.obs_delta_body_start,
            rounds=self.rounds,
        )

    @functools.cached_property
    def used_set(self) -> frozenset[complex]:
        return self.start.data_set | self.end.data_set | self.body.to_patch().used_set

    def to_magic_init_step(self) -> "MagicInitStep":
        return MagicInitStep(self)

    def to_magic_end_step(self) -> "MagicEndStep":
        return MagicEndStep(self)

    def build_rounds(
        self,
        *,
        builder: Builder,
        rel_order_func: Callable[[complex], Iterable[complex]],
        alternate_ordering_with_round_parity: bool,
        start_round_index: int,
        cmp_layer: Any | None,
        save_layer: Any | None,
        edit_cur_obs: dict[str, set[complex]],
        o2i: dict[str, int | None],
    ) -> None:
        assert self.rounds > 0
        empty = PatchTransitionOutline.empty()
        patch = self.body.to_patch(rel_order_func=rel_order_func)

        def loop_round_key(r: int) -> Any:
            return (save_layer, "round", r)

        def fast_forward_record(
            *, rec_offset: int, old_round_key: Any, new_round_key: Any
        ):
            builder.tracker.next_measurement_index += rec_offset
            for m in patch.measure_set:
                builder.tracker.recorded[AtLayer(m, new_round_key)] = [
                    e + rec_offset
                    for e in builder.tracker.recorded[AtLayer(m, old_round_key)]
                ]

        round_builders = []
        round_index = start_round_index
        end_round_index = start_round_index + self.rounds
        while round_index < end_round_index:
            round_save_layer = loop_round_key(round_index)
            round_builders.append(builder.fork())
            bd: list[tuple[str, ClosedCurve]] = []
            if round_index == start_round_index:
                bd.extend(self.obs_delta_body_start.items())
            if round_index == end_round_index - 1:
                bd.extend(self.obs_delta_body_end.items())
            _css_surface_code_round(
                builder=round_builders[-1],
                edit_cur_obs=edit_cur_obs,
                start_outline=self.start if round_index == start_round_index else empty,
                end_outline=self.end if round_index == end_round_index - 1 else empty,
                observable_stabilizer_deltas=bd,
                patch_outline=self.body,
                save_layer=round_save_layer,
                cmp_layer=(
                    cmp_layer
                    if round_index == start_round_index
                    else loop_round_key(round_index - 1)
                ),
                rel_order_func=rel_order_func,
                reverse_order=alternate_ordering_with_round_parity
                and round_index % 2 == 1,
                o2i=o2i,
            )

            round_index += 1

            # Use repeat blocks when the circuit starts repeating.
            bulk_rounds_left = (
                end_round_index
                - round_index
                - bool(self.end or self.obs_delta_body_end)
            )
            if bulk_rounds_left > 0:
                if (
                    alternate_ordering_with_round_parity
                    and bulk_rounds_left % 2 == 0
                    and len(round_builders) >= 4
                    and round_builders[-3].circuit == round_builders[-1].circuit
                    and round_builders[-4].circuit == round_builders[-2].circuit
                ):
                    round_builders.pop()
                    round_builders.pop()
                    reversed_half = round_builders.pop()
                    round_builders[-1].circuit += reversed_half.circuit
                    m = round_builders[-1].circuit.num_measurements
                    double_rounds_to_run = bulk_rounds_left // 2
                    round_builders[-1].circuit *= double_rounds_to_run + 2
                    round_index += double_rounds_to_run * 2
                    fast_forward_record(
                        rec_offset=m * (double_rounds_to_run - 1),
                        new_round_key=loop_round_key(round_index - 1),
                        old_round_key=round_save_layer,
                    )
                elif (
                    not alternate_ordering_with_round_parity
                    and len(round_builders) >= 2
                    and round_builders[-1].circuit == round_builders[-2].circuit
                ):
                    round_builders.pop()
                    rounds_to_run = bulk_rounds_left
                    m = round_builders[-1].circuit.num_measurements
                    round_builders[-1].circuit *= rounds_to_run + 2
                    round_index += rounds_to_run
                    fast_forward_record(
                        rec_offset=m * rounds_to_run,
                        new_round_key=loop_round_key(round_index - 1),
                        old_round_key=round_save_layer,
                    )

        for sub_builder in round_builders:
            builder.circuit += sub_builder.circuit

        # Expose last round tracker info as overall saved tracker info
        round_save_layer = loop_round_key(end_round_index - 1)
        for q in self.end.data_set | patch.measure_set:
            builder.tracker.recorded[AtLayer(q, save_layer)] = builder.tracker.recorded[
                AtLayer(q, round_save_layer)
            ]


def _css_surface_code_round(
    *,
    builder: Builder,
    o2i: dict[str, int | None],
    edit_cur_obs: dict[str, set[complex]],
    start_outline: PatchTransitionOutline,
    end_outline: PatchTransitionOutline,
    observable_stabilizer_deltas: Iterable[tuple[str, ClosedCurve]],
    patch_outline: PatchOutline,
    rel_order_func: Callable[[complex], Iterable[complex]],
    reverse_order: bool,
    save_layer: Any,
    cmp_layer: Any | None,
) -> None:
    patch = patch_outline.to_patch(rel_order_func=rel_order_func)
    x_tiles = [tile for tile in patch.tiles if tile.basis == "X"]
    z_tiles = [tile for tile in patch.tiles if tile.basis == "Z"]
    if len(x_tiles) + len(z_tiles) != len(patch.tiles):
        raise NotImplementedError(f"Non-CSS {patch.tiles=}")

    # Reset moment.
    reset_bases = {
        "X": {tile.measurement_qubit for tile in x_tiles} | start_outline.data_x_set,
        "Z": {tile.measurement_qubit for tile in z_tiles} | start_outline.data_z_set,
    }
    for basis, qs in reset_bases.items():
        if qs:
            builder.gate(f"R{basis}", qs)
    builder.tick()

    # CX moments.
    (num_layers,) = {len(e.ordered_data_qubits) for e in patch.tiles}
    for k in range(num_layers)[:: -1 if reverse_order else +1]:
        pairs = []
        for tile in patch.tiles:
            q = tile.ordered_data_qubits[k]
            if q is not None:
                pair = (tile.measurement_qubit, q)
                if tile.basis == "Z":
                    pair = pair[::-1]
                pairs.append(pair)
        builder.gate2("CX", pairs)
        builder.tick()

    # Measure moment.
    measure_bases = {
        "X": {tile.measurement_qubit for tile in x_tiles} | end_outline.data_x_set,
        "Z": {tile.measurement_qubit for tile in z_tiles} | end_outline.data_z_set,
    }
    tmp_save_layer = ("raw", save_layer)
    for basis, qs in measure_bases.items():
        if qs:
            builder.measure(
                qs,
                basis=basis,
                save_layer=tmp_save_layer,
            )

    # Compare to resets and/or previous round.
    for tile in patch.tiles:
        comm = start_outline.data_x_set
        anti = start_outline.data_z_set
        if tile.basis == "Z":
            comm, anti = anti, comm
        if not tile.data_set.isdisjoint(anti):
            continue
        keys = [AtLayer(tile.measurement_qubit, tmp_save_layer)]
        if not (tile.data_set <= comm):
            if cmp_layer is None:
                # No comparison available.
                continue
            prev_key = AtLayer(tile.measurement_qubit, cmp_layer)
            keys.append(prev_key)
            if prev_key not in builder.tracker.recorded:
                continue
        builder.detector(keys, pos=tile.measurement_qubit)

    # Handle data measurements.
    for tile in patch.tiles:
        comm = end_outline.data_x_set
        anti = end_outline.data_z_set
        if tile.basis == "Z":
            comm, anti = anti, comm
        save_key = AtLayer(tile.measurement_qubit, save_layer)

        if not tile.data_set.isdisjoint(anti):
            # Stabilizer lost due to measurements.
            builder.tracker.record_obstacle(save_key)
        elif tile.data_set <= comm:
            # Stabilizer finalized by measurements.
            builder.detector(
                [AtLayer(q, tmp_save_layer) for q in tile.used_set],
                pos=tile.measurement_qubit,
                t=0.5,
            )
            builder.tracker.record_obstacle(save_key)
        else:
            # All or part of stabilizer survived measurements.
            builder.tracker.make_measurement_group(
                [AtLayer(tile.measurement_qubit, tmp_save_layer)]
                + [AtLayer(q, tmp_save_layer) for q in tile.data_set if q in comm],
                key=save_key,
            )
    for q in end_outline.data_set:
        builder.tracker.recorded[AtLayer(q, save_layer)] = builder.tracker.recorded[
            AtLayer(q, tmp_save_layer)
        ]

    # Apply observable deltas.
    for obs_name, delta in start_outline.observable_deltas.items():
        obs_index = o2i[obs_name]
        if obs_index is None:
            continue
        pts = delta.int_point_set
        assert pts <= start_outline.data_set, (obs_name, pts, start_outline.data_set)
        assert pts.isdisjoint(edit_cur_obs[obs_name])
        edit_cur_obs[obs_name] ^= pts
    for obs_name, delta in observable_stabilizer_deltas:
        obs_index = o2i[obs_name]
        if obs_index is None:
            continue
        pts = delta.interior_set(include_boundary=True)
        b = delta.basis
        assert b is not None
        ms = {
            tile.measurement_qubit
            for tile in patch.tiles
            if tile.basis == b and tile.data_set <= pts
        }
        for pt in ms:
            edit_cur_obs[obs_name] ^= patch.m2tile[pt].data_set
        builder.obs_include(
            [AtLayer(m, tmp_save_layer) for m in ms], obs_index=obs_index
        )
    for obs_name, delta in end_outline.observable_deltas.items():
        obs_index = o2i[obs_name]
        if obs_index is None:
            continue
        pts = delta.int_point_set
        assert pts <= end_outline.data_x_set | end_outline.data_z_set
        assert pts <= edit_cur_obs[obs_name]
        edit_cur_obs[obs_name] ^= pts
        builder.obs_include(
            [AtLayer(q, tmp_save_layer) for q in pts], obs_index=obs_index
        )

    builder.shift_coords(dt=1)
    builder.tick()


class MagicInitStep:
    def __init__(self, step: StepOutline):
        self.step = step

    @property
    def rounds(self) -> int:
        return self.step.rounds

    def build_rounds(
        self,
        *,
        builder: Builder,
        rel_order_func: Callable[[complex], Iterable[complex]],
        alternate_ordering_with_round_parity: bool,
        start_round_index: int,
        cmp_layer: Any | None,
        save_layer: Any | None,
        edit_cur_obs: dict[str, set[complex]],
        o2i: dict[str, int | None],
    ) -> None:
        builder.gate("DEPOLARIZE1", builder.q2i.keys(), 0.75)
        builder.tick()
        patch = self.step.body.to_patch()
        for tile in patch.tiles:
            builder.measure_pauli_product(
                tile.to_data_pauli_string(),
                key=AtLayer(tile.measurement_qubit, save_layer),
            )
        for obs_name, delta in self.step.start.observable_deltas.items():
            obs_index = o2i[obs_name]
            if obs_index is None:
                continue
            builder.measure_pauli_product(
                delta.to_pauli_string(),
                key=AtLayer(obs_name, save_layer),
            )
            assert not edit_cur_obs[obs_name]
            edit_cur_obs[obs_name] ^= delta.int_point_set
        for obs_name, delta in self.step.start.observable_deltas.items():
            obs_index = o2i[obs_name]
            if obs_index is None:
                continue
            builder.obs_include([AtLayer(obs_name, save_layer)], obs_index=obs_index)
        builder.shift_coords(dt=1)
        builder.tick()


class MagicEndStep:
    def __init__(self, step: StepOutline):
        self.step = step

    @property
    def rounds(self) -> int:
        return self.step.rounds

    def build_rounds(
        self,
        *,
        builder: Builder,
        rel_order_func: Callable[[complex], Iterable[complex]],
        alternate_ordering_with_round_parity: bool,
        start_round_index: int,
        cmp_layer: Any | None,
        save_layer: Any | None,
        edit_cur_obs: dict[str, set[complex]],
        o2i: dict[str, int | None],
    ) -> None:
        patch = self.step.body.to_patch()
        for tile in patch.tiles:
            builder.measure_pauli_product(
                tile.to_data_pauli_string(),
                key=AtLayer(tile.measurement_qubit, save_layer),
            )
        for obs_name, delta in self.step.end.observable_deltas.items():
            obs_index = o2i[obs_name]
            if obs_index is None:
                continue
            builder.measure_pauli_product(
                delta.to_pauli_string(),
                key=AtLayer(obs_name, save_layer),
            )
            assert edit_cur_obs[obs_name] == delta.int_point_set, (
                obs_name,
                edit_cur_obs[obs_name],
                delta.int_point_set,
            )
            edit_cur_obs[obs_name].clear()

        for tile in patch.tiles:
            builder.detector(
                [
                    AtLayer(tile.measurement_qubit, cmp_layer),
                    AtLayer(tile.measurement_qubit, save_layer),
                ],
                pos=tile.measurement_qubit,
            )
        for obs_name, delta in self.step.end.observable_deltas.items():
            obs_index = o2i[obs_name]
            if obs_index is None:
                continue
            builder.obs_include([AtLayer(obs_name, save_layer)], obs_index=obs_index)
        builder.shift_coords(dt=1)
        builder.tick()
        builder.gate("DEPOLARIZE1", builder.q2i.keys(), 0.75)
