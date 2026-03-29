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

#include "gtest/gtest.h"

#include "chromobius/commands/main_all.test.h"

using namespace chromobius;

TEST(main_describe_decoder, basic_usage) {
    auto result = result_of_running_main(
        {"describe_decoder"},
        R"stdin(
        error(0.1) D0 L0
        error(0.1) D0 D1 L1
        error(0.1) D1 L2
        detector(0, 0, 0, 0) D0
        detector(0, 0, 0, 1) D1
      )stdin");
    ASSERT_EQ("\n" + result, R"stdout(
chromobius::Decoder{

.charge_graph=ChargeGraph{.nodes={
    ChargeGraphNode{.neighbors={{0,0}, {1,2}, {BOUNDARY_NODE,1}}}, // node 0
    ChargeGraphNode{.neighbors={{0,2}, {1,0}, {BOUNDARY_NODE,4}}}, // node 1
}}

.rgb_reps={
    RgbEdge{.red_node=0, .green_node=1, .blue_node=BOUNDARY_NODE, .obs_flip=2, .charge_flip=B} // rep 0
    RgbEdge{.red_node=0, .green_node=1, .blue_node=BOUNDARY_NODE, .obs_flip=2, .charge_flip=B} // rep 1
}

.drag_graph=DragGraph{.mmm={
    NEUTRAL@0:NEUTRAL@0 = 0
    NEUTRAL@0:R@0 = 1
    R@0:NEUTRAL@0 = 1
    NEUTRAL@0:NEUTRAL@1 = 0
    R@0:R@1 = 0
    R@0:G@1 = 2
    G@0:G@1 = 0
    NEUTRAL@1:NEUTRAL@0 = 0
    R@1:R@0 = 0
    G@1:R@0 = 2
    G@1:G@0 = 0
    NEUTRAL@1:NEUTRAL@1 = 0
    NEUTRAL@1:G@1 = 4
    G@1:NEUTRAL@1 = 4
}}

.mobius_dem=stim::DetectorErrorModel{
detector(0, 0, 0, 0, 2) D0
detector(0, 0, 0, 0, 3) D1
detector(0, 0, 0, 1, 1) D2
detector(0, 0, 0, 1, 3) D3
error(0.01000000000000000194) D0 D1
error(0.1000000000000000056) D0 D2 ^ D1 D3
error(0.01000000000000000194) D2 D3
}

}
)stdout");
}
