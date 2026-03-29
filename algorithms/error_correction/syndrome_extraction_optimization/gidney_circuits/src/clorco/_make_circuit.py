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
from typing import Union, Callable, Any

import stim

import gen
from clorco._make_circuit_params import Params
from clorco.color2surface_code._keyed_constructions import (
    make_named_color2surface_code_constructions,
)
from clorco.color_code import make_named_color_code_constructions
from clorco.pyramid_code._keyed_constructions import (
    make_named_pyramid_code_constructions,
)
from clorco.surface_code import make_named_surface_code_constructions
from clorco.rep_code import make_named_rep_code_constructions


def _make_constructions() -> dict[str, Callable[[Params], stim.Circuit]]:
    constructions: dict[str, Callable[[Params], stim.Circuit]] = {
        **make_named_color_code_constructions(),
        **make_named_surface_code_constructions(),
        **make_named_rep_code_constructions(),
        **make_named_color2surface_code_constructions(),
        **make_named_pyramid_code_constructions(),
    }
    return constructions


CONSTRUCTIONS = _make_constructions()


def make_circuit(
    *,
    style: str,
    noise_model: gen.NoiseModel | None,
    noise_strength: float,
    rounds: int,
    diameter: int = 0,
    debug_out_dir: Union[None, str, pathlib.Path] = None,
    convert_to_cz: bool = True,
    editable_extras: dict[str, Any],
) -> stim.Circuit:
    if debug_out_dir is not None:
        debug_out_dir = pathlib.Path(debug_out_dir)
        debug_out_dir.mkdir(exist_ok=True, parents=True)

    params = Params(
        style=style,
        rounds=rounds,
        diameter=diameter,
        debug_out_dir=debug_out_dir,
        convert_to_cz=convert_to_cz,
        noise_model=noise_model,
        noise_strength=noise_strength,
        editable_extras=editable_extras,
    )
    construction = CONSTRUCTIONS.get(style)
    if construction is None:
        msg = f"Unrecognized circuit style: {style!r}.\n\nRecognized styles are:"
        for k in sorted(CONSTRUCTIONS.keys()):
            msg += "\n    " + k
        raise NotImplementedError(msg)
    noisy_circuit = construction(params)

    if params.debug_out_dir is not None:
        gen.write_file(params.debug_out_dir / "noisy_circuit.stim", noisy_circuit)
        gen.write_file(
            params.debug_out_dir / "noisy_circuit_dets_ops.svg",
            noisy_circuit.without_noise().diagram("detslice-with-ops-svg"),
        )
        gen.write_file(
            params.debug_out_dir / "noisy_circuit_dets.svg",
            noisy_circuit.without_noise().diagram("detslice-svg"),
        )
        gen.write_file(
            params.debug_out_dir / "noisy_circuit_slice.svg",
            noisy_circuit.diagram("timeslice-svg"),
        )

    return noisy_circuit
