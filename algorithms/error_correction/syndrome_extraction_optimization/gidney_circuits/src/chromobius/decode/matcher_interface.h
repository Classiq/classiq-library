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

#ifndef _CHROMOBIUS_DECODE_MATCHER_INTERFACE_H
#define _CHROMOBIUS_DECODE_MATCHER_INTERFACE_H

#include <cstdint>
#include <vector>
#include <memory>

#include "stim.h"

namespace chromobius {

/// This class is used to implement polymorphism
struct MatcherInterface {
    virtual ~MatcherInterface(){};

    /// Creates a new instance of the matcher, configured for the given detector error model.
    virtual std::unique_ptr<MatcherInterface> configured_for_mobius_dem(const stim::DetectorErrorModel &dem) = 0;

    /// Performs matching on the given mobius dem detection events, producing edges.
    ///
    /// Args:
    ///     mobius_detection_event_indices: The detection events to decode.
    ///     out_edge_buffer: Where to write edges to. Edges should be rewritten in an
    ///         interleaved fashion, so that (out_edge_buffer[2*k], out_edge_buffer[2*k+1])
    ///         is an edge. There should be no boundary edges in the result, since the mobius
    ///         dem is guaranteed to not contain any boundary edges.
    virtual void match_edges(
        const std::vector<uint64_t> &mobius_detection_event_indices, std::vector<int64_t> *out_edge_buffer) = 0;
};

}  // namespace chromobius

#endif
