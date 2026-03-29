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

import collections
import itertools
from typing import Callable

import gen


BASIS_COLORS = {
    "X": "#FF8080",
    "Z": "#8080FF",
    "Y": "#80FF80",
    "notX": "#00FFFF",
    "notY": "#FF00FF",
    "notZ": "#FFFF00",
    None: "gray",
}
BASIS_COLORS_DARKER = {
    "X": "#BB0000",
    "Z": "#0000BB",
    "Y": "#0BBF00",
    "notX": "#00BBBB",
    "notY": "#BB00BB",
    "notZ": "#BBBB00",
}


def _draw_tile_polygon(
    tile: gen.Tile,
    draw_coord: Callable[[complex], complex],
    out_svg: list[str],
):
    stroke_width = abs(draw_coord(0.03) - draw_coord(0))
    common_basis = tile.basis
    fill_color = BASIS_COLORS[common_basis]
    path_dirs = gen.svg_path_directions_for_tile(
        tile=tile,
        draw_coord=draw_coord,
    )
    if path_dirs is not None:
        out_svg.append(
            f'''    <path d="{path_dirs}"'''
            f''' fill="{fill_color}"'''
            f''' stroke="black"'''
            f''' stroke-width="{stroke_width}"'''
            f""" />"""
        )


def code_capacity_mobius_graph_svg(patch: gen.Patch) -> str:
    min_c, max_c = gen.min_max_complex(patch.used_set)
    min_c -= 1 + 1j
    max_c += 1 + 1j
    d_c = max_c - min_c
    w = d_c.real
    h = d_c.imag
    w *= 2
    s = 1000 / max(w, h, 1)
    w *= s
    h *= s

    def draw_coord_x(c: complex) -> complex:
        c -= min_c
        c *= s
        return c

    def draw_coord_z(c: complex) -> complex:
        c -= min_c
        c *= s
        c += w / 2
        return c

    lines = [f"""<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">"""]

    rgb_patch_x = gen.Patch(
        [
            gen.Tile(
                bases="XYZ"[int(tile.extra_coords[0]) % 3],
                measurement_qubit=tile.measurement_qubit,
                ordered_data_qubits=tile.ordered_data_qubits,
            )
            for tile in patch.tiles
            if tile.extra_coords[0] // 3 == 0
        ]
    )

    rgb_patch_z = gen.Patch(
        [
            gen.Tile(
                bases="XYZ"[int(tile.extra_coords[0]) % 3],
                measurement_qubit=tile.measurement_qubit,
                ordered_data_qubits=tile.ordered_data_qubits,
            )
            for tile in patch.tiles
            if tile.extra_coords[0] // 3 == 1
        ]
    )

    code_capacity_mobius_graph_helper_piece(
        rgb_patch=rgb_patch_x,
        draw_coord=draw_coord_x,
        lines=lines,
    )
    code_capacity_mobius_graph_helper_piece(
        rgb_patch=rgb_patch_z,
        draw_coord=draw_coord_z,
        lines=lines,
    )

    lines.append("</svg>")
    return "\n".join(lines)


def code_capacity_mobius_graph_helper_piece(
    *, rgb_patch: gen.Patch, draw_coord: Callable[[complex], complex], lines: list[str]
):
    for tile in rgb_patch.tiles:
        _draw_tile_polygon(tile=tile, draw_coord=draw_coord, out_svg=lines)

    # Map tile+subgraph to draw coordinates for the node.
    t2d = {}
    for tile in rgb_patch.tiles:
        center = sum(tile.data_set) / len(tile.data_set)
        if len(tile.data_set) == 2:
            center = sum(tile.used_set) / len(tile.used_set)
        na = draw_coord(center + 0.4 - 0.1j)
        nb = draw_coord(center - 0.4 - 0.1j)
        nc = draw_coord(center + 0.4j)
        if tile.basis != "X":
            t2d[(tile, "notX")] = na
        if tile.basis != "Y":
            t2d[(tile, "notY")] = nb
        if tile.basis != "Z":
            t2d[(tile, "notZ")] = nc

    stroke_width = abs(draw_coord(0.03) - draw_coord(0))

    # Index tiles by their data qubits.
    q2t = collections.defaultdict(list)
    for tile in rgb_patch.tiles:
        for q in tile.data_set:
            q2t[q].append(tile)

    # Draw edges.
    for q, tiles in q2t.items():
        if len(tiles) == 1:
            # Draw boundary edge.
            for c1 in ["notX", "notY", "notZ"]:
                for c2 in ["notX", "notY", "notZ"]:
                    a = t2d.get((tiles[0], c1))
                    b = t2d.get((tiles[0], c2))
                    if a is not None and b is not None:
                        lines.append(
                            f"""<path d="M {a.real},{a.imag} L {b.real},{b.imag}" stroke="black" stroke-width="{stroke_width*5}" />"""
                        )

        used = set()

        # Draw bulk edges.
        for tile1, tile2 in itertools.combinations(tiles, 2):
            for c in ["notX", "notY", "notZ"]:
                a = t2d.get((tile1, c))
                b = t2d.get((tile2, c))
                if a is not None and b is not None:
                    lines.append(
                        f"""<path d="M {a.real},{a.imag} L {b.real},{b.imag}" stroke="{BASIS_COLORS_DARKER[c]}" stroke-width="{stroke_width*3}" />"""
                    )
                    used.add(c)

        # Draw boundary edges.
        if len(tiles) == 2:
            tile1, tile2 = tiles
            for c1 in ["notX", "notY", "notZ"]:
                for c2 in ["notX", "notY", "notZ"]:
                    if c1 not in used and c2 not in used:
                        a = t2d.get((tile1, c1))
                        b = t2d.get((tile2, c2))
                        if a is not None and b is not None:
                            if c1 == c2:
                                rem = c1
                            else:
                                (rem,) = {"notX", "notY", "notZ"} - {c1, c2}
                            rem = rem[3:]
                            center1 = sum(tile1.data_set) / len(tile1.data_set)
                            center2 = sum(tile2.data_set) / len(tile2.data_set)
                            p2 = draw_coord(q)
                            p2 = p2 + ((a - p2) + (b - p2)) * -0.4
                            if gen.is_colinear(q, center1, center2):
                                lines.append(
                                    f"""<path d="M {a.real},{a.imag} L {b.real},{b.imag}" stroke="{BASIS_COLORS_DARKER[rem]}" stroke-width="{stroke_width*3}" fill="none" />"""
                                )
                            else:
                                lines.append(
                                    f"""<path d="M {a.real},{a.imag} C {p2.real} {p2.imag},  {p2.real} {p2.imag}, {b.real},{b.imag}" stroke="{BASIS_COLORS_DARKER[rem]}" stroke-width="{stroke_width*3}" fill="none" />"""
                                )

    # Draw nodes.
    for (tile, color), pos in t2d.items():
        lines.append(
            f"""<circle cx="{pos.real}" cy="{pos.imag}" r="{abs(draw_coord(0.2) - draw_coord(0))}" fill="{BASIS_COLORS[color]}" stroke="black" />"""
        )
