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

from typing import Callable, Iterable, TypeVar, Any

TItem = TypeVar("TItem")


def complex_key(c: complex) -> Any:
    return c.real != int(c.real), c.real, c.imag


def sorted_complex(
    values: Iterable[TItem], *, key: Callable[[TItem], Any] = lambda e: e
) -> list[TItem]:
    return sorted(values, key=lambda e: complex_key(key(e)))


def min_max_complex(
    coords: Iterable[complex], *, default: complex | None = None
) -> tuple[complex, complex]:
    """Computes the bounding box of a collection of complex numbers.

    Args:
        coords: The complex numbers to place a bounding box around.
        default: If no elements are included, the bounding box will cover this
            single value when the collection of complex numbers is empty. If
            this argument isn't set (or is set to None), an exception will be
            raised instead when given an empty collection.

    Returns:
        A pair of complex values (c_min, c_max) where c_min's real component
        where c_min is the minimum corner of the bounding box and c_max is the
        maximum corner of the bounding box.
    """
    coords = list(coords)
    if not coords and default is not None:
        return default, default
    real = [c.real for c in coords]
    imag = [c.imag for c in coords]
    min_r = min(real)
    min_i = min(imag)
    max_r = max(real)
    max_i = max(imag)
    return min_r + min_i * 1j, max_r + max_i * 1j
