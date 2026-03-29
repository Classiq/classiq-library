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

import math
from typing import Iterable, TYPE_CHECKING, Literal, Union

from gen._core._util import min_max_complex

if TYPE_CHECKING:
    from gen._surf._patch_outline import PatchOutline
    from gen._surf._patch_transition_outline import PatchTransitionOutline


def patch_outline_svg_viewer(
    values: Iterable[Union["PatchOutline", "PatchTransitionOutline"]],
    *,
    other_segments: Iterable[tuple[complex, Literal["X", "Y", "Z"], complex]] = (),
    canvas_height: int = 500,
) -> str:
    """Returns a picture of the stabilizers measured by various plan."""
    from gen._surf._patch_outline import PatchOutline
    from gen._surf._patch_transition_outline import PatchTransitionOutline

    outlines = tuple(values)
    control_points = [
        pt for outline in outlines for pt in outline.iter_control_points()
    ]
    min_c, max_c = min_max_complex(control_points, default=0)
    min_c -= 1 + 1j
    max_c += 1 + 1j
    box_width = max_c.real - min_c.real
    box_height = max_c.imag - min_c.imag
    pad = max(box_width, box_height) * 0.1 + 1
    box_width += pad
    box_height += pad
    columns = math.ceil(math.sqrt(len(outlines)))
    rows = math.ceil(len(outlines) / max(1, columns))
    total_height = max(1.0, box_height * rows - pad)
    total_width = max(1.0, box_width * columns - pad)
    scale_factor = canvas_height / max(total_height, 1)
    canvas_width = int(math.ceil(canvas_height * (total_width / total_height)))
    stroke_width = scale_factor / 25

    def transform_pt(plan_i2: int, pt2: complex) -> complex:
        pt2 += box_width * (plan_i2 % columns)
        pt2 += box_height * (plan_i2 // columns) * 1j
        pt2 += pad * (0.5 + 0.5j)
        pt2 *= scale_factor
        return pt2

    lines = [
        f"""<svg viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">"""
    ]

    BASE_COLORS = {"X": "#FF0000", "Z": "#0000FF", "Y": "#00FF00", None: "gray"}
    OBS_COLORS = {"X": "#800000", "Z": "#000080", "Y": "#008000", None: "black"}

    lines.append(
        f'<rect fill="{BASE_COLORS["X"]}" x="1" y="1" width="20" height="20" />'
    )
    lines.append(
        "<text"
        ' x="11"'
        ' y="11"'
        ' fill="white"'
        ' font-size="20"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        ">X</text>"
    )

    lines.append(
        f'<rect fill="{BASE_COLORS["Y"]}" x="1" y="21" width="20" height="20" />'
    )
    lines.append(
        "<text"
        ' x="11"'
        ' y="31"'
        ' fill="white"'
        ' font-size="20"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        ">Y</text>"
    )

    lines.append(
        f'<rect fill="{BASE_COLORS["Z"]}" x="1" y="41" width="20" height="20" />'
    )
    lines.append(
        "<text"
        ' x="11"'
        ' y="51"'
        ' fill="white"'
        ' font-size="20"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        ">Z</text>"
    )

    # Draw interior.
    for outline_index, outline in enumerate(outlines):
        pieces = []
        if isinstance(outline, PatchOutline):
            for curve in outline.region_curves:
                pieces.append("M")
                for k in range(len(curve)):
                    a = transform_pt(outline_index, curve.points[k])
                    pieces.append(f"{a.real},{a.imag}")
            pieces.append("Z")
            path = " ".join(pieces)
            lines.append(f'<path d="{path}" fill="#ddd" stroke="none"/>')
        elif isinstance(outline, PatchTransitionOutline):
            fill_color = "#000"
            for curve in outline.data_boundary_planes:
                fill_color = BASE_COLORS[curve.basis]
                pieces.append("M")
                for k in range(len(curve)):
                    a = transform_pt(outline_index, curve.points[k])
                    pieces.append(f"{a.real},{a.imag}")
            pieces.append("Z")
            path = " ".join(pieces)
            lines.append(f'<path d="{path}" fill="{fill_color}" stroke="none"/>')
        else:
            raise NotImplementedError(f"{outline=}")

    # Trace boundaries.
    for outline_index, outline in enumerate(outlines):
        if isinstance(outline, PatchOutline):
            for curve in outline.region_curves:
                for k in range(len(curve)):
                    a = transform_pt(outline_index, curve.points[k - 1])
                    b = transform_pt(outline_index, curve.points[k])
                    stroke_color = BASE_COLORS[curve.bases[k]]
                    lines.append(
                        f"<line "
                        f'x1="{a.real}" '
                        f'y1="{a.imag}" '
                        f'x2="{b.real}" '
                        f'y2="{b.imag}" '
                        f'stroke-width="{stroke_width * 8}" '
                        f'stroke="{stroke_color}" />'
                    )
            for k, obs_pair in enumerate(outline.observables):
                k -= len(outline.observables) / 2
                for basis, obs in obs_pair:
                    for a, b, _basis in obs.segments:
                        a = transform_pt(outline_index, a)
                        b = transform_pt(outline_index, b)
                        stroke_color = OBS_COLORS[basis]
                        lines.append(
                            f"<line "
                            f'x1="{a.real + 0.01*k*scale_factor}" '
                            f'y1="{a.imag + 0.01*k*scale_factor}" '
                            f'x2="{b.real + 0.01*k*scale_factor}" '
                            f'y2="{b.imag + 0.01*k*scale_factor}" '
                            f'stroke-width="{stroke_width * 3}" '
                            f'stroke-dasharray="0 1 0" '
                            f'stroke="{stroke_color}" />'
                        )
            for a, basis, b in other_segments:
                a = transform_pt(outline_index, a)
                b = transform_pt(outline_index, b)
                stroke_color = OBS_COLORS[basis]
                lines.append(
                    f"<line "
                    f'x1="{a.real}" '
                    f'y1="{a.imag}" '
                    f'x2="{b.real}" '
                    f'y2="{b.imag}" '
                    f'stroke-width="{stroke_width * 20}" '
                    f'stroke-dasharray="0 1 0" '
                    f'stroke="{stroke_color}" />'
                )

    # Trace control points.
    for outline_index, outline in enumerate(outlines):
        for pt in outline.iter_control_points():
            a = transform_pt(outline_index, pt)
            lines.append(
                f"<circle "
                f'cx="{a.real}" '
                f'cy="{a.imag}" '
                f'r="{stroke_width * 5}" '
                f'stroke-width="{stroke_width}" '
                f'fill="black" '
                f'stroke="black" />'
            )

    # Frames
    for outline_index, outline in enumerate(outlines):
        a = transform_pt(outline_index, min_c)
        b = transform_pt(outline_index, max_c)
        lines.append(
            f'<rect fill="none" stroke="#999" x="{a.real}" y="{a.imag}" width="{(b - a).real}" height="{(b - a).imag}" />'
        )

    lines.append("</svg>")
    return "\n".join(lines)
