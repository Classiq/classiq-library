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

#ifndef _CHROMOBIUS_COLLECT_NODES_H
#define _CHROMOBIUS_COLLECT_NODES_H

#include <span>

#include "chromobius/datatypes/atomic_error.h"
#include "chromobius/datatypes/color_basis.h"
#include "stim.h"

namespace chromobius {

/// Creates a list of color/basis data for all detectors in the dem.
///
/// The color/basis data is read from the 4th coordinate of each detector's
/// coordinate data using the convention 0=XR 1=XG 2=XB 3=ZR 4=ZG 5=ZB.
///
/// Args:
///     dem: The detector error model to read detector data from.
///     out_mobius_dem: Optional. If not set to null, transformed coordinate
///         data for the mobius dem's detectors is appended to this dem.
///
/// Returns:
///     A vector containing the color and basis data, indexed by detector id.
std::vector<ColorBasis> collect_nodes_from_dem(
    const stim::DetectorErrorModel &dem, stim::DetectorErrorModel *out_mobius_dem);

}  // namespace chromobius

#endif
