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

import pathlib
from typing import Iterable, Literal, Any, Callable, Sequence

import stim

from gen._core._builder import Builder, AtLayer
from gen._core._noise import NoiseRule, NoiseModel
from gen._core._patch import Patch
from gen._core._pauli_string import PauliString
from gen._core._util import sorted_complex
from gen._util import write_file


class StabilizerCode:
    """This class stores the stabilizers and observables of a stabilizer code.

    The exact semantics of the class are somewhat loose. For example, by default
    this class doesn't verify that its fields actually form a valid stabilizer
    code. This is so that the class can be used as a sort of useful data dumping
    ground even in cases where what is being built isn't a stabilizer code. For
    example, you can store a gauge code in the fields... it's just that methods
    like 'make_code_capacity_circuit' will no longer work.

    The stabilizers are defined by the 'tiles' of the code's 'patch'. Each tile
    defines data qubits and a measurement qubit. The measurement qubit is also a
    very loose concept; it may literally represent a single ancilla qubit used
    for measuring the stabilizer. Or it may be more like a unique key identifying
    the tile, with no relation to any real qubit.
    """

    def __init__(
        self,
        *,
        patch: Patch,
        observables_x: Iterable[PauliString],
        observables_z: Iterable[PauliString],
    ):
        self.patch = patch
        self.observables_x = tuple(observables_x)
        self.observables_z = tuple(observables_z)

    @staticmethod
    def from_patch_with_inferred_observables(patch: Patch) -> "StabilizerCode":
        """Creates a code by finding degrees of freedom leftover from stabilizers.

        If there are M linearly independent stabilizers covering N qubits, then the
        returned code will have N-M observables.
        """
        q2i = {q: i for i, q in enumerate(sorted_complex(patch.data_set))}
        i2q = {i: q for q, i in q2i.items()}

        stabilizers: list[stim.PauliString] = []
        for tile in patch.tiles:
            stabilizer = stim.PauliString(len(q2i))
            for p, q in zip(tile.bases, tile.ordered_data_qubits):
                if q is not None:
                    stabilizer[q2i[q]] = p
            stabilizers.append(stabilizer)

        stabilizer_set: set[str] = set(str(e) for e in stabilizers)
        solved_tableau = stim.Tableau.from_stabilizers(
            stabilizers,
            allow_redundant=True,
            allow_underconstrained=True,
        )

        obs_xs = []
        obs_zs = []

        k: int = len(solved_tableau)
        while k > 0 and str(solved_tableau.z_output(k - 1)) not in stabilizer_set:
            k -= 1
            obs_xs.append(
                PauliString.from_stim_pauli_string(
                    solved_tableau.x_output(k)
                ).with_transformed_coords(i2q.__getitem__)
            )
            obs_zs.append(
                PauliString.from_stim_pauli_string(
                    solved_tableau.z_output(k)
                ).with_transformed_coords(i2q.__getitem__)
            )

        return StabilizerCode(patch=patch, observables_x=obs_xs, observables_z=obs_zs)

    def entangled_observables(
        self, ancilla_qubits_for_xz_pairs: Sequence[complex] | None
    ) -> tuple[list[PauliString], list[complex]]:
        """Makes XZ observables commute by entangling them with ancilla qubits.

        This is useful when attempting to test all observables simultaneously.
        As long as noise is not applied to the ancilla qubits, the observables
        returned by this method cover the same noise as the original observables
        but the returned observables can be simultaneously measured.
        """
        num_common = min(len(self.observables_x), len(self.observables_z))
        if ancilla_qubits_for_xz_pairs is None:
            a = (
                min(q.real for q in self.patch.data_set)
                + min(q.imag for q in self.patch.data_set) * 1j
                - 1j
            )
            ancilla_qubits_for_xz_pairs = [a + k for k in range(num_common)]
        else:
            assert len(ancilla_qubits_for_xz_pairs) == num_common
        observables = []
        for k, obs in enumerate(self.observables_x):
            if k < len(ancilla_qubits_for_xz_pairs):
                a = ancilla_qubits_for_xz_pairs[k]
                obs = obs * PauliString({a: "X"})
            observables.append(obs)
        for k, obs in enumerate(self.observables_z):
            if k < len(ancilla_qubits_for_xz_pairs):
                a = ancilla_qubits_for_xz_pairs[k]
                obs = obs * PauliString({a: "Z"})
            observables.append(obs)
        return observables, list(ancilla_qubits_for_xz_pairs)

    def check_commutation_relationships(self) -> None:
        """Verifies observables and stabilizers relate as a stabilizer code."""
        for tile in self.patch.tiles:
            t = tile.to_data_pauli_string()
            for obs in self.observables_x + self.observables_z:
                if not obs.commutes(t):
                    raise ValueError(
                        f"Tile stabilizer {tile=} anticommutes with {obs=}."
                    )
        all_obs = self.observables_x + self.observables_z
        anticommuting_pairs = set()
        for k in range(min(len(self.observables_x), len(self.observables_z))):
            anticommuting_pairs.add((k, k + len(self.observables_x)))
        for k1 in range(len(all_obs)):
            for k2 in range(k1 + 1, len(all_obs)):
                obs1 = all_obs[k1]
                obs2 = all_obs[k2]
                if (k1, k2) in anticommuting_pairs:
                    if obs1.commutes(obs2):
                        raise ValueError(
                            f"X/Z observable pair commutes: {obs1=}, {obs2=}."
                        )
                else:
                    if not obs1.commutes(obs2):
                        raise ValueError(
                            f"Unpaired observables should commute: {obs1=}, {obs2=}."
                        )

    def write_svg(
        self,
        path: str | pathlib.Path,
        *,
        show_order: bool | Literal["undirected", "3couplerspecial"] = False,
        show_measure_qubits: bool = False,
        show_data_qubits: bool = True,
        system_qubits: Iterable[complex] = (),
        opacity: float = 1,
    ) -> None:
        if not system_qubits:
            if show_measure_qubits and show_data_qubits:
                system_qubits = self.patch.used_set
            elif show_measure_qubits:
                system_qubits = self.patch.measure_set
            elif show_data_qubits:
                system_qubits = self.patch.data_set

        obs_patches = []
        for k in range(max(len(self.observables_x), len(self.observables_z))):
            obs_tiles = []
            if k < len(self.observables_x):
                obs_tiles.append(self.observables_x[k].to_tile())
            if k < len(self.observables_z):
                obs_tiles.append(self.observables_z[k].to_tile())
            obs_patches.append(Patch(obs_tiles))

        self.patch.write_svg(
            path=path,
            show_order=show_order,
            show_data_qubits=show_data_qubits,
            show_measure_qubits=show_measure_qubits,
            system_qubits=system_qubits,
            opacity=opacity,
            other=obs_patches,
        )

    def with_transformed_coords(
        self, coord_transform: Callable[[complex], complex]
    ) -> "StabilizerCode":
        return StabilizerCode(
            patch=self.patch.with_transformed_coords(coord_transform),
            observables_x=[
                e.with_transformed_coords(coord_transform) for e in self.observables_x
            ],
            observables_z=[
                e.with_transformed_coords(coord_transform) for e in self.observables_z
            ],
        )

    def make_code_capacity_circuit(
        self,
        *,
        noise: float | NoiseRule,
        debug_out_dir: pathlib.Path | None = None,
    ) -> stim.Circuit:
        """Creates a circuit implementing this code with a code capacity noise model.

        A code capacity noise model represents transmission over a noisy network
        with a noiseless sender and noiseless receiver. There is no noise from
        applying operations or measuring stabilizers, and there aren't multiple rounds.
        Encoding is done perfectly, then noise is applied to every data qubit, then
        decoding is done perfectly.

        Args:
            noise: Noise to apply to each data qubit, between the perfect encoding and
                perfect decoding. If this is a float, it refers to the strength of a
                `DEPOLARIZE1` noise channel. If it's a noise rule, the `after` specifies
                the noise to apply to each data qubit (whereas any `flip_result` noise
                specified by the rule will have no effect).
            debug_out_dir: A location to write files useful for debugging, like a
                picture of the stabilizers.

        Returns:
            A stim circuit that encodes the code perfectly, applies code capacity noise,
            then decodes the code. The circuit will check all observables simultaneously,
            using noiseless ancilla qubits if necessary in order to turn anticommuting
            observable pairs into commuting observables.
        """
        if isinstance(noise, (int, float)):
            noise = NoiseRule(after={"DEPOLARIZE1": noise})
        assert noise.flip_result == 0
        if debug_out_dir is not None:
            self.write_svg(debug_out_dir / "code.svg")
            self.patch.without_wraparound_tiles().write_svg(
                debug_out_dir / "patch.svg", show_order=False
            )
        circuit = _make_code_capacity_circuit_for_stabilizer_code(
            code=self,
            noise=noise,
        )
        if debug_out_dir is not None:
            from gen._viz_circuit_html import stim_circuit_html_viewer

            write_file(debug_out_dir / "detslice.svg", circuit.diagram("detslice-svg"))
            write_file(
                debug_out_dir / "graph.html", circuit.diagram("match-graph-3d-html")
            )
            write_file(
                debug_out_dir / "ideal_circuit.html",
                stim_circuit_html_viewer(circuit, patch=self.patch),
            )
            write_file(
                debug_out_dir / "circuit.html",
                stim_circuit_html_viewer(circuit.without_noise(), patch=self.patch),
            )
        return circuit

    def make_phenom_circuit(
        self,
        *,
        noise: float | NoiseRule | NoiseModel,
        rounds: int,
        debug_out_dir: pathlib.Path | None = None,
    ) -> stim.Circuit:
        """Creates a circuit implementing this code with a phenomenological noise model.

        A phenomenological noise model applies noise to data qubits between layers of
        stabilizer measurements and to the measurement results produced by those
        measurements. There is no noise accumulated between stabilizer measurements
        in the same layer, or within one stabilizer measurement (like would happen
        in a full circuit noise model where it was decomposed into multiple gates).

        Args:
            noise: If this is a float, it refers to the strength of a `DEPOLARIZE1` noise
                channel applied between each round and also the probability of flipping
                each measurement result.  If it's a noise rule, its `after` specifies
                the noise to apply to each data qubit between each round, and its
                `flip_result` is the probability of flipping each measurement result.
            rounds: The number of times that the patch stabilizers are noisily measured.
                There is an additional noiseless layer of measurements at the start and
                at the end, to terminate the problem. Note that data noise is applied
                both between normal rounds, and also between a round and one of these
                special start/end layers. This means measurement noise is applied `rounds`
                times, whereas between-round measurement is applied `rounds+1` times. So
                code capacity noise occurs at `rounds=0`.

                TODO: redefine this so code cap noise is at rounds=1.
            debug_out_dir: A location to write files useful for debugging, like a
                picture of the stabilizers.

        Returns:
            A stim circuit that encodes the code perfectly, performs R rounds of
            phenomenological noise. then decodes the code perfect;y. The circuit
            will check all observables simultaneously, using noiseless ancilla qubits
            if necessary in order to turn anticommuting observable pairs into commuting observables.
        """

        if isinstance(noise, NoiseModel):
            noise = NoiseRule(
                after=noise.idle_noise.after,
                flip_result=(
                    noise.any_measurement_rule or noise.measure_rules["Z"]
                ).flip_result,
            )
        if isinstance(noise, (int, float)):
            noise = NoiseRule(after={"DEPOLARIZE1": noise}, flip_result=noise)
        if debug_out_dir is not None:
            self.write_svg(debug_out_dir / "code.svg")
            self.patch.without_wraparound_tiles().write_svg(
                debug_out_dir / "patch.svg", show_order=False
            )
        circuit = _make_phenom_circuit_for_stabilizer_code(
            code=self,
            noise=noise,
            rounds=rounds,
        )
        if debug_out_dir is not None:
            from gen._viz_circuit_html import stim_circuit_html_viewer

            write_file(debug_out_dir / "detslice.svg", circuit.diagram("detslice-svg"))
            write_file(
                debug_out_dir / "graph.html", circuit.diagram("match-graph-3d-html")
            )
            write_file(
                debug_out_dir / "ideal_circuit.html",
                stim_circuit_html_viewer(circuit, patch=self.patch),
            )
            write_file(
                debug_out_dir / "circuit.html",
                stim_circuit_html_viewer(circuit.without_noise(), patch=self.patch),
            )
        return circuit

    def __repr__(self) -> str:
        def indented(x: str) -> str:
            return x.replace("\n", "\n    ")

        def indented_repr(x: Any) -> str:
            if isinstance(x, tuple):
                return indented(
                    indented("[\n" + ",\n".join(indented_repr(e) for e in x)) + ",\n]"
                )
            return indented(repr(x))

        return f"""gen.StabilizerCode(
    patch={indented_repr(self.patch)},
    observables_x={indented_repr(self.observables_x)},
    observables_z={indented_repr(self.observables_z)},
)"""

    def __eq__(self, other) -> bool:
        if not isinstance(other, StabilizerCode):
            return NotImplemented
        return (
            self.patch == other.patch
            and self.observables_x == other.observables_x
            and self.observables_z == other.observables_z
        )

    def __ne__(self, other) -> bool:
        return not (self == other)


def _make_phenom_circuit_for_stabilizer_code(
    *,
    code: StabilizerCode,
    noise: NoiseRule,
    suggested_ancilla_qubits: list[complex] | None = None,
    rounds: int,
) -> stim.Circuit:
    observables, immune = code.entangled_observables(
        ancilla_qubits_for_xz_pairs=suggested_ancilla_qubits,
    )
    immune = set(immune)
    builder = Builder.for_qubits(code.patch.data_set | immune)

    for k, obs in enumerate(observables):
        builder.measure_pauli_string(obs, key=f"OBS_START{k}")
        builder.obs_include([f"OBS_START{k}"], obs_index=k)
    builder.measure_patch(code.patch, save_layer="init")
    builder.tick()

    loop = builder.fork()
    for k, p in noise.after.items():
        loop.circuit.append(
            k, [builder.q2i[q] for q in sorted_complex(code.patch.data_set - immune)], p
        )
    loop.measure_patch(
        code.patch, save_layer="loop", cmp_layer="init", noise=noise.flip_result
    )
    loop.shift_coords(dt=1)
    loop.tick()
    builder.circuit += loop.circuit * rounds

    builder.measure_patch(code.patch, save_layer="end", cmp_layer="loop")
    for k, obs in enumerate(observables):
        builder.measure_pauli_string(obs, key=f"OBS_END{k}")
        builder.obs_include([f"OBS_END{k}"], obs_index=k)

    return builder.circuit


def _make_code_capacity_circuit_for_stabilizer_code(
    *,
    code: StabilizerCode,
    noise: NoiseRule,
    suggested_ancilla_qubits: list[complex] | None = None,
) -> stim.Circuit:
    assert noise.flip_result == 0
    observables, immune = code.entangled_observables(
        ancilla_qubits_for_xz_pairs=suggested_ancilla_qubits,
    )
    immune = set(immune)
    builder = Builder.for_qubits(code.patch.data_set | immune)

    for k, obs in enumerate(observables):
        builder.measure_pauli_string(obs, key=f"OBS_START{k}")
        builder.obs_include([f"OBS_START{k}"], obs_index=k)
    builder.measure_patch(code.patch, save_layer="init")
    builder.tick()

    for k, p in noise.after.items():
        builder.circuit.append(
            k, [builder.q2i[q] for q in sorted_complex(code.patch.data_set - immune)], p
        )
    builder.tick()

    builder.measure_patch(code.patch, save_layer="end", cmp_layer="init")
    for k, obs in enumerate(observables):
        builder.measure_pauli_string(obs, key=f"OBS_END{k}")
        builder.obs_include([f"OBS_END{k}"], obs_index=k)

    return builder.circuit
