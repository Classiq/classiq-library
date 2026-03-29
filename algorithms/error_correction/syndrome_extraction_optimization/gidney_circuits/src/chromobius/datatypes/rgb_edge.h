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

#ifndef _CHROMOBIUS_DEM_GRAPH_H
#define _CHROMOBIUS_DEM_GRAPH_H

#include <ostream>
#include <string>

#include "chromobius/datatypes/atomic_error.h"
#include "chromobius/datatypes/color_basis.h"
#include "stim.h"

namespace chromobius {

struct RgbEdge;

/// Represents an error with at most one symptom of each color.
struct RgbEdge {
    node_offset_int red_node;
    node_offset_int green_node;
    node_offset_int blue_node;
    obsmask_int obs_flip;
    Charge charge_flip;

    inline node_offset_int color_node(Charge c) const {
        if (c == 0) {
            return BOUNDARY_NODE;
        }
        return (&red_node)[c - 1];
    }
    inline node_offset_int &color_node(Charge c) {
        return (&red_node)[c - 1];
    }

    size_t weight() const;
    bool operator<(const RgbEdge &other) const;
    bool operator==(const RgbEdge &other) const;
    bool operator!=(const RgbEdge &other) const;
    std::string str() const;
};
std::ostream &operator<<(std::ostream &out, const RgbEdge &val);

}  // namespace chromobius

#endif
