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
from typing import Callable, Any
from typing import Literal
from typing import cast

import stim

import gen
from clorco._make_circuit_params import Params
from clorco.color_code._color_code_layouts import (
    make_color_code_layout,
    make_color_code_layout_488,
    make_toric_color_code_layout,
)
from clorco.color_code._midout_planar_color_code_circuits import (
    make_midout_color_code_circuit_chunks,
)
from clorco.color_code._mxyz_color_codes import make_mxyz_color_code_from_stim_gen
from clorco.color_code._mxyz_color_codes import make_mxyz_phenom_color_code
from clorco.color_code._superdense_planar_color_code_circuits import (
    make_color_code_layout_for_superdense,
)
from clorco.color_code._superdense_planar_color_code_circuits import (
    make_superdense_color_code_circuit,
)
from clorco.color_code._toric_color_code_circuits import (
    make_toric_color_code_circuit_with_magic_time_boundaries,
)


def make_named_color_code_constructions() -> (
    dict[str, Callable[[Params], stim.Circuit]]
):
    return {
        **_midout_color_code_circuit_constructions(),
        **_simplified_noise_color_code_constructions(),
        **_toric_color_code_constructions(),
        **_superdense_color_code_circuit_constructions(),
    }


def _midout_color_code_circuit_constructions() -> (
    dict[str, Callable[[Params], stim.Circuit]]
):
    constructions: dict[str, Callable[[Params], stim.Circuit]] = {}

    def _chunks_to_circuit(params: Params, chunks: list[gen.Chunk]) -> stim.Circuit:
        circuit = gen.compile_chunks_into_circuit(chunks)

        if params.debug_out_dir is not None:
            make_layout = (
                make_color_code_layout_488
                if "488" in params.style
                else make_color_code_layout
            )
            rgb_patch = make_layout(
                base_width=params.diameter,
                spurs="midout",
                coord_style="rect",
                single_rgb_layer_instead_of_actual_code=True,
            ).patch
            gen.write_file(
                params.debug_out_dir / "ideal_circuit.html",
                gen.stim_circuit_html_viewer(circuit, patch=rgb_patch),
            )

        if params.convert_to_cz:
            circuit = gen.transpile_to_z_basis_interaction_circuit(circuit)
        circuit = circuit.with_inlined_feedback()
        if params.noise_model is not None:
            circuit = params.noise_model.noisy_circuit(circuit)

        if params.debug_out_dir is not None:
            make_layout = (
                make_color_code_layout_488
                if "488" in params.style
                else make_color_code_layout
            )
            make_layout(
                base_width=params.diameter,
                spurs="smooth",
                coord_style="rect",
                single_rgb_layer_instead_of_actual_code=True,
            ).patch.write_svg(
                params.debug_out_dir / "rgb_patch_smooth.svg",
                show_data_qubits=True,
                show_order=False,
                show_measure_qubits=False,
            )
            make_layout(
                base_width=params.diameter,
                spurs="smooth",
                coord_style=cast(Any, "oct" if "488" in params.style else "hex"),
                single_rgb_layer_instead_of_actual_code=True,
            ).patch.write_svg(
                params.debug_out_dir / "rgb_patch_hex_smooth.svg",
                show_data_qubits=True,
                show_order=False,
                show_measure_qubits=False,
            )
            make_layout(
                base_width=params.diameter,
                spurs="midout",
                coord_style=cast(Any, "oct" if "488" in params.style else "hex"),
                single_rgb_layer_instead_of_actual_code=True,
            ).patch.write_svg(
                params.debug_out_dir / "rgb_patch_hex.svg",
                show_data_qubits=True,
                show_order=False,
                show_measure_qubits=False,
            )
            make_layout(
                base_width=params.diameter,
                spurs="midout_readout_line_constraint",
                coord_style="rect",
                single_rgb_layer_instead_of_actual_code=True,
            ).patch.write_svg(
                params.debug_out_dir / "rgb_patch_extra_spurs.svg",
                show_data_qubits=True,
                show_order=False,
                show_measure_qubits=False,
            )
            rgb_patch = make_layout(
                base_width=params.diameter,
                spurs="midout",
                coord_style="rect",
                single_rgb_layer_instead_of_actual_code=True,
            ).patch
            rgb_patch.write_svg(
                params.debug_out_dir / "rgb_patch.svg",
                show_data_qubits=True,
                show_order=False,
                show_measure_qubits=False,
            )
            gen.write_file(
                params.debug_out_dir / "circuit.html",
                gen.stim_circuit_html_viewer(circuit, patch=rgb_patch),
            )

        return circuit

    constructions["mxyz_color_code"] = (
        lambda params: make_mxyz_color_code_from_stim_gen(
            distance=params.diameter,
            rounds=params.rounds,
            noise=params.noise_model,
            convert_to_cz=params.convert_to_cz,
        )
    )
    constructions["phenom_mxyz_color_code"] = (
        lambda params: make_mxyz_phenom_color_code(
            base_width=params.diameter,
            rounds=params.rounds,
            noise=params.noise_strength,
        )
    )

    constructions["midout_color_code_Z"] = lambda params: _chunks_to_circuit(
        params,
        make_midout_color_code_circuit_chunks(
            basis="Z",
            base_width=params.diameter,
            rounds=params.rounds,
            use_488=False,
        ),
    )
    constructions["midout_color_code_X"] = lambda params: _chunks_to_circuit(
        params,
        make_midout_color_code_circuit_chunks(
            basis="X",
            base_width=params.diameter,
            rounds=params.rounds,
            use_488=False,
        ),
    )
    constructions["midout_color_code_Z"] = lambda params: _chunks_to_circuit(
        params,
        make_midout_color_code_circuit_chunks(
            basis="Z",
            base_width=params.diameter,
            rounds=params.rounds,
            use_488=False,
        ),
    )
    constructions["midout_color_code_488_X"] = lambda params: _chunks_to_circuit(
        params,
        make_midout_color_code_circuit_chunks(
            basis="X",
            base_width=params.diameter,
            rounds=params.rounds,
            use_488=True,
        ),
    )
    constructions["midout_color_code_488_Z"] = lambda params: _chunks_to_circuit(
        params,
        make_midout_color_code_circuit_chunks(
            basis="Z",
            base_width=params.diameter,
            rounds=params.rounds,
            use_488=True,
        ),
    )
    return constructions


def _superdense_color_code_circuit_constructions() -> (
    dict[str, Callable[[Params], stim.Circuit]]
):
    constructions: dict[str, Callable[[Params], stim.Circuit]] = {}

    def _chunks_to_circuit(params: Params) -> stim.Circuit:
        basis = params.style[-1]
        assert basis == "X" or basis == "Z"
        circuit = make_superdense_color_code_circuit(
            base_data_width=params.diameter,
            basis=cast(Literal["X", "Z"], basis),
            rounds=params.rounds,
        )

        if params.debug_out_dir is not None:
            rgb_patch = make_color_code_layout_for_superdense(
                base_data_width=params.diameter,
                single_rgb_layer_instead_of_actual_code=True,
            ).patch
            gen.write_file(
                params.debug_out_dir / "ideal_circuit.html",
                gen.stim_circuit_html_viewer(circuit, patch=rgb_patch),
            )
            rgb_patch = make_color_code_layout_for_superdense(
                base_data_width=params.diameter,
                single_rgb_layer_instead_of_actual_code="double_measure_qubit",
            ).patch
            rgb_patch.write_svg(
                params.debug_out_dir / "rgb_patch.svg",
                show_order=False,
                show_measure_qubits=False,
            )
            rgb_patch.write_svg(
                params.debug_out_dir / "rgb_patch_qubits.svg",
                show_order=False,
                show_measure_qubits=True,
                show_data_qubits=True,
            )
            make_color_code_layout_for_superdense(
                base_data_width=params.diameter,
                single_rgb_layer_instead_of_actual_code=False,
            ).write_svg(params.debug_out_dir / "code.svg", show_measure_qubits=True)

        if params.convert_to_cz:
            circuit = gen.transpile_to_z_basis_interaction_circuit(circuit)
        if params.noise_model is not None:
            circuit = params.noise_model.noisy_circuit(circuit)
        return circuit

    constructions["superdense_color_code_X"] = _chunks_to_circuit
    constructions["superdense_color_code_Z"] = _chunks_to_circuit
    return constructions


def _simplified_noise_color_code_constructions() -> (
    dict[str, Callable[[Params], stim.Circuit]]
):
    constructions: dict[str, Callable[[Params], stim.Circuit]] = {}

    def _make_simple_circuit(
        params: Params, *, code: gen.StabilizerCode, phenom: bool
    ) -> stim.Circuit:
        if phenom:
            return code.make_phenom_circuit(
                noise=params.noise_model,
                rounds=params.rounds,
                debug_out_dir=params.debug_out_dir,
            )
        assert params.rounds == 1
        return code.make_code_capacity_circuit(
            noise=params.noise_model.idle_noise, debug_out_dir=params.debug_out_dir
        )

    constructions["transit_color_code"] = lambda params: _make_simple_circuit(
        params=params,
        code=make_color_code_layout(
            base_width=params.diameter,
            coord_style="rect",
            single_rgb_layer_instead_of_actual_code=False,
            spurs="smooth",
        ),
        phenom=False,
    )
    constructions["phenom_color_code"] = lambda params: _make_simple_circuit(
        params=params,
        code=make_color_code_layout(
            base_width=params.diameter,
            coord_style="rect",
            single_rgb_layer_instead_of_actual_code=False,
            spurs="smooth",
        ),
        phenom=True,
    )
    constructions["phenom_color_code_488"] = lambda params: _make_simple_circuit(
        params=params,
        code=make_color_code_layout_488(
            base_width=params.diameter,
            coord_style="rect",
            single_rgb_layer_instead_of_actual_code=False,
            spurs="smooth",
        ),
        phenom=True,
    )
    constructions["transit_color_code_488"] = lambda params: _make_simple_circuit(
        params=params,
        code=make_color_code_layout_488(
            base_width=params.diameter,
            coord_style="rect",
            single_rgb_layer_instead_of_actual_code=False,
            spurs="smooth",
        ),
        phenom=False,
    )
    return constructions


def _toric_color_code_constructions() -> dict[str, Callable[[Params], stim.Circuit]]:
    def _infer_size(params: Params):
        width = params.editable_extras.get("w")
        height = params.editable_extras.get("h")
        if width is None:
            width = params.diameter
        if height is None:
            height = width // 6 * 8
        params.editable_extras["w"] = width
        params.editable_extras["h"] = height
        return width, height

    def _make_circuit(
        params: Params, *, style: Any, ablate_into_matchable_code: bool
    ) -> stim.Circuit:
        width, height = _infer_size(params)
        circuit = make_toric_color_code_circuit_with_magic_time_boundaries(
            width=width,
            height=height,
            noise=params.noise_model,
            rounds=params.rounds,
            style=style,
            convert_to_cz=params.convert_to_cz,
            ablate_into_matchable_code=ablate_into_matchable_code,
        )
        if params.debug_out_dir is not None:
            gen.write_file(
                params.debug_out_dir / "circuit.html",
                gen.stim_circuit_html_viewer(circuit),
            )
        return circuit

    constructions = {}
    constructions["toric_superdense_color_code_magicEPR"] = functools.partial(
        _make_circuit, style="superdense", ablate_into_matchable_code=False
    )
    constructions["toric_midout_color_code_magicEPR"] = functools.partial(
        _make_circuit, style="midout", ablate_into_matchable_code=False
    )
    constructions["ablated_toric_superdense_color_code_magicEPR"] = functools.partial(
        _make_circuit, style="superdense", ablate_into_matchable_code=True
    )
    constructions["ablated_toric_midout_color_code_magicEPR"] = functools.partial(
        _make_circuit, style="midout", ablate_into_matchable_code=True
    )

    def _make_simple_circuit(
        params: Params, *, ablate_into_matchable_code: bool, phenom: bool
    ) -> stim.Circuit:
        width, height = _infer_size(params)
        code = make_toric_color_code_layout(
            width=width,
            height=height,
            ablate_into_matchable_code=ablate_into_matchable_code,
        )
        if params.debug_out_dir is not None:
            code.write_svg(params.debug_out_dir / "code.svg")
            code.patch.without_wraparound_tiles().write_svg(
                params.debug_out_dir / "patch.svg", show_order=False
            )
            code.patch.write_svg(
                params.debug_out_dir / "patch_xz.svg",
                other=[
                    code.patch.with_only_x_tiles(),
                    code.patch.with_only_z_tiles(),
                ],
                show_order=False,
                system_qubits=code.patch.data_set,
                wraparound_clip=True,
            )
        if phenom:
            circuit = code.make_phenom_circuit(
                noise=params.noise_strength, rounds=params.rounds
            )
        else:
            assert params.rounds == 1
            circuit = code.make_code_capacity_circuit(noise=params.noise_strength)
        if params.debug_out_dir is not None:
            gen.write_file(
                params.debug_out_dir / "detslice.svg", circuit.diagram("detslice-svg")
            )
            gen.write_file(
                params.debug_out_dir / "graph.html",
                circuit.diagram("match-graph-3d-html"),
            )
        return circuit

    constructions["transit_toric_color_code"] = functools.partial(
        _make_simple_circuit, ablate_into_matchable_code=False, phenom=False
    )
    constructions["transit_ablated_toric_color_code"] = functools.partial(
        _make_simple_circuit, ablate_into_matchable_code=True, phenom=False
    )
    constructions["phenom_toric_color_code"] = functools.partial(
        _make_simple_circuit, ablate_into_matchable_code=False, phenom=True
    )
    constructions["phenom_ablated_toric_color_code"] = functools.partial(
        _make_simple_circuit, ablate_into_matchable_code=True, phenom=True
    )

    return constructions
