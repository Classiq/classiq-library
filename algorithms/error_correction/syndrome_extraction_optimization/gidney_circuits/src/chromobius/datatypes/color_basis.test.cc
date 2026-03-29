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

#include "chromobius/datatypes/color_basis.h"

#include "gtest/gtest.h"

using namespace chromobius;

TEST(types, color_basis_basic) {
    ColorBasis e{.color = Charge::R, .basis = Basis::X};

    ASSERT_TRUE(e == (ColorBasis{.color = Charge::R, .basis = Basis::X}));
    ASSERT_FALSE(e == (ColorBasis{.color = Charge::G, .basis = Basis::X}));
    ASSERT_FALSE(e == (ColorBasis{.color = Charge::R, .basis = Basis::Z}));

    ASSERT_TRUE(e != (ColorBasis{.color = Charge::G, .basis = Basis::X}));

    ASSERT_EQ(e.str(), "ColorBasis{.color=R, .basis=X}");
}

TEST(atomic_error, detector_instruction_to_color_basis) {
    std::vector<double> args{-1, -1, -1, 2};
    std::vector<double> offsets{-3, -3, -3, 3, -2};
    stim::DemInstruction instruction{
        .arg_data = args,
        .target_data = {},
        .type = stim::DemInstructionType::DEM_ERROR,
    };
    ASSERT_EQ(detector_instruction_to_color_basis(instruction, offsets), (ColorBasis{Charge::B, Basis::Z}));
    offsets[3] = 100;
    ASSERT_THROW({ detector_instruction_to_color_basis(instruction, offsets); }, std::invalid_argument);
    offsets[3] = 0.5;
    ASSERT_THROW({ detector_instruction_to_color_basis(instruction, offsets); }, std::invalid_argument);
    args[3] = 0.5;
    ASSERT_EQ(detector_instruction_to_color_basis(instruction, offsets), (ColorBasis{Charge::G, Basis::X}));
}

TEST(atomic_error, mobius_node_to_detector_vs_detector_to_mobius_node) {
    std::vector<ColorBasis> colors;
    colors.resize(50);

    colors[29].color = Charge::R;
    ASSERT_EQ(
        mobius_node_to_detector(29 * 2 + SUBGRAPH_OFFSET_Red_NotGreen, colors),
        (std::tuple<node_offset_int, Charge, SubGraphCoord>(29, Charge::R, SubGraphCoord::NotGreen)));
    ASSERT_EQ(detector_to_mobius_node(29, SubGraphCoord::NotGreen, colors), 29 * 2 + SUBGRAPH_OFFSET_Red_NotGreen);

    colors[31].color = Charge::R;
    ASSERT_EQ(
        mobius_node_to_detector(31 * 2 + SUBGRAPH_OFFSET_Red_NotBlue, colors),
        (std::tuple<node_offset_int, Charge, SubGraphCoord>(31, Charge::R, SubGraphCoord::NotBlue)));
    ASSERT_EQ(detector_to_mobius_node(31, SubGraphCoord::NotBlue, colors), 31 * 2 + SUBGRAPH_OFFSET_Red_NotBlue);

    colors[36].color = Charge::G;
    ASSERT_EQ(
        mobius_node_to_detector(36 * 2 + SUBGRAPH_OFFSET_Green_NotRed, colors),
        (std::tuple<node_offset_int, Charge, SubGraphCoord>(36, Charge::G, SubGraphCoord::NotRed)));
    ASSERT_EQ(detector_to_mobius_node(36, SubGraphCoord::NotRed, colors), 36 * 2 + SUBGRAPH_OFFSET_Green_NotRed);

    colors[41].color = Charge::G;
    ASSERT_EQ(
        mobius_node_to_detector(41 * 2 + SUBGRAPH_OFFSET_Green_NotBlue, colors),
        (std::tuple<node_offset_int, Charge, SubGraphCoord>(41, Charge::G, SubGraphCoord::NotBlue)));
    ASSERT_EQ(detector_to_mobius_node(41, SubGraphCoord::NotBlue, colors), 41 * 2 + SUBGRAPH_OFFSET_Green_NotBlue);

    colors[43].color = Charge::B;
    ASSERT_EQ(
        mobius_node_to_detector(43 * 2 + SUBGRAPH_OFFSET_Blue_NotRed, colors),
        (std::tuple<node_offset_int, Charge, SubGraphCoord>(43, Charge::B, SubGraphCoord::NotRed)));
    ASSERT_EQ(detector_to_mobius_node(43, SubGraphCoord::NotRed, colors), 43 * 2 + SUBGRAPH_OFFSET_Blue_NotRed);

    colors[47].color = Charge::B;
    ASSERT_EQ(
        mobius_node_to_detector(47 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen, colors),
        (std::tuple<node_offset_int, Charge, SubGraphCoord>(47, Charge::B, SubGraphCoord::NotGreen)));
    ASSERT_EQ(detector_to_mobius_node(47, SubGraphCoord::NotGreen, colors), 47 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen);
}
