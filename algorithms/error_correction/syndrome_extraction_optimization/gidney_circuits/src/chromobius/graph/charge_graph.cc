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

#include <cstddef>
#include <map>
#include <sstream>

using namespace chromobius;

bool ChargeGraphNode::operator==(const ChargeGraphNode &other) const {
    return neighbors == other.neighbors;
}
bool ChargeGraphNode::operator!=(const ChargeGraphNode &other) const {
    return !(*this == other);
}
std::string ChargeGraphNode::str() const {
    std::stringstream ss;
    ss << *this;
    return ss.str();
}

std::ostream &chromobius::operator<<(std::ostream &out, const ChargeGraphNode &val) {
    out << "ChargeGraphNode{.neighbors={";
    std::vector<node_offset_int> ns;
    for (const auto &p : val.neighbors) {
        ns.push_back(p.first);
    }
    std::sort(ns.begin(), ns.end());
    for (size_t k = 0; k < ns.size(); k++) {
        if (k > 0) {
            out << ", ";
        }
        out << "{";
        if (ns[k] == BOUNDARY_NODE) {
            out << "BOUNDARY_NODE";
        } else {
            out << ns[k];
        }
        out << "," << val.neighbors.at(ns[k]) << "}";
    }
    out << "}}";
    return out;
}

bool ChargeGraph::operator==(const ChargeGraph &other) const {
    return nodes == other.nodes;
}
bool ChargeGraph::operator!=(const ChargeGraph &other) const {
    return !(*this == other);
}
std::string ChargeGraph::str() const {
    std::stringstream ss;
    ss << *this;
    return ss.str();
}
std::ostream &chromobius::operator<<(std::ostream &out, const ChargeGraph &val) {
    out << "ChargeGraph{.nodes={\n";
    for (size_t k = 0; k < val.nodes.size(); k++) {
        out << "    " << val.nodes[k] << ", // node " << k << "\n";
    }
    out << "}}";
    return out;
}

void ChargeGraph::add_edge(node_offset_int n1, node_offset_int n2, obsmask_int obs_flip) {
    if (n1 != BOUNDARY_NODE) {
        nodes[n1].neighbors[n2] = obs_flip;
    }
    if (n2 != BOUNDARY_NODE) {
        nodes[n2].neighbors[n1] = obs_flip;
    }
}

ChargeGraph ChargeGraph::from_atomic_errors(
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors, size_t num_nodes) {

    // Create a charge graph of the correct size.
    ChargeGraph charge_graph;
    charge_graph.nodes.resize(num_nodes);
    for (size_t k = 0; k < num_nodes; k++) {
        charge_graph.nodes[k].neighbors[k] = obsmask_int{0};
    }

    // Add all directly included edges into the charge graph.
    for (const auto &[err, obs_flip] : atomic_errors) {
        if (err.dets[2] == BOUNDARY_NODE) {
            charge_graph.add_edge(err.dets[0], err.dets[1], obs_flip);
        }
    }

    // Index errors by each node touched by the error.
    std::map<node_offset_int, std::vector<AtomicErrorKey>> node2neighbors;
    for (const auto &[err, obs_flip] : atomic_errors) {
        for (auto n : err.dets) {
            if (n != BOUNDARY_NODE) {
                node2neighbors[n].push_back(err);
            }
        }
    }

    // Form more graphlike edges by pairing overlapping errors.
    stim::SparseXorVec<node_offset_int> xor_buf;
    for (const auto &[_, neighbors] : node2neighbors) {
        for (size_t k1 = 0; k1 < neighbors.size(); k1++) {
            for (size_t k2 = k1 + 1; k2 < neighbors.size(); k2++) {
                const auto &e1 = neighbors[k1];
                const auto &e2 = neighbors[k2];
                if (e1.weight() < 3 && e2.weight() < 3) {
                    // These errors were already graphlike.
                    continue;
                }

                // Merge the errors.
                xor_buf.clear();
                xor_buf.xor_item(e1.dets[0]);
                xor_buf.xor_item(e1.dets[1]);
                xor_buf.xor_item(e1.dets[2]);
                xor_buf.xor_item(e2.dets[0]);
                xor_buf.xor_item(e2.dets[1]);
                xor_buf.xor_item(e2.dets[2]);

                // Check if the resulting error is graphlike, pulling out its symptoms.
                node_offset_int a;
                node_offset_int b;
                if (xor_buf.sorted_items.size() == 1) {
                    a = xor_buf.sorted_items[0];
                    b = BOUNDARY_NODE;
                } else if (
                    xor_buf.sorted_items.size() == 2 ||
                    (xor_buf.sorted_items.size() == 3 && xor_buf.sorted_items.back() == BOUNDARY_NODE)) {
                    a = xor_buf.sorted_items[0];
                    b = xor_buf.sorted_items[1];
                } else {
                    continue;
                }

                // Add the composite graphlike error into the graph.
                charge_graph.add_edge(a, b, atomic_errors.at(e1) ^ atomic_errors.at(e2));
            }
        }
    }

    return charge_graph;
}
