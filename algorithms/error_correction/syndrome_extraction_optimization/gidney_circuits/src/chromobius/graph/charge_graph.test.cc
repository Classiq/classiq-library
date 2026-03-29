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

#include "chromobius/graph/charge_graph.h"

#include "gtest/gtest.h"

using namespace chromobius;

TEST(charge_graph, charge_node_basics) {
    ChargeGraphNode n{.neighbors = {{5, 1}, {6, 2}}};

    ASSERT_TRUE(n == (ChargeGraphNode{.neighbors = {{5, 1}, {6, 2}}}));
    ASSERT_FALSE(n == (ChargeGraphNode{.neighbors = {{7, 1}, {6, 2}}}));
    ASSERT_FALSE(n == (ChargeGraphNode{.neighbors = {}}));
    ASSERT_FALSE(n != (ChargeGraphNode{.neighbors = {{5, 1}, {6, 2}}}));

    ASSERT_EQ(n.str(), "ChargeGraphNode{.neighbors={{5,1}, {6,2}}}");
}

TEST(charge_graph, charge_graph_basics) {
    ChargeGraph g{
        .nodes = {
            ChargeGraphNode{.neighbors = {{0, 0}, {1, 5}}},
            ChargeGraphNode{.neighbors = {{0, 5}, {1, 0}}},
        }};

    ASSERT_TRUE(
        g == (ChargeGraph{
                 .nodes = {
                     ChargeGraphNode{.neighbors = {{0, 0}, {1, 5}}},
                     ChargeGraphNode{.neighbors = {{0, 5}, {1, 0}}},
                 }}));
    ASSERT_FALSE(g == (ChargeGraph{}));
    ASSERT_TRUE(g != (ChargeGraph{}));

    ASSERT_EQ(g.str(), R"GRAPH(ChargeGraph{.nodes={
    ChargeGraphNode{.neighbors={{0,0}, {1,5}}}, // node 0
    ChargeGraphNode{.neighbors={{0,5}, {1,0}}}, // node 1
}})GRAPH");
}

TEST(charge_graph, from_dem_edges_basic_cases) {
    ChargeGraph actual;

    actual= ChargeGraph::from_atomic_errors({
    }, 3);
    ASSERT_EQ(actual, (ChargeGraph{.nodes={
        ChargeGraphNode{.neighbors={{0, 0}}},
        ChargeGraphNode{.neighbors={{1, 0}}},
        ChargeGraphNode{.neighbors={{2, 0}}},
    }}));

    actual = ChargeGraph::from_atomic_errors({
        {AtomicErrorKey{1, BOUNDARY_NODE, BOUNDARY_NODE}, 0b1},
    }, 3);
    ASSERT_EQ(actual, (ChargeGraph{.nodes={
        ChargeGraphNode{.neighbors={{0, 0}}},
        ChargeGraphNode{.neighbors={{1, 0}, {BOUNDARY_NODE, 0b1}}},
        ChargeGraphNode{.neighbors={{2, 0}}},
    }}));

    actual = ChargeGraph::from_atomic_errors({
        {AtomicErrorKey{1, 2, BOUNDARY_NODE}, 0b100},
    }, 3);
    ASSERT_EQ(actual, (ChargeGraph{.nodes={
        ChargeGraphNode{.neighbors={{0, 0}}},
        ChargeGraphNode{.neighbors={{1, 0}, {2, 0b100}}},
        ChargeGraphNode{.neighbors={{1, 0b100}, {2, 0}}},
    }}));

    actual = ChargeGraph::from_atomic_errors({
        {AtomicErrorKey{1, 2, 0}, 0b100},
    }, 3);
    ASSERT_EQ(actual, (ChargeGraph{.nodes={
        ChargeGraphNode{.neighbors={{0, 0}}},
        ChargeGraphNode{.neighbors={{1, 0}}},
        ChargeGraphNode{.neighbors={{2, 0}}},
    }}));

    actual = ChargeGraph::from_atomic_errors({
        {AtomicErrorKey{1, 2, 0}, 0b100},
        {AtomicErrorKey{1, 2, 3}, 0b010},
    }, 4);
    ASSERT_EQ(actual, (ChargeGraph{.nodes={
        ChargeGraphNode{.neighbors={{0, 0}, {3, 0b110}}},
        ChargeGraphNode{.neighbors={{1, 0}}},
        ChargeGraphNode{.neighbors={{2, 0}}},
        ChargeGraphNode{.neighbors={{0, 0b110}, {3, 0}}},
    }}));
//
//     ASSERT_EQ(
//         ChargeGraph::from_dem_edges(
//             4,
//             (std::set<DemEdge>{
//                 DemEdge{.n1=2, .n2=3, .obs_flip=5},
//             }),
//             (std::set<RgbEdge>{})),
//         (ChargeGraph{.nodes={
//             ChargeGraphNode{.neighbors={{0, 0}}},
//             ChargeGraphNode{.neighbors={{1, 0}}},
//             ChargeGraphNode{.neighbors={{2, 0}, {3, 5}}},
//             ChargeGraphNode{.neighbors={{3, 0}, {2, 5}}},
//         }}));
//
//     ASSERT_EQ(
//         ChargeGraph::from_dem_edges(
//             3,
//             (std::set<DemEdge>{
//                 DemEdge{.n1=1, .n2=2, .obs_flip=5},
//             }),
//             (std::set<RgbEdge>{})),
//         (ChargeGraph{.nodes={
//             ChargeGraphNode{.neighbors={{0, 0}}},
//             ChargeGraphNode{.neighbors={{1, 0}, {2, 5}}},
//             ChargeGraphNode{.neighbors={{2, 0}, {1, 5}}},
//         }}));
//
//     ASSERT_EQ(
//         ChargeGraph::from_dem_edges(
//             7,
//             (std::set<DemEdge>{}),
//             (std::set<RgbEdge>{
//                 RgbEdge{.red_node=2, .green_node=3, .blue_node=5, .obs_flip=7},
//             })),
//         (ChargeGraph{.nodes={
//             ChargeGraphNode{.neighbors={{0, 0}}},
//             ChargeGraphNode{.neighbors={{1, 0}}},
//             ChargeGraphNode{.neighbors={{2, 0}}},
//             ChargeGraphNode{.neighbors={{3, 0}}},
//             ChargeGraphNode{.neighbors={{4, 0}}},
//             ChargeGraphNode{.neighbors={{5, 0}}},
//             ChargeGraphNode{.neighbors={{6, 0}}},
//         }}));
//
//     ASSERT_EQ(
//         ChargeGraph::from_dem_edges(
//             7,
//             (std::set<DemEdge>{}),
//             (std::set<RgbEdge>{
//                 RgbEdge{.red_node=2, .green_node=3, .blue_node=5, .obs_flip=7},
//                 RgbEdge{.red_node=2, .green_node=3, .blue_node=4, .obs_flip=1},
//             })),
//         (ChargeGraph{.nodes={
//             ChargeGraphNode{.neighbors={{0, 0}}},
//             ChargeGraphNode{.neighbors={{1, 0}}},
//             ChargeGraphNode{.neighbors={{2, 0}}},
//             ChargeGraphNode{.neighbors={{3, 0}}},
//             ChargeGraphNode{.neighbors={{4, 0}, {5, 6}}},
//             ChargeGraphNode{.neighbors={{5, 0}, {4, 6}}},
//             ChargeGraphNode{.neighbors={{6, 0}}},
//         }}));
//
//     ASSERT_EQ(
//         ChargeGraph::from_dem_edges(
//             7,
//             (std::set<DemEdge>{}),
//             (std::set<RgbEdge>{
//                 RgbEdge{.red_node=2, .green_node=3, .blue_node=5, .obs_flip=7},
//                 RgbEdge{.red_node=2, .green_node=3, .blue_node=5, .obs_flip=1},
//             })),
//         (ChargeGraph{.nodes={
//             ChargeGraphNode{.neighbors={{0, 0}}},
//             ChargeGraphNode{.neighbors={{1, 0}}},
//             ChargeGraphNode{.neighbors={{2, 0}}},
//             ChargeGraphNode{.neighbors={{3, 0}}},
//             ChargeGraphNode{.neighbors={{4, 0}}},
//             ChargeGraphNode{.neighbors={{5, 0}}},
//             ChargeGraphNode{.neighbors={{6, 0}}},
//         }}));
//
//     ASSERT_EQ(
//         ChargeGraph::from_dem_edges(
//             7,
//             (std::set<DemEdge>{}),
//             (std::set<RgbEdge>{
//                 RgbEdge{.red_node=2, .green_node=3, .blue_node=BOUNDARY_NODE, .obs_flip=7},
//                 RgbEdge{.red_node=2, .green_node=3, .blue_node=4, .obs_flip=1},
//             })),
//         (ChargeGraph{.nodes={
//             ChargeGraphNode{.neighbors={{0, 0}}},
//             ChargeGraphNode{.neighbors={{1, 0}}},
//             ChargeGraphNode{.neighbors={{2, 0}}},
//             ChargeGraphNode{.neighbors={{3, 0}}},
//             ChargeGraphNode{.neighbors={{4, 0}, {BOUNDARY_NODE, 6}}},
//             ChargeGraphNode{.neighbors={{5, 0}}},
//             ChargeGraphNode{.neighbors={{6, 0}}},
//         }}));
//
//     ASSERT_EQ(
//         ChargeGraph::from_dem_edges(
//             7,
//             (std::set<DemEdge>{}),
//             (std::set<RgbEdge>{
//                 RgbEdge{.red_node=2, .green_node=3, .blue_node=BOUNDARY_NODE, .obs_flip=7},
//                 RgbEdge{.red_node=2, .green_node=BOUNDARY_NODE, .blue_node=4, .obs_flip=8},
//             })),
//         (ChargeGraph{.nodes={
//             ChargeGraphNode{.neighbors={{0, 0}}},
//             ChargeGraphNode{.neighbors={{1, 0}}},
//             ChargeGraphNode{.neighbors={{2, 0}}},
//             ChargeGraphNode{.neighbors={{3, 0}, {4, 15}}},
//             ChargeGraphNode{.neighbors={{4, 0}, {3, 15}}},
//             ChargeGraphNode{.neighbors={{5, 0}}},
//             ChargeGraphNode{.neighbors={{6, 0}}},
//         }}));
 }
//
// TEST(charge_graph, from_dem_edges_d5) {
//     ASSERT_EQ(
//         ChargeGraph::from_dem_edges(
//             10,
//             (std::set<DemEdge>{
//                 DemEdge{.n1=1, .n2=BOUNDARY_NODE, .obs_flip=10},
//                 DemEdge{.n1=1, .n2=3, .obs_flip=11},
//                 DemEdge{.n1=1, .n2=2, .obs_flip=12},
//                 DemEdge{.n1=3, .n2=4, .obs_flip=14},
//                 DemEdge{.n1=2, .n2=5, .obs_flip=16},
//                 DemEdge{.n1=5, .n2=7, .obs_flip=19},
//                 DemEdge{.n1=4, .n2=8, .obs_flip=20},
//                 DemEdge{.n1=8, .n2=BOUNDARY_NODE, .obs_flip=24},
//                 DemEdge{.n1=6, .n2=8, .obs_flip=25},
//                 DemEdge{.n1=6, .n2=9, .obs_flip=26},
//                 DemEdge{.n1=7, .n2=9, .obs_flip=27},
//                 DemEdge{.n1=7, .n2=BOUNDARY_NODE, .obs_flip=28},
//             }),
//             (std::set<RgbEdge>{
//                 RgbEdge{.red_node=BOUNDARY_NODE, .green_node=1, .blue_node=BOUNDARY_NODE, .obs_flip=10},
//                 RgbEdge{.red_node=BOUNDARY_NODE, .green_node=1, .blue_node=3, .obs_flip=11},
//                 RgbEdge{.red_node=2, .green_node=1, .blue_node=BOUNDARY_NODE, .obs_flip=12},
//                 RgbEdge{.red_node=2, .green_node=1, .blue_node=3, .obs_flip=13},
//                 RgbEdge{.red_node=BOUNDARY_NODE, .green_node=4, .blue_node=3, .obs_flip=14},
//                 RgbEdge{.red_node=2, .green_node=5, .blue_node=3, .obs_flip=15},
//                 RgbEdge{.red_node=2, .green_node=5, .blue_node=BOUNDARY_NODE, .obs_flip=16},
//                 RgbEdge{.red_node=6, .green_node=4, .blue_node=3, .obs_flip=17},
//                 RgbEdge{.red_node=6, .green_node=5, .blue_node=3, .obs_flip=18},
//                 RgbEdge{.red_node=7, .green_node=5, .blue_node=BOUNDARY_NODE, .obs_flip=19},
//                 RgbEdge{.red_node=BOUNDARY_NODE, .green_node=4, .blue_node=8, .obs_flip=20},
//                 RgbEdge{.red_node=6, .green_node=4, .blue_node=8, .obs_flip=21},
//                 RgbEdge{.red_node=6, .green_node=5, .blue_node=9, .obs_flip=22},
//                 RgbEdge{.red_node=7, .green_node=5, .blue_node=9, .obs_flip=23},
//                 RgbEdge{.red_node=BOUNDARY_NODE, .green_node=BOUNDARY_NODE, .blue_node=8, .obs_flip=24},
//                 RgbEdge{.red_node=6, .green_node=BOUNDARY_NODE, .blue_node=8, .obs_flip=25},
//                 RgbEdge{.red_node=6, .green_node=BOUNDARY_NODE, .blue_node=9, .obs_flip=26},
//                 RgbEdge{.red_node=7, .green_node=BOUNDARY_NODE, .blue_node=9, .obs_flip=27},
//                 RgbEdge{.red_node=7, .green_node=BOUNDARY_NODE, .blue_node=BOUNDARY_NODE, .obs_flip=28},
//             })),
//         (ChargeGraph{.nodes={
//             ChargeGraphNode{.neighbors={{0, 0}}},
//             ChargeGraphNode{.neighbors={{1, 0}, {2, 12}, {3, 11}, {4, 11 ^ 14}, {5, 15 ^ 13}, {BOUNDARY_NODE, 10}}},
//             ChargeGraphNode{.neighbors={{2, 0}, {1, 12}, {3, 11 ^ 12}, {5, 16}, {6, 15 ^ 18}, {7, 19 ^ 16},
//             {BOUNDARY_NODE, 11 ^ 13}}}, ChargeGraphNode{.neighbors={{1,11}, {2,7}, {3,0}, {4,14}, {8,4}, {9,4},
//             {BOUNDARY_NODE,31}}}, ChargeGraphNode{.neighbors={{1,5}, {3,14}, {4,0}, {5,3}, {6,13}, {8,20},
//             {BOUNDARY_NODE,12}}}, ChargeGraphNode{.neighbors={{1,2}, {2,16}, {4,3}, {5,0}, {7,19}, {9,8},
//             {BOUNDARY_NODE,12}}}, ChargeGraphNode{.neighbors={{2,29}, {4,13}, {6,0}, {7,1}, {8,25}, {9,26},
//             {BOUNDARY_NODE,1}}}, ChargeGraphNode{.neighbors={{2,3}, {5,19}, {6,1}, {7,0}, {9,27},
//             {BOUNDARY_NODE,28}}}, ChargeGraphNode{.neighbors={{3,4}, {4,20}, {6,25}, {8,0}, {9,3},
//             {BOUNDARY_NODE,24}}}, ChargeGraphNode{.neighbors={{3,4}, {5,8}, {6,26}, {7,27}, {8,3}, {9,0},
//             {BOUNDARY_NODE,4}}},
//         }}));
// }
