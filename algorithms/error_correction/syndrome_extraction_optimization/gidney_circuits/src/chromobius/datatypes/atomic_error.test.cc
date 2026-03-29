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

#include "chromobius/datatypes/atomic_error.h"

#include "gtest/gtest.h"

using namespace chromobius;

TEST(atomic_error, sort3) {
    std::mt19937 rng;
    for (size_t k = 0; k < 1000; k++) {
        uint32_t a = rng();
        uint32_t b = rng();
        uint32_t c = rng();
        std::array<uint32_t, 3> expected{a, b, c};
        std::sort(expected.begin(), expected.end());
        auto abc = sort3(a, b, c);
        ASSERT_EQ(abc, expected) << a << ", " << b << ", " << c;
    }
}

TEST(atomic_error, atomic_error_key_basic) {
    AtomicErrorKey n{2, 3, 5};
    ASSERT_EQ(n.dets[0], 2);
    ASSERT_EQ(n.dets[1], 3);
    ASSERT_EQ(n.dets[2], 5);

    ASSERT_TRUE(n == (AtomicErrorKey{2, 3, 5}));
    ASSERT_TRUE(n == (AtomicErrorKey{3, 2, 5}));
    ASSERT_TRUE(n == (AtomicErrorKey{2, 5, 3}));
    ASSERT_TRUE(n == (AtomicErrorKey{3, 5, 2}));
    ASSERT_TRUE(n == (AtomicErrorKey{5, 2, 3}));
    ASSERT_TRUE(n == (AtomicErrorKey{5, 3, 2}));
    ASSERT_FALSE(n == (AtomicErrorKey{2, 3, 7}));
    ASSERT_FALSE(n != (AtomicErrorKey{2, 3, 5}));
    ASSERT_TRUE(n != (AtomicErrorKey{2, 3, 7}));

    ASSERT_EQ(n.str(), "AtomicErrorKey{.dets={2, 3, 5}}");
    ASSERT_EQ((AtomicErrorKey{BOUNDARY_NODE, 2, 3}).str(), "AtomicErrorKey{.dets={2, 3, BOUNDARY_NODE}}");
}

TEST(atomic_error, check_invariants) {
    std::vector<ColorBasis> colors{
        {Charge::R, Basis::X},
        {Charge::G, Basis::X},
        {Charge::B, Basis::X},
        {Charge::R, Basis::X},
        {Charge::R, Basis::Z},
    };

    AtomicErrorKey k{0, 1, 2};
    k.check_invariants(colors);

    k.dets[0] = 3;
    ASSERT_THROW({ k.check_invariants(colors); }, std::invalid_argument);

    k.dets[0] = 0;
    k.dets[2] = 9;
    ASSERT_THROW({ k.check_invariants(colors); }, std::invalid_argument);

    k.dets[2] = BOUNDARY_NODE;
    k.check_invariants(colors);

    k.dets[0] = BOUNDARY_NODE;
    k.dets[1] = BOUNDARY_NODE;
    ASSERT_THROW({ k.check_invariants(colors); }, std::invalid_argument);

    k.dets = {0, 1, 3};
    ASSERT_THROW({ k.check_invariants(colors); }, std::invalid_argument);
}

TEST(atomic_error, iter_mobius_edges) {
    std::vector<ColorBasis> node_colors{
        ColorBasis{Charge::R, Basis::X},
        ColorBasis{Charge::G, Basis::X},
        ColorBasis{Charge::B, Basis::X},
        ColorBasis{Charge::R, Basis::X},
        ColorBasis{Charge::G, Basis::X},
        ColorBasis{Charge::B, Basis::X},
    };
    using S = std::set<std::pair<node_offset_int, node_offset_int>>;
    auto collect = [&](AtomicErrorKey atom) {
        S result;
        atom.iter_mobius_edges(node_colors, [&](node_offset_int d1, node_offset_int d2) {
            result.insert({d1, d2});
        });
        return result;
    };

    // Empty.
    ASSERT_EQ(collect(AtomicErrorKey{BOUNDARY_NODE, BOUNDARY_NODE, BOUNDARY_NODE}), (S{}));
    // Single.
    ASSERT_EQ(
        collect(AtomicErrorKey{0, BOUNDARY_NODE, BOUNDARY_NODE}),
        (S{
            {0, 1},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{1, BOUNDARY_NODE, BOUNDARY_NODE}),
        (S{
            {2, 3},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{2, BOUNDARY_NODE, BOUNDARY_NODE}),
        (S{
            {4, 5},
        }));

    // Same-color Pair.
    ASSERT_EQ(
        collect(AtomicErrorKey{0, 3, BOUNDARY_NODE}),
        (S{
            {0, 6},
            {1, 7},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{1, 4, BOUNDARY_NODE}),
        (S{
            {2, 8},
            {3, 9},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{2, 5, BOUNDARY_NODE}),
        (S{
            {4, 10},
            {5, 11},
        }));

    // RG Pair.
    ASSERT_EQ(
        collect(AtomicErrorKey{0, 1, BOUNDARY_NODE}),
        (S{
            {0, 2},
            {1, 3},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{3, 1, BOUNDARY_NODE}),
        (S{
            {2, 6},
            {3, 7},
        }));

    // RG Pair.
    ASSERT_EQ(
        collect(AtomicErrorKey{0, 1, BOUNDARY_NODE}),
        (S{
            {0 * 2 + SUBGRAPH_OFFSET_Red_NotGreen, 1 * 2 + SUBGRAPH_OFFSET_Green_NotRed},
            {0 * 2 + SUBGRAPH_OFFSET_Red_NotBlue, 1 * 2 + SUBGRAPH_OFFSET_Green_NotBlue},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{3, 1, BOUNDARY_NODE}),
        (S{
            {1 * 2 + SUBGRAPH_OFFSET_Green_NotRed, 3 * 2 + SUBGRAPH_OFFSET_Red_NotGreen},
            {1 * 2 + SUBGRAPH_OFFSET_Green_NotBlue, 3 * 2 + SUBGRAPH_OFFSET_Red_NotBlue},
        }));

    // RB Pair.
    ASSERT_EQ(
        collect(AtomicErrorKey{0, 2, BOUNDARY_NODE}),
        (S{
            {0 * 2 + SUBGRAPH_OFFSET_Red_NotBlue, 2 * 2 + SUBGRAPH_OFFSET_Blue_NotRed},
            {0 * 2 + SUBGRAPH_OFFSET_Red_NotGreen, 2 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{3, 2, BOUNDARY_NODE}),
        (S{
            {2 * 2 + SUBGRAPH_OFFSET_Blue_NotRed, 3 * 2 + SUBGRAPH_OFFSET_Red_NotBlue},
            {2 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen, 3 * 2 + SUBGRAPH_OFFSET_Red_NotGreen},
        }));

    // GB Pair.
    ASSERT_EQ(
        collect(AtomicErrorKey{1, 2, BOUNDARY_NODE}),
        (S{
            {1 * 2 + SUBGRAPH_OFFSET_Green_NotBlue, 2 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen},
            {1 * 2 + SUBGRAPH_OFFSET_Green_NotRed, 2 * 2 + SUBGRAPH_OFFSET_Blue_NotRed},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{4, 2, BOUNDARY_NODE}),
        (S{
            {2 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen, 4 * 2 + SUBGRAPH_OFFSET_Green_NotBlue},
            {2 * 2 + SUBGRAPH_OFFSET_Blue_NotRed, 4 * 2 + SUBGRAPH_OFFSET_Green_NotRed},
        }));

    // RGB triplet.
    ASSERT_EQ(
        collect(AtomicErrorKey{0, 1, 2}),
        (S{
            {0 * 2 + SUBGRAPH_OFFSET_Red_NotGreen, 2 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen},
            {0 * 2 + SUBGRAPH_OFFSET_Red_NotBlue, 1 * 2 + SUBGRAPH_OFFSET_Green_NotBlue},
            {1 * 2 + SUBGRAPH_OFFSET_Green_NotRed, 2 * 2 + SUBGRAPH_OFFSET_Blue_NotRed},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{1, 2, 3}),
        (S{
            {2 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen, 3 * 2 + SUBGRAPH_OFFSET_Red_NotGreen},
            {1 * 2 + SUBGRAPH_OFFSET_Green_NotBlue, 3 * 2 + SUBGRAPH_OFFSET_Red_NotBlue},
            {1 * 2 + SUBGRAPH_OFFSET_Green_NotRed, 2 * 2 + SUBGRAPH_OFFSET_Blue_NotRed},
        }));
    ASSERT_EQ(
        collect(AtomicErrorKey{2, 3, 4}),
        (S{
            {2 * 2 + SUBGRAPH_OFFSET_Blue_NotGreen, 3 * 2 + SUBGRAPH_OFFSET_Red_NotGreen},
            {3 * 2 + SUBGRAPH_OFFSET_Red_NotBlue, 4 * 2 + SUBGRAPH_OFFSET_Green_NotBlue},
            {2 * 2 + SUBGRAPH_OFFSET_Blue_NotRed, 4 * 2 + SUBGRAPH_OFFSET_Green_NotRed},
        }));
}
