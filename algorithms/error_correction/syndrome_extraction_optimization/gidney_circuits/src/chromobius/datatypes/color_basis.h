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

#ifndef _CHROMOBIUS_COLOR_BASIS_H
#define _CHROMOBIUS_COLOR_BASIS_H

#include <ostream>
#include <span>

#include "chromobius/datatypes/conf.h"
#include "stim.h"

namespace chromobius {

enum Charge : uint8_t {
    NEUTRAL = 0,
    R = 1,
    G = 2,
    B = 3,
};
inline Charge next_non_neutral_charge(Charge c) {
    return (Charge)(c % 3 + 1);
}
inline Charge operator^(Charge c1, Charge c2) {
    return (Charge)((uint8_t)c1 ^ (uint8_t)c2);
}
inline Charge &operator^=(Charge &c1, Charge c2) {
    c1 = (Charge)((uint8_t)c1 ^ (uint8_t)c2);
    return c1;
}

enum SubGraphCoord : uint8_t {
    UNKNOWN_SUBGRAPH_COORD = 0,
    NotRed = 1,
    NotGreen = 2,
    NotBlue = 3,
};

constexpr uint8_t SUBGRAPH_OFFSET_Red_NotGreen = 0;
constexpr uint8_t SUBGRAPH_OFFSET_Red_NotBlue = 1;
constexpr uint8_t SUBGRAPH_OFFSET_Green_NotRed = 0;
constexpr uint8_t SUBGRAPH_OFFSET_Green_NotBlue = 1;
constexpr uint8_t SUBGRAPH_OFFSET_Blue_NotRed = 0;
constexpr uint8_t SUBGRAPH_OFFSET_Blue_NotGreen = 1;

enum Basis : uint8_t {
    UNKNOWN_BASIS = 0,
    X = 1,
    Z = 2,
};

struct ColorBasis {
    Charge color;
    Basis basis;
    bool operator==(const ColorBasis &other) const;
    bool operator!=(const ColorBasis &other) const;
    std::string str() const;
};
std::ostream &operator<<(std::ostream &out, const ColorBasis &val);
std::ostream &operator<<(std::ostream &out, const Charge &val);
std::ostream &operator<<(std::ostream &out, const SubGraphCoord &val);
std::ostream &operator<<(std::ostream &out, const Basis &val);

ColorBasis detector_instruction_to_color_basis(
    const stim::DemInstruction &instruction, std::span<const double> coord_offsets);
std::tuple<node_offset_int, Charge, SubGraphCoord> mobius_node_to_detector(
    uint64_t mobius_node, std::span<const ColorBasis> colors);
uint64_t detector_to_mobius_node(node_offset_int node, SubGraphCoord subgraph, std::span<const ColorBasis> colors);

}  // namespace chromobius

#endif
