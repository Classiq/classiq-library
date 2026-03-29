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

#include "chromobius/graph/euler_tours.h"

#include "gtest/gtest.h"

using namespace chromobius;

TEST(euler_tours, euler_tours_of_edge_list) {
    EulerTourGraph g(10);

    auto do_case = [&](std::vector<std::pair<node_offset_int, node_offset_int>> edge_list) {
        std::vector<std::vector<node_offset_int>> result;
        std::vector<ColorBasis> node_colors;
        node_colors.resize(g.nodes.size(), ColorBasis{Charge::R, Basis::X});

        std::vector<int64_t> interleaved_edges;
        for (auto [a, b] : edge_list) {
            interleaved_edges.push_back(a);
            interleaved_edges.push_back(b);
        }

        g.iter_euler_tours_of_interleaved_edge_list(
            interleaved_edges, {}, [&](std::span<const node_offset_int> cycle) {
                result.push_back({});
                for (size_t k = 0; k < cycle.size(); k++) {
                    result.back().push_back(cycle[k]);
                }
            });

        return result;
    };

    ASSERT_EQ((do_case({})), (std::vector<std::vector<node_offset_int>>{}));

    ASSERT_THROW(
        {
            do_case({
                {1, 2},
            });
        },
        std::invalid_argument);

    ASSERT_EQ(
        (do_case({
            {1, 2},
            {2, 1},
        })),
        (std::vector<std::vector<node_offset_int>>{
            {1, 2},
        }));

    ASSERT_EQ(
        (do_case({
            {1, 2},
            {3, 1},
            {2, 3},
        })),
        (std::vector<std::vector<node_offset_int>>{
            {1, 2, 3},
        }));

    ASSERT_EQ(
        (do_case({
            {1, 2},
            {4, 5},
            {2, 1},
            {5, 6},
            {6, 4},
        })),
        (std::vector<std::vector<node_offset_int>>{
            {1, 2},
            {4, 5, 6},
        }));

    ASSERT_EQ(
        (do_case({
            {1, 2},
            {2, 1},
            {2, 3},
            {3, 2},
            {3, 4},
            {4, 3},
            {2, 5},
            {5, 2},
        })),
        (std::vector<std::vector<node_offset_int>>{
            {3, 2, 5, 2, 1, 2, 3, 4},
        }));
}
