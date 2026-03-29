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

#include "chromobius/datatypes/atomic_error.h"

using namespace chromobius;

void AtomicErrorKey::check_invariants(std::span<const ColorBasis> det_types) {
    Charge net_charge = Charge::NEUTRAL;
    for (auto d : dets) {
        if (d < det_types.size()) {
            net_charge ^= det_types[d].color;
        } else if (d != BOUNDARY_NODE) {
            std::stringstream ss;
            ss << *this << " has a too-large detector index. det_types.size() = " << det_types.size();
            throw std::invalid_argument(ss.str());
        }
    }

    if (dets[0] == BOUNDARY_NODE) {
        throw std::invalid_argument("Vacuous: " + str());
    }
    if (dets[0] > dets[1] || dets[1] > dets[2]) {
        throw std::invalid_argument("Not sorted: " + str());
    }
    if (net_charge != Charge::NEUTRAL && dets[2] != BOUNDARY_NODE) {
        std::stringstream ss;
        ss << "Triplet " << *this << " has non-neutral charge " << net_charge;
        throw std::invalid_argument(ss.str());
    }
}

std::ostream &chromobius::operator<<(std::ostream &out, const AtomicErrorKey &val) {
    out << "AtomicErrorKey{.dets={";
    for (size_t k = 0; k < 3; k++) {
        if (k > 0) {
            out << ", ";
        }
        if (val.dets[k] == BOUNDARY_NODE) {
            out << "BOUNDARY_NODE";
        } else {
            out << val.dets[k];
        }
    }
    out << "}}";
    return out;
}
std::string AtomicErrorKey::str() const {
    std::stringstream ss;
    ss << *this;
    return ss.str();
}
