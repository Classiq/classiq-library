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

from gen._core._util import min_max_complex, sorted_complex


def test_sorted_complex():
    assert sorted_complex([1, 2j, 2, 1 + 2j]) == [2j, 1, 1 + 2j, 2]


def test_min_max_complex():
    with pytest.raises(ValueError):
        min_max_complex([])
    assert min_max_complex([], default=0) == (0, 0)
    assert min_max_complex([], default=1 + 2j) == (1 + 2j, 1 + 2j)
    assert min_max_complex([1j], default=0) == (1j, 1j)
    assert min_max_complex([1j, 2]) == (0, 2 + 1j)
    assert min_max_complex([1j + 1, 2]) == (1, 2 + 1j)
