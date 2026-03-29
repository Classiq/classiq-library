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

from typing import AbstractSet, Callable, Any, Literal

from gen._core._builder import Builder, AtLayer
from gen._core._patch import Patch
from gen._core._tile import Tile
from gen._core._util import sorted_complex
from gen._surf._closed_curve import ClosedCurve
from gen._surf._patch_outline import PatchOutline
from gen._surf._surface_code_legacy import measure_patch_legacy


def surface_code_patch(
    *,
    width: int,
    height: int,
    top_basis: Literal["X", "Z"],
    bot_basis: Literal["X", "Z"],
    left_basis: Literal["X", "Z"],
    right_basis: Literal["X", "Z"],
    rel_order_func: Callable[[complex], tuple[complex, ...]],
) -> Patch:
    """Generates the stabilizer configuration for a surface code patch."""

    c = ClosedCurve.from_cycle(
        [
            top_basis,
            width - 1,
            right_basis,
            width + height * 1j - 1 - 1j,
            bot_basis,
            height * 1j - 1j,
            left_basis,
            0,
        ]
    )
    return PatchOutline([c]).to_patch(rel_order_func=rel_order_func)


def layer_loop(
    *,
    builder: Builder,
    patch: Patch,
    style: Literal["css", "mpp", "cz"],
    compare_layer: Any,
    save_layer: Any,
    repetitions: int,
    mark_as_post_selected: Callable[[AtLayer], bool] = lambda _: False,
) -> None:
    if repetitions == 0:
        for tile in patch.tiles:
            m = tile.measurement_qubit
            builder.tracker.make_measurement_group(
                [AtLayer(m, compare_layer)], key=AtLayer(m, save_layer)
            )
        return

    measure_index_before_first_iteration = builder.tracker.next_measurement_index
    loop_start_layer = ("loop_start", save_layer)

    # Perform first iteration of loop.
    child = builder.fork()
    measure_patch_legacy(
        builder=child,
        patch=patch,
        save_layer=loop_start_layer,
        style=style,
    )
    for tile in patch.tiles:
        m = tile.measurement_qubit
        child.detector(
            [AtLayer(m, compare_layer), AtLayer(m, loop_start_layer)],
            pos=m,
            mark_as_post_selected=mark_as_post_selected(AtLayer(m, save_layer)),
        )
    child.circuit.append("SHIFT_COORDS", [], [0, 0, 1])
    child.tick()

    # Update tracker to contain last iteration information at desired save index.
    num_measurements_in_loop = (
        builder.tracker.next_measurement_index - measure_index_before_first_iteration
    )
    first_to_last_offset = num_measurements_in_loop * (repetitions - 1)
    for tile in patch.tiles:
        m = tile.measurement_qubit
        (start,) = builder.tracker.recorded[AtLayer(m, loop_start_layer)]
        builder.tracker.recorded[AtLayer(m, save_layer)] = [
            start + first_to_last_offset
        ]
    builder.tracker.next_measurement_index += first_to_last_offset

    # Append loop body to circuit.
    builder.circuit += child.circuit * repetitions


def layer_single_shot(
    *,
    builder: Builder,
    patch: Patch,
    style: Literal["cz", "css", "mpp"],
    data_basis: str | Callable[[complex], str],
    data_obs_qubit_sets: dict[int, AbstractSet[complex]] | None = None,
) -> None:
    if isinstance(data_basis, str):
        fixed_data_basis = data_basis
        data_basis = lambda _: fixed_data_basis
    dq = {q: data_basis(q) for q in patch.data_set}
    measure_patch_legacy(
        patch=patch,
        style=style,
        builder=builder,
        data_resets=dq,
        data_measures=dq,
        save_layer="single",
    )

    def matches_basis(t: Tile) -> bool:
        for b, d in zip(t.bases, t.ordered_data_qubits):
            if d is not None and b != data_basis(d):
                return False
        return True

    for tile in patch.tiles:
        if matches_basis(tile):
            builder.detector(
                [
                    AtLayer(tile.measurement_qubit, "single"),
                ],
                pos=tile.measurement_qubit,
            )
    for tile in patch.tiles:
        if matches_basis(tile):
            builder.detector(
                [AtLayer(q, "single") for q in tile.used_set],
                pos=tile.measurement_qubit,
                t=0.5,
            )
    for index, obs_qubits in data_obs_qubit_sets.items():
        builder.obs_include([AtLayer(q, "single") for q in obs_qubits], obs_index=index)


def layer_begin(
    *,
    builder: Builder,
    style: Literal["cz", "css", "mpp"],
    patch: Patch,
    save_layer: Any,
    obs_key_sets: dict[int, AbstractSet[complex]] | None = None,
    reset_basis: str | Callable[[complex], str],
    mark_as_post_selected: Callable[[AtLayer], bool] = lambda _: False,
) -> None:
    layer_transition(
        builder=builder,
        style=style,
        kept_data_qubits=set(),
        past_patch=None,
        past_save_layer=None,
        past_compare_layer=None,
        past_layer_lost_data_measure_basis=None,
        past_layer_lost_data_obs_qubit_sets=None,
        future_patch=patch,
        future_save_layer=save_layer,
        future_layer_obs_key_sets=obs_key_sets,
        future_layer_gain_data_reset_basis=reset_basis,
        mark_as_post_selected=mark_as_post_selected,
    )


def layer_end(
    *,
    builder: Builder,
    style: Literal["cz", "css", "mpp"],
    patch: Patch,
    save_layer: Any,
    compare_layer: Any,
    data_measure_basis: str | Callable[[complex], str],
    data_obs_qubit_sets: dict[int, AbstractSet[complex]] | None = None,
    mark_as_post_selected: Callable[[AtLayer], bool] = lambda _: False,
) -> None:
    layer_transition(
        builder=builder,
        style=style,
        kept_data_qubits=set(),
        past_patch=patch,
        past_save_layer=save_layer,
        past_compare_layer=compare_layer,
        past_layer_lost_data_measure_basis=data_measure_basis,
        past_layer_lost_data_obs_qubit_sets=data_obs_qubit_sets,
        future_patch=None,
        future_save_layer=None,
        future_layer_obs_key_sets=None,
        future_layer_gain_data_reset_basis=None,
        mark_as_post_selected=mark_as_post_selected,
    )


def layer_transition(
    *,
    builder: Builder,
    style: Literal["css", "mpp"],
    kept_data_qubits: set[complex] | frozenset[complex],
    past_patch: Patch | None,
    past_save_layer: Any | None,
    past_compare_layer: Any | None,
    past_layer_lost_data_measure_basis: None | str | Callable[[complex], str],
    past_layer_lost_data_obs_qubit_sets: dict[int, AbstractSet[complex]] | None = None,
    future_patch: Patch | None,
    future_save_layer: Any | None,
    future_layer_obs_key_sets: dict[int, AbstractSet[complex]] | None = None,
    future_layer_gain_data_reset_basis: None | str | Callable[[complex], str],
    mark_as_post_selected: Callable[[AtLayer], bool] = lambda _: False,
) -> None:
    assert future_patch is not None or past_patch is not None
    assert (
        (future_save_layer is None)
        == (future_patch is None)
        == (future_layer_gain_data_reset_basis is None)
    )
    assert (
        (past_save_layer is None)
        == (past_patch is None)
        == (past_compare_layer is None)
        == (past_layer_lost_data_measure_basis is None)
    )
    if future_patch is None:
        future_patch = Patch([])
    if past_patch is None:
        past_patch = Patch([])
    if isinstance(past_layer_lost_data_measure_basis, str):
        fixed_future_time_basis = past_layer_lost_data_measure_basis
        past_layer_lost_data_measure_basis = lambda _: fixed_future_time_basis
    if isinstance(future_layer_gain_data_reset_basis, str):
        fixed_past_time_basis = future_layer_gain_data_reset_basis
        future_layer_gain_data_reset_basis = lambda _: fixed_past_time_basis

    assert kept_data_qubits <= past_patch.data_set
    assert kept_data_qubits <= future_patch.data_set, repr(
        sorted_complex(kept_data_qubits - future_patch.data_set)
    )
    lost_data = past_patch.data_set - kept_data_qubits
    gained_data = future_patch.data_set - kept_data_qubits

    def matches_past_basis(tile: Tile) -> bool:
        for b, d in zip(tile.bases, tile.ordered_data_qubits):
            if (
                d is not None
                and d in gained_data
                and b != future_layer_gain_data_reset_basis(d)
            ):
                return False
        return True

    def matches_future_basis(tile: Tile) -> bool:
        for b, d in zip(tile.bases, tile.ordered_data_qubits):
            if (
                d is not None
                and d in lost_data
                and b != past_layer_lost_data_measure_basis(d)
            ):
                return False
        return True

    if past_patch.tiles:
        measure_patch_legacy(
            style=style,
            patch=past_patch,
            builder=builder,
            data_measures={q: past_layer_lost_data_measure_basis(q) for q in lost_data},
            save_layer=past_save_layer,
        )
        for prev_tile in past_patch.tiles:
            m = prev_tile.measurement_qubit
            builder.detector(
                [AtLayer(m, past_compare_layer), AtLayer(m, past_save_layer)],
                pos=m,
                mark_as_post_selected=mark_as_post_selected(
                    AtLayer(m, past_save_layer)
                ),
            )
        for prev_tile in past_patch.tiles:
            m = prev_tile.measurement_qubit
            if matches_future_basis(prev_tile) and prev_tile.data_set.isdisjoint(
                kept_data_qubits
            ):
                builder.detector(
                    [AtLayer(q, past_save_layer) for q in prev_tile.used_set],
                    pos=m,
                    t=0.5,
                )
        if past_layer_lost_data_obs_qubit_sets:
            for obs_index, obs_qubits in past_layer_lost_data_obs_qubit_sets.items():
                builder.obs_include(
                    [AtLayer(q, past_save_layer) for q in lost_data & obs_qubits],
                    obs_index=obs_index,
                )
        builder.shift_coords(dt=1)
        builder.tick()

    if future_patch.tiles:
        measure_patch_legacy(
            patch=future_patch,
            style=style,
            builder=builder,
            data_resets={q: future_layer_gain_data_reset_basis(q) for q in gained_data},
            save_layer=future_save_layer,
        )
        for next_tile in future_patch.tiles:
            if not matches_past_basis(next_tile):
                # Anticommutes with time boundary.
                continue

            m = next_tile.measurement_qubit
            comparison = [AtLayer(m, future_save_layer)]
            prev_tile = past_patch.m2tile.get(m)
            if prev_tile is not None and not prev_tile.data_set.isdisjoint(
                kept_data_qubits
            ):
                comparison.append(AtLayer(m, past_save_layer))
                for q in prev_tile.data_set:
                    if q not in kept_data_qubits:
                        comparison.append(AtLayer(q, past_save_layer))
            builder.detector(
                comparison,
                pos=m,
                mark_as_post_selected=mark_as_post_selected(
                    AtLayer(m, future_save_layer)
                ),
            )

        builder.shift_coords(dt=1)
        if future_layer_obs_key_sets:
            for obs_index, obs_qubits in future_layer_obs_key_sets.items():
                builder.obs_include(
                    [AtLayer(q, future_save_layer) for q in obs_qubits],
                    obs_index=obs_index,
                )
        builder.tick()
