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

import pytest

from gen._surf._geo import int_points_inside_polygon
from gen._surf._order import Order_Z, Order_ᴎ, checkerboard_basis
from gen._surf._patch_outline import PatchOutline
from gen._surf._closed_curve import ClosedCurve
from gen._surf._css_observable_boundary_pair import CssObservableBoundaryPair
from gen._surf._path_outline import PathOutline
from gen._surf._viz_patch_outline_svg import patch_outline_svg_viewer


def test_tight_boundary():
    c1 = ClosedCurve.from_cycle(["Z", (5 + 0j), "X", (5 + 3j), "Z", 3j, "X", 0j, "Z"])

    c2 = ClosedCurve.from_cycle(
        [
            "X",
            5 + 4j,
            "X",
            5 + 6j,
            "X",
            0 + 6j,
            "X",
            0 + 4j,
        ]
    )

    b = PatchOutline([c1, c2])
    fused = b.fused(c1.med(), c2.med())

    c3 = ClosedCurve.from_cycle(
        [
            "Z",
            5 + 0j,
            "X",
            5 + 3j,
            "X",
            5 + 4j,
            "X",
            5 + 6j,
            "X",
            0 + 6j,
            "X",
            0 + 4j,
            "X",
            0 + 3j,
            "X",
            0 + 0j,
        ]
    )
    assert fused == PatchOutline([c3])

    p = b.to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )
    assert sum(e.basis == "X" and len(e.data_set) == 2 for e in p.tiles) == 11
    assert sum(e.basis == "Z" and len(e.data_set) == 2 for e in p.tiles) == 4


def test_pitchfork_boundary():
    b = PatchOutline(
        [
            ClosedCurve(
                points=[0, 3, 3 + 10j, 2 + 10j, 2 + 6j, 1 + 6j, 1 + 10j, 10j],
                bases="XXXXZXXX",
            ),
        ]
    )
    p = b.to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )

    assert sum(e.basis == "X" and len(e.data_set) == 2 for e in p.tiles) == 15
    assert sum(e.basis == "X" and len(e.data_set) == 3 for e in p.tiles) == 1
    assert sum(e.basis == "Z" and len(e.data_set) == 2 for e in p.tiles) == 2
    assert sum(e.basis == "Z" and len(e.data_set) == 3 for e in p.tiles) == 0


def test_line():
    c = ClosedCurve.from_cycle(
        [
            "Z",
            6,
            "X",
            6,
            "Z",
            0,
            "X",
            0,
        ]
    )
    b = PatchOutline([c])
    p = b.to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )
    assert p.data_set == {0, 1, 2, 3, 4, 5, 6}
    assert p.measure_set == {
        0.5 + 0.5j,
        1.5 - 0.5j,
        2.5 + 0.5j,
        3.5 - 0.5j,
        4.5 + 0.5j,
        5.5 - 0.5j,
    }
    assert all(len(e.data_set) == 2 for e in p.tiles)
    assert len(p.tiles) == 6


def test_hole():
    c = ClosedCurve.from_cycle(
        [
            "Z",
            0,
            "X",
            10,
            "Z",
            10 + 10j,
            "X",
            10j,
        ]
    )

    c2 = ClosedCurve.from_cycle(
        [
            "X",
            2 + 2j,
            "X",
            8 + 2j,
            "X",
            8 + 8j,
            "X",
            2 + 8j,
        ]
    )

    b = PatchOutline([c, c2])
    p = b.to_patch(
        rel_order_func=lambda m: Order_Z if checkerboard_basis(m) == "Z" else Order_ᴎ
    )
    assert sum(e.basis == "X" and len(e.data_set) == 2 for e in p.tiles) == 18
    assert sum(e.basis == "Z" and len(e.data_set) == 2 for e in p.tiles) == 10
    assert sum(e.basis == "X" and len(e.data_set) == 3 for e in p.tiles) == 2
    assert sum(e.basis == "Z" and len(e.data_set) == 3 for e in p.tiles) == 0


def test_fused_simple():
    a = ClosedCurve.from_cycle(
        [
            "X",
            4 + 0j,
            "Z",
            4 + 4j,
            "X",
            0 + 4j,
            "Z",
            0 + 0j,
        ]
    )

    b = PatchOutline([a, a.offset_by(6)])
    b = b.fused(2 + 2j, 8 + 2j)
    assert b == PatchOutline(
        [
            ClosedCurve(
                points=[
                    4 + 0j,
                    6 + 0j,
                    10 + 0j,
                    10 + 4j,
                    6 + 4j,
                    4 + 4j,
                    0 + 4j,
                    0 + 0j,
                ],
                bases=["X", "X", "X", "Z", "X", "X", "X", "Z"],
            ),
        ]
    )


def test_fused_stability():
    a = ClosedCurve.from_cycle(
        [
            "Z",
            4 + 0j,
            "Z",
            4 + 4j,
            "Z",
            0 + 4j,
            "Z",
            0 + 0j,
        ]
    )

    b = PatchOutline([a, a.offset_by(6j), a.offset_by(12j)])
    b = b.fused(2 + 2j, 2 + 8j)
    assert b == PatchOutline(
        [
            ClosedCurve(
                points=[
                    4 + 0j,
                    4 + 4j,
                    4 + 6j,
                    4 + 10j,
                    0 + 10j,
                    0 + 6j,
                    0 + 4j,
                    0 + 0j,
                ],
                bases=["Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z"],
            ),
            a.offset_by(12j),
        ]
    )

    b = b.fused(2 + 8j, 2 + 14j)
    assert b == PatchOutline(
        [
            ClosedCurve(
                points=[
                    4 + 0j,
                    4 + 4j,
                    4 + 6j,
                    4 + 10j,
                    4 + 12j,
                    4 + 16j,
                    0 + 16j,
                    0 + 12j,
                    0 + 10j,
                    0 + 6j,
                    0 + 4j,
                    0 + 0j,
                ],
                bases=["Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z"],
            ),
        ]
    )


def test_fused_t():
    a = ClosedCurve.from_cycle(
        [
            "Z",
            4 + 0j,
            "Z",
            4 + 4j,
            "Z",
            0 + 4j,
            "Z",
            0 + 0j,
        ]
    )

    b = PatchOutline([a, a.offset_by(6j), a.offset_by(6j - 6)])
    b = b.fused(2 + 2j, 2 + 8j)
    assert b == PatchOutline(
        [
            ClosedCurve(
                points=[
                    4 + 0j,
                    4 + 4j,
                    4 + 6j,
                    4 + 10j,
                    0 + 10j,
                    0 + 6j,
                    0 + 4j,
                    0 + 0j,
                ],
                bases=["Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z"],
            ),
            a.offset_by(6j - 6),
        ]
    )

    b = b.fused(-4 + 8j, 2 + 8j)
    assert b == PatchOutline(
        [
            ClosedCurve(
                points=[
                    4 + 0j,
                    4 + 4j,
                    4 + 6j,
                    4 + 10j,
                    0 + 10j,
                    -2 + 10j,
                    -6 + 10j,
                    -6 + 6j,
                    -2 + 6j,
                    0 + 6j,
                    0 + 4j,
                    0 + 0j,
                ],
                bases=["Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z", "Z"],
            ),
        ]
    )
    assert (
        len(
            [
                p
                for p in int_points_inside_polygon(
                    b.region_curves[0].points, include_boundary=False
                )
                if p.real == 0
            ]
        )
        == 3
    )


def test_fused_interior():
    a = ClosedCurve.from_cycle(
        [
            "Z",
            12 + 0j,
            "Z",
            12 + 4j,
            "Z",
            8 + 4j,
            "Z",
            4 + 4j,
            "Z",
            4 + 8j,
            "Z",
            8 + 8j,
            "Z",
            12 + 8j,
            "Z",
            12 + 12j,
            "Z",
            0 + 12j,
            "Z",
            0,
        ]
    )

    actual = PatchOutline([a]).fused(10 + 2j, 10 + 10j)
    assert actual == PatchOutline(
        [
            ClosedCurve(
                points=[(12 + 0j), (12 + 4j), (12 + 8j), (12 + 12j), 12j, 0],
                bases=["Z", "Z", "Z", "Z", "Z", "Z"],
            ),
            ClosedCurve(
                points=[(8 + 4j), (4 + 4j), (4 + 8j), (8 + 8j)],
                bases=["Z", "Z", "Z", "Z"],
            ),
        ]
    )


def test_fused_inner():
    b1 = ClosedCurve.from_cycle(
        [
            "X",
            0 + 16j,
            6 + 16j,
            8 + 16j,
            14 + 16j,
            16 + 16j,
            22 + 16j,
            22 + 18j,
            22 + 20j,
            22 + 22j,
            22 + 24j,
            22 + 26j,
            22 + 28j,
            22 + 30j,
            16 + 30j,
            16 + 28j,
            16 + 26j,
            14 + 26j,
            8 + 26j,
            "Z",
            8 + 24j,
            "X",
            14 + 24j,
            16 + 24j,
            16 + 22j,
            16 + 20j,
            16 + 18j,
            14 + 18j,
            8 + 18j,
            6 + 18j,
            6 + 20j,
            8 + 20j,
            14 + 20j,
            "Z",
            14 + 22j,
            "X",
            8 + 22j,
            6 + 22j,
            6 + 24j,
            6 + 26j,
            6 + 28j,
            8 + 28j,
            14 + 28j,
            "Z",
            14 + 30j,
            "X",
            8 + 30j,
            6 + 30j,
            30j,
            28j,
            26j,
            24j,
            22j,
            20j,
            18j,
        ]
    ).to_patch_outline()
    b2 = b1.fused(19 + 29j, 11 + 29j)

    assert len(b2.region_curves) == 2
    assert all(e == "X" for e in b2.region_curves[0].bases)
    assert b2.region_curves[1] == ClosedCurve.from_cycle(
        [
            "X",
            (16 + 28j),
            (16 + 26j),
            (14 + 26j),
            (8 + 26j),
            "Z",
            (8 + 24j),
            "X",
            (14 + 24j),
            (16 + 24j),
            (16 + 22j),
            (16 + 20j),
            (16 + 18j),
            (14 + 18j),
            (8 + 18j),
            (6 + 18j),
            (6 + 20j),
            (8 + 20j),
            (14 + 20j),
            "Z",
            (14 + 22j),
            "X",
            (8 + 22j),
            (6 + 22j),
            (6 + 24j),
            (6 + 26j),
            (6 + 28j),
            (8 + 28j),
            (14 + 28j),
        ]
    )


def test_validate():
    patch = ClosedCurve.from_cycle([0, "X", 5, "Z", 5 + 5j, "X", 5j, "Z", 0])
    obs = CssObservableBoundaryPair(
        x_obs=PathOutline([(0, 5j, "X")]),
        z_obs=PathOutline([(0, 5, "Z")]),
    )
    PatchOutline(
        [patch],
        observables=[obs],
    ).validate()
    with pytest.raises(ValueError, match="X0 and Z1"):
        PatchOutline(
            [patch],
            observables=[obs, obs],
        ).validate()
    with pytest.raises(ValueError, match="terminate on same-basis boundaries"):
        PatchOutline(
            [patch],
            observables=[
                CssObservableBoundaryPair(
                    x_obs=PathOutline([(0, 5j, "X")]),
                    z_obs=PathOutline([(0, 4, "Z")]),
                )
            ],
        ).validate()
    with pytest.raises(ValueError, match="only runs along same-basis boundaries"):
        PatchOutline(
            [patch],
            observables=[
                CssObservableBoundaryPair(
                    x_obs=PathOutline([(0, 5, "X")]),
                    z_obs=PathOutline([(0, 5j, "Z")]),
                )
            ],
        ).validate()


def test_diagram():
    boundary = PatchOutline(
        [ClosedCurve.from_cycle([0, "X", 5, "Z", 5 + 5j, "X", 5j, "Z", 0])],
        observables=[
            CssObservableBoundaryPair(
                x_obs=PathOutline([(0, 5j, "X")]),
                z_obs=PathOutline([(1j, 1j + 5, "Z")]),
            ),
        ],
    )
    assert (
        patch_outline_svg_viewer([boundary]).strip()
        == """
<svg viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
<rect fill="#FF0000" x="1" y="1" width="20" height="20" />
<text x="11" y="11" fill="white" font-size="20" text-anchor="middle" alignment-baseline="central">X</text>
<rect fill="#00FF00" x="1" y="21" width="20" height="20" />
<text x="11" y="31" fill="white" font-size="20" text-anchor="middle" alignment-baseline="central">Y</text>
<rect fill="#0000FF" x="1" y="41" width="20" height="20" />
<text x="11" y="51" fill="white" font-size="20" text-anchor="middle" alignment-baseline="central">Z</text>
<path d="M 60.71428571428572,60.71428571428572 417.85714285714283,60.71428571428572 417.85714285714283,417.85714285714283 60.71428571428572,417.85714285714283 Z" fill="#ddd" stroke="none"/>
<line x1="60.71428571428572" y1="417.85714285714283" x2="60.71428571428572" y2="60.71428571428572" stroke-width="22.857142857142858" stroke="#0000FF" />
<line x1="60.71428571428572" y1="60.71428571428572" x2="417.85714285714283" y2="60.71428571428572" stroke-width="22.857142857142858" stroke="#FF0000" />
<line x1="417.85714285714283" y1="60.71428571428572" x2="417.85714285714283" y2="417.85714285714283" stroke-width="22.857142857142858" stroke="#0000FF" />
<line x1="417.85714285714283" y1="417.85714285714283" x2="60.71428571428572" y2="417.85714285714283" stroke-width="22.857142857142858" stroke="#FF0000" />
<line x1="60.35714285714287" y1="60.35714285714287" x2="60.35714285714287" y2="417.5" stroke-width="8.571428571428571" stroke-dasharray="0 1 0" stroke="#800000" />
<line x1="60.35714285714287" y1="131.78571428571428" x2="417.5" y2="131.78571428571428" stroke-width="8.571428571428571" stroke-dasharray="0 1 0" stroke="#000080" />
<circle cx="60.71428571428572" cy="60.71428571428572" r="14.285714285714286" stroke-width="2.857142857142857" fill="black" stroke="black" />
<circle cx="417.85714285714283" cy="60.71428571428572" r="14.285714285714286" stroke-width="2.857142857142857" fill="black" stroke="black" />
<circle cx="417.85714285714283" cy="417.85714285714283" r="14.285714285714286" stroke-width="2.857142857142857" fill="black" stroke="black" />
<circle cx="60.71428571428572" cy="417.85714285714283" r="14.285714285714286" stroke-width="2.857142857142857" fill="black" stroke="black" />
<rect fill="none" stroke="#999" x="-10.714285714285708" y="-10.714285714285708" width="500.0" height="500.0" />
</svg>
""".strip()
    )
