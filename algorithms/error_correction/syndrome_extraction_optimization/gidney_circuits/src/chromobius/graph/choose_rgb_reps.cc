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

using namespace chromobius;

std::vector<RgbEdge> chromobius::choose_rgb_reps_from_atomic_errors(
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors, std::span<const ColorBasis> node_colors) {
    std::vector<RgbEdge> result;
    RgbEdge empty{
        .red_node = BOUNDARY_NODE,
        .green_node = BOUNDARY_NODE,
        .blue_node = BOUNDARY_NODE,
        .obs_flip = 0,
        .charge_flip = Charge::NEUTRAL,
    };
    result.resize(node_colors.size(), empty);

    // Assign node representatives from the highest weight RGB edges they are part
    // of.
    for (const auto &[err, obs_flip] : atomic_errors) {
        RgbEdge rep{BOUNDARY_NODE, BOUNDARY_NODE, BOUNDARY_NODE, obs_flip, Charge::NEUTRAL};
        size_t weight = 0;
        for (auto n : err.dets) {
            if (n != BOUNDARY_NODE) {
                Charge c = node_colors[n].color;
                rep.color_node(c) = n;
                rep.charge_flip ^= c;
                weight += 1;
            }
        }

        if (rep.weight() != weight) {
            // Color appeared more than once.
            continue;
        }

        for (node_offset_int n : err.dets) {
            if (n != BOUNDARY_NODE && weight > result[n].weight()) {
                result[n] = rep;
            }
        }
    }

    // In a phenom circuit, the final layer of stabilizer measurements has no
    // RGB errors. As a result, the detectors from this layer need to be linked
    // together using RGB errors from the previous layer times a measurement error
    // to the final layer.
    for (const auto &[e, obs_flip] : atomic_errors) {
        if (e.weight() != 2) {
            continue;
        }
        Charge c1 = node_colors[e.dets[0]].color;
        Charge c2 = node_colors[e.dets[1]].color;
        if (c1 == c2) {
            auto w1 = result[e.dets[0]].weight();
            auto w2 = result[e.dets[1]].weight();
            RgbEdge *r1 = &result[e.dets[0]];
            RgbEdge *r2 = &result[e.dets[1]];
            if (w1 == 0 && w2 > 0) {
                *r1 = *r2;
                assert(r1->color_node(c1) == e.dets[1]);
                assert(r2->color_node(c1) == e.dets[1]);
                r1->color_node(c1) = e.dets[0];
                r1->obs_flip ^= obs_flip;
            }
            if (w2 == 0 && w1 > 0) {
                *r2 = *r1;
                assert(r1->color_node(c2) == e.dets[0]);
                assert(r2->color_node(c2) == e.dets[0]);
                r2->color_node(c2) = e.dets[1];
                r2->obs_flip ^= obs_flip;
            }
        }
    }

    return result;
}
