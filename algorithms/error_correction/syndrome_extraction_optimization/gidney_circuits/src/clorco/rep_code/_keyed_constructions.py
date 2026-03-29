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
from typing import Callable

import stim

import gen
from clorco._make_circuit_params import Params
from clorco.rep_code._rep_code_circuits import make_rep_code_circuit
from clorco.rep_code._rep_code_layouts import make_rep_code_layout


def make_named_rep_code_constructions() -> dict[str, Callable[[Params], stim.Circuit]]:
    constructions: dict[str, Callable[[Params], stim.Circuit]] = {
        **_simplified_noise_rep_code_constructions(),
    }

    for coloring in ["r", "rg", "rbrrr"]:
        for toric in [False, True]:
            prefix = ""
            if toric:
                prefix += "toric_"
            suffix = "" if coloring == "r" else f"_{coloring}"
            constructions[f"{prefix}rep_code{suffix}"] = functools.partial(
                _make_circuit, coloring=coloring, toric=toric
            )

    return constructions


def _make_circuit(
    params: Params,
    *,
    coloring: str,
    toric: bool,
) -> stim.Circuit:
    round_colorings = []
    for k in range(len(coloring)):
        round_colorings.append((coloring * 2)[k : k + len(coloring)])
    circuit = make_rep_code_circuit(
        distance=params.diameter,
        toric=toric,
        rounds=params.rounds,
        round_colorings=round_colorings,
    )

    if params.debug_out_dir is not None:
        code = make_rep_code_layout(distance=params.diameter, toric=toric)
        code.write_svg(params.debug_out_dir / "code.svg")
        gen.write_file(
            params.debug_out_dir / "ideal_circuit.html",
            gen.stim_circuit_html_viewer(
                circuit,
                patch=code.patch,
            ),
        )
        gen.write_file(params.debug_out_dir / "ideal_circuit.stim", circuit)
        gen.write_file(
            params.debug_out_dir / "ideal_circuit_dets.svg",
            circuit.diagram("time+detector-slice-svg"),
        )

    if params.convert_to_cz:
        circuit = gen.transpile_to_z_basis_interaction_circuit(circuit)
    if params.noise_model is not None:
        circuit = params.noise_model.noisy_circuit(circuit)

    if params.debug_out_dir is not None:
        code = make_rep_code_layout(distance=params.diameter, toric=toric)
        gen.write_file(
            params.debug_out_dir / "circuit.html",
            gen.stim_circuit_html_viewer(
                circuit,
                patch=code.patch,
            ),
        )
        gen.write_file(params.debug_out_dir / "circuit.stim", circuit)
        gen.write_file(
            params.debug_out_dir / "circuit_dets.svg",
            circuit.diagram("time+detector-slice-svg"),
        )

    return circuit


def _simplified_noise_rep_code_constructions() -> (
    dict[str, Callable[[Params], stim.Circuit]]
):
    constructions: dict[str, Callable[[Params], stim.Circuit]] = {}

    def _make_simple_circuit(
        params: Params,
        *,
        coloring: str,
        toric: bool,
        phenom: bool,
    ) -> stim.Circuit:
        code = make_rep_code_layout(
            distance=params.diameter,
            coloring=coloring,
            toric=toric,
        )
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

    for coloring in ["r", "rg", "rbrrr"]:
        for toric in [False, True]:
            for phenom in [False, True]:
                prefix = "phenom_" if phenom else "transit_"
                if toric:
                    prefix += "toric_"
                suffix = "" if coloring == "r" else f"_{coloring}"
                constructions[f"{prefix}rep_code{suffix}"] = functools.partial(
                    _make_simple_circuit, coloring=coloring, toric=toric, phenom=phenom
                )

    return constructions
