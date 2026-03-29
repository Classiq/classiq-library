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

from typing import Tuple

import numpy as np
import pygltflib

from gen import PatchOutline
from gen._surf._step_sequence_outline import StepSequenceOutline
from gen._surf._patch_transition_outline import PatchTransitionOutline
from gen._surf._viz_gltf_3d import (
    ColoredTriangleData,
    gltf_model_from_colored_triangle_data,
    ColoredLineData,
)

_X_COLOR = (1, 0, 0, 1)
_Z_COLOR = (0, 0, 1, 1)


def _coords(c: complex, t: float) -> tuple[float, float, float]:
    return c.real, t, c.imag


def _patch_transition_to_floor(
    *,
    trans: PatchTransitionOutline,
    t: float,
    out_triangles: list[ColoredTriangleData],
    out_lines: list[ColoredLineData],
    order: int
):
    for q in trans.data_set:
        for d in range(4):
            a = q + 1j**d
            b = q + 1j**d * 1j
            if a in trans.data_set and b in trans.data_set:
                out_triangles.append(
                    ColoredTriangleData(
                        rgba=_X_COLOR if q in trans.data_x_set else _Z_COLOR,
                        triangle_list=np.array(
                            [
                                _coords(q, t),
                                _coords(a, t),
                                _coords(b, t),
                            ][::order],
                            dtype=np.float32,
                        ),
                    )
                )
    for plane in trans.data_boundary_planes:
        for _, a, c in plane:
            out_lines.append(
                ColoredLineData(
                    rgba=(0, 0, 0, 1),
                    edge_list=np.array(
                        [_coords(a, t), _coords(c, t)], dtype=np.float32
                    ),
                )
            )


def _patch_boundary_to_walls(
    *,
    boundary: PatchOutline,
    t: float,
    dt: float,
    out_triangles: list[ColoredTriangleData],
    out_lines: list[ColoredLineData]
):
    for curve in boundary.region_curves:
        for basis, p1, p2 in curve:
            out_triangles.append(
                ColoredTriangleData.square(
                    rgba=_X_COLOR if basis == "X" else _Z_COLOR,
                    origin=_coords(p1, t),
                    d1=_coords(p2 - p1, 0),
                    d2=_coords(0, dt),
                )
            )
            out_triangles.append(
                ColoredTriangleData.square(
                    rgba=_X_COLOR if basis == "X" else _Z_COLOR,
                    origin=_coords(p1, t),
                    d1=_coords(p2 - p1, 0),
                    d2=_coords(0, dt),
                )
            )
    for pt in boundary.iter_control_points():
        out_lines.append(
            ColoredLineData(
                rgba=(0, 0, 0, 1),
                edge_list=np.array(
                    [_coords(pt, t), _coords(pt, t + dt)], dtype=np.float32
                ),
            )
        )
    for curve in boundary.region_curves:
        for _, a, c in curve:
            for t2 in [t, t + dt]:
                out_lines.append(
                    ColoredLineData(
                        rgba=(0, 0, 0, 1),
                        edge_list=np.array(
                            [_coords(a, t2), _coords(c, t2)], dtype=np.float32
                        ),
                    )
                )


def patch_sequence_to_model(sequence: StepSequenceOutline) -> pygltflib.GLTF2:
    t = 0
    triangles = []
    lines = []
    for segment in sequence.steps:
        _patch_transition_to_floor(
            trans=segment.start,
            t=t + 0.01,
            out_triangles=triangles,
            order=-1,
            out_lines=lines,
        )
        dt = max(1, segment.rounds)
        _patch_boundary_to_walls(
            boundary=segment.body, t=t, dt=dt, out_triangles=triangles, out_lines=lines
        )
        t += dt
        _patch_transition_to_floor(
            trans=segment.end, t=t, out_triangles=triangles, order=+1, out_lines=lines
        )
    return gltf_model_from_colored_triangle_data(triangles, colored_line_data=lines)
