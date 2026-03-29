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

#ifndef _CHROMOBIUS_COLLECT_COMPOSITE_ERRORS_H
#define _CHROMOBIUS_COLLECT_COMPOSITE_ERRORS_H

#include <span>

#include "chromobius/datatypes/atomic_error.h"
#include "chromobius/datatypes/color_basis.h"
#include "chromobius/graph/collect_atomic_errors.h"
#include "stim.h"

namespace chromobius {

/// Builds the mobius dem by decomposing errors from a dem into known atomic errors.
///
/// Args:
///     dem: The detector error model to read original error instructions from.
///     node_colors: Previously collected node color and basis data.
///     atomic_errors: Previously collected basic errors to decompose into.
///     ignore_decomposition_failures: If set to True, then failing to decompose
///         an error into atomic errors causes the error to be discarded instead of
///         throwing an exception.
///     out_mobius_dem: Where to write the decomposed mobius error mechanisms.
///     out_remnants: Some errors can't be perfectly decomposed into existing atomic
///         errors, but can be decomposed into an atomic error and a leftover part that
///         would be a valid atomic error. This is where the remnants that are used
///         get written.
void collect_composite_errors_and_remnants_into_mobius_dem(
    const stim::DetectorErrorModel &dem,
    std::span<const ColorBasis> node_colors,
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors,
    bool drop_mobius_errors_involving_remnant_errors,
    bool ignore_decomposition_failures,
    stim::DetectorErrorModel *out_mobius_dem,
    std::map<AtomicErrorKey, obsmask_int> *out_remnants);

}  // namespace chromobius

#endif
