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

import stim

from gen._util import estimate_qubit_count_during_postselection


def test_estimate_qubit_count_during_postselection():
    assert (
        estimate_qubit_count_during_postselection(
            stim.Circuit(
                """
        QUBIT_COORDS(0, 0) 100
        H 55
        M 55
    """
            )
        )
        == 0
    )

    assert (
        estimate_qubit_count_during_postselection(
            stim.Circuit(
                """
        QUBIT_COORDS(0, 0) 100
        H 55
        M 55
        DETECTOR(0, 0, 0, 999) rec[-1]
    """
            )
        )
        == 1
    )

    assert (
        estimate_qubit_count_during_postselection(
            stim.Circuit(
                """
        QUBIT_COORDS(0, 0) 100
        H 55 56
        M 55
        DETECTOR(0, 0, 0, 999) rec[-1]
    """
            )
        )
        == 2
    )

    assert (
        estimate_qubit_count_during_postselection(
            stim.Circuit(
                """
        QUBIT_COORDS(0, 0) 100
        H 55 56
        M 55
        DETECTOR(0, 0, 0, 999) rec[-1]
        H 57
    """
            )
        )
        == 2
    )

    assert (
        estimate_qubit_count_during_postselection(
            stim.Circuit(
                """
        QUBIT_COORDS(0, 0) 100
        H 55 56
        M 55
        REPEAT 10 {
            H 58
        }
        DETECTOR(0, 0, 0, 999) rec[-1]
        H 57
    """
            )
        )
        == 3
    )
