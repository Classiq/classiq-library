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

#include "chromobius/graph/collect_composite_errors.h"

#include "chromobius/graph/collect_atomic_errors.h"

using namespace chromobius;

static inline void try_grow_decomposition(
    AtomicErrorKey e1,
    AtomicErrorKey e2,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::vector<AtomicErrorKey> *out_atoms,
    int &best_score) {
    bool c1 = atomic_errors.contains(e1);
    bool c2 = atomic_errors.contains(e2);
    int score = c1 + 2 * c2;
    if (score <= best_score) {
        return;
    }
    if (score == 1 && e2.weight() == 3 && e2.net_charge(node_colors) != Charge::NEUTRAL) {
        return;
    }
    if (score == 2 && e1.weight() == 3 && e1.net_charge(node_colors) != Charge::NEUTRAL) {
        return;
    }

    if (best_score > 0) {
        out_atoms->pop_back();
        out_atoms->pop_back();
    }
    out_atoms->push_back(e1);
    out_atoms->push_back(e2);
    best_score = score;
}

static inline bool try_finish_decomposition(
    int best_score,
    obsmask_int obs_flip,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::vector<AtomicErrorKey> *out_atoms,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {
    assert(best_score == 0 || out_atoms->size() >= 2);
    if (best_score == 1) {
        AtomicErrorKey cur = (*out_atoms)[out_atoms->size() - 2];
        AtomicErrorKey rem = (*out_atoms)[out_atoms->size() - 1];
        (*out_remnants)[rem] = obs_flip ^ atomic_errors.at(cur);
    } else if (best_score == 2) {
        AtomicErrorKey cur = (*out_atoms)[out_atoms->size() - 1];
        AtomicErrorKey rem = (*out_atoms)[out_atoms->size() - 2];
        (*out_remnants)[rem] = obs_flip ^ atomic_errors.at(cur);
    }
    return best_score > 0;
}

static bool decompose_single_basis_dets_into_atoms_helper_n2(
    std::span<const node_offset_int> dets,
    obsmask_int obs_flip,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::vector<AtomicErrorKey> *out_atoms,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {
    // Check if it's just directly included.
    AtomicErrorKey e{dets[0], dets[1], BOUNDARY_NODE};
    if (atomic_errors.contains(e)) {
        out_atoms->push_back(e);
        return true;
    }

    int best_score = 0;

    // 1:1 decomposition.
    for (size_t k1 = 0; k1 < dets.size(); k1++) {
        try_grow_decomposition(
            AtomicErrorKey{dets[k1], BOUNDARY_NODE, BOUNDARY_NODE},
            AtomicErrorKey{
                dets[0 + (k1 <= 0)],
                BOUNDARY_NODE,
                BOUNDARY_NODE,
            },
            node_colors,
            atomic_errors,
            out_atoms,
            best_score);
    }

    return try_finish_decomposition(best_score, obs_flip, atomic_errors, out_atoms, out_remnants);
}

static bool decompose_single_basis_dets_into_atoms_helper_n3(
    std::span<const node_offset_int> dets,
    obsmask_int obs_flip,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::vector<AtomicErrorKey> *out_atoms,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {
    // Check if it's just directly included.
    AtomicErrorKey e{dets[0], dets[1], dets[2]};
    if (atomic_errors.contains(e)) {
        out_atoms->push_back(e);
        return true;
    }

    int best_score = 0;

    // 1:2 decomposition.
    for (size_t k1 = 0; k1 < dets.size(); k1++) {
        try_grow_decomposition(
            AtomicErrorKey{dets[k1], BOUNDARY_NODE, BOUNDARY_NODE},
            AtomicErrorKey{
                dets[0 + (k1 <= 0)],
                dets[1 + (k1 <= 1)],
                BOUNDARY_NODE,
            },
            node_colors,
            atomic_errors,
            out_atoms,
            best_score);
    }

    return try_finish_decomposition(best_score, obs_flip, atomic_errors, out_atoms, out_remnants);
}

static bool decompose_single_basis_dets_into_atoms_helper_n4(
    std::span<const node_offset_int> dets,
    obsmask_int obs_flip,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::vector<AtomicErrorKey> *out_atoms,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {
    int best_score = 0;

    // 2:2 decomposition.
    for (size_t k1 = 0; k1 < dets.size() && best_score < 2; k1++) {
        for (size_t k2 = k1 + 1; k2 < dets.size(); k2++) {
            try_grow_decomposition(
                AtomicErrorKey{dets[k1], dets[k2], BOUNDARY_NODE},
                AtomicErrorKey{
                    dets[0 + (k1 <= 0) + (k2 <= 0)],
                    dets[1 + (k1 <= 1) + (k2 <= 1)],
                    BOUNDARY_NODE,
                },
                node_colors,
                atomic_errors,
                out_atoms,
                best_score);
        }
    }

    // 1:3 decomposition.
    for (size_t k1 = 0; k1 < dets.size(); k1++) {
        try_grow_decomposition(
            AtomicErrorKey{dets[k1], BOUNDARY_NODE, BOUNDARY_NODE},
            AtomicErrorKey{
                dets[0 + (k1 <= 0)],
                dets[1 + (k1 <= 1)],
                dets[2 + (k1 <= 2)],
            },
            node_colors,
            atomic_errors,
            out_atoms,
            best_score);
    }

    return try_finish_decomposition(best_score, obs_flip, atomic_errors, out_atoms, out_remnants);
}

static bool decompose_single_basis_dets_into_atoms_helper_n5(
    std::span<const node_offset_int> dets,
    obsmask_int obs_flip,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::vector<AtomicErrorKey> *out_atoms,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {
    int best_score = 0;

    // 2:3 decomposition.
    for (size_t k1 = 0; k1 < dets.size() && best_score < 2; k1++) {
        for (size_t k2 = k1 + 1; k2 < dets.size(); k2++) {
            try_grow_decomposition(
                AtomicErrorKey{dets[k1], dets[k2], BOUNDARY_NODE},
                AtomicErrorKey{
                    dets[0 + (k1 <= 0) + (k2 <= 0)],
                    dets[1 + (k1 <= 1) + (k2 <= 1)],
                    dets[2 + (k1 <= 2) + (k2 <= 2)],
                },
                node_colors,
                atomic_errors,
                out_atoms,
                best_score);
        }
    }

    return try_finish_decomposition(best_score, obs_flip, atomic_errors, out_atoms, out_remnants);
}

static bool decompose_single_basis_dets_into_atoms_helper_n6(
    std::span<const node_offset_int> dets,
    obsmask_int obs_flip,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::vector<AtomicErrorKey> *out_atoms,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {
    int best_score = 0;

    // 3:3 decomposition.
    for (size_t k1 = 0; k1 < dets.size() && best_score < 2; k1++) {
        for (size_t k2 = k1 + 1; k2 < dets.size(); k2++) {
            for (size_t k3 = k2 + 1; k3 < dets.size(); k3++) {
                try_grow_decomposition(
                    AtomicErrorKey{dets[k1], dets[k2], dets[k3]},
                    AtomicErrorKey{
                        dets[0 + (k1 <= 0) + (k2 <= 0) + (k3 <= 0)],
                        dets[1 + (k1 <= 1) + (k2 <= 1) + (k3 <= 1)],
                        dets[2 + (k1 <= 2) + (k2 <= 2) + (k3 <= 2)],
                    },
                    node_colors,
                    atomic_errors,
                    out_atoms,
                    best_score);
            }
        }
    }

    return try_finish_decomposition(best_score, obs_flip, atomic_errors, out_atoms, out_remnants);
}

static bool decompose_single_basis_dets_into_atoms(
    std::span<const node_offset_int> dets,
    obsmask_int obs_flip,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::vector<AtomicErrorKey> *out_atoms,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {
    switch (dets.size()) {
        case 0:
            return true;
        case 1:
            out_atoms->push_back(AtomicErrorKey{dets[0], BOUNDARY_NODE, BOUNDARY_NODE});
            return atomic_errors.contains(out_atoms->back());
        case 2:
            return decompose_single_basis_dets_into_atoms_helper_n2(
                dets, obs_flip, node_colors, atomic_errors, out_atoms, out_remnants);
        case 3:
            return decompose_single_basis_dets_into_atoms_helper_n3(
                dets, obs_flip, node_colors, atomic_errors, out_atoms, out_remnants);
        case 4:
            return decompose_single_basis_dets_into_atoms_helper_n4(
                dets, obs_flip, node_colors, atomic_errors, out_atoms, out_remnants);
        case 5:
            return decompose_single_basis_dets_into_atoms_helper_n5(
                dets, obs_flip, node_colors, atomic_errors, out_atoms, out_remnants);
        case 6:
            return decompose_single_basis_dets_into_atoms_helper_n6(
                dets, obs_flip, node_colors, atomic_errors, out_atoms, out_remnants);
        default:
            return false;
    }
}

static void decompose_dets_into_atoms(
    std::span<const node_offset_int> dets,
    obsmask_int obs_flip,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    bool ignore_decomposition_failures,
    std::vector<node_offset_int> *buf_x_detectors,
    std::vector<node_offset_int> *buf_z_detectors,
    const stim::DemInstruction &instruction_for_error_message,
    const stim::DetectorErrorModel *dem_for_error_message,
    std::vector<AtomicErrorKey> *out_atoms,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {
    // Split into X and Z parts.
    buf_x_detectors->clear();
    buf_z_detectors->clear();
    for (const auto &t : dets) {
        auto cb = node_colors[t];
        int c = (int)cb.color - 1;
        int b = (int)cb.basis - 1;
        if (c < 0 || c >= 3 || b < 0 || b >= 2) {
            std::stringstream ss;
            ss << "Detector D" << t << " originating from instruction (after shifting) '"
               << instruction_for_error_message << "'";
            ss << " is missing coordinate data indicating its color and basis.\n";
            ss << "Every detector used in an error must have a 4th coordinate in "
                  "[0,6) where RedX=0, GreenX=1, BlueX=2, RedZ=3, GreenZ=4, BlueZ=5.";
            throw std::invalid_argument(ss.str());
        }
        if (b == 0) {
            buf_x_detectors->push_back(t);
        } else {
            buf_z_detectors->push_back(t);
        }
    }

    // Split into atomic errors.
    out_atoms->clear();
    bool x_worked = decompose_single_basis_dets_into_atoms(
        *buf_x_detectors, obs_flip, node_colors, atomic_errors, out_atoms, out_remnants);
    bool z_worked = decompose_single_basis_dets_into_atoms(
        *buf_z_detectors, obs_flip, node_colors, atomic_errors, out_atoms, out_remnants);
    if (!(x_worked && z_worked) && !ignore_decomposition_failures) {
        std::stringstream ss;
        ss << "Failed to decompose a complex error instruction into basic errors.\n";
        ss << "    The instruction (after shifting): " + instruction_for_error_message.str() << "\n";
        if (!x_worked) {
            ss << "    The undecomposed X detectors: [" << stim::comma_sep(*buf_x_detectors) << "]\n";
        }
        if (!z_worked) {
            ss << "    The undecomposed Z detectors: [" << stim::comma_sep(*buf_z_detectors) << "]\n";
        }
        ss << "    Detector data:\n";
        std::set<uint64_t> ds;
        for (const auto &t : instruction_for_error_message.target_data) {
            if (t.is_relative_detector_id()) {
                ds.insert(t.raw_id());
            }
        }
        std::map<uint64_t, std::vector<double>> coords;
        if (dem_for_error_message != nullptr) {
            coords = dem_for_error_message->get_detector_coordinates(ds);
        }
        for (const auto &t : instruction_for_error_message.target_data) {
            if (t.is_relative_detector_id()) {
                auto d = t.raw_id();
                ss << "        " << t << ": coords=[" << stim::comma_sep(coords[d]) << "] " << node_colors[d] << "\n";
            }
        }
        ss << "This problem can unfortunately be quite difficult to debug. Likely causes are:\n";
        ss << "    (1) The source circuit has detectors with invalid color/basis annotations.\n";
        ss << "    (2) The source circuit is producing errors too complex to decompose (e.g. more than 6 symptoms in "
              "one basis).\n";
        ss << "    (3) chromobius is missing logic for a corner case present in the source circuit; a corner case that "
              "didn't appear in the test circuits used during development.\n";
        throw std::invalid_argument(ss.str());
    }
}

void chromobius::collect_composite_errors_and_remnants_into_mobius_dem(
    const stim::DetectorErrorModel &dem,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    bool drop_mobius_errors_involving_remnant_errors,
    bool ignore_decomposition_failures,
    stim::DetectorErrorModel *out_mobius_dem,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants) {

    stim::SparseXorVec<node_offset_int> dets;
    std::vector<node_offset_int> x_buf;
    std::vector<node_offset_int> z_buf;
    std::vector<AtomicErrorKey> atoms_buf;
    std::vector<stim::DemTarget> composite_error_buffer;

    dem.iter_flatten_error_instructions([&](stim::DemInstruction instruction) {
        obsmask_int obs_flip;
        extract_obs_and_dets_from_error_instruction(instruction, &dets, &obs_flip);

        decompose_dets_into_atoms(
            dets.sorted_items,
            obs_flip,
            node_colors,
            atomic_errors,
            ignore_decomposition_failures,
            &x_buf,
            &z_buf,
            instruction,
            &dem,
            &atoms_buf,
            out_remnants);

        if (drop_mobius_errors_involving_remnant_errors && !out_remnants->empty()) {
            atoms_buf.clear();
            out_remnants->clear();
        }

        // Convert atomic errors into mobius detection events with decomposition suggestions.
        composite_error_buffer.clear();
        bool has_corner_node = false;
        for (const auto &atom : atoms_buf) {
            has_corner_node |= atom.dets[1] == BOUNDARY_NODE;
            atom.iter_mobius_edges(node_colors, [&](node_offset_int d1, node_offset_int d2) {
                composite_error_buffer.push_back(stim::DemTarget::relative_detector_id(d1));
                composite_error_buffer.push_back(stim::DemTarget::relative_detector_id(d2));
                composite_error_buffer.push_back(stim::DemTarget::separator());
            });
        }

        // Put the composite error into the mobius dem as an error instruction.
        if (!composite_error_buffer.empty()) {
            composite_error_buffer.pop_back();
            double p = instruction.arg_data[0];
            if (has_corner_node) {
                // Corner nodes have edges to themselves that correspond to reaching the boundary in one subgraph
                // and then bouncing back in another subgraph. Accounting for this correctly requires doubling the
                // weight of the edge, which corresponds to squaring the probability.
                p *= p;
            }
            out_mobius_dem->append_error_instruction(p, composite_error_buffer);
        }
    });
}
