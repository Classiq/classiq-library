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

from typing import Iterator

from gen._surf._path_outline import PathOutline


class CssObservableBoundaryPair:
    def __init__(self, *, x_obs: PathOutline, z_obs: PathOutline):
        self.x_obs = x_obs
        self.z_obs = z_obs

    def __iter__(self) -> Iterator[tuple[str, PathOutline]]:
        yield "X", self.x_obs
        yield "Z", self.z_obs
