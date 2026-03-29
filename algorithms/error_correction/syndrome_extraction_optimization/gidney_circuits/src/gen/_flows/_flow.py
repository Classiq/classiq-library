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

from typing import Iterable, Any, Callable

from gen._core import PauliString


class Flow:
    """A rule for how a stabilizer travels into, through, and/or out of a chunk."""

    def __init__(
        self,
        *,
        start: PauliString | None = None,
        end: PauliString | None = None,
        measurement_indices: Iterable[int] = (),
        obs_index: Any = None,
        additional_coords: Iterable[float] = (),
        center: complex,
        postselect: bool = False,
        allow_vacuous: bool = False,
    ):
        if not allow_vacuous:
            assert start or end or measurement_indices, "vacuous flow"
        self.start = PauliString({}) if start is None else start
        self.end = PauliString({}) if end is None else end
        self.measurement_indices: tuple[int, ...] = tuple(measurement_indices)
        self.additional_coords = tuple(additional_coords)
        self.obs_index = obs_index
        self.center = center
        self.postselect = postselect

    def __eq__(self, other):
        if not isinstance(other, Flow):
            return NotImplemented
        return (
            self.start == other.start
            and self.end == other.end
            and self.measurement_indices == other.measurement_indices
            and self.obs_index == other.obs_index
            and self.additional_coords == other.additional_coords
            and self.center == other.center
            and self.postselect == other.postselect
        )

    def __repr__(self):
        return (
            f"Flow(start={self.start!r}, "
            f"end={self.end!r}, "
            f"measurement_indices={self.measurement_indices!r}, "
            f"additional_coords={self.additional_coords!r}, "
            f"obs_index={self.obs_index!r}, "
            f"postselect={self.postselect!r})"
        )

    def postselected(self) -> "Flow":
        return Flow(
            start=self.start,
            end=self.end,
            measurement_indices=self.measurement_indices,
            obs_index=self.obs_index,
            additional_coords=self.additional_coords,
            center=self.center,
            postselect=True,
        )

    def with_xz_flipped(self) -> "Flow":
        return Flow(
            start=self.start.with_xz_flipped(),
            end=self.end.with_xz_flipped(),
            measurement_indices=self.measurement_indices,
            obs_index=self.obs_index,
            additional_coords=self.additional_coords,
            center=self.center,
            postselect=self.postselect,
        )

    def with_transformed_coords(
        self, transform: Callable[[complex], complex]
    ) -> "Flow":
        return Flow(
            start=self.start.with_transformed_coords(transform),
            end=self.end.with_transformed_coords(transform),
            measurement_indices=self.measurement_indices,
            obs_index=self.obs_index,
            additional_coords=self.additional_coords,
            center=transform(self.center),
            postselect=self.postselect,
        )

    def concat(self, other: "Flow", other_measure_offset: int) -> "Flow":
        if other.start != self.end:
            raise ValueError("other.start != self.end")
        if other.obs_index != self.obs_index:
            raise ValueError("other.obs_index != self.obs_index")
        if other.additional_coords != self.additional_coords:
            raise ValueError("other.additional_coords != self.additional_coords")
        return Flow(
            start=self.start,
            end=other.end,
            center=(self.center + other.center) / 2,
            measurement_indices=self.measurement_indices
            + tuple(m + other_measure_offset for m in other.measurement_indices),
            obs_index=self.obs_index,
            additional_coords=self.additional_coords,
            postselect=self.postselect or other.postselect,
        )
