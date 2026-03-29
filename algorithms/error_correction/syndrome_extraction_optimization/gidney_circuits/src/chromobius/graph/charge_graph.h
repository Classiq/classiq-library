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

#ifndef _CHROMOBIUS_CHARGE_GRAPH_H
#define _CHROMOBIUS_CHARGE_GRAPH_H

#include <span>
#include <unordered_map>
#include <vector>

#include "chromobius/datatypes/rgb_edge.h"
#include "stim.h"

namespace chromobius {

struct ChargeGraphNode;

/// Like the error graph, but hyperedges have been combined into normal edges.
///
/// Every edge in the charge graph is graphlike (degree 2 or degree 1). The
/// charge graph includes edges that were in the original detector error model,
/// as well as synthetic edges that can be formed by combining pairs of RGB
/// errors from the original detector error model.
///
/// Stored as an adjacency list graph.
struct ChargeGraph {
    std::vector<ChargeGraphNode> nodes;

    static ChargeGraph from_atomic_errors(const std::map<AtomicErrorKey, obsmask_int> &atomic_errors, size_t num_nodes);

    void add_edge(node_offset_int n1, node_offset_int n2, obsmask_int obs_flip);
    bool operator==(const ChargeGraph &other) const;
    bool operator!=(const ChargeGraph &other) const;
    std::string str() const;
};
std::ostream &operator<<(std::ostream &out, const ChargeGraph &val);

struct ChargeGraphNode {
    std::unordered_map<node_offset_int, obsmask_int> neighbors;

    bool operator==(const ChargeGraphNode &other) const;
    bool operator!=(const ChargeGraphNode &other) const;
    std::string str() const;
};
std::ostream &operator<<(std::ostream &out, const ChargeGraphNode &val);

}  // namespace chromobius

#endif
