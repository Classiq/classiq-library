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

#include "chromobius/datatypes/color_basis.h"

#include <sstream>

using namespace chromobius;

bool ColorBasis::operator==(const ColorBasis &other) const {
    return color == other.color && basis == other.basis;
}

bool ColorBasis::operator!=(const ColorBasis &other) const {
    return !(*this == other);
}
std::string ColorBasis::str() const {
    std::stringstream ss;
    ss << *this;
    return ss.str();
}
std::ostream &chromobius::operator<<(std::ostream &out, const ColorBasis &val) {
    out << "ColorBasis{.color=" << val.color << ", .basis=" << val.basis << "}";
    return out;
}

std::ostream &chromobius::operator<<(std::ostream &out, const Basis &val) {
    switch (val) {
        case Basis::UNKNOWN_BASIS:
            out << "UNKNOWN_BASIS";
            break;
        case Basis::X:
            out << "X";
            break;
        case Basis::Z:
            out << "Z";
            break;
        default:
            out << (int)val;
    }
    return out;
}

std::ostream &chromobius::operator<<(std::ostream &out, const Charge &val) {
    switch (val) {
        case Charge::NEUTRAL:
            out << "NEUTRAL";
            break;
        case Charge::R:
            out << "R";
            break;
        case Charge::G:
            out << "G";
            break;
        case Charge::B:
            out << "B";
            break;
        default:
            out << (int)val;
    }
    return out;
}
std::ostream &chromobius::operator<<(std::ostream &out, const SubGraphCoord &val) {
    switch (val) {
        case SubGraphCoord::UNKNOWN_SUBGRAPH_COORD:
            out << "UNKNOWN_SUBGRAPH_COORD";
            break;
        case SubGraphCoord::NotRed:
            out << "NotRed";
            break;
        case SubGraphCoord::NotGreen:
            out << "NotGreen";
            break;
        case SubGraphCoord::NotBlue:
            out << "NotBlue";
            break;
        default:
            out << (int)val;
    }
    return out;
}

ColorBasis chromobius::detector_instruction_to_color_basis(
    const stim::DemInstruction &instruction, std::span<const double> coord_offsets) {
    assert(instruction.type == stim::DemInstructionType::DEM_ERROR);
    double c = -1;
    if (instruction.arg_data.size() > 3) {
        c = instruction.arg_data[3];
        if (coord_offsets.size() > 3) {
            c += coord_offsets[3];
        }
    }
    int r = (int)c;
    if (r < 0 || r >= 6 || r != c) {
        throw std::invalid_argument(
            "Expected all detectors to have at least 4 coordinates, with the 4th "
            "identifying the basis and color "
            "(RedX=0, GreenX=1, BlueX=2, RedZ=3, GreenZ=4, BlueZ=5), but got " +
            instruction.str());
    }
    constexpr std::array<ColorBasis, 6> mapping{
        ColorBasis{Charge::R, Basis::X},
        ColorBasis{Charge::G, Basis::X},
        ColorBasis{Charge::B, Basis::X},
        ColorBasis{Charge::R, Basis::Z},
        ColorBasis{Charge::G, Basis::Z},
        ColorBasis{Charge::B, Basis::Z},
    };
    return mapping[r];
}

std::tuple<node_offset_int, Charge, SubGraphCoord> chromobius::mobius_node_to_detector(
    uint64_t mobius_node, std::span<const ColorBasis> colors) {
    auto n = mobius_node >> 1;
    uint8_t g = (mobius_node & 1) + 1;
    Charge c = colors[n].color;
    g += (uint8_t)g >= (uint8_t)c;
    return {n, c, (SubGraphCoord)g};
}

uint64_t chromobius::detector_to_mobius_node(
    node_offset_int node, SubGraphCoord subgraph, std::span<const ColorBasis> colors) {
    auto c = colors[node].color;
    uint8_t offset;
    if (c == Charge::R && subgraph == SubGraphCoord::NotGreen) {
        offset = SUBGRAPH_OFFSET_Red_NotGreen;
    } else if (c == Charge::R && subgraph == SubGraphCoord::NotBlue) {
        offset = SUBGRAPH_OFFSET_Red_NotBlue;
    } else if (c == Charge::G && subgraph == SubGraphCoord::NotRed) {
        offset = SUBGRAPH_OFFSET_Green_NotRed;
    } else if (c == Charge::G && subgraph == SubGraphCoord::NotBlue) {
        offset = SUBGRAPH_OFFSET_Green_NotBlue;
    } else if (c == Charge::B && subgraph == SubGraphCoord::NotRed) {
        offset = SUBGRAPH_OFFSET_Blue_NotRed;
    } else if (c == Charge::B && subgraph == SubGraphCoord::NotGreen) {
        offset = SUBGRAPH_OFFSET_Blue_NotGreen;
    } else {
        throw std::invalid_argument("Bad node subgraph.");
    }
    return node * 2 + offset;
}
