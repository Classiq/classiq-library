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
import pathlib
from typing import Any

import gen


@dataclasses.dataclass
class Params:
    style: str
    rounds: int
    diameter: int
    noise_strength: float
    noise_model: gen.NoiseModel | None
    debug_out_dir: pathlib.Path | None
    convert_to_cz: bool
    editable_extras: dict[str, Any]
