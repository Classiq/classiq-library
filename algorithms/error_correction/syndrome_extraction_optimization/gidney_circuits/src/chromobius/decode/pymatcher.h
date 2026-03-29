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

#ifndef _CHROMOBIUS_DECODE_PYMATCHER_H
#define _CHROMOBIUS_DECODE_PYMATCHER_H

#include "chromobius/decode/matcher_interface.h"
#include "pymatching/sparse_blossom/driver/mwpm_decoding.h"

namespace chromobius {

struct PymatchingMatcher : MatcherInterface {
    pm::Mwpm pymatching_matcher;

    PymatchingMatcher();
    PymatchingMatcher(const stim::DetectorErrorModel &dem);
    virtual ~PymatchingMatcher() = default;

    virtual std::unique_ptr<MatcherInterface> configured_for_mobius_dem(const stim::DetectorErrorModel &dem) override;

    virtual void match_edges(
        const std::vector<uint64_t> &mobius_detection_event_indices, std::vector<int64_t> *out_edge_buffer) override;
};

}  // namespace chromobius

#endif
