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

from typing import Callable, Literal, TYPE_CHECKING, cast, Iterable, Dict

import stim

from gen._core._util import sorted_complex

if TYPE_CHECKING:
    import gen


class PauliString:
    """A qubit-to-pauli mapping."""

    def __init__(self, qubits: dict[complex, Literal["X", "Y", "Z"]]):
        self.qubits = {q: qubits[q] for q in sorted_complex(qubits.keys())}
        self._hash: int = hash(tuple(self.qubits.items()))

    @staticmethod
    def from_stim_pauli_string(stim_pauli_string: stim.PauliString) -> "PauliString":
        return PauliString(
            {
                q: "_XYZ"[stim_pauli_string[q]]
                for q in range(len(stim_pauli_string))
                if stim_pauli_string[q]
            }
        )

    @staticmethod
    def from_tile_data(tile: "gen.Tile") -> "PauliString":
        return PauliString(
            {
                k: v
                for k, v in zip(tile.ordered_data_qubits, tile.bases)
                if k is not None
            }
        )

    @staticmethod
    def from_xyzs(
        *,
        xs: Iterable[complex] = (),
        ys: Iterable[complex] = (),
        zs: Iterable[complex] = (),
    ) -> "PauliString":
        qs: dict[complex, Literal["X", "Y", "Z"]] = {}
        for q in xs:
            qs[q] = "X"
        for q in ys:
            p = qs.get(q)
            if p is None:
                qs[q] = "Y"
            elif p == "X":
                qs[q] = "Z"
            else:
                raise NotImplementedError(f"{p=}")
        for q in zs:
            p = qs.get(q)
            if p is None:
                qs[q] = "Z"
            elif p == "X":
                qs[q] = "Y"
            elif p == "Y":
                qs[q] = "X"
            else:
                raise NotImplementedError(f"{p=}")
        return PauliString(qs)

    @staticmethod
    def from_b2q(
        b2q: dict[Literal["X", "Y", "Z"], Iterable[complex]],
    ) -> "PauliString":
        return PauliString.from_xyzs(
            xs=b2q.get("X", ()),
            ys=b2q.get("Y", ()),
            zs=b2q.get("Z", ()),
        )

    def __bool__(self) -> bool:
        return bool(self.qubits)

    def __mul__(self, other: "PauliString") -> "PauliString":
        result: dict[complex, Literal["X", "Y", "Z"]] = {}
        for q in self.qubits.keys() | other.qubits.keys():
            a = self.qubits.get(q, "I")
            b = other.qubits.get(q, "I")
            ax = a in "XY"
            az = a in "YZ"
            bx = b in "XY"
            bz = b in "YZ"
            cx = ax ^ bx
            cz = az ^ bz
            c = "IXZY"[cx + cz * 2]
            if c != "I":
                result[q] = cast(Literal["X", "Y", "Z"], c)
        return PauliString(result)

    def __repr__(self) -> str:
        return f"gen.PauliString(qubits={self.qubits!r})"

    def __str__(self) -> str:
        return "*".join(
            f"{self.qubits[q]}{q}" for q in sorted_complex(self.qubits.keys())
        )

    def with_xz_flipped(self) -> "PauliString":
        return PauliString(
            {
                q: "Z" if p == "X" else "X" if p == "Z" else p
                for q, p in self.qubits.items()
            }
        )

    def commutes(self, other: "PauliString") -> bool:
        return not self.anticommutes(other)

    def anticommutes(self, other: "PauliString") -> bool:
        t = 0
        for q in self.qubits.keys() & other.qubits.keys():
            t += self.qubits[q] != other.qubits[q]
        return t % 2 == 1

    def with_transformed_coords(
        self, transform: Callable[[complex], complex]
    ) -> "PauliString":
        return PauliString({transform(q): p for q, p in self.qubits.items()})

    def to_tile(self) -> "gen.Tile":
        from gen._core._tile import Tile

        qs = list(self.qubits.keys())
        m = qs[0] if qs else 0
        return Tile(
            bases="".join(self.qubits.values()),
            ordered_data_qubits=qs,
            measurement_qubit=m,
        )

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other) -> bool:
        if not isinstance(other, PauliString):
            return NotImplemented
        return self.qubits == other.qubits
