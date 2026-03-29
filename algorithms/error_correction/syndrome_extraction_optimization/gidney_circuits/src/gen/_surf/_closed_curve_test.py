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

from gen._surf._closed_curve import ClosedCurve


def test_to_from_cycle():
    c1 = ClosedCurve(points=[(5 + 0j), (5 + 3j), 3j, 0j], bases=["Z", "X", "Z", "X"])
    assert c1.to_cycle() == ["Z", (5 + 0j), "X", (5 + 3j), "Z", 3j, "X", 0j, "Z"]
    assert (
        ClosedCurve.from_cycle(["Z", (5 + 0j), "X", (5 + 3j), "Z", 3j, "X", 0j, "Z"])
        == c1
    )
    assert (
        ClosedCurve.from_cycle(["Z", (5 + 0j), "X", (5 + 3j), "Z", 3j, "X", 0j]) == c1
    )
    assert (
        ClosedCurve.from_cycle([(5 + 0j), "X", (5 + 3j), "Z", 3j, "X", 0j, "Z"]) == c1
    )
    assert (
        ClosedCurve.from_cycle([(5 + 0j), "X", (5 + 3j), "Z", 3j, "X", 0j, "Z", 5])
        == c1
    )

    c2 = ClosedCurve(points=[(5 + 0j), (5 + 3j), 3j, 0j], bases=["Z", "Z", "Z", "X"])
    assert (
        ClosedCurve.from_cycle(["Z", (5 + 0j), "Z", (5 + 3j), "Z", 3j, "X", 0j, "Z"])
        == c2
    )
    assert (
        ClosedCurve.from_cycle(
            ["Z", (5 + 0j), 5, 5, "X", 5, "Z", 5, "Z", (5 + 3j), "Z", 3j, "X", 0j, "Z"]
        )
        == c2
    )
    assert (
        ClosedCurve.from_cycle(["Z", (5 + 0j), (5 + 3j), "Z", 3j, "X", 0j, "Z"]) == c2
    )
    assert (
        ClosedCurve.from_cycle(["Z", (5 + 0j), "Z", (5 + 3j), 3j, "X", 0j, "Z"]) == c2
    )
    assert (
        ClosedCurve.from_cycle(["Z", (5 + 0j), (5 + 3j), "Z", 3j, "X", 0j, "Z"]) == c2
    )
    assert ClosedCurve.from_cycle([(5 + 0j), (5 + 3j), "Z", 3j, "X", 0j, "Z"]) == c2
