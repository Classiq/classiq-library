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

#ifndef _CHROMOBIUS_DECODER_H
#define _CHROMOBIUS_DECODER_H

#include "chromobius/datatypes/rgb_edge.h"
#include "chromobius/graph/charge_graph.h"
#include "chromobius/graph/collect_atomic_errors.h"
#include "chromobius/graph/collect_composite_errors.h"
#include "chromobius/graph/collect_nodes.h"
#include "chromobius/graph/drag_graph.h"
#include "chromobius/graph/euler_tours.h"
#include "chromobius/decode/matcher_interface.h"

namespace chromobius {

/// Invariant: drain_cycle_index_1 <= drain_cycle_index_2
struct ChargeDrain {
    size_t drain_cycle_index_1;
    Charge charge1;  // Set to Charge::NEUTRAL to disable.

    size_t drain_cycle_index_2;
    Charge charge2;  // Set to Charge::NEUTRAL to disable.
};

struct DecoderConfigOptions {
    /// Controls whether or not errors that required the introduction of a
    /// remnant atomic error in order to decompose should be discarded or not.
    /// Defaults to true because that seems to give the best performance in
    /// the most cases.
    bool drop_mobius_errors_involving_remnant_errors = true;

    /// When an error is encountered that can't be understood in terms of
    /// atomic errors, this decides whether or not that error is simply
    /// discarded or else if an exception is raised.
    bool ignore_decomposition_failures = false;

    /// Decides whether or not the underlying mobius detector error model will
    /// contain coordinate information. This can be useful when debugging or
    /// printing out information.
    bool include_coords_in_mobius_dem = false;

    /// Decides which matcher to use. If not set to anything, chromobius will
    /// default to using PyMatching.
    std::shared_ptr<MatcherInterface> matcher;

    std::unique_ptr<MatcherInterface> matcher_for(const stim::DetectorErrorModel &mobius_dem) const;
};

struct Decoder {
    /// The color and basis of each node in the graph.
    std::vector<ColorBasis> node_colors;
    /// The basic errors that more complex errors are decomposed into.
    std::map<AtomicErrorKey, obsmask_int> atomic_errors;
    /// The doubled detector error model given to the matcher.
    stim::DetectorErrorModel mobius_dem;

    ChargeGraph charge_graph;
    std::vector<RgbEdge> rgb_reps;
    DragGraph drag_graph;
    bool write_mobius_match_to_std_err = false;

    /// The configured matcher (e.g. from pymatching) used to decode the mobius problem.
    std::unique_ptr<MatcherInterface> matcher;

    /// Ephemeral workspace for putting detection event data to give to the matcher.
    std::vector<uint64_t> sparse_det_buffer;
    /// Ephemeral workspace for the matcher to save its results into.
    std::vector<int64_t> matcher_edge_buf;
    /// Ephemeral workspace for decomposing results from the matcher into separately solvable pieces.
    EulerTourGraph euler_tour_solver{0};
    /// Ephemeral workspace for tracking which detection events have been processed (within one euler cycle).
    std::vector<uint64_t> resolved_detection_event_buffer;

    /// Creates a decoder for a DEM with annotated detector colors and bases.
    ///
    /// The input DEM must have each detector annotated with its basis and color.
    /// The annotations use the 4th coordinate of the detector to do this. The
    /// value of the 4th coordinate identifies the basis and color:
    ///     0: basis=X, color=R
    ///     1: basis=X, color=G
    ///     2: basis=X, color=B
    ///     3: basis=Z, color=R
    ///     4: basis=Z, color=G
    ///     5: basis=Z, color=B
    ///
    /// Args:
    ///     dem: The detector error model to configure the decoder with.
    ///     options: Various configuration options affecting how decoding is
    ///         configured and performed. See the DecoderConfigOptions class
    ///         for details.
    ///
    /// Returns:
    ///     The configured decoder, ready to perform decoding.
    static Decoder from_dem(
        const stim::DetectorErrorModel &dem,
        DecoderConfigOptions options);

    void check_invariants() const;

    /// Predicts the observables flipped by errors producing the given detection
    /// events.
    ///
    /// As part of running, this method clears the detection event data back to 0.
    obsmask_int decode_detection_events(std::span<const uint8_t> bit_packed_detection_events);

   private:
    /// Handles getting rid of excitation events within a cycle found by the
    /// matcher.
    ///
    /// This method requires that either the cycle has neutral charge, or that
    /// there are subgraph-crossing edges to dump the charge into
    ///
    /// Args:
    ///     packed_detection_event_data_to_clear: The detection events being
    ///     explained.
    ///         As part of running, the method will all detection events within
    ///         the cycle.
    ///     cycle: The cycle of nodes to process. The specific format here
    ///     alternates
    ///         between node indices and the charge change to the next node. So,
    ///         for example, the cycle might be [5, NEUTRAL, 8, NEUTRAL, 9, RED,
    ///         10, NEUTRAL].
    ///
    /// Returns:
    ///     The observables that were flipped by the errors inserted to clear out
    ///     the detection events.
    obsmask_int discharge_cycle(
        std::span<const uint8_t> packed_detection_event_data_to_clear, std::span<const node_offset_int> cycle);
};
std::ostream &operator<<(std::ostream &out, const Decoder &val);

}  // namespace chromobius

#endif
