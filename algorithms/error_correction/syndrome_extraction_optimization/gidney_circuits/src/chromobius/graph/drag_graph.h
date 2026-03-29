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

#ifndef _CHROMOBIUS_DRAG_GRAPH_H
#define _CHROMOBIUS_DRAG_GRAPH_H

#include "chromobius/datatypes/color_basis.h"
#include "chromobius/graph/charge_graph.h"

namespace chromobius {

struct DragNode;
struct DragChange;

struct SortedPair {
    node_offset_int a;
    node_offset_int b;
    inline SortedPair() : a(0), b(0) {
    }
    inline SortedPair(node_offset_int init_a, node_offset_int init_b) : a(init_a), b(init_b) {
        inplace_sort2(a, b);
    }
    inline bool operator<(const SortedPair &other) const {
        return a != other.a ? a < other.a : b < other.b;
    }
    inline bool operator==(const SortedPair &other) const {
        return a == other.a && b == other.b;
    }
};

struct ChargedEdge {
    node_offset_int n1;
    node_offset_int n2;
    Charge c1;
    Charge c2;
    inline bool operator<(const ChargedEdge &other) const {
        if (n1 != other.n1) {
            return n1 < other.n1;
        }
        if (n2 != other.n2) {
            return n2 < other.n2;
        }
        if (c1 != other.c1) {
            return c1 < other.c1;
        }
        return c2 < other.c2;
    }
    inline bool operator==(const ChargedEdge &other) const {
        return n1 == other.n1 && n2 == other.n2 && c1 == other.c1 && c2 == other.c2;
    }
};

/// The drag graph stores information on how to drag charge from node to node.
///
/// When dragging charge around, the charge is always kept near the current
/// target node T. For charge of the same color as T, the charge is exactly a
/// detection event at T. Charges for colors different from T, are kept on R
/// where R is a node near T that matches the charge's color (R is called
/// the `representative` of that charge color for T). In some cases, when there
/// is no node of a color near T, charge of that color must be split into the
/// two other color charges in order to be stored near T. In that case the
/// representative for T of that color is actually two nodes (with one of them
/// being T itself).
struct DragGraph {
    std::map<ChargedEdge, obsmask_int> mmm;

    static DragGraph from_charge_graph_paths_for_sub_edges_of_atomic_errors(
        const ChargeGraph &charge_graph,
        const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
        std::span<const RgbEdge> rgb_reps,
        std::span<const ColorBasis> node_colors);

    bool operator==(const DragGraph &other) const;
    bool operator!=(const DragGraph &other) const;
    std::string str() const;
};
std::ostream &operator<<(std::ostream &out, const DragGraph &val);

}  // namespace chromobius

#endif
