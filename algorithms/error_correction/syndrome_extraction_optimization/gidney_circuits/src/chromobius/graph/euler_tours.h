/*
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef _CHROMOBIUS_EULER_TOURS_H
#define _CHROMOBIUS_EULER_TOURS_H

#include <span>

#include "chromobius/datatypes/atomic_error.h"
#include "chromobius/datatypes/color_basis.h"
#include "stim.h"

namespace chromobius {

/// This structure is used for decomposing a graph into a set of Euler tours.
///
/// The graph must only have even degree nodes.
/// The graph is permitted to have multiple connected components.
/// There will be one Euler tour per connected component.
struct EulerTourGraph;

struct EulerTourNeighbor {
    node_offset_int node;
    uint16_t back_index;
};

struct EulerTourNode {
    /// The list of neighbors of this node.
    /// Entries with .node set to BOUNDARY_NODE are voided and should be ignored.
    std::vector<EulerTourNeighbor> neighbors;
    /// Tracks the neighbors that have been looked at.
    size_t next_neighbor;

    /// Advances `next_neighbor` to the next uncleared neighbor and returns it.
    /// If `next_neighbor` is past the end of the list, returns SIZE_MAX.
    size_t look_next_neighbor();
};
std::ostream &operator<<(std::ostream &out, const EulerTourNode &val);

struct EulerTourGraph;
std::ostream &operator<<(std::ostream &out, const EulerTourGraph &val);
struct EulerTourGraph {
    std::vector<EulerTourNode> nodes;
    std::vector<node_offset_int> cycle_buf;
    std::vector<node_offset_int> cycle_buf2;

    inline EulerTourGraph(size_t num_nodes) : nodes(num_nodes, {.neighbors = {}, .next_neighbor = 0}) {
    }

    void add_edge(node_offset_int a, node_offset_int b);

    // Deletes all edges and buffer contents.
    //
    // This method takes time proportional to the number of nodes, instead of
    // proportional to the number of edges.
    void hard_reset();

   private:
    void extend_cycle_depth_first();
    bool rotate_cycle_to_end_with_unfinished_node();

    template <typename CALLBACK>
    inline void burn_component_at(node_offset_int n, const CALLBACK &callback) {
        if (nodes[n].look_next_neighbor() == SIZE_MAX) {
            return;
        }
        cycle_buf.push_back(n);
        do {
            extend_cycle_depth_first();
        } while (rotate_cycle_to_end_with_unfinished_node());
        assert(cycle_buf.size() > 0);
        callback(std::span<const node_offset_int>(cycle_buf));
        cycle_buf.clear();
    }

   public:
    template <typename CALLBACK>
    inline void iter_euler_tours_of_interleaved_edge_list(
        std::span<const int64_t> interleaved_edge_list,
        std::span<const uint64_t> mobius_dets,
        const CALLBACK &callback) {
        const auto &ee = interleaved_edge_list;
        assert(ee.size() % 2 == 0);
        for (size_t k = 0; k < ee.size(); k += 2) {
            assert(ee[k] != -1);
            assert(ee[k + 1] != -1);
            add_edge(ee[k], ee[k + 1]);
        }
        for (size_t k = 0; k < mobius_dets.size(); k += 2) {
            add_edge(mobius_dets[k], mobius_dets[k + 1]);
        }
        for (auto n : interleaved_edge_list) {
            burn_component_at(n, callback);
        }
        for (auto n : interleaved_edge_list) {
            assert(nodes[n].next_neighbor == nodes[n].neighbors.size());
            nodes[n].next_neighbor = 0;
            nodes[n].neighbors.clear();
        }
    }
};

}  // namespace chromobius

#endif
