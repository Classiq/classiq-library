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

import base64
import collections
import dataclasses
import math
import random
import sys
from typing import Iterable

import stim

from gen._core._patch import Patch

PITCH = 48 * 2
DIAM = 32
RAD = DIAM / 2
NOISY_GATES = {
    "X_ERROR",
    "Y_ERROR",
    "Z_ERROR",
    "E",
    "ELSE_CORRELATED_ERROR",
    "DEPOLARIZE1",
    "DEPOLARIZE2",
}


def rand_color() -> str:
    color = "#"
    for _ in range(6):
        color += "0123456789abcdef"[random.randint(0, 15)]
    return color


MEASUREMENT_NAMES = {"M", "MX", "MY", "MR", "MRX", "MRY"}


@dataclasses.dataclass
class GateStyle:
    label: str
    fill_color: str
    text_color: str


def _init_gate_box_labels() -> dict[str, GateStyle]:
    result = {"I": GateStyle(label="I", fill_color="white", text_color="gray")}
    for name in ["X", "Y", "Z"]:
        result[name] = GateStyle(label=name, fill_color="white", text_color="black")
    for name in ["R", "M", "RX", "RY", "MX", "MY", "MR", "MRX", "MRY"]:
        result[name] = GateStyle(label=name, fill_color="black", text_color="white")
    for key in [
        "H",
        "H_YZ",
        "H_XY",
        "S",
        "SQRT_X",
        "SQRT_Y",
        "S_DAG",
        "SQRT_X_DAG",
        "SQRT_Y_DAG",
    ]:
        name = key.replace("SQRT_", "√")
        name = name.replace("_DAG", "⁻¹")
        a, b = name.split("_") if "_" in name else (name, "")
        result[key] = GateStyle(
            label=a + b.lower(), fill_color="yellow", text_color="black"
        )
    for name in ["C_XYZ", "C_ZYX"]:
        result[name] = GateStyle(
            label=name[0] + name[2:].lower(), fill_color="teal", text_color="black"
        )
    return result


GATE_BOX_LABELS = _init_gate_box_labels()
TWO_QUBIT_GATE_STYLES = {
    "CX": ("Z", "X"),
    "CY": ("Z", "Y"),
    "CZ": ("Z", "Z"),
    "XCX": ("X", "X"),
    "XCY": ("X", "Y"),
    "XCZ": ("X", "Z"),
    "YCX": ("Y", "X"),
    "YCY": ("Y", "Y"),
    "YCZ": ("Y", "Z"),
    "SQRT_XX": ("SQRT_XX", "SQRT_XX"),
    "SQRT_XX_DAG": ("SQRT_XX", "SQRT_XX"),
    "SQRT_YY": ("SQRT_YY", "SQRT_YY"),
    "SQRT_YY_DAG": ("SQRT_YY", "SQRT_YY"),
    "SQRT_ZZ": ("SQRT_ZZ", "SQRT_ZZ"),
    "SQRT_ZZ_DAG": ("SQRT_ZZ", "SQRT_ZZ"),
    "ISWAP": ("ISWAP", "ISWAP"),
    "ISWAP_DAG": ("ISWAP", "ISWAP"),
    "SWAP": ("SWAP", "SWAP"),
    "CXSWAP": ("ZSWAP", "XSWAP"),
    "SWAPCX": ("XSWAP", "ZSWAP"),
}


def tag_str(tag, *, content: bool | str = False, **kwargs) -> str:
    parts = [f"<{tag}"]
    for k, v in kwargs.items():
        parts.append(f"{k.replace('_', '-')}={str(v)!r}")
    instr = " ".join(parts)
    if not content:
        instr += " />"
    elif isinstance(content, str):
        instr += f">{content}</{tag}>"
    elif content is True:
        instr += ">"
    else:
        raise NotImplementedError(repr(content))

    return instr


class _SvgLayer:
    def __init__(self):
        self.svg_instructions: list[str] = []
        self.q2i_dict: dict[int, tuple[float, float]] = {}
        self.used_indices: set[int] = set()
        self.used_positions: set[tuple[float, float]] = set()
        self.measurement_positions: dict[int, tuple[float, float]] = {}

    def add(self, tag, *, content: bool | str = False, **kwargs) -> None:
        self.svg_instructions.append("    " + tag_str(tag, content=content, **kwargs))

    def bounds(self) -> tuple[float, float, float, float]:
        min_y = min(e for _, e in self.used_positions)
        max_y = max(e for _, e in self.used_positions)
        min_x = min(e for e, _ in self.used_positions)
        max_x = max(e for e, _ in self.used_positions)
        min_x -= PITCH
        min_y -= PITCH
        max_x += PITCH
        max_y += PITCH
        return min_x, min_y, max_x, max_y

    def add_idles(self, all_used_positions: set[tuple[float, float]]):
        for x, y in all_used_positions - self.used_positions:
            self.add("circle", cx=x, cy=y, r=5, fill="gray", stroke="black")
        self.used_positions |= all_used_positions
        min_x, min_y, max_x, max_y = self.bounds()
        xs = {e for e, _ in self.used_positions}
        ys = {e for _, e in self.used_positions}
        for x in xs:
            x2 = x
            x2 /= PITCH
            if x2 == int(x2):
                x2 = int(x2)
            self.add(
                "text",
                x=x,
                y=max_y - 5,
                fill="black",
                content=str(x2),
                text_anchor="middle",
                dominant_baseline="auto",
                font_size=24,
            )
        for y in ys:
            y2 = y
            y2 /= PITCH
            if y2 == int(y2):
                y2 = int(y2)
            self.add(
                "text",
                x=min_x + 5,
                y=y,
                fill="black",
                content=str(y2),
                text_anchor="left",
                alignment_baseline="middle",
                font_size=24,
            )

    def svg(
        self,
        *,
        html_id: str | None = None,
        as_img_with_data_uri: bool = False,
        width: int,
        height: int,
    ) -> str:
        min_x, min_y, max_x, max_y = self.bounds()
        kwargs = {} if html_id is None or as_img_with_data_uri else {"id": html_id}
        svg = "\n".join(
            [
                tag_str(
                    "svg",
                    xmlns="http://www.w3.org/2000/svg",
                    viewBox=f"{min_x} {min_y} {max_x - min_x} {max_y - min_y}",
                    content=True,
                    **kwargs,
                ),
                *self.svg_instructions,
                "</svg>",
            ]
        )
        if as_img_with_data_uri:
            kwargs = {} if html_id is None else {"id": html_id}
            svg = tag_str(
                "img",
                width=width,
                height=height,
                **kwargs,
                src="data:image/svg+xml;base64,"
                + base64.standard_b64encode(svg.encode("utf-8")).decode("utf-8"),
            )
            svg = svg.replace("/>", ">")
        return svg


class _SvgState:
    def __init__(self):
        self.layers: list[_SvgLayer] = [_SvgLayer()]
        self.coord_shift: list[int] = [0, 0]
        self.measurement_layer_indices: list[int] = []
        self.detector_index = 0
        self.detector_coords = {}
        self.measurement_marks = collections.Counter()
        self.highlighted_detectors = set()
        self.highlighted_errors: list[tuple[int, int, str]] = []
        self.flipped_measurements: set[int] = set()
        self.noted_errors: list[tuple[int, int, str]] = []
        self.control_count = 0

    def tick(self) -> None:
        self.layers.append(_SvgLayer())
        self.layers[-1].q2i_dict = dict(self.layers[-2].q2i_dict)

    def q2i(self, i: int) -> tuple[float, float]:
        x, y = self.layers[-1].q2i_dict.setdefault(i, (i, 0))
        pt = x * PITCH, y * PITCH
        self.layers[-1].used_indices.add(i)
        self.layers[-1].used_positions.add(pt)
        return pt

    def are_adjacent(self, q1: stim.GateTarget, q2: stim.GateTarget) -> bool:
        if q1.is_qubit_target and q2.is_qubit_target:
            x1, y1 = self.layers[-1].q2i_dict.setdefault(q1.value, (q1.value, 0))
            x2, y2 = self.layers[-1].q2i_dict.setdefault(q2.value, (q2.value, 0))
            if abs(x2 - x1) + abs(y2 - y1) < 1.5:
                return True
        return False

    def add(self, tag, *, content="", **kwargs) -> None:
        self.layers[-1].add(tag, content=content, **kwargs)

    def add_box(
        self, x: float, y: float, text: str, *, fill="white", text_color="black"
    ):
        self.add(
            "rect",
            x=x - RAD,
            y=y - RAD,
            width=DIAM,
            height=DIAM,
            fill=fill,
            stroke="black",
        )
        self.add(
            "text",
            x=x,
            y=y,
            fill=text_color,
            content=text,
            font_size=32 if len(text) == 1 else 24 if len(text) == 2 else 18,
            text_anchor="middle",
            alignment_baseline="central",
        )

    def add_measurement(self, target: stim.GateTarget) -> None:
        assert (
            target.is_qubit_target
            or target.is_x_target
            or target.is_y_target
            or target.is_z_target
        )
        m_index = len(self.measurement_layer_indices)
        self.measurement_layer_indices.append(len(self.layers) - 1)
        self.layers[-1].measurement_positions[m_index] = self.q2i(target.value)

    def mark_measurements(
        self, targets: list[stim.GateTarget], prefix: str, index: int | None
    ) -> None:
        if index is None:
            assert prefix == "D"
            index = self.detector_index
            self.detector_index += 1
        if prefix == "D":
            color = "black"
            if index in self.highlighted_detectors:
                color = "red"
        elif prefix == "L":
            color = "blue"
        elif prefix == "C":
            color = "green"
        else:
            color = "black"
        name = f"{prefix}{index}"
        for t in targets:
            m_index = len(self.measurement_layer_indices) + t.value
            if m_index < 0:
                print(
                    "Attempted to mark a measurement before the beginning of time.\n"
                    "Skipping this mark.",
                    file=sys.stderr,
                )
                continue
            assert m_index >= 0, m_index
            assert t.is_measurement_record_target
            layer = self.layers[self.measurement_layer_indices[m_index]]
            x, y = layer.measurement_positions[m_index]
            x += RAD + 1
            y -= RAD
            y += self.measurement_marks[m_index] * 15
            self.measurement_marks[m_index] += 1
            layer.add(
                "text",
                x=x,
                y=y,
                fill=color,
                content=name,
                text_anchor="left",
                alignment_baseline="hanging",
                font_size=16,
            )


def _draw_endpoint(x: float, y: float, style: str, *, out: _SvgState) -> None:
    add = out.add
    if style == "X":
        add("circle", cx=x, cy=y, r=RAD, stroke="black", fill="white")
        add("line", x1=x - RAD, x2=x + RAD, y1=y, y2=y, stroke="black")
        add("line", x1=x, x2=x, y1=y - RAD, y2=y + RAD, stroke="black")
    elif style == "Y":
        s = 0.5**0.5
        add("circle", cx=x, cy=y, r=RAD, stroke="black", fill="white")
        add("line", x1=x, x2=x, y1=y, y2=y + RAD, stroke="black")
        add("line", x1=x, x2=x - RAD * s, y1=y, y2=y - RAD * s, stroke="black")
        add("line", x1=x, x2=x + RAD * s, y1=y, y2=y - RAD * s, stroke="black")
    elif style == "Z":
        add("circle", cx=x, cy=y, r=RAD, fill="black")
    elif style == "SWAP":
        r = RAD / 3
        add("line", x1=x - r, x2=x + r, y1=y - r, y2=y + r, stroke="black")
        add("line", x1=x - r, x2=x + r, y1=y + r, y2=y - r, stroke="black")
    elif style == "ISWAP":
        r = RAD
        add("circle", cx=x, cy=y, r=RAD / 2, fill="gray")
        add("line", x1=x - r, x2=x + r, y1=y - r, y2=y + r, stroke="black")
        add("line", x1=x - r, x2=x + r, y1=y + r, y2=y - r, stroke="black")
    elif style == "SQRT_ZZ":
        out.add_box(x=x, y=y, text="√ZZ")
    elif style == "SQRT_YY":
        out.add_box(x=x, y=y, text="√YY")
    elif style == "SQRT_XX":
        out.add_box(x=x, y=y, text="√XX")
    elif style == "XSWAP":
        r = RAD * 0.4
        add("circle", cx=x, cy=y, r=RAD, fill="white", stroke="black")
        add(
            "line",
            x1=x - r,
            x2=x + r,
            y1=y - r,
            y2=y + r,
            stroke="black",
            stroke_width=5,
        )
        add(
            "line",
            x1=x - r,
            x2=x + r,
            y1=y + r,
            y2=y - r,
            stroke="black",
            stroke_width=5,
        )
    elif style == "ZSWAP":
        r = RAD * 0.4
        add("circle", cx=x, cy=y, r=RAD, fill="black", stroke="black")
        add(
            "line",
            x1=x - r,
            x2=x + r,
            y1=y - r,
            y2=y + r,
            stroke="white",
            stroke_width=5,
        )
        add(
            "line",
            x1=x - r,
            x2=x + r,
            y1=y + r,
            y2=y - r,
            stroke="white",
            stroke_width=5,
        )
    else:
        raise NotImplementedError(style)


def _draw_2q(instruction: stim.CircuitInstruction, *, out: _SvgState) -> None:
    style1, style2 = TWO_QUBIT_GATE_STYLES[instruction.name]
    targets = instruction.targets_copy()
    q2i = out.q2i

    assert len(targets) % 2 == 0
    for k in range(0, len(targets), 2):
        t1 = targets[k]
        t2 = targets[k + 1]
        if t1.is_measurement_record_target or t2.is_measurement_record_target:
            if t1.is_qubit_target:
                t = t1.value
                m = t2
            elif t2.is_qubit_target:
                t = t2.value
                m = t1
            else:
                continue
            b = (
                "X"
                if instruction.name in ["XCZ", "CX"]
                else (
                    "Y"
                    if instruction.name in ["YCZ", "CY"]
                    else "Z" if instruction.name == "CZ" else "?"
                )
            )
            x, y = q2i(t)
            out.add(
                "text",
                x=x - RAD + 1,
                y=y,
                fill="green",
                content=b,
                font_size=18,
                text_anchor="left",
                alignment_baseline="central",
            )
            out.add(
                "text",
                x=x - 1,
                y=y - RAD / 2,
                fill="green",
                content=f"C{out.control_count}",
                font_size=8,
                text_anchor="left",
                alignment_baseline="central",
            )
            out.mark_measurements([m], prefix="C", index=out.control_count)
            out.control_count += 1
            continue
        assert t1.is_qubit_target
        assert t2.is_qubit_target
        x1, y1 = q2i(t1.value)
        x2, y2 = q2i(t2.value)
        dx = x2 - x1
        dy = y2 - y1
        r = (dx * dx + dy * dy) ** 0.5
        px = dy
        py = -dx
        px *= 25 / r
        py *= 25 / r
        cx1 = dx / 10 + px
        cy1 = dy / 10 + py
        cx2 = dx - dx / 10 + px
        cy2 = dy - dy / 10 + py

        if out.are_adjacent(t1, t2):
            out.add("line", x1=x1, x2=x2, y1=y1, y2=y2, stroke="black")
        else:
            out.add(
                "path",
                d=f"M {x1},{y1} c {cx1},{cy1} {cx2},{cy2} {dx},{dy}",
                stroke="black",
                fill="none",
            )

        _draw_endpoint(x1, y1, style1, out=out)
        _draw_endpoint(x2, y2, style2, out=out)


def _draw_mpp(instruction: stim.CircuitInstruction, *, out: _SvgState) -> None:
    targets = instruction.targets_copy()
    add = out.add
    add_box = out.add_box
    q2i = out.q2i

    chunks = []
    start = 0
    end = 1
    while start < len(targets):
        while end < len(targets) and targets[end].is_combiner:
            end += 2
        chunks.append(targets[start:end:2])
        start = end
        end = start + 1
    for chunk in chunks:
        out.add_measurement(chunk[0])
        tx, ty = 0, 0
        for t in chunk:
            x, y = q2i(t.value)
            tx += x
            ty += y
        tx /= len(chunk)
        ty /= len(chunk)
        color = rand_color()
        no_text = False
        if all(t.is_x_target for t in chunk):
            color = "red"
            no_text = True
        if all(t.is_y_target for t in chunk):
            color = "green"
            no_text = True
        if all(t.is_z_target for t in chunk):
            color = "blue"
            no_text = True
        for t in chunk:
            x, y = q2i(t.value)
            add("line", x1=x, x2=tx, y1=y, y2=ty, stroke=color, stroke_width=8)
        for k, c in enumerate(chunk):
            if c.is_x_target:
                text = "PX"
            elif c.is_y_target:
                text = "PY"
            elif c.is_z_target:
                text = "PZ"
            else:
                raise NotImplementedError(repr(c))
            x, y = q2i(c.value)
            add_box(x, y, text * (1 - int(no_text)), fill=color)


def _draw_1q(instruction: stim.CircuitInstruction, *, out: _SvgState):
    targets = instruction.targets_copy()
    if instruction.name in MEASUREMENT_NAMES:
        for t in targets:
            out.add_measurement(t)
    for t in targets:
        assert t.is_qubit_target
        x, y = out.q2i(t.value)
        style = GATE_BOX_LABELS[instruction.name]
        out.add_box(
            x, y, style.label, fill=style.fill_color, text_color=style.text_color
        )


def _stim_circuit_to_svg_helper(circuit: stim.Circuit, state: _SvgState) -> None:
    for instruction in circuit:
        if isinstance(instruction, stim.CircuitRepeatBlock):
            body = instruction.body_copy()
            for _ in range(instruction.repeat_count):
                _stim_circuit_to_svg_helper(body, state)
        elif isinstance(instruction, stim.CircuitInstruction):
            targets: list[stim.GateTarget] = instruction.targets_copy()
            if instruction.name == "QUBIT_COORDS":
                pos = instruction.gate_args_copy()
                for t in instruction.targets_copy():
                    assert t.is_qubit_target
                    if len(pos) == 1:
                        pos = (pos[0], 0)
                    state.layers[-1].q2i_dict[t.value] = (
                        pos[0] + state.coord_shift[0],
                        pos[1] + state.coord_shift[1],
                    )
            elif instruction.name == "SHIFT_COORDS":
                pos = instruction.gate_args_copy()
                if len(pos) >= 1:
                    state.coord_shift[0] += pos[0]
                if len(pos) >= 2:
                    state.coord_shift[1] += pos[1]
            elif instruction.name in GATE_BOX_LABELS:
                _draw_1q(instruction, out=state)
            elif instruction.name in TWO_QUBIT_GATE_STYLES:
                _draw_2q(instruction, out=state)
            elif instruction.name == "TICK":
                state.tick()
            elif instruction.name == "MPP":
                _draw_mpp(instruction, out=state)
            elif instruction.name == "DETECTOR":
                state.mark_measurements(targets, prefix="D", index=None)
            elif instruction.name == "OBSERVABLE_INCLUDE":
                state.mark_measurements(
                    targets, prefix="L", index=int(instruction.gate_args_copy()[0])
                )
            elif instruction.name in NOISY_GATES:
                for t in instruction.targets_copy():
                    state.noted_errors.append((t.value, len(state.layers) - 1, "E"))
            else:
                raise NotImplementedError(repr(instruction))
        else:
            raise NotImplementedError(repr(instruction))


def append_patch_polygons(*, out: list[str], patch: Patch, q2i: dict[complex, int]):
    for e in patch.tiles:
        if e.basis == "X":
            r, g, b = (1, 0, 0)
        elif e.basis == "Y":
            r, g, b = (0, 1, 0)
        elif e.basis == "Z":
            r, g, b = (0, 0, 1)
        else:
            r, g, b = (1, 1, 0)
        qs = [q for q in e.ordered_data_qubits if q is not None]
        c = e.measurement_qubit
        if any(abs(q - c) < 1e-4 for q in e.data_set):
            c = sum(e.data_set) / len(e.data_set)
        qs = sorted(qs, key=lambda q: math.atan2(q.imag - c.imag, q.real - c.real))
        alpha = 0.75 if len(qs) == 2 else 0.5
        line = f"POLYGON({r},{g},{b},{alpha})"
        for q in qs:
            line += f"_{q2i.get(q, 0)}"
        out.append(line)


def stim_circuit_html_viewer(
    circuit: stim.Circuit,
    *,
    patch: None | Patch | dict[int, Patch] = None,
    width: int = 500,
    height: int = 500,
    known_error: Iterable[stim.ExplainedError] | None = None,
) -> str:
    q2i = {
        v[0] + 1j * v[1]: k for k, v in circuit.get_final_qubit_coordinates().items()
    }

    state = _SvgState()
    state.detector_coords = circuit.get_detector_coordinates()
    if known_error is None:
        # noinspection PyBroadException
        try:
            known_error = circuit.shortest_graphlike_error(
                ignore_ungraphlike_errors=True,
                canonicalize_circuit_errors=True,
            )
        except Exception:
            pass
    if known_error is not None:
        for product in known_error:
            loc = next(iter(product.circuit_error_locations))
            for flipped in loc.flipped_pauli_product:
                if flipped.gate_target.is_x_target:
                    b = "X"
                elif flipped.gate_target.is_y_target:
                    b = "Y"
                elif flipped.gate_target.is_z_target:
                    b = "Z"
                else:
                    raise NotImplementedError(repr(loc))
                state.highlighted_errors.append(
                    (flipped.gate_target.value, loc.tick_offset, b)
                )
            if loc.flipped_measurement is not None:
                state.flipped_measurements.add(loc.flipped_measurement.record_index)
            for term in product.dem_error_terms:
                target = term.dem_target
                if target.is_relative_detector_id():
                    state.highlighted_detectors.add(target.val)

    _stim_circuit_to_svg_helper(circuit, state)
    all_pos = {pt for layer in state.layers for pt in layer.used_positions}
    for layer in state.layers:
        layer.add_idles(all_pos)

    for m in state.flipped_measurements:
        layer = state.layers[state.measurement_layer_indices[m]]
        x, y = layer.measurement_positions[m]
        layer.add(
            "rect",
            x=x - RAD,
            y=y - RAD,
            width=DIAM,
            height=DIAM,
            fill="#FF000080",
            stroke="#FF0000",
        )
    for qubit, time, basis in state.highlighted_errors:
        layer = state.layers[time]
        x, y = state.q2i(qubit)
        layer.add(
            "text",
            x=x,
            y=y,
            fill="red",
            content=basis,
            text_anchor="middle",
            dominant_baseline="middle",
            font_size=64,
        )
    for qubit, time, basis in set(state.noted_errors):
        if time >= len(state.layers):
            print(f"Error time is past end of circuit: {time}", file=sys.stderr)
            continue
        layer = state.layers[time]
        x, y = state.q2i(qubit)
        layer.add(
            "text",
            x=x - RAD,
            y=y,
            fill="red",
            content=basis,
            text_anchor="end",
            dominant_baseline="middle",
            font_size=12,
        )

    svg_image_tags = []
    for k, layer in enumerate(state.layers):
        svg = layer.svg(html_id=f"layer{k}", width=width, height=height)
        data = base64.standard_b64encode(svg.encode("utf-8")).decode("utf-8")
        svg_image_tags.append(
            f'<img style="max-width: 95%; max-height: 95%; display: none" '
            f"id=layer{k} "
            f'src="data:image/svg+xml;base64,{data}" />'
        )
    all_svg_image_tags = "\n".join(svg_image_tags)

    flattened = circuit.flattened()
    circuit_coords = [str(inst) for inst in flattened if inst.name == "QUBIT_COORDS"]
    if isinstance(patch, Patch):
        patch = {0: patch}
    if patch is None:
        patch = {}
    tick = 0
    circuit_rest = []
    for inst in flattened:
        if tick in patch:
            append_patch_polygons(out=circuit_rest, patch=patch[tick], q2i=q2i)
            circuit_rest.append("TICK")
            tick += 1
        if inst.name == "TICK":
            tick += 1
        if inst.name != "QUBIT_COORDS":
            circuit_rest.append(str(inst))
    max_patch_tick = max(patch.keys(), default=0)
    while tick <= max_patch_tick:
        if tick in patch:
            circuit_rest.append("TICK")
            append_patch_polygons(out=circuit_rest, patch=patch[tick], q2i=q2i)
        tick += 1

    escaped = ";".join(circuit_coords + circuit_rest)
    escaped = escaped.replace(", ", ",").replace(" ", "_")
    escaped = escaped.replace("QUBIT_COORDS", "Q")
    escaped = escaped.replace("DETECTOR", "DT")
    escaped = escaped.replace("(", "%28").replace(")", "%29")
    escaped = escaped.replace("[", "%5B").replace("]", "%5D")
    local_server_crumble_url = f"""https://algassert.com/crumble#circuit={escaped}"""

    return (
        f"""<div id="step">Loading...</div>
    <button id="btnPrev">Previous Layer (hotkey: a)</button>
    <button id="btnNext">Next Layer (hotkey: d)</button>
    <a href="{local_server_crumble_url}">Open in Crumble</a>
    <div id="viewer" style="border: 1px solid black; margin-bottom: 50px; width: 100%; height: 90%;
             resize: both; overflow: auto">
        """
        + all_svg_image_tags
        + """
</div>
<script>
    let layer_index = 0;
    let layers = [];
    while (true) {
        let svg = document.getElementById('layer' + layers.length);
        if (svg === null) {
            break;
        }
        layers.push(svg);
    }

    function handleLayerIndexChange() {
        if (layer_index < 0) {
            layer_index = 0;
        }
        if (layer_index >= layers.length) {
            layer_index = layers.length - 1;
        }

        let layerName = layer_index + 1;
        document.getElementById('step').innerHTML = "Layer: " + layerName + "/" + layers.length;
        for (let k = 0; k < layers.length; k++) {
            let svg = layers[k];
            if (layer_index === k) {
                svg.style.display = "";
            } else {
                svg.style.display = "none";
            }
        }
    }
    document.getElementById("btnPrev").addEventListener("click", ev => {
        layer_index -= 1;
        handleLayerIndexChange();
    });
    document.getElementById("btnNext").addEventListener("click", ev => {
        layer_index += 1;
        handleLayerIndexChange();
    });
    document.addEventListener('keydown', ev => {
        if (ev.code == "KeyA" && !ev.getModifierState("Control")) {
            layer_index -= 1;
            ev.preventDefault();
            handleLayerIndexChange();
        } else if (ev.code == "KeyD") {
            layer_index += 1;
            ev.preventDefault();
            handleLayerIndexChange();
        }
    });

    handleLayerIndexChange();
</script>"""
    )
