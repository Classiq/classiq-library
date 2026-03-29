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

#include "chromobius/graph/drag_graph.h"

#include <optional>

using namespace chromobius;

/// Per-node state during a breadth first search,
struct BfsSearcher {
    uint64_t next_seen_tag;
    std::vector<uint64_t> node_seen_tags;
    std::vector<std::pair<node_offset_int, obsmask_int>> cur_cost_stack;
    std::vector<std::pair<node_offset_int, obsmask_int>> next_cost_stack;

    BfsSearcher() = delete;
    BfsSearcher(size_t num_nodes) : next_seen_tag(1), node_seen_tags(num_nodes), cur_cost_stack(), next_cost_stack() {
    }

    /// Searches for a short path between node1 and node2 within the charge graph.
    ///
    /// Args:
    ///    graph: The graph to do pathfinding inside.
    ///    node_colors:
    ///    node1: One endpoint of the path.
    ///    node2: Other endpoint of the path.
    ///    tag_counter: Used to avoid having to clear the tagged buffer between
    ///        searches. This value will be incremented to create unique values,
    ///        which can then be recognized when searching in order to notice when
    ///        the current search has a reached a node without getting confused by
    ///        junk left from previous searches.
    ///    tagged_buffer: Used to store intermediate search state. Before the very
    ///        first search this should be zero'd, but it doesn't need to be zero'd
    ///        from search to search as long the tag counter isn't reset.
    ///
    /// Returns:
    ///    The observable flip mask of the path.
    std::optional<obsmask_int> find_shortest_path_obs_flip(
        const ChargeGraph &graph,
        node_offset_int src,
        node_offset_int dst,
        size_t max_cost) {

        // Trivial case: same node.
        if (src == dst) {
            return 0;
        }

        // Trivial case: neighbor.
        if (graph.nodes[src].neighbors.contains(dst)) {
            return graph.nodes[src].neighbors.at(dst);
        }

        // Note: assuming never wraps around.
        uint64_t tag = next_seen_tag++;

        // Meet-in-the-middle breadth first search.
        cur_cost_stack.clear();
        next_cost_stack.clear();
        cur_cost_stack.push_back({src, 0});
        size_t cur_cost = 0;
        while (true) {
            if (cur_cost_stack.empty()) {
                std::swap(cur_cost_stack, next_cost_stack);
                cur_cost++;
                if (cur_cost_stack.empty() || cur_cost >= max_cost) {
                    return {};
                }
            }
            auto [n, path_obs_flip] = cur_cost_stack.back();
            cur_cost_stack.pop_back();

            for (const auto [neighbor, edge_obs_flip] : graph.nodes[n].neighbors) {
                obsmask_int new_path_flip = path_obs_flip ^ edge_obs_flip;
                if (neighbor == dst) {
                    return new_path_flip;
                }
                if (neighbor == BOUNDARY_NODE) {
                    // We're only searching in the bulk.
                    continue;
                }
                if (node_seen_tags[neighbor] == tag) {
                    // Already been here.
                    continue;
                }
                node_seen_tags[neighbor] = tag;
                next_cost_stack.push_back({neighbor, new_path_flip});
            }
        }
    }
};

DragGraph DragGraph::from_charge_graph_paths_for_sub_edges_of_atomic_errors(
    const ChargeGraph &charge_graph,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    std::span<const RgbEdge> rgb_reps,
    std::span<const ColorBasis> node_colors) {

    constexpr size_t max_cost = 2;

    std::set<SortedPair> decomposed_edges;
    BfsSearcher searcher(node_colors.size());
    DragGraph drag_graph;

    auto add_edge = [&](node_offset_int n1, node_offset_int n2, Charge c1, Charge c2, obsmask_int flip) {
        drag_graph.mmm[ChargedEdge{.n1=n1, .n2=n2, .c1=c1, .c2=c2}] = flip;
        drag_graph.mmm[ChargedEdge{.n1=n2, .n2=n1, .c1=c2, .c2=c1}] = flip;
    };

    auto add_boundary_dumping_edge = [&](node_offset_int a, node_offset_int b, obsmask_int ab_obs_flip) {
        if (rgb_reps[a].weight() != 3) {
            return;
        }
        Charge ca = node_colors[a].color;
        Charge cb = node_colors[b].color;
        Charge c = ca ^ cb;
        if (c == Charge::NEUTRAL) {
            return;
        }
        auto r1_flip = searcher.find_shortest_path_obs_flip(charge_graph, rgb_reps[a].color_node(ca), a, max_cost);
        auto r2_flip = searcher.find_shortest_path_obs_flip(charge_graph, rgb_reps[a].color_node(cb), b, max_cost);
        if (r1_flip.has_value() && r2_flip.has_value()) {
            add_edge(a, b, c, Charge::NEUTRAL, *r1_flip ^ *r2_flip ^ rgb_reps[a].obs_flip ^ ab_obs_flip);
        }
    };

    for (const auto &[err, err_obs_flip] : atomic_errors) {
        auto w = err.weight();
        if (w == 3) {
            assert(err.net_charge(node_colors) == Charge::NEUTRAL);
            auto [a, b, c] = err.dets;
            decomposed_edges.insert(SortedPair{a, b});
            decomposed_edges.insert(SortedPair{a, c});
            decomposed_edges.insert(SortedPair{b, c});
        } else if (w == 2) {
            auto a = err.dets[0];
            auto b = err.dets[1];
            Charge ca = node_colors[a].color;
            Charge cb = node_colors[b].color;
            obsmask_int p = charge_graph.nodes[a].neighbors.at(b);
            // The boundary error turns charge on one node into charge on the other node.
            add_edge(a, b, ca, cb, p);
            add_edge(a, b, Charge::NEUTRAL, Charge::NEUTRAL, 0);
            // The boundary error can also be used to dump the other type of charge, if it's nearby.
            add_boundary_dumping_edge(a, b, err_obs_flip);
            add_boundary_dumping_edge(b, a, err_obs_flip);
            decomposed_edges.insert(SortedPair{a, b});
        } else if (w == 1) {
            auto n = err.dets[0];
            Charge c = node_colors[n].color;

            // Applying the corner error dumps (or restores) the node's charge.
            add_edge(n, n, c, Charge::NEUTRAL, err_obs_flip);
            add_edge(n, n, Charge::NEUTRAL, Charge::NEUTRAL, 0);

            // The corner error, plus the node's rep error, will flip between the other two nearby charges.
            auto r = rgb_reps[n];
            if (r.weight() == 3) {
                auto f = r.obs_flip ^ err_obs_flip;
                Charge c1 = next_non_neutral_charge(c);
                Charge c2 = next_non_neutral_charge(c1);
                add_edge(n, n, c1, c2, f);
            }
        }
    }

    for (const auto &[n1, n2] : decomposed_edges) {
        assert(n1 != BOUNDARY_NODE);
        assert(n2 != BOUNDARY_NODE);
        auto reps1 = rgb_reps[n1];
        auto reps2 = rgb_reps[n2];
        for (size_t k = 1; k < 4; k++) {
            Charge c = (Charge)k;
            auto r1 = reps1.color_node(c);
            auto r2 = reps2.color_node(c);
            if (r1 != BOUNDARY_NODE && r2 != BOUNDARY_NODE) {
                // Solve for how to drag charge type c from near n1 to near n2.
                auto res = searcher.find_shortest_path_obs_flip(charge_graph, r1, r2, max_cost);
                if (res.has_value()) {
                    add_edge(n1, n2, c, c, *res);
                }
            }
        }
        // Can drag neutral charge around by doing nothing.
        add_edge(n1, n2, Charge::NEUTRAL, Charge::NEUTRAL, 0);
    }

    return drag_graph;
}

bool DragGraph::operator==(const DragGraph &other) const {
    return mmm == other.mmm;
}
bool DragGraph::operator!=(const DragGraph &other) const {
    return !(*this == other);
}
std::string DragGraph::str() const {
    std::stringstream ss;
    ss << *this;
    return ss.str();
}
std::ostream &chromobius::operator<<(std::ostream &out, const DragGraph &val) {
    out << "DragGraph{.mmm={\n";
    for (const auto &[k, v] : val.mmm) {
        out << "    " << k.c1 << "@" << k.n1 << ":" << k.c2 << "@" << k.n2 << " = " << v << "\n";
    }
    out << "}}";
    return out;
}
