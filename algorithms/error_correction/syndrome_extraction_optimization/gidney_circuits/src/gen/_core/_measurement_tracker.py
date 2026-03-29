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

import dataclasses
from typing import Iterable, Any

import stim


@dataclasses.dataclass(frozen=True)
class AtLayer:
    """A special class that indicates the layer to read a measurement key from."""

    key: Any
    layer: Any


class MeasurementTracker:
    """Tracks measurements and groups of measurements, for producing stim record targets."""

    def __init__(self):
        self.recorded: dict[Any, list[int] | None] = {}
        self.next_measurement_index = 0

    def copy(self) -> "MeasurementTracker":
        result = MeasurementTracker()
        result.recorded = {k: list(v) for k, v in self.recorded.items()}
        result.next_measurement_index = self.next_measurement_index
        return result

    def _rec(self, key: Any, value: list[int] | None) -> None:
        if key in self.recorded:
            raise ValueError(f"Measurement key collision: {key=}")
        self.recorded[key] = value

    def record_measurement(self, key: Any) -> None:
        self._rec(key, [self.next_measurement_index])
        self.next_measurement_index += 1

    def make_measurement_group(self, sub_keys: Iterable[Any], *, key: Any) -> None:
        self._rec(key, self.measurement_indices(sub_keys))

    def record_obstacle(self, key: Any) -> None:
        self._rec(key, None)

    def measurement_indices(self, keys: Iterable[Any]) -> list[int]:
        result = set()
        for key in keys:
            if key not in self.recorded:
                raise ValueError(f"No such measurement: {key=}")
            for v in self.recorded[key]:
                if v is None:
                    raise ValueError(f"Obstacle at {key=}")
                if v in result:
                    result.remove(v)
                else:
                    result.add(v)
        return sorted(result)

    def current_measurement_record_targets_for(
        self, keys: Iterable[Any]
    ) -> list[stim.GateTarget]:
        t0 = self.next_measurement_index
        times = self.measurement_indices(keys)
        return [stim.target_rec(t - t0) for t in sorted(times)]
