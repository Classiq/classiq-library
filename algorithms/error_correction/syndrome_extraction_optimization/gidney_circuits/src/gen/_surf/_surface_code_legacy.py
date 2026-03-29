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

from typing import Callable, Any, Literal, AbstractSet, Iterable

from gen._layers import transpile_to_z_basis_interaction_circuit
from gen._core import Patch, Builder, AtLayer, PauliString, complex_key, sorted_complex


def _measure_css(
    *,
    patch: Patch,
    data_resets: dict[complex, str],
    data_measures: dict[complex, str],
    builder: Builder,
    tracker_key: Callable[[complex], Any],
    tracker_layer: float,
) -> None:
    assert patch.measure_set.isdisjoint(data_resets)
    if not patch.tiles:
        return

    x_tiles = [tile for tile in patch.tiles if tile.basis == "X"]
    z_tiles = [tile for tile in patch.tiles if tile.basis == "Z"]
    other_tiles = [
        tile for tile in patch.tiles if tile.basis != "X" and tile.basis != "Z"
    ]
    reset_bases = {
        "X": [tile.measurement_qubit for tile in x_tiles],
        "Y": [],
        "Z": [tile.measurement_qubit for tile in z_tiles + other_tiles],
    }
    for q, b in data_resets.items():
        reset_bases[b].append(q)
    for b, qs in reset_bases.items():
        if qs:
            builder.gate(f"R{b}", qs)
    builder.tick()

    (num_layers,) = {len(e.ordered_data_qubits) for e in patch.tiles}
    for k in range(num_layers):
        pairs = []
        for tile in x_tiles:
            q = tile.ordered_data_qubits[k]
            if q is not None:
                pairs.append((tile.measurement_qubit, q))
        for tile in z_tiles:
            q = tile.ordered_data_qubits[k]
            if q is not None:
                pairs.append((q, tile.measurement_qubit))
        builder.gate2("CX", pairs)
        for tile in sorted(
            other_tiles, key=lambda tile: complex_key(tile.measurement_qubit)
        ):
            q = tile.ordered_data_qubits[k]
            b = tile.bases[k]
            if q is not None:
                builder.gate2(f"{b}CX", [(q, tile.measurement_qubit)])
        builder.tick()

    measure_bases = {
        "X": [tile.measurement_qubit for tile in x_tiles],
        "Y": [],
        "Z": [tile.measurement_qubit for tile in z_tiles + other_tiles],
    }
    for q, b in data_measures.items():
        measure_bases[b].append(q)
    for b, qs in measure_bases.items():
        if qs:
            builder.measure(
                qs,
                basis=b,
                tracker_key=tracker_key,
                save_layer=tracker_layer,
            )


def _measure_cz(
    *,
    patch: Patch,
    data_resets: dict[complex, str],
    data_measures: dict[complex, str],
    builder: Builder,
    tracker_key: Callable[[complex], Any],
    tracker_layer: float,
) -> None:
    out = builder.fork()
    _measure_css(
        patch=patch,
        data_resets=data_resets,
        data_measures=data_measures,
        builder=out,
        tracker_key=tracker_key,
        tracker_layer=tracker_layer,
    )
    builder.circuit += transpile_to_z_basis_interaction_circuit(
        out.circuit, is_entire_circuit=False
    )


def _measure_mpp(
    patch,
    *,
    data_resets: dict[complex, str],
    data_measures: dict[complex, str],
    builder: Builder,
    tracker_key: Callable[[complex], Any],
    tracker_layer: float,
) -> None:
    assert patch.measure_set.isdisjoint(data_resets)

    if data_resets:
        for b in "XYZ":
            builder.gate(f"R{b}", {q for q, db in data_resets.items() if b == db})

    for v in patch.tiles:
        builder.measure_pauli_string(
            PauliString(
                {q: b for q, b in zip(v.ordered_data_qubits, v.bases) if q is not None}
            ),
            key=AtLayer(tracker_key(v.measurement_qubit), tracker_layer),
        )

    if data_measures:
        for b in "XYZ":
            builder.measure(
                {q for q, db in data_measures.items() if b == db},
                basis=b,
                tracker_key=tracker_key,
                save_layer=tracker_layer,
            )


def measure_patch_legacy(
    patch,
    *,
    data_resets: dict[complex, str] | None = None,
    data_measures: dict[complex, str] | None = None,
    builder: Builder,
    tracker_key: Callable[[complex], Any] = lambda e: e,
    save_layer: Any,
    style: Literal["css", "cz", "mpp"] = "cz",
) -> None:
    if data_resets is None:
        data_resets = {}
    if data_measures is None:
        data_measures = {}
    if style == "css":
        _measure_css(
            patch=patch,
            data_resets=data_resets,
            data_measures=data_measures,
            builder=builder,
            tracker_key=tracker_key,
            tracker_layer=save_layer,
        )
    elif style == "cz":
        _measure_cz(
            patch=patch,
            data_resets=data_resets,
            data_measures=data_measures,
            builder=builder,
            tracker_key=tracker_key,
            tracker_layer=save_layer,
        )
    elif style == "mpp":
        _measure_mpp(
            patch=patch,
            data_resets=data_resets,
            data_measures=data_measures,
            builder=builder,
            tracker_key=tracker_key,
            tracker_layer=save_layer,
        )
    else:
        raise NotImplementedError(f"{style=}")


def measure_patch_legacy_detect(
    patch,
    *,
    comparison_overrides: dict[Any, list[Any] | None] | None = None,
    skipped_comparisons: Iterable[Any] = (),
    singleton_detectors: Iterable[Any] = (),
    data_resets: dict[complex, str] | None = None,
    data_measures: dict[complex, str] | None = None,
    builder: Builder,
    repetitions: int | None = None,
    tracker_key: Callable[[complex], Any] = lambda e: e,
    cmp_layer: Any | None,
    save_layer: Any,
    tracker_layer_last_rep: Any | None = None,
    post_selected_positions: AbstractSet[complex] = frozenset(),
    style: Literal["css", "cz", "mpp"] = "cz",
) -> None:
    if data_resets is None:
        data_resets = {}
    if data_measures is None:
        data_measures = {}
    assert (repetitions is not None) == (tracker_layer_last_rep is not None)
    if repetitions is not None:
        assert not data_resets
        assert not data_measures
    if repetitions == 0:
        for plaq in patch.tiles:
            m = plaq.measurement_qubit
            builder.tracker.make_measurement_group(
                [AtLayer(m, cmp_layer)], key=AtLayer(m, tracker_layer_last_rep)
            )
        return

    child = builder.fork()
    pm = builder.tracker.next_measurement_index
    measure_patch_legacy(
        patch=patch,
        data_resets=data_resets,
        data_measures=data_measures,
        builder=child,
        tracker_key=tracker_key,
        save_layer=save_layer,
        style=style,
    )
    num_measurements = builder.tracker.next_measurement_index - pm

    if comparison_overrides is None:
        comparison_overrides = {}
    assert patch.measure_set.isdisjoint(data_resets)
    skipped_comparisons_set = frozenset(skipped_comparisons)
    singleton_detectors_set = frozenset(singleton_detectors)
    for e in sorted_complex(patch.tiles, key=lambda e2: e2.measurement_qubit):
        if all(e is None for e in e.ordered_data_qubits):
            continue
        failed = False
        for q, b in zip(e.ordered_data_qubits, e.bases):
            if q is not None and data_resets.get(q, b) != b:
                failed = True
        if failed:
            continue
        m = e.measurement_qubit
        if m in skipped_comparisons_set:
            continue
        if m in singleton_detectors_set:
            comparisons = []
        elif cmp_layer is not None:
            comparisons = comparison_overrides.get(m, [AtLayer(m, cmp_layer)])
        else:
            comparisons = []
        if comparisons is None:
            continue
        assert isinstance(
            comparisons, list
        ), f"Vs exception must be a list but got {comparisons!r} for {m!r}"
        child.detector(
            [AtLayer(m, save_layer), *comparisons],
            pos=m,
            mark_as_post_selected=m in post_selected_positions,
        )
    child.circuit.append("SHIFT_COORDS", [], [0, 0, 1])
    specified_reps = repetitions is not None
    if repetitions is None:
        repetitions = 1
    if specified_reps:
        child.tick()

    if repetitions > 1 or tracker_layer_last_rep is not None:
        if tracker_layer_last_rep is None:
            raise ValueError("repetitions > 1 and tracker_layer_last_rep is None")
        offset = num_measurements * (repetitions - 1)
        builder.tracker.next_measurement_index += offset
        for m in data_measures.keys() | patch.measure_set:
            builder.tracker.recorded[AtLayer(m, tracker_layer_last_rep)] = [
                e + offset for e in builder.tracker.recorded[AtLayer(m, save_layer)]
            ]
    builder.circuit += child.circuit * repetitions
