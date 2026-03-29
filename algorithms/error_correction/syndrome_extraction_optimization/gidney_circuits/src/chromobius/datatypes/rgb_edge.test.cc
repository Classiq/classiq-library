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

#include "chromobius/datatypes/rgb_edge.h"

#include "gtest/gtest.h"

using namespace chromobius;

TEST(dem_rgb_edge, dem_rgb_edge_basics) {
    RgbEdge e{.red_node = 5, .green_node = 7, .blue_node = 9, .obs_flip = 1, .charge_flip = Charge::NEUTRAL};

    ASSERT_TRUE(e == (RgbEdge{5, 7, 9, 1, Charge::NEUTRAL}));
    ASSERT_FALSE(e == (RgbEdge{4, 7, 9, 1, Charge::NEUTRAL}));
    ASSERT_FALSE(e == (RgbEdge{5, 6, 9, 1, Charge::NEUTRAL}));
    ASSERT_FALSE(e == (RgbEdge{5, 7, 8, 1, Charge::NEUTRAL}));
    ASSERT_FALSE(e == (RgbEdge{5, 7, 9, 2, Charge::NEUTRAL}));
    ASSERT_FALSE(e == (RgbEdge{5, 7, 9, 1, Charge::R}));

    ASSERT_TRUE(e != (RgbEdge{5, 7, 9, 2, Charge::NEUTRAL}));
    ASSERT_FALSE(e != (RgbEdge{5, 7, 9, 1, Charge::NEUTRAL}));

    ASSERT_EQ(
        e.str(),
        "RgbEdge{.red_node=5, .green_node=7, .blue_node=9, .obs_flip=1, "
        ".charge_flip=NEUTRAL}");
}

TEST(dem_rgb_edge, dem_rgb_edge_weight) {
    ASSERT_EQ((RgbEdge{.red_node = 2, .green_node = 3, .blue_node = 7, .obs_flip = 5}.weight()), 3);
    ASSERT_EQ((RgbEdge{.red_node = 2, .green_node = 3, .blue_node = 7, .obs_flip = 0}.weight()), 3);
    ASSERT_EQ(
        (RgbEdge{.red_node = BOUNDARY_NODE, .green_node = BOUNDARY_NODE, .blue_node = 7, .obs_flip = 5}.weight()), 1);
    ASSERT_EQ(
        (RgbEdge{.red_node = BOUNDARY_NODE, .green_node = BOUNDARY_NODE, .blue_node = BOUNDARY_NODE, .obs_flip = 5}
             .weight()),
        0);
    ASSERT_EQ((RgbEdge{.red_node = BOUNDARY_NODE, .green_node = 3, .blue_node = 7, .obs_flip = 5}.weight()), 2);
    ASSERT_EQ((RgbEdge{.red_node = 2, .green_node = BOUNDARY_NODE, .blue_node = 7, .obs_flip = 5}.weight()), 2);
    ASSERT_EQ((RgbEdge{.red_node = 2, .green_node = 5, .blue_node = BOUNDARY_NODE, .obs_flip = 5}.weight()), 2);
}
