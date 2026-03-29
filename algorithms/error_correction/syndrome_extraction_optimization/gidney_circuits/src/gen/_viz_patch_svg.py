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
from typing import Iterable, Union, Literal, TYPE_CHECKING, Sequence, Callable

from gen._core._patch import Patch, Tile
from gen._core._util import min_max_complex

if TYPE_CHECKING:
    import gen


def is_colinear(a: complex, b: complex, c: complex) -> bool:
    d1 = b - a
    d2 = c - a
    return abs(d1.real * d2.imag - d2.real * d1.imag) < 1e-4


def _path_commands_for_points_with_one_point(
    *,
    a: complex,
    draw_coord: Callable[[complex], complex],
    draw_radius: float | None = None,
):
    draw_a = draw_coord(a)
    if draw_radius is None:
        draw_radius = abs(draw_coord(0.2) - draw_coord(0))
    r = draw_radius
    left = draw_a - draw_radius
    return [
        f"""M {left.real},{left.imag}""",
        f"""a {r},{r} 0 0,0 {2*r},{0}""",
        f"""a {r},{r} 0 0,0 {-2*r},{0}""",
    ]


def _path_commands_for_points_with_two_points(
    *,
    a: complex,
    b: complex,
    hint_point: complex,
    draw_coord: Callable[[complex], complex],
) -> list[str]:
    def transform_dif(d: complex) -> complex:
        return draw_coord(d) - draw_coord(0)

    da = a - hint_point
    db = b - hint_point
    angle = math.atan2(da.imag, da.real) - math.atan2(db.imag, db.real)
    angle %= math.pi * 2
    if angle < math.pi:
        a, b = b, a

    if abs(abs(da) - abs(db)) < 1e-4 < abs(da + db):
        # Semi-circle oriented towards measure qubit.
        draw_a = draw_coord(a)
        draw_ba = transform_dif(b - a)
        return [
            f"""M {draw_a.real},{draw_a.imag}""",
            f"""a 1,1 0 0,0 {draw_ba.real},{draw_ba.imag}""",
            f"""L {draw_a.real},{draw_a.imag}""",
        ]
    else:
        # A wedge between the two data qubits.
        dif = b - a
        average = (a + b) * 0.5
        perp = dif * 1j
        if abs(perp) > 1:
            perp /= abs(perp)
        ac1 = average + perp * 0.2 - dif * 0.2
        ac2 = average + perp * 0.2 + dif * 0.2
        bc1 = average + perp * -0.2 + dif * 0.2
        bc2 = average + perp * -0.2 - dif * 0.2

        tac1 = draw_coord(ac1)
        tac2 = draw_coord(ac2)
        tbc1 = draw_coord(bc1)
        tbc2 = draw_coord(bc2)
        draw_a = draw_coord(a)
        draw_b = draw_coord(b)
        return [
            f"M {draw_a.real},{draw_a.imag}",
            f"C {tac1.real} {tac1.imag}, {tac2.real} {tac2.imag}, {draw_b.real} {draw_b.imag}",
            f"C {tbc1.real} {tbc1.imag}, {tbc2.real} {tbc2.imag}, {draw_a.real} {draw_a.imag}",
        ]


def _path_commands_for_points_with_many_points(
    *,
    pts: Sequence[complex],
    draw_coord: Callable[[complex], complex],
) -> list[str]:
    assert len(pts) >= 3
    ori = draw_coord(pts[-1])
    path_commands = [f"""M{ori.real},{ori.imag}"""]
    for k in range(len(pts)):
        prev_prev_q = pts[k - 2]
        prev_q = pts[k - 1]
        q = pts[k]
        next_q = pts[(k + 1) % len(pts)]
        if is_colinear(prev_q, q, next_q) or is_colinear(prev_prev_q, prev_q, q):
            prev_pt = draw_coord(prev_q)
            cur_pt = draw_coord(q)
            d = cur_pt - prev_pt
            p1 = prev_pt + d * (-0.25 + 0.05j)
            p2 = cur_pt + d * (0.25 + 0.05j)
            path_commands.append(
                f"""C {p1.real} {p1.imag}, {p2.real} {p2.imag}, {cur_pt.real} {cur_pt.imag}"""
            )
        else:
            q2 = draw_coord(q)
            path_commands.append(f"""L {q2.real},{q2.imag}""")
    return path_commands


def svg_path_directions_for_tile(
    *, tile: "gen.Tile", draw_coord: Callable[[complex], complex]
) -> str | None:
    hint_point = tile.measurement_qubit
    if any(abs(q - hint_point) < 1e-4 for q in tile.data_set):
        hint_point = sum(tile.data_set) / len(tile.data_set)

    points = sorted(
        tile.data_set,
        key=lambda p2: math.atan2(p2.imag - hint_point.imag, p2.real - hint_point.real),
    )

    if len(points) == 0:
        return None

    if len(points) == 1:
        return " ".join(
            _path_commands_for_points_with_one_point(
                a=points[0],
                draw_coord=draw_coord,
            )
        )

    if len(points) == 2:
        return " ".join(
            _path_commands_for_points_with_two_points(
                a=points[0],
                b=points[1],
                hint_point=hint_point,
                draw_coord=draw_coord,
            )
        )

    return " ".join(
        _path_commands_for_points_with_many_points(
            pts=points,
            draw_coord=draw_coord,
        )
    )


BASE_COLORS = {"X": "#FF8080", "Z": "#8080FF", "Y": "#80FF80", None: "gray"}


def _data_span_sort(tile: "gen.Tile") -> float:
    min_c, max_c = min_max_complex(tile.data_set, default=0)
    return max_c.real - min_c.real + max_c.imag - min_c.imag


def _patch_svg_viewer_helper_single_patch_wraparound_clip(
    *,
    patch: Patch,
    transform_pt: Callable[[complex], complex],
    out_lines: list[str],
    show_order: str,
    opacity: float,
    show_data_qubits: bool,
    show_measure_qubits: bool,
    available_qubits: frozenset[complex],
    extra_used_coords: frozenset[complex],
    clip_path_id_ptr: list[int],
):
    if len(patch.without_wraparound_tiles().tiles) == len(patch.tiles):
        _patch_svg_viewer_helper_single_patch(
            patch=patch,
            transform_pt=transform_pt,
            out_lines=out_lines,
            show_order=show_order,
            opacity=opacity,
            show_data_qubits=show_data_qubits,
            show_measure_qubits=show_measure_qubits,
            clip_path_id_ptr=clip_path_id_ptr,
            available_qubits=available_qubits,
            extra_used_coords=extra_used_coords,
        )
        return

    p_min, p_max = min_max_complex(patch.data_set, default=0)
    w = p_max.real - p_min.real
    h = p_max.imag - p_min.imag
    left = p_min.real + w * 0.1
    right = p_min.real + w * 0.9
    top = p_min.imag + h * 0.1
    bot = p_min.imag + h * 0.9
    pad_w = 1
    pad_h = 1
    pad_shift = -pad_w - 1j * pad_h
    pad_shift /= 2
    w += pad_w
    h += pad_h

    def new_transform(q: complex) -> complex:
        q -= p_min
        q /= (p_max - p_min).real
        q *= w
        q += p_min
        return transform_pt(q)

    def is_normal_tile(tile: Tile) -> bool:
        t_min, t_max = min_max_complex(tile.data_set, default=0)
        if t_min.real < left and t_max.real > right:
            return False
        if t_min.imag < top and t_max.imag > bot:
            return False
        return True

    def unwraparound(tile: Tile):
        t_min, t_max = min_max_complex(tile.data_set, default=0)
        dw = w
        dh = h
        if not (t_min.real < left and t_max.real > right):
            dw = 0
        if not (t_min.imag < top and t_max.imag > bot):
            dh = 0

        def trans(q: complex) -> complex:
            if q.real < w / 2:
                q += dw
            if q.imag < h / 2:
                q += dh * 1j
            return q

        return trans

    new_tiles = []
    for tile in patch.tiles:
        if is_normal_tile(tile):
            new_tiles.append(tile)
            continue
        new_tile_1 = tile.with_transformed_coords(unwraparound(tile))
        new_tile_2 = new_tile_1.with_transformed_coords(lambda q: q - w)
        new_tile_3 = new_tile_1.with_transformed_coords(lambda q: q - h * 1j)
        new_tile_4 = new_tile_1.with_transformed_coords(lambda q: q - w - h * 1j)
        new_tiles.append(new_tile_1)
        new_tiles.append(new_tile_2)
        new_tiles.append(new_tile_3)
        new_tiles.append(new_tile_4)

    clip_ip = clip_path_id_ptr[0]
    clip_path_id_ptr[0] += 1
    out_lines.append(f"""<clipPath id="clipPath{clip_ip}">""")
    tl = transform_pt(p_min)
    br = transform_pt(p_max)
    out_lines.append(
        f"""    <path d="M{tl.real},{tl.imag} L{br.real},{tl.imag} L{br.real},{br.imag} L{tl.real},{br.imag} Z" />"""
    )
    out_lines.append(f"""</clipPath>""")
    _patch_svg_viewer_helper_single_patch(
        patch=Patch(new_tiles).with_transformed_coords(lambda q: q + pad_shift),
        transform_pt=new_transform,
        out_lines=out_lines,
        show_order=show_order,
        opacity=opacity,
        show_data_qubits=show_data_qubits,
        show_measure_qubits=show_measure_qubits,
        clip_path_id_ptr=clip_path_id_ptr,
        available_qubits=frozenset([q + pad_shift for q in available_qubits]),
        extra_used_coords=frozenset([q + pad_shift for q in extra_used_coords]),
        extra_clip_path_arg=f'clip-path="url(#clipPath{clip_ip})" ',
    )


def _patch_svg_viewer_helper_single_patch(
    *,
    patch: Patch,
    transform_pt: Callable[[complex], complex],
    out_lines: list[str],
    show_order: str,
    opacity: float,
    show_data_qubits: bool,
    show_measure_qubits: bool,
    clip_path_id_ptr: list[int],
    available_qubits: frozenset[complex],
    extra_used_coords: frozenset[complex],
    extra_clip_path_arg: str = "",
):
    layer_1q2 = []
    layer_1q = []
    fill_layer2q = []
    stroke_layer2q = []
    fill_layer_mq = []
    stroke_layer_mq = []
    stroke_width = abs(transform_pt(0.02) - transform_pt(0))

    sorted_tiles = sorted(patch.tiles, key=_data_span_sort, reverse=True)
    for tile in sorted_tiles:
        c = tile.measurement_qubit
        if any(abs(q - c) < 1e-4 for q in tile.data_set):
            c = sum(tile.data_set) / len(tile.data_set)
        dq = sorted(
            tile.data_set,
            key=lambda p2: math.atan2(p2.imag - c.imag, p2.real - c.real),
        )
        if not dq:
            continue
        common_basis = tile.basis
        fill_color = BASE_COLORS[common_basis]

        path_directions = svg_path_directions_for_tile(
            tile=tile,
            draw_coord=transform_pt,
        )
        path_cmd_start = None
        if path_directions is not None:
            if len(tile.data_set) == 1:
                fl = layer_1q
                sl = layer_1q2
            elif len(tile.data_set) == 2:
                fl = fill_layer2q
                sl = stroke_layer2q
            else:
                fl = fill_layer_mq
                sl = stroke_layer_mq
            fl.append(
                f'''<path d="{path_directions}"'''
                f''' fill="{fill_color}"'''
                f''' opacity="{opacity}"'''
                f''' stroke="none"'''
                f""" stroke-width="{stroke_width}" """
                f""" {extra_clip_path_arg} """
                f""" />"""
            )

            # # Draw lines from data qubits to measurement qubit.
            # for d in tile.data_set:
            #     pd = transform_pt(d)
            #     pc = transform_pt(c)
            #     sl.append(
            #         f'''<path d="M {pd.real},{pd.imag} L {pc.real},{pc.imag}"'''
            #         f''' fill="none"'''
            #         f''' stroke="black"'''
            #         f""" stroke-width="{stroke_width}" """
            #         f""" />"""
            #     )

            if show_order != "undirected":
                sl.append(
                    f'''<path d="{path_directions}"'''
                    f''' fill="none"'''
                    f''' stroke="black"'''
                    f""" stroke-width="{stroke_width}" """
                    f""" {extra_clip_path_arg} """
                    f""" />"""
                )
        else:
            cur_pt = transform_pt(dq[-1])
            path_cmd_start = f'<path d="M{cur_pt.real},{cur_pt.imag}'
            for k in range(len(dq)):
                prev_prev_q = dq[k - 2]
                prev_q = dq[k - 1]
                q = dq[k]
                next_q = dq[(k + 1) % len(dq)]
                if is_colinear(prev_q, q, next_q) or is_colinear(
                    prev_prev_q, prev_q, q
                ):
                    prev_pt = transform_pt(prev_q)
                    cur_pt = transform_pt(q)
                    d = cur_pt - prev_pt
                    p1 = prev_pt + d * (-0.25 + 0.05j)
                    p2 = cur_pt + d * (0.25 + 0.05j)
                    path_cmd_start += f" C {p1.real} {p1.imag}, {p2.real} {p2.imag}, {cur_pt.real} {cur_pt.imag}"
                else:
                    cur_pt = transform_pt(q)
                    path_cmd_start += f" L {cur_pt.real},{cur_pt.imag}"
            path_cmd_start += '"'
            fill_layer_mq.append(
                f'{path_cmd_start} fill="{fill_color}" opacity="{opacity}" stroke="none" />'
            )
            if show_order != "undirected":
                stroke_layer_mq.append(
                    f"{path_cmd_start} "
                    f'stroke-width="{stroke_width}" '
                    f'stroke="black" '
                    f""" {extra_clip_path_arg} """
                    f'fill="none" />'
                )

        if show_measure_qubits:
            m = tile.measurement_qubit
            if show_order == "undirected":
                m = m * 0.8 + c * 0.2
            p = transform_pt(m)
            layer_1q2.append(
                f"<circle "
                f'cx="{p.real}" '
                f'cy="{p.imag}" '
                f'r="{abs(transform_pt(0.1) - transform_pt(0))}" '
                f'fill="black" '
                f'stroke-width="{stroke_width}" '
                f""" {extra_clip_path_arg} """
                f"""stroke="{'black' if show_order != 'undirected' else 'none'}" />"""
            )
        if show_data_qubits:
            for d in tile.data_set:
                p = transform_pt(d)
                layer_1q2.append(
                    f"<circle "
                    f'cx="{p.real}" '
                    f'cy="{p.imag}" '
                    f'r="{abs(transform_pt(0.1) - transform_pt(0))}" '
                    f'fill="black" '
                    f'stroke-width="{stroke_width}" '
                    f""" {extra_clip_path_arg} """
                    f"""stroke="{'black' if show_order != 'undirected' else 'none'}" />"""
                )

        if common_basis is None and path_cmd_start is not None:
            clip_path_id_ptr[0] += 1
            fill_layer_mq.append(f'<clipPath id="clipPath{clip_path_id_ptr[0]}">')
            fill_layer_mq.append(f"    {path_cmd_start} />")
            fill_layer_mq.append(f"</clipPath>")
            for k, q in enumerate(tile.ordered_data_qubits):
                if q is None:
                    continue
                v = transform_pt(q)
                fill_layer_mq.append(
                    f"<circle "
                    f'clip-path="url(#clipPath{clip_path_id_ptr[0]})" '
                    f'cx="{v.real}" '
                    f'cy="{v.imag}" '
                    f'r="{abs(transform_pt(0.45) - transform_pt(0))}" '
                    f'fill="{BASE_COLORS[tile.bases[k]]}" '
                    f""" {extra_clip_path_arg} """
                    f'stroke="none" />'
                )
    out_lines.extend(fill_layer_mq)
    out_lines.extend(stroke_layer_mq)
    out_lines.extend(fill_layer2q)
    out_lines.extend(stroke_layer2q)
    out_lines.extend(layer_1q)
    out_lines.extend(layer_1q2)

    if available_qubits | extra_used_coords:
        for q in available_qubits | (patch.used_set | extra_used_coords):
            fill_color = "black" if q in available_qubits else "orange"
            if (
                not show_measure_qubits
                and not q in available_qubits
                and q in patch.measure_set
            ):
                continue
            q2 = transform_pt(q)
            out_lines.append(
                f"<circle"
                f' cx="{q2.real}"'
                f' cy="{q2.imag}"'
                f' fill="{fill_color}"'
                f' stroke-width="{stroke_width}" '
                f' stroke="white"'
                f""" {extra_clip_path_arg} """
                f' r="{abs(transform_pt(0.05) - transform_pt(0))}"'
                f"/>"
            )


def patch_svg_viewer(
    patches: Iterable[Patch],
    *,
    canvas_height: int = 500,
    show_order: Union[bool, Literal["undirected", "3couplerspecial"]] = True,
    opacity: float = 1,
    show_measure_qubits: bool = True,
    show_data_qubits: bool = False,
    available_qubits: Iterable[complex] = (),
    extra_used_coords: Iterable[complex] = (),
    wraparound_clip: bool = False,
) -> str:
    """Returns a picture of the stabilizers measured by various plan."""

    available_qubits = frozenset(available_qubits)
    extra_used_coords = frozenset(extra_used_coords)
    patches = tuple(patches)
    min_c, max_c = min_max_complex(
        [
            q
            for plan in patches
            for q in plan.used_set | available_qubits | extra_used_coords
        ],
        default=0,
    )
    min_c -= 1 + 1j
    max_c += 1 + 1j
    box_width = max_c.real - min_c.real
    box_height = max_c.imag - min_c.imag
    pad = max(box_width, box_height) * 0.1 + 1
    box_width += pad
    box_height += pad
    columns = math.ceil(math.sqrt(len(patches) + 2))
    rows = math.ceil(len(patches) / max(1, columns))
    total_height = max(1.0, box_height * rows - pad)
    total_width = max(1.0, box_width * columns + 1)
    scale_factor = canvas_height / max(total_height + 1, 1)
    canvas_width = int(math.ceil(canvas_height * (total_width / total_height)))

    def transform_pt(plan_i2: int, pt2: complex) -> complex:
        pt2 += box_width * (plan_i2 % columns)
        pt2 += box_height * (plan_i2 // columns) * 1j
        pt2 += pad * (0.5 + 0.5j)
        pt2 += pad
        pt2 -= min_c + 1 + 1j
        pt2 *= scale_factor
        return pt2

    def transform_dif(dif: complex) -> complex:
        return dif * scale_factor

    def pt(plan_i2: int, q2: complex) -> str:
        return f"{transform_pt(plan_i2, q2).real},{transform_pt(plan_i2, q2).imag}"

    lines = [
        f"""<svg viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">"""
    ]

    # Draw each plan element as a polygon.
    clip_path_id_ptr = [0]

    lines.append(
        f'<rect fill="{BASE_COLORS["X"]}" x="1" y="1" width="20" height="20" />'
    )
    lines.append(
        "<text"
        ' x="11"'
        ' y="11"'
        ' fill="white"'
        f' font-size="{20}"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        ">X</text>"
    )

    lines.append(
        f'<rect fill="{BASE_COLORS["Z"]}" x="1" y="21" width="20" height="20" />'
    )
    lines.append(
        "<text"
        ' x="11"'
        ' y="31"'
        ' fill="white"'
        ' font-size="20"'
        ' text-anchor="middle"'
        ' alignment-baseline="central"'
        ">Z</text>"
    )

    helper = (
        _patch_svg_viewer_helper_single_patch_wraparound_clip
        if wraparound_clip
        else _patch_svg_viewer_helper_single_patch
    )
    for plan_i, patch in enumerate(patches):
        helper(
            patch=patch,
            transform_pt=lambda q: transform_pt(plan_i, q),
            out_lines=lines,
            show_order=show_order,
            opacity=opacity,
            show_data_qubits=show_data_qubits,
            show_measure_qubits=show_measure_qubits,
            clip_path_id_ptr=clip_path_id_ptr,
            available_qubits=available_qubits,
            extra_used_coords=extra_used_coords,
        )

    stroke_width = abs(transform_pt(0, 0.02) - transform_pt(0, 0))

    # Draw each element's measurement order as a zig zag arrow.
    assert show_order in [False, True, "3couplerspecial", "undirected"]
    if show_order:
        for plan_i, plan in enumerate(patches):
            for tile in plan.tiles:
                c = tile.measurement_qubit
                if len(tile.data_set) == 3 or c in tile.data_set:
                    c = 0
                    for q in tile.data_set:
                        c += q
                    c /= len(tile.data_set)
                pts: list[complex] = []

                path_cmd_start = f'<path d="M'
                arrow_color = "black"
                delay = 0
                prev = None
                for q in tile.ordered_data_qubits:
                    if q is not None:
                        f = 0.6 if show_order != "undirected" else 0.8
                        v = q * f + c * (1 - f)
                        path_cmd_start += pt(plan_i, v) + " "
                        v = transform_pt(plan_i, v)
                        pts.append(v)
                        for d in range(delay):
                            if prev is None:
                                prev = v
                            v2 = (prev + v) / 2
                            lines.append(
                                f'<circle cx="{v2.real}" cy="{v2.imag}" r="{transform_dif(d * 0.06 + 0.04).real}" '
                                f'stroke-width="{stroke_width}" '
                                f'stroke="yellow" '
                                f'fill="none" />'
                            )
                        delay = 0
                        prev = v
                    else:
                        delay += 1
                path_cmd_start = path_cmd_start.strip()
                path_cmd_start += (
                    f'" fill="none" '
                    f'stroke-width="{stroke_width}" '
                    f'stroke="{arrow_color}" />'
                )
                lines.append(path_cmd_start)

                # Draw arrow at end of arrow.
                if show_order is True and len(pts) > 1:
                    p = pts[-1]
                    d2 = p - pts[-2]
                    if d2:
                        d2 /= abs(d2)
                        d2 *= 4 * stroke_width
                    a = p + d2
                    b = p + d2 * 1j
                    c = p + d2 * -1j
                    lines.append(
                        f"<path"
                        f' d="M{a.real},{a.imag} {b.real},{b.imag} {c.real},{c.imag} {a.real},{a.imag}"'
                        f' stroke="none"'
                        f' fill="{arrow_color}" />'
                    )
                if show_order == "3couplerspecial" and len(pts) > 2:
                    # Show location of measurement qubit.
                    p = transform_pt(
                        plan_i, tile.ordered_data_qubits[-2] * 0.6 + c * 0.4
                    )
                    lines.append(
                        f"<circle "
                        f'cx="{p.real}" '
                        f'cy="{p.imag}" '
                        f'r="{transform_dif(0.02).real}" '
                        f'fill="black" '
                        f'stroke-width="{stroke_width}" '
                        f'stroke="black" />'
                    )

    # Frames
    for outline_index, outline in enumerate(patches):
        if wraparound_clip and len(outline.without_wraparound_tiles().tiles) < len(
            outline.tiles
        ):
            p_min, p_max = min_max_complex(outline.data_set, default=0)
            a = transform_pt(outline_index, p_min)
            b = transform_pt(outline_index, p_max)
        else:
            a = transform_pt(outline_index, min_c + 0.1j + 0.1)
            b = transform_pt(outline_index, max_c - 0.1j - 0.1)
        lines.append(
            f'<rect fill="none" stroke="#999" x="{a.real}" y="{a.imag}" width="{(b - a).real}" height="{(b - a).imag}" />'
        )

    lines.append("</svg>")
    return "\n".join(lines)
