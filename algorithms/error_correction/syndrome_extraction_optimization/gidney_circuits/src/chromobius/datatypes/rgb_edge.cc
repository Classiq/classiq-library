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

#include "chromobius/datatypes/rgb_edge.h"

#include <span>
#include <sstream>

using namespace chromobius;

bool RgbEdge::operator==(const RgbEdge &other) const {
    return red_node == other.red_node && blue_node == other.blue_node && green_node == other.green_node &&
           obs_flip == other.obs_flip && charge_flip == other.charge_flip;
}
bool RgbEdge::operator!=(const RgbEdge &other) const {
    return !(*this == other);
}
std::string RgbEdge::str() const {
    std::stringstream ss;
    ss << *this;
    return ss.str();
}
std::ostream &chromobius::operator<<(std::ostream &out, const RgbEdge &val) {
    out << "RgbEdge{.red_node=";
    if (val.red_node == BOUNDARY_NODE) {
        out << "BOUNDARY_NODE";
    } else {
        out << val.red_node;
    }
    out << ", .green_node=";
    if (val.green_node == BOUNDARY_NODE) {
        out << "BOUNDARY_NODE";
    } else {
        out << val.green_node;
    }
    out << ", .blue_node=";
    if (val.blue_node == BOUNDARY_NODE) {
        out << "BOUNDARY_NODE";
    } else {
        out << val.blue_node;
    }
    out << ", .obs_flip=" << val.obs_flip;
    out << ", .charge_flip=" << val.charge_flip;
    out << "}";
    return out;
}
size_t RgbEdge::weight() const {
    return (red_node != BOUNDARY_NODE) + (green_node != BOUNDARY_NODE) + (blue_node != BOUNDARY_NODE);
}

bool RgbEdge::operator<(const RgbEdge &other) const {
    if (red_node != other.red_node) {
        return red_node < other.red_node;
    }
    if (green_node != other.green_node) {
        return green_node < other.green_node;
    }
    if (blue_node != other.blue_node) {
        return blue_node < other.blue_node;
    }
    if (obs_flip != other.obs_flip) {
        return obs_flip < other.obs_flip;
    }
    return charge_flip < other.charge_flip;
}
