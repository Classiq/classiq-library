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

#include "chromobius/decode/decoder.h"

#include "gtest/gtest.h"

#include "chromobius/test_util.test.h"

using namespace chromobius;

TEST(decoder, from_dem_d5_color_code_x_only) {
    stim::DetectorErrorModel dem(R"DEM(
        error(0.1) D0 L0 L1
        error(0.1) D0 D2 L0
        error(0.1) D2 D3 L0
        error(0.1) D3 D7 L0
        error(0.1) D7 L0
        error(0.1) D0 D1
        error(0.1) D0 D1 D2 L1
        error(0.1) D1 D2 D4 L1
        error(0.1) D1 D4
        error(0.1) D4 D6
        error(0.1) D6
        error(0.1) D6 D8
        error(0.1) D4 D5 D8 L1
        error(0.1) D2 D4 D5
        error(0.1) D3 D5 D7
        error(0.1) D5 D7
        error(0.1) D5 D8 L1
        error(0.1) D2 D3 D5
        error(0.1) D4 D6 D8
        detector(+0, 0, 0, 0) D0
        detector(+0, 2, 0, 1) D2
        detector(+0, 4, 0, 2) D5
        detector(+1, 1, 0, 2) D1
        detector(+1, 3, 0, 0) D4
        detector(+1, 5, 0, 1) D8
        detector(+2, 4, 0, 2) D6
        detector(-1, 3, 0, 0) D3
        detector(-1, 5, 0, 1) D7
    )DEM");
    Decoder decoder = Decoder::from_dem(dem, DecoderConfigOptions{});
    ASSERT_EQ(
        decoder.node_colors,
        (std::vector<ColorBasis>{
            {.color = Charge::R, .basis = Basis::X},
            {.color = Charge::B, .basis = Basis::X},
            {.color = Charge::G, .basis = Basis::X},
            {.color = Charge::R, .basis = Basis::X},
            {.color = Charge::R, .basis = Basis::X},
            {.color = Charge::B, .basis = Basis::X},
            {.color = Charge::B, .basis = Basis::X},
            {.color = Charge::G, .basis = Basis::X},
            {.color = Charge::G, .basis = Basis::X}}));
    ASSERT_EQ(
        decoder.rgb_reps,
        (std::vector<RgbEdge>{
            {.red_node = 0, .green_node = 2, .blue_node = 1, .obs_flip = 0b10},
            {.red_node = 0, .green_node = 2, .blue_node = 1, .obs_flip = 0b10},
            {.red_node = 0, .green_node = 2, .blue_node = 1, .obs_flip = 0b10},
            {.red_node = 3, .green_node = 2, .blue_node = 5, .obs_flip = 0b00},
            {.red_node = 4, .green_node = 2, .blue_node = 1, .obs_flip = 0b10},
            {.red_node = 3, .green_node = 2, .blue_node = 5, .obs_flip = 0b00},
            {.red_node = 4, .green_node = 8, .blue_node = 6, .obs_flip = 0b00},
            {.red_node = 3, .green_node = 7, .blue_node = 5, .obs_flip = 0b00},
            {.red_node = 4, .green_node = 8, .blue_node = 5, .obs_flip = 0b10},
        }));
    stim::DetectorErrorModel expected_mobius_dem(R"DEM(
        error(0.01) D0 D1
        error(0.1) D0 D4 ^ D1 D5
        error(0.1) D4 D6 ^ D5 D7
        error(0.1) D6 D14 ^ D7 D15
        error(0.01) D14 D15
        error(0.1) D0 D3 ^ D1 D2
        error(0.1) D1 D5 ^ D2 D4 ^ D0 D3
        error(0.1) D5 D9 ^ D2 D4 ^ D3 D8
        error(0.1) D2 D9 ^ D3 D8
        error(0.1) D8 D13 ^ D9 D12
        error(0.01) D12 D13
        error(0.1) D12 D16 ^ D13 D17
        error(0.1) D9 D17 ^ D10 D16 ^ D8 D11
        error(0.1) D5 D9 ^ D4 D10 ^ D8 D11
        error(0.1) D7 D15 ^ D10 D14 ^ D6 D11
        error(0.1) D10 D14 ^ D11 D15
        error(0.1) D10 D16 ^ D11 D17
        error(0.1) D5 D7 ^ D4 D10 ^ D6 D11
        error(0.1) D9 D17 ^ D12 D16 ^ D8 D13
        detector D17
    )DEM");
    ASSERT_TRUE(decoder.mobius_dem.approx_equals(expected_mobius_dem, 1e-5));
}

TEST(decoder, mobius_dem) {
    stim::DetectorErrorModel dem(R"DEM(
        error(0.125) D0 D1 D2
        error(0.0625) D3 D4 D5
        error(0.0625) D0 D1 D2 D3 D4 D5
        error(0.25) D0 L1
        detector(0, 0, 0, 0) D0
        detector(0, 0, 0, 1) D1
        detector(0, 0, 0, 2) D2
        detector(0, 0, 0, 3) D3
        repeat 2 {
            detector(0, 0, 0, 4) D4
            shift_detectors(0, 0, 0, 1) 1
        }
    )DEM");

    Decoder decoder = Decoder::from_dem(dem, DecoderConfigOptions{.include_coords_in_mobius_dem=true});
    stim::DetectorErrorModel expected(R"DEM(
        detector(0, 0, 0, 0, 2) D0
        detector(0, 0, 0, 0, 3) D1
        detector(0, 0, 0, 1, 1) D2
        detector(0, 0, 0, 1, 3) D3
        detector(0, 0, 0, 2, 1) D4
        detector(0, 0, 0, 2, 2) D5
        detector(0, 0, 0, 3, 2) D6
        detector(0, 0, 0, 3, 3) D7
        detector(0, 0, 0, 4, 1) D8
        detector(0, 0, 0, 4, 3) D9
        detector(0, 0, 0, 5, 1) D10
        detector(0, 0, 0, 5, 2) D11
        error(0.125) D1 D3 ^ D2 D4 ^ D0 D5
        error(0.0625) D7 D9 ^ D8 D10 ^ D6 D11
        error(0.0625) D1 D3 ^ D2 D4 ^ D0 D5 ^ D7 D9 ^ D8 D10 ^ D6 D11
        error(0.0625) D0 D1
    )DEM");
    ASSERT_TRUE(decoder.mobius_dem.approx_equals(expected, 1e-5));
}
