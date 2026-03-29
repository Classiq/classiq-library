// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "chromobius/graph/choose_rgb_reps.h"

#include "gtest/gtest.h"

using namespace chromobius;

TEST(choose_rgb_reps, choose_rgb_reps_from_atomic_errors) {
    std::vector<ColorBasis> node_colors{
        ColorBasis{.color = R, .basis = X},
        ColorBasis{.color = G, .basis = X},
        ColorBasis{.color = B, .basis = X},
        ColorBasis{.color = R, .basis = X},
    };
    std::map<AtomicErrorKey, obsmask_int> atomic_errors{
        {AtomicErrorKey{0, 1, 2}, 1},
        {AtomicErrorKey{2, 3, BOUNDARY_NODE}, 02},
    };

    auto reps = choose_rgb_reps_from_atomic_errors(atomic_errors, node_colors);
    ASSERT_EQ(
        reps,
        (std::vector<RgbEdge>{
            RgbEdge{.red_node = 0, .green_node = 1, .blue_node = 2, .obs_flip = 1, .charge_flip = Charge::NEUTRAL},
            RgbEdge{.red_node = 0, .green_node = 1, .blue_node = 2, .obs_flip = 1, .charge_flip = Charge::NEUTRAL},
            RgbEdge{.red_node = 0, .green_node = 1, .blue_node = 2, .obs_flip = 1, .charge_flip = Charge::NEUTRAL},
            RgbEdge{
                .red_node = 3, .green_node = BOUNDARY_NODE, .blue_node = 2, .obs_flip = 2, .charge_flip = Charge::G},
        }));
}
