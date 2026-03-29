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

#include <optional>

using namespace chromobius;

void EulerTourGraph::add_edge(node_offset_int a, node_offset_int b) {
    uint16_t na = (uint16_t)nodes[a].neighbors.size();
    uint16_t nb = (uint16_t)nodes[b].neighbors.size();
    nodes[a].neighbors.push_back(EulerTourNeighbor{
        .node = b,
        .back_index = nb,
    });
    nodes[b].neighbors.push_back(EulerTourNeighbor{
        .node = a,
        .back_index = na,
    });
}

size_t EulerTourNode::look_next_neighbor() {
    while (true) {
        if (next_neighbor >= neighbors.size()) {
            return SIZE_MAX;
        }
        if (neighbors[next_neighbor].node == BOUNDARY_NODE) {
            next_neighbor++;
            continue;
        }
        return next_neighbor;
    }
}
std::ostream &chromobius::operator<<(std::ostream &out, const EulerTourNode &val) {
    out << "EulerTourNode{.next_neighbor=" << val.next_neighbor << ", .neighbors={";
    for (auto &e : val.neighbors) {
        out << e.node << ",";
    }
    out << "}}";
    return out;
}

void EulerTourGraph::hard_reset() {
    for (auto &n : nodes) {
        n.neighbors.clear();
        n.next_neighbor = 0;
    }
    cycle_buf.clear();
    cycle_buf2.clear();
}

void EulerTourGraph::extend_cycle_depth_first() {
    while (true) {
        auto &n = nodes[cycle_buf.back()];
        size_t neighbor_k = n.look_next_neighbor();
        if (neighbor_k == SIZE_MAX) {
            return;
        }
        n.next_neighbor++;
        auto &neighbor = n.neighbors[neighbor_k];
        cycle_buf.push_back(neighbor.node);
        nodes[neighbor.node].neighbors[neighbor.back_index].node = BOUNDARY_NODE;
    }
}

bool EulerTourGraph::rotate_cycle_to_end_with_unfinished_node() {
    if (cycle_buf.back() != cycle_buf.front()) {
        hard_reset();
        throw std::invalid_argument("Graph didn't decompose into Euler tours.");
    }
    cycle_buf.pop_back();

    size_t cycle_k = 1;
    for (; cycle_k < cycle_buf.size() && nodes[cycle_buf[cycle_k]].look_next_neighbor() == SIZE_MAX; cycle_k++) {
    }
    if (cycle_k < cycle_buf.size()) {
        cycle_buf2.insert(cycle_buf2.end(), cycle_buf.begin() + cycle_k, cycle_buf.end());
        cycle_buf2.insert(cycle_buf2.end(), cycle_buf.begin(), cycle_buf.begin() + cycle_k + 1);
        cycle_buf.swap(cycle_buf2);
        cycle_buf2.clear();
        return true;
    } else {
        return false;
    }
}

std::ostream &chromobius::operator<<(std::ostream &out, const EulerTourGraph &val) {
    out << "EulerTourGraph{\n";
    out << "    .cycle_buf={" << stim::comma_sep(val.cycle_buf) << "}\n";
    out << "    .nodes.size()=" << val.nodes.size() << "\n";
    for (size_t k = 0; k < val.nodes.size(); k++) {
        if (!val.nodes[k].neighbors.empty()) {
            out << "    .nodes[" << k << "]=" << val.nodes[k] << "\n";
        }
    }
    out << "}";
    return out;
}
