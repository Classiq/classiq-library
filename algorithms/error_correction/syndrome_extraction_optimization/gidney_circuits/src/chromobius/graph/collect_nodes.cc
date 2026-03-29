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

#include "chromobius/graph/collect_nodes.h"

using namespace chromobius;

static void collect_nodes_from_dem_helper_process_detector_instruction(
    stim::DemInstruction instruction,
    std::span<const double> coord_offsets,
    uint64_t det_offset,
    std::vector<double> *coord_buffer,
    std::span<ColorBasis> out_node_color,
    stim::DetectorErrorModel *out_mobius_dem) {
    double c = -1;
    if (instruction.arg_data.size() > 3) {
        c = instruction.arg_data[3];
        if (coord_offsets.size() > 3) {
            c += coord_offsets[3];
        }
    }
    int r = (int)c;
    if (r < 0 || r >= 6 || r != c) {
        throw std::invalid_argument(
            "Expected all detectors to have at least 4 coordinates, with the 4th "
            "identifying the basis and color "
            "(RedX=0, GreenX=1, BlueX=2, RedZ=3, GreenZ=4, BlueZ=5), but got " +
            instruction.str());
    }
    constexpr std::array<ColorBasis, 6> mapping{
        ColorBasis{Charge::R, Basis::X},
        ColorBasis{Charge::G, Basis::X},
        ColorBasis{Charge::B, Basis::X},
        ColorBasis{Charge::R, Basis::Z},
        ColorBasis{Charge::G, Basis::Z},
        ColorBasis{Charge::B, Basis::Z},
    };
    ColorBasis cb = mapping[r];

    for (const auto &t : instruction.target_data) {
        auto n = t.raw_id() + det_offset;
        out_node_color[n] = cb;

        if (out_mobius_dem != nullptr) {
            SubGraphCoord g0;
            SubGraphCoord g1;
            switch (cb.color) {
                case Charge::R:
                    g0 = SubGraphCoord::NotGreen;
                    g1 = SubGraphCoord::NotBlue;
                    break;
                case Charge::G:
                    g0 = SubGraphCoord::NotRed;
                    g1 = SubGraphCoord::NotBlue;
                    break;
                case Charge::B:
                    g0 = SubGraphCoord::NotRed;
                    g1 = SubGraphCoord::NotGreen;
                    break;
                default:
                    throw std::invalid_argument("Uncolored detection event from " + instruction.str());
            }
            assert(g1 > g0);

            coord_buffer->clear();
            coord_buffer->insert(coord_buffer->begin(), instruction.arg_data.begin(), instruction.arg_data.end());
            for (size_t k = 0; k < coord_offsets.size() && k < coord_buffer->size(); k++) {
                (*coord_buffer)[k] += coord_offsets[k];
            }
            coord_buffer->push_back(-1);

            stim::DemTarget d0 = stim::DemTarget::relative_detector_id(n * 2 + 0);
            stim::DemTarget d1 = stim::DemTarget::relative_detector_id(n * 2 + 1);

            coord_buffer->back() = (double)g0;
            out_mobius_dem->append_detector_instruction(*coord_buffer, d0);
            coord_buffer->back() = (double)g1;
            out_mobius_dem->append_detector_instruction(*coord_buffer, d1);
        }
    }
}

static void collect_nodes_from_dem_helper(
    const stim::DetectorErrorModel &dem,
    uint64_t *det_offset,
    std::vector<double> *coord_offsets,
    std::vector<double> *coord_buffer,
    std::span<ColorBasis> out_node_color,
    stim::DetectorErrorModel *out_mobius_dem) {
    for (const auto &instruction : dem.instructions) {
        switch (instruction.type) {
            case stim::DemInstructionType::DEM_DETECTOR: {
                collect_nodes_from_dem_helper_process_detector_instruction(
                    instruction, *coord_offsets, *det_offset, coord_buffer, out_node_color, out_mobius_dem);
                break;
            }
            case stim::DemInstructionType::DEM_SHIFT_DETECTORS: {
                if (!instruction.target_data.empty()) {
                    *det_offset += instruction.target_data[0].raw_id();
                }
                for (size_t k = 0; k < instruction.arg_data.size(); k++) {
                    if (coord_offsets->size() < instruction.arg_data.size()) {
                        coord_offsets->push_back(0);
                    }
                    (*coord_offsets)[k] += instruction.arg_data[k];
                }
                break;
            }
            case stim::DemInstructionType::DEM_REPEAT_BLOCK: {
                const auto &block = instruction.repeat_block_body(dem);
                auto reps = instruction.repeat_block_rep_count();
                for (uint64_t k = 0; k < reps; k++) {
                    collect_nodes_from_dem_helper(
                        block, det_offset, coord_offsets, coord_buffer, out_node_color, out_mobius_dem);
                }
                break;
            }
            case stim::DemInstructionType::DEM_ERROR:
                // Ignored.
                break;
            case stim::DemInstructionType::DEM_LOGICAL_OBSERVABLE:
                // Ignored.
                break;
            default:
                throw std::invalid_argument("Unrecognized instruction type: " + instruction.str());
        }
    }
}

std::vector<ColorBasis> chromobius::collect_nodes_from_dem(
    const stim::DetectorErrorModel &dem, stim::DetectorErrorModel *out_mobius_dem) {
    uint64_t det_offset = 0;
    std::vector<double> coord_offsets;
    std::vector<double> coord_buffer;
    std::vector<ColorBasis> result;

    uint64_t num_detectors = dem.count_detectors();
    result.resize(num_detectors);
    collect_nodes_from_dem_helper(dem, &det_offset, &coord_offsets, &coord_buffer, result, out_mobius_dem);
    return result;
}
