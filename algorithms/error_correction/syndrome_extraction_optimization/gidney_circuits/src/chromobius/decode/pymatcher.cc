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

#include "chromobius/decode/pymatcher.h"

using namespace chromobius;

PymatchingMatcher::PymatchingMatcher() : pymatching_matcher() {
}

PymatchingMatcher::PymatchingMatcher(const stim::DetectorErrorModel &dem)
    : pymatching_matcher(pm::detector_error_model_to_mwpm(dem, 1 << 24, true)) {
}

void PymatchingMatcher::match_edges(
    const std::vector<uint64_t> &mobius_detection_event_indices, std::vector<int64_t> *out_edge_buffer) {
    pm::decode_detection_events_to_edges(pymatching_matcher, mobius_detection_event_indices, *out_edge_buffer);
}

std::unique_ptr<MatcherInterface> PymatchingMatcher::configured_for_mobius_dem(const stim::DetectorErrorModel &dem) {
    std::unique_ptr<MatcherInterface> result;
    result.reset(new PymatchingMatcher(dem));
    return result;
}
