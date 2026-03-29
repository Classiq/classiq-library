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

from typing import Iterable, Callable, Any, TYPE_CHECKING
from typing import Sequence

import stim

from gen._core._measurement_tracker import MeasurementTracker, AtLayer
from gen._core._pauli_string import PauliString
from gen._core._util import complex_key, sorted_complex

if TYPE_CHECKING:
    import gen


SYMMETRIC_GATES = {
    "CZ",
    "XCX",
    "YCY",
    "ZCZ",
    "SWAP",
    "ISWAP",
    "ISWAP_DAG",
    "SQRT_XX",
    "SQRT_YY",
    "SQRT_ZZ",
    "SQRT_XX_DAG",
    "SQRT_YY_DAG",
    "SQRT_ZZ_DAG",
}


class Builder:
    """Helper class for building stim circuits.

    Handles qubit indexing (complex -> int conversion).
    Handles measurement tracking (naming results and referring to them by name).
    """

    def __init__(
        self,
        *,
        q2i: dict[complex, int],
        circuit: stim.Circuit,
        tracker: MeasurementTracker,
    ):
        self.q2i = q2i
        self.circuit = circuit
        self.tracker = tracker

    def copy(self) -> "Builder":
        """Returns a Builder with independent copies of this builder's circuit and tracking data."""
        return Builder(
            q2i=dict(self.q2i), circuit=self.circuit.copy(), tracker=self.tracker.copy()
        )

    def fork(self) -> "Builder":
        """Returns a Builder with the same underlying tracking but which appends into a different circuit."""
        return Builder(q2i=self.q2i, circuit=stim.Circuit(), tracker=self.tracker)

    @staticmethod
    def for_qubits(
        qubits: Iterable[complex],
        *,
        to_circuit_coord_data: Callable[[complex], complex] = lambda e: e,
    ) -> "Builder":
        q2i = {q: i for i, q in enumerate(sorted_complex(set(qubits)))}
        circuit = stim.Circuit()
        for q, i in q2i.items():
            c = to_circuit_coord_data(q)
            circuit.append("QUBIT_COORDS", [i], [c.real, c.imag])
        return Builder(
            q2i=q2i,
            circuit=circuit,
            tracker=MeasurementTracker(),
        )

    def gate(self, name: str, qubits: Iterable[complex], arg: Any = None) -> None:
        assert name not in [
            "CZ",
            "ZCZ",
            "XCX",
            "YCY",
            "ISWAP",
            "ISWAP_DAG",
            "SWAP",
            "M",
            "MX",
            "MY",
        ]
        qubits = sorted_complex(qubits)
        if not qubits:
            return
        self.circuit.append(name, [self.q2i[q] for q in qubits], arg)

    def gate2(self, name: str, pairs: Iterable[tuple[complex, complex]]) -> None:
        pairs = sorted(
            pairs, key=lambda pair: (complex_key(pair[0]), complex_key(pair[1]))
        )
        if name == "XCZ":
            pairs = [pair[::-1] for pair in pairs]
            name = "CX"
        if name == "YCZ":
            pairs = [pair[::-1] for pair in pairs]
            name = "CY"
        if name == "SWAPCX":
            pairs = [pair[::-1] for pair in pairs]
            name = "CXSWAP"
        if name in SYMMETRIC_GATES:
            pairs = [sorted_complex(pair) for pair in pairs]
        if not pairs:
            return
        self.circuit.append(name, [self.q2i[q] for pair in pairs for q in pair])

    def shift_coords(self, *, dp: complex = 0, dt: int):
        self.circuit.append("SHIFT_COORDS", [], [dp.real, dp.imag, dt])

    def measure_stabilizer_code(
        self,
        code: "gen.StabilizerCode",
        *,
        save_layer: Any,
        det_cmp_layer: Any | None = None,
        noise: float | None = None,
        sorted_by_basis: bool = False,
        observables_first: bool = False,
        ancilla_qubits_for_xz_observable_pairs: Sequence[complex],
    ) -> None:
        m_obs = lambda: self.measure_observables_and_include(
            observables=code.entangled_observables(
                ancilla_qubits_for_xz_observable_pairs
            )[0],
            save_layer=save_layer,
            noise=noise,
        )
        m_det = lambda: self.measure_patch(
            patch=code.patch,
            save_layer=save_layer,
            cmp_layer=det_cmp_layer,
            noise=noise,
            sorted_by_basis=sorted_by_basis,
        )
        if observables_first:
            m_obs()
            m_det()
        else:
            m_det()
            m_obs()

    def measure_observables_and_include(
        self,
        observables: Iterable["gen.PauliString | None"],
        *,
        save_layer: Any | None = None,
        noise: float | None = None,
    ) -> None:
        for obs_index, obs in enumerate(observables):
            if obs is None:
                continue
            key = (
                None if save_layer is None else AtLayer(f"obs_{obs_index}", save_layer)
            )
            self.measure_pauli_string(
                obs,
                key=key,
                noise=noise,
            )
            self.circuit.append("OBSERVABLE_INCLUDE", stim.target_rec(-1), [obs_index])

    def measure_patch(
        self,
        patch: "gen.Patch",
        *,
        save_layer: Any,
        cmp_layer: Any | None = None,
        noise: float | None = None,
        sorted_by_basis: bool = False,
    ) -> None:
        """Directly measures the stabilizers in a patch using MPP.

        Args:
            patch: The patch to get stabilizers (tiles) from.
            save_layer: The layer used when saving results to the tracker. The
                measurement for a tile is saved under the key
                `gen.AtLayer(tile.measurement_qubit, save_layer)`.
            cmp_layer: If set to None, does nothing. If set to something else,
                adds detectors comparing the new layer's measurements to this
                layer's measurements.
            noise: The probability of measurement results being wrong. If set to
                None, does nothing. If set to a float, adds it as an argument
                to the MPP instruction.
            sorted_by_basis: Sorts the tiles by basis when deciding what order
                to perform measurements in. This can be important when making
                sure measurement offsets line up when entering and exiting
                loops. Extremely hacky.
        """
        if sorted_by_basis:
            from gen._core._patch import Patch

            patch = Patch(sorted(patch.tiles, key=lambda t: t.basis), do_not_sort=True)
        for tile in patch.tiles:
            self.measure_pauli_string(
                PauliString(
                    {
                        tile.ordered_data_qubits[k]: tile.bases[k]
                        for k in range(len(tile.ordered_data_qubits))
                        if tile.ordered_data_qubits[k] is not None
                    }
                ),
                key=AtLayer(tile.measurement_qubit, save_layer),
                noise=noise,
            )
        if cmp_layer is not None:
            for tile in patch.tiles:
                m = tile.measurement_qubit
                self.detector(
                    [AtLayer(m, save_layer), AtLayer(m, cmp_layer)],
                    pos=m,
                    extra_coords=tile.extra_coords,
                )

    def demolition_measure_with_feedback_passthrough(
        self,
        xs: Iterable[complex] = (),
        ys: Iterable[complex] = (),
        zs: Iterable[complex] = (),
        *,
        tracker_key: Callable[[complex], Any] = lambda e: e,
        save_layer: Any,
    ) -> None:
        """Performs demolition measurements that look like measurements w.r.t. detectors.

        This is done by adding feedback operations that flip the demolished qubits depending
        on the measurement result. This feedback can then later be removed using
        stim.Circuit.with_inlined_feedback. The benefit is that it can be easier to
        programmatically create the detectors using the passthrough measurements, and
        then they can be automatically converted.
        """
        self.measure(
            qubits=xs, basis="X", tracker_key=tracker_key, save_layer=save_layer
        )
        self.measure(
            qubits=ys, basis="Y", tracker_key=tracker_key, save_layer=save_layer
        )
        self.measure(
            qubits=zs, basis="Z", tracker_key=tracker_key, save_layer=save_layer
        )
        self.tick()
        self.gate("RX", xs)
        self.gate("RY", ys)
        self.gate("RZ", zs)
        for qs, b in [(xs, "Z"), (ys, "X"), (zs, "X")]:
            for q in qs:
                self.classical_paulis(
                    control_keys=[AtLayer(tracker_key(q), save_layer)],
                    targets=[q],
                    basis=b,
                )

    def measure(
        self,
        qubits: Iterable[complex],
        *,
        basis: str = "Z",
        tracker_key: Callable[[complex], Any] = lambda e: e,
        save_layer: Any,
    ) -> None:
        qubits = sorted_complex(qubits)
        if not qubits:
            return
        self.circuit.append(f"M{basis}", [self.q2i[q] for q in qubits])
        for q in qubits:
            self.tracker.record_measurement(AtLayer(tracker_key(q), save_layer))

    def measure_pauli_string(
        self,
        observable: "gen.PauliString",
        *,
        noise: float | None = None,
        key: Any | None,
    ):
        """Adds an MPP operation to measure the given pauli string.

        Args:
            observable: A gen.PauliString to measure.
            key: The value used to refer to the result later.
            noise: Optional measurement flip probability argument to add to the measurement.
        """
        targets = []
        for q in sorted_complex(observable.qubits):
            b = observable.qubits[q]
            if b == "X":
                m = stim.target_x
            elif b == "Y":
                m = stim.target_y
            elif b == "Z":
                m = stim.target_z
            else:
                raise NotImplementedError(f"{b=}")
            targets.append(m(self.q2i[q]))
            targets.append(stim.target_combiner())

        if targets:
            targets.pop()
            self.circuit.append("MPP", targets, noise)
            if key is not None:
                self.tracker.record_measurement(key)
        elif key is not None:
            self.tracker.make_measurement_group([], key=key)

    def detector(
        self,
        keys: Iterable[Any],
        *,
        pos: complex | None,
        t: float = 0,
        extra_coords: Iterable[float] = (),
        mark_as_post_selected: bool = False,
        ignore_non_existent: bool = False,
    ) -> None:
        if pos is not None:
            coords = [pos.real, pos.imag, t] + list(extra_coords)
            if mark_as_post_selected:
                coords.append(1)
        else:
            if list(extra_coords):
                raise ValueError("pos is None but extra_coords is not empty")
            if mark_as_post_selected:
                raise ValueError("pos is None and mark_as_post_selected")
            coords = None

        if ignore_non_existent:
            keys = [k for k in keys if k in self.tracker.recorded]
        targets = self.tracker.current_measurement_record_targets_for(keys)
        self.circuit.append("DETECTOR", targets, coords)

    def obs_include(self, keys: Iterable[Any], *, obs_index: int) -> None:
        ms = self.tracker.current_measurement_record_targets_for(keys)
        if ms:
            self.circuit.append(
                "OBSERVABLE_INCLUDE",
                ms,
                obs_index,
            )

    def tick(self) -> None:
        self.circuit.append("TICK")

    def cz(self, pairs: list[tuple[complex, complex]]) -> None:
        sorted_pairs = []
        for a, b in pairs:
            if complex_key(a) > complex_key(b):
                a, b = b, a
            sorted_pairs.append((a, b))
        sorted_pairs = sorted(
            sorted_pairs, key=lambda e: (complex_key(e[0]), complex_key(e[1]))
        )
        for a, b in sorted_pairs:
            self.circuit.append("CZ", [self.q2i[a], self.q2i[b]])

    def swap(self, pairs: list[tuple[complex, complex]]) -> None:
        sorted_pairs = []
        for a, b in pairs:
            if complex_key(a) > complex_key(b):
                a, b = b, a
            sorted_pairs.append((a, b))
        sorted_pairs = sorted(
            sorted_pairs, key=lambda e: (complex_key(e[0]), complex_key(e[1]))
        )
        for a, b in sorted_pairs:
            self.circuit.append("SWAP", [self.q2i[a], self.q2i[b]])

    def classical_paulis(
        self, *, control_keys: Iterable[Any], targets: Iterable[complex], basis: str
    ) -> None:
        gate = f"C{basis}"
        indices = [self.q2i[q] for q in sorted_complex(targets)]
        for rec in self.tracker.current_measurement_record_targets_for(control_keys):
            for i in indices:
                self.circuit.append(gate, [rec, i])
