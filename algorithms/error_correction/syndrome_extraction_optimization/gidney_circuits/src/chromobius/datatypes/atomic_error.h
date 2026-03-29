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

#ifndef _CHROMOBIUS_ATOMIC_ERROR_H
#define _CHROMOBIUS_ATOMIC_ERROR_H

#include <span>

#include "chromobius/datatypes/color_basis.h"
#include "stim.h"

namespace chromobius {

inline void inplace_sort2(node_offset_int &a, node_offset_int &b) {
    auto cmp2 = -(a > b) & (a ^ b);
    a ^= cmp2;
    b ^= cmp2;
}

inline std::array<uint32_t, 3> sort3(node_offset_int a, node_offset_int b, node_offset_int c) {
    inplace_sort2(b, c);
    inplace_sort2(a, b);
    inplace_sort2(b, c);
    return {a, b, c};
}

/// Atomic errors are the building blocks all other errors are decomposed into.
///
/// There are four kinds of atomic error:
///     Neutral Triplet: Three detection events, each with different color.
///         Example: A bulk error in a code capacity color code.
///     Neutral Pair: Two detection events that have the same color.
///         Example: A measurement error in a phenom color code.
///     Charged Pair: Two detection events that have different colors.
///         Example: A boundary error in a code capacity color code.
///     Charged Singlet: One detection event.
///         Example: A corner error in a code capacity color code.
///
/// Invariants:
///     sorted: 0 <= n1 <= n2 <= n3 <= BOUNDARY_NODE
///     not empty: n1 != BOUNDARY_NODE
///     neutral triplets: (n3 != BOUNDARY_NODE) ==> (net_charge == NEUTRAL)
///     single basis: len({basis[n] for n in dets if n != BOUNDARY_NODE}) == 1
struct AtomicErrorKey {
    std::array<node_offset_int, 3> dets;
    inline AtomicErrorKey(node_offset_int det1, node_offset_int det2, node_offset_int det3)
        : dets(sort3(det1, det2, det3)) {
    }
    inline bool operator<(const AtomicErrorKey &other) const {
        for (size_t k = 0; k < 3; k++) {
            if (dets[k] != other.dets[k]) {
                return dets[k] < other.dets[k];
            }
        }
        return false;
    }
    inline uint8_t weight() const {
        return (dets[0] != BOUNDARY_NODE) + (dets[1] != BOUNDARY_NODE) + (dets[2] != BOUNDARY_NODE);
    }
    inline Charge net_charge(std::span<const ColorBasis> node_colors) const {
        Charge c = Charge::NEUTRAL;
        for (auto d : dets) {
            if (d != BOUNDARY_NODE) {
                c ^= node_colors[d].color;
            }
        }
        return c;
    }
    inline bool operator==(const AtomicErrorKey &other) const {
        return dets == other.dets;
    }
    inline bool operator!=(const AtomicErrorKey &other) const {
        return !(*this == other);
    }
    void check_invariants(std::span<const ColorBasis> det_types);
    std::string str() const;

    /// Decomposes the atomic error into edges for the mobius dem.
    ///
    /// Each symptom splits into two, and the symptoms then get distributed to the various mobius subgraphs.
    /// The pairing of the split up symptoms is important to ensure the subgraphs are connected (and disconnected)
    /// in the appropriate ways.
    inline void iter_mobius_edges(std::span<const ColorBasis> node_colors, const std::function<void(node_offset_int, node_offset_int)> &callback) const {
        auto [n1, n2, n3] = dets;
        if (n1 == BOUNDARY_NODE) {
            // No edge.
            return;
        } else if (n2 == BOUNDARY_NODE) {
            callback(n1 * 2 + 0, n1 * 2 + 1);
        } else if (n3 == BOUNDARY_NODE) {
            auto c1 = node_colors[n1].color;
            auto c2 = node_colors[n2].color;
            bool flip_order = (c1 ^ c2) == Charge::G;
            callback(n1 * 2 + 0, (n2 * 2 + 0) ^ flip_order);
            callback(n1 * 2 + 1, (n2 * 2 + 1) ^ flip_order);
        } else {
            assert((node_colors[n1].color ^ node_colors[n2].color ^ node_colors[n3].color) == Charge::NEUTRAL);
            node_offset_int rgb[3]{BOUNDARY_NODE, BOUNDARY_NODE, BOUNDARY_NODE};
            rgb[node_colors[n1].color - 1] = n1;
            rgb[node_colors[n2].color - 1] = n2;
            rgb[node_colors[n3].color - 1] = n3;
            auto [r, g, b] = rgb;
            assert(r != BOUNDARY_NODE);
            assert(g != BOUNDARY_NODE);
            assert(b != BOUNDARY_NODE);
            auto a0 = r * 2 + SUBGRAPH_OFFSET_Red_NotBlue;
            auto b0 = g * 2 + SUBGRAPH_OFFSET_Green_NotBlue;
            auto a1 = g * 2 + SUBGRAPH_OFFSET_Green_NotRed;
            auto b1 = b * 2 + SUBGRAPH_OFFSET_Blue_NotRed;
            auto a2 = r * 2 + SUBGRAPH_OFFSET_Red_NotGreen;
            auto b2 = b * 2 + SUBGRAPH_OFFSET_Blue_NotGreen;
            inplace_sort2(a0, b0);
            inplace_sort2(a1, b1);
            inplace_sort2(a2, b2);
            callback(a0, b0);
            callback(a1, b1);
            callback(a2, b2);
        }
    }
};
std::ostream &operator<<(std::ostream &out, const AtomicErrorKey &val);

}  // namespace chromobius

#endif
