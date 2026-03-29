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
from typing import Union, Optional, Callable, Any, Iterable, Tuple

import stim

import gen
from gen._core import Builder, AtLayer
from gen._surf._closed_curve import ClosedCurve
from gen._surf._order import Order_Z
from gen._surf._patch_outline import PatchOutline
from gen._surf._patch_transition_outline import PatchTransitionOutline
from gen._surf._step_outline import StepOutline
from gen._util import write_file


class StepSequenceOutline:
    def __init__(self, steps: Iterable[StepOutline]):
        self.steps = list(steps)

    def to_circuit(
        self, *, rel_order_func: Callable[[complex], Iterable[complex]]
    ) -> stim.Circuit:
        builder = Builder.for_qubits(...)

        round_index = 0
        cmp_layer = None
        save_layer = 0
        for step in self.steps:
            step.build_rounds(
                builder=builder,
                rel_order_func=rel_order_func,
                alternate_ordering_with_round_parity=True,
                start_round_index=round_index,
                edit_cur_obs=None,
                o2i=None,
                cmp_layer=cmp_layer,
                save_layer=("step_to_circuit", save_layer),
            )
            cmp_layer = save_layer
            round_index += step.rounds

        return builder.circuit

    def write_outlines_svg(self, path: str | pathlib.Path) -> None:
        from gen._surf._viz_patch_outline_svg import patch_outline_svg_viewer

        viewer = patch_outline_svg_viewer(
            [
                piece
                for segment in self.steps
                for piece in [segment.start, segment.body, segment.end]
                if any(piece.iter_control_points())
            ]
        )
        write_file(path, viewer)

    def write_patches_svg(
        self,
        path: str | pathlib.Path,
        *,
        rel_order_func: Callable[[complex], Iterable[complex]] = None,
    ) -> None:
        from gen._viz_patch_svg import patch_svg_viewer

        show_order = True
        if rel_order_func is None:
            rel_order_func = lambda _: Order_Z
            show_order = False
        patches = []
        for k in range(len(self.steps)):
            segment = self.steps[k]
            patch = segment.body.to_patch(rel_order_func=rel_order_func)
            if segment.start.data_set:
                b2 = segment.start.data_basis_map
                tiles = list(segment.start.patch.tiles)
                for t in patch.tiles:
                    if all(
                        b2.get(q, b) == b
                        for q, b in t.to_data_pauli_string().qubits.items()
                    ):
                        tiles.append(t)
                patches.append(gen.Patch(tiles))
            patches.append(patch)
            if segment.end.data_set:
                b2 = segment.end.data_basis_map
                tiles = list(segment.end.patch.tiles)
                for t in patch.tiles:
                    if all(
                        b2.get(q, b) == b
                        for q, b in t.to_data_pauli_string().qubits.items()
                    ):
                        tiles.append(t)
                patches.append(gen.Patch(tiles))
        viewer = patch_svg_viewer(
            patches, show_order=show_order, show_measure_qubits=False
        )
        write_file(path, viewer)

    def write_gltf(self, path: str | pathlib.Path) -> None:
        from gen._surf._viz_sequence_3d import patch_sequence_to_model

        print(f"wrote file://{pathlib.Path(path).absolute()}")
        patch_sequence_to_model(self).save_json(str(path))

    def write_3d_viewer_html(self, path: str | pathlib.Path) -> None:
        from gen._surf._viz_gltf_3d import viz_3d_gltf_model_html
        from gen._surf._viz_sequence_3d import patch_sequence_to_model

        write_file(path, viz_3d_gltf_model_html(patch_sequence_to_model(self)))
