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

#include "chromobius/graph/collect_atomic_errors.h"

using namespace chromobius;

static void extract_atomic_errors_from_dem_error_instruction_dets(
    std::span<const node_offset_int> dets,
    obsmask_int obs_flip,
    std::span<const ColorBasis> node_colors,
    std::map<AtomicErrorKey, obsmask_int> *out_atomic_errors) {
    switch (dets.size()) {
        case 1: {
            (*out_atomic_errors)[AtomicErrorKey{dets[0], BOUNDARY_NODE, BOUNDARY_NODE}] = obs_flip;
            return;
        }
        case 2: {
            ColorBasis c0 = node_colors[dets[0]];
            ColorBasis c1 = node_colors[dets[1]];
            if (c0.basis == c1.basis) {
                (*out_atomic_errors)[AtomicErrorKey{dets[0], dets[1], BOUNDARY_NODE}] = obs_flip;
            }
            return;
        }
        case 3: {
            ColorBasis c0 = node_colors[dets[0]];
            ColorBasis c1 = node_colors[dets[1]];
            ColorBasis c2 = node_colors[dets[2]];
            Charge net_charge = c0.color ^ c1.color ^ c2.color;
            if (net_charge == Charge::NEUTRAL && c0.basis == c1.basis && c1.basis == c2.basis) {
                (*out_atomic_errors)[AtomicErrorKey{dets[0], dets[1], dets[2]}] = obs_flip;
            }
            return;
        }
    }
}

void chromobius::extract_obs_and_dets_from_error_instruction(
    stim::DemInstruction instruction,
    stim::SparseXorVec<node_offset_int> *out_xor_detectors_buffer,
    obsmask_int *out_obs_flip) {
    out_xor_detectors_buffer->clear();
    *out_obs_flip = 0;
    for (const auto &t : instruction.target_data) {
        if (t.is_relative_detector_id()) {
            uint64_t u = t.raw_id();
            if (u > std::numeric_limits<node_offset_int>::max()) {
                std::stringstream ss;
                ss << "The detector error model is too large. It has a detector with "
                      "index ";
                ss << u;
                ss << " but the max supported by chromobius is ";
                ss << std::numeric_limits<node_offset_int>::max();
                throw std::invalid_argument(ss.str());
            }
            out_xor_detectors_buffer->xor_item((node_offset_int)u);
        } else if (t.is_observable_id()) {
            if (t.raw_id() >= sizeof(obsmask_int) * 8) {
                std::stringstream ss;
                ss << "Max logical observable is L" << (sizeof(obsmask_int) * 8 - 1);
                ss << " but a larger one appeared in '" << instruction << "'";
                throw std::invalid_argument(ss.str());
            }
            *out_obs_flip ^= obsmask_int{1} << t.raw_id();
        } else if (t.is_separator()) {
            // Ignored.
        } else {
            throw std::invalid_argument("Unrecognized target type in " + instruction.str());
        }
    }
}

std::map<AtomicErrorKey, obsmask_int> chromobius::collect_atomic_errors(
    const stim::DetectorErrorModel &dem, std::span<const ColorBasis> node_colors) {
    obsmask_int obs_flip;
    stim::SparseXorVec<node_offset_int> dets;
    std::map<AtomicErrorKey, obsmask_int> result;

    dem.iter_flatten_error_instructions([&](stim::DemInstruction instruction) {
        extract_obs_and_dets_from_error_instruction(instruction, &dets, &obs_flip);

        extract_atomic_errors_from_dem_error_instruction_dets(dets.sorted_items, obs_flip, node_colors, &result);
    });

    return result;
}
