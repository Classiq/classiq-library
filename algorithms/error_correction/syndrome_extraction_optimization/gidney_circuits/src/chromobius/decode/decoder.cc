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

#include "chromobius/decode/pymatcher.h"
#include "chromobius/graph/choose_rgb_reps.h"
#include "chromobius/graph/collect_composite_errors.h"
#include "chromobius/graph/collect_nodes.h"

using namespace chromobius;

Decoder Decoder::from_dem(const stim::DetectorErrorModel &dem, DecoderConfigOptions options) {
    Decoder result;

    // Find color of each detector, while optionally adding coordinate data to the mobius dem.
    result.node_colors = collect_nodes_from_dem(dem, options.include_coords_in_mobius_dem ? &result.mobius_dem : nullptr);

    // Find the basic building-block errors that errors will be decomposed into.
    result.atomic_errors = collect_atomic_errors(dem, result.node_colors);

    // Decompose all errors into the building-block errors, adding them into the mobius dem.
    // To make the decomposition more robust, a composite error can split into a known building block and a remnant.
    // The remnants are accumulated so they can be added to the building blocks before continuing.
    std::map<AtomicErrorKey, obsmask_int> remnant_edges;
    collect_composite_errors_and_remnants_into_mobius_dem(
        dem,
        result.node_colors,
        result.atomic_errors,
        options.drop_mobius_errors_involving_remnant_errors,
        options.ignore_decomposition_failures,
        &result.mobius_dem,
        &remnant_edges);
    for (const auto &e : remnant_edges) {
        result.atomic_errors.emplace(std::move(e));
    }
    if (!options.include_coords_in_mobius_dem || result.mobius_dem.count_detectors() < result.node_colors.size() * 2) {
        // Ensure the number of detectors in the mobius dem is exactly correct.
        result.mobius_dem.append_detector_instruction(
            {}, stim::DemTarget::relative_detector_id(result.node_colors.size() * 2 - 1));
    }

    // For each node, pick nearby RGB representatives for holding charge near that node.
    result.rgb_reps = choose_rgb_reps_from_atomic_errors(result.atomic_errors, result.node_colors);

    // Find the basic ways for moving charge around the graph, by combining pairs of errors to get simpler errors.
    result.charge_graph = ChargeGraph::from_atomic_errors(result.atomic_errors, result.node_colors.size());

    // Solve for how to drag charge around the graph while travelling from node to node.
    result.drag_graph = DragGraph::from_charge_graph_paths_for_sub_edges_of_atomic_errors(
        result.charge_graph, result.atomic_errors, result.rgb_reps, result.node_colors);

    // Prepare the matcher.
    result.matcher = options.matcher_for(result.mobius_dem);
    result.euler_tour_solver = EulerTourGraph(result.node_colors.size() * 2);

    return result;
}

std::unique_ptr<MatcherInterface> DecoderConfigOptions::matcher_for(const stim::DetectorErrorModel &mobius_dem) const {
    if (matcher) {
        return matcher->configured_for_mobius_dem(mobius_dem);
    }
    std::unique_ptr<MatcherInterface> result;
    result.reset(new PymatchingMatcher(mobius_dem));
    return result;
}

static std::optional<obsmask_int> discharge_cycle_helper_single_start_charge_many_cur_charge(
    std::span<const ColorBasis> node_colors,
    std::span<const RgbEdge> rgb_reps,
    const DragGraph &drag_graph,
    std::span<const uint8_t> packed_bit_packed_detection_events,
    std::span<const node_offset_int> cycle,
    Charge start_charge,
    std::vector<uint64_t> *used_buf) {

    used_buf->clear();
    std::array<std::optional<obsmask_int>, 4> cur_states;
    cur_states[start_charge] = {0};
    node_offset_int cur_loc = cycle.back() >> 1;

    for (size_t k = 0; k < cycle.size(); k++) {
        node_offset_int next_loc = cycle[k] >> 1;

        bool has_detection_event_at_loc = (packed_bit_packed_detection_events[cur_loc >> 3]) & (1 << (cur_loc & 7));
        if (next_loc == cur_loc && has_detection_event_at_loc && std::find(used_buf->begin(), used_buf->end(), cur_loc) == used_buf->end()) {
            // Pick up the detection event.
            used_buf->push_back(cur_loc);
            Charge det_charge = node_colors[cur_loc].color;
            std::array<std::optional<obsmask_int>, 4> states_after_det;
            states_after_det[det_charge] = cur_states[Charge::NEUTRAL];
            states_after_det[Charge::NEUTRAL] = cur_states[det_charge];
            auto r = rgb_reps[cur_loc];
            if (r.weight() == 3) {
                auto c1 = next_non_neutral_charge(det_charge);
                auto c2 = next_non_neutral_charge(c1);
                if (cur_states[c1].has_value()) {
                    states_after_det[c2] = *cur_states[c1] ^ r.obs_flip;
                }
                if (cur_states[c2].has_value()) {
                    states_after_det[c1] = *cur_states[c2] ^ r.obs_flip;
                }
            }
            cur_states = states_after_det;
        } else {
            // Drag the current charge to near the new location, potentially switching the charge type.
            std::array<std::optional<obsmask_int>, 4> states_after_drag;
            for (size_t cur_charge = 0; cur_charge < 4; cur_charge++) {
                const auto &cur_obs_flip = cur_states[cur_charge];
                if (cur_obs_flip.has_value()) {
                    for (size_t next_charge = 0; next_charge < 4; next_charge++) {
                        auto f = drag_graph.mmm.find(ChargedEdge{
                            .n1 = cur_loc, .n2 = next_loc, .c1 = (Charge)cur_charge, .c2 = (Charge)next_charge});
                        if (f != drag_graph.mmm.end()) {
                            states_after_drag[next_charge] = *cur_obs_flip ^ f->second;
                        }
                    }
                }
            }
            cur_states = states_after_drag;
        }
        cur_loc = next_loc;
    }

    return cur_states[start_charge];
}

static std::optional<obsmask_int> discharge_cycle_helper_any_start_charge_many_cur_charge(
    std::span<const ColorBasis> node_colors,
    std::span<const RgbEdge> rgb_reps,
    const DragGraph &drag_graph,
    std::span<const uint8_t> packed_bit_packed_detection_events,
    std::span<const node_offset_int> cycle,
    std::vector<uint64_t> *used_buf) {

    for (size_t c = 0; c < 4; c++) {
        auto v = discharge_cycle_helper_single_start_charge_many_cur_charge(
            node_colors,
            rgb_reps,
            drag_graph,
            packed_bit_packed_detection_events,
            cycle,
            (Charge)c,
            used_buf);
        if (v.has_value()) {
            return v;
        }
    }
    return {};
}
obsmask_int Decoder::discharge_cycle(
    std::span<const uint8_t> packed_bit_packed_detection_events, std::span<const node_offset_int> cycle) {
    auto result = discharge_cycle_helper_any_start_charge_many_cur_charge(
        node_colors,
        rgb_reps,
        drag_graph,
        packed_bit_packed_detection_events,
        cycle,
        &resolved_detection_event_buffer);
    if (result.has_value()) {
        return *result;
    }

    std::stringstream ss;
    ss << "Failed to lift a flattened edge cycle from the matcher into an explanation of the detection events in the cycle.\n";
    ss << "This error could be due to a coloring error in the model used to configure the decoder, or a bug in the decoder.\n";
    ss << "The cycle: {";
    for (auto e : cycle) {
        auto d = e >> 1;
        ss << "\n    D" << d << "[";
        ss << node_colors[d].color;
        ss << node_colors[d].basis;
        if (packed_bit_packed_detection_events[d >> 3] & (1 << (d & 7))) {
            ss << ", triggered";
        }
        ss << "]";
    }
    ss << "\n}\n";
    ss << "All detection events in the shot: {";
    for (size_t k = 0; k < node_colors.size(); k++) {
        if (packed_bit_packed_detection_events[k >> 3] & (1 << (k & 7))) {
            ss << "\n    D" << k << "[";
            ss << node_colors[k].color;
            ss << node_colors[k].basis;
            ss << ", triggered]";
        }
    }
    ss << "\n}";

    throw std::invalid_argument(ss.str());
}

static void check_mobius_dem_errors_are_edge_like(const Decoder &decoder) {
    for (const auto &instruction : decoder.mobius_dem.instructions) {
        bool instruction_valid = true;
        if (instruction.type == stim::DemInstructionType::DEM_ERROR) {
            for (size_t k = 0; k < instruction.target_data.size(); k += 3) {
                instruction_valid &= instruction.target_data[k].is_relative_detector_id();
            }
            for (size_t k = 1; k < instruction.target_data.size(); k += 3) {
                instruction_valid &= instruction.target_data[k].is_relative_detector_id();
            }
            for (size_t k = 2; k < instruction.target_data.size(); k += 3) {
                instruction_valid &= instruction.target_data[k].is_separator();
            }
            instruction_valid &= instruction.target_data.size() % 3 == 2;
        }
        if (!instruction_valid) {
            throw std::invalid_argument(
                "A mobius dem error wasn't split into pairs of detectors: " + instruction.str());
        }
    }
}

void Decoder::check_invariants() const {
    check_mobius_dem_errors_are_edge_like(*this);
}

static void detection_events_to_mobius_detection_events(
    std::span<const uint8_t> bit_packed_detection_events,
    std::vector<uint64_t> *out_mobius_detection_events) {
    // Derive the mobius matching problem.
    for (size_t k = 0; k < bit_packed_detection_events.size(); k++) {
        for (uint8_t b = bit_packed_detection_events[k], k2 = 0; b; b >>= 1, k2++) {
            if (b & 1) {
                auto d = k * 8 + k2;
                out_mobius_detection_events->push_back(d * 2 + 0);
                out_mobius_detection_events->push_back(d * 2 + 1);
            }
        }
    }
}

obsmask_int Decoder::decode_detection_events(std::span<const uint8_t> bit_packed_detection_events) {
    // Derive and decode the mobius matching problem.
    sparse_det_buffer.clear();
    matcher_edge_buf.clear();
    detection_events_to_mobius_detection_events(bit_packed_detection_events, &sparse_det_buffer);
    matcher->match_edges(sparse_det_buffer, &matcher_edge_buf);

    // Write solution to stderr if requested.
    if (write_mobius_match_to_std_err) {
        std::cerr << "matched ";
        for (size_t k = 0; k < matcher_edge_buf.size(); k += 2) {
            auto [n1, c1, g1] = mobius_node_to_detector(matcher_edge_buf[k], node_colors);
            auto [n2, c2, g2] = mobius_node_to_detector(matcher_edge_buf[k + 1], node_colors);
            std::cerr << " [" << n1 << "," << c1 << "," << g1 << "]:[" << n2 << "," << c2 << "," << g2 << "]";
        }
        std::cerr << "\n";
    }

    // Lift the solution by decomposing into disjoint Euler cycles and solving each cycle.
    obsmask_int solution = 0;
    euler_tour_solver.iter_euler_tours_of_interleaved_edge_list(
        matcher_edge_buf,
        sparse_det_buffer,
        [&](std::span<const node_offset_int> cycle) {
            solution ^= discharge_cycle(bit_packed_detection_events, cycle);
        });

    return solution;
}

std::ostream &chromobius::operator<<(std::ostream &out, const Decoder &val) {
    out << "chromobius::Decoder{\n\n";
    out << ".charge_graph=" << val.charge_graph << "\n\n";
    out << ".rgb_reps={";
    for (size_t k = 0; k < val.rgb_reps.size(); k++) {
        out << "\n    " << val.rgb_reps[k] << " // rep " << k;
    }
    out << "\n}\n\n";
    out << ".drag_graph=" << val.drag_graph << "\n\n";
    out << ".mobius_dem=stim::DetectorErrorModel{\n" << val.mobius_dem << "\n}";
    out << "\n\n}";
    return out;
}
