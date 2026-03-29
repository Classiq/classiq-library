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

#ifndef _CHROMOBIUS_CHOOSE_RGB_REPS_H
#define _CHROMOBIUS_CHOOSE_RGB_REPS_H

#include "chromobius/datatypes/atomic_error.h"
#include "chromobius/datatypes/rgb_edge.h"

namespace chromobius {

std::vector<RgbEdge> choose_rgb_reps_from_atomic_errors(
    const std::map<AtomicErrorKey, obsmask_int> &atomic_errors, std::span<const ColorBasis> node_colors);

}  // namespace chromobius

#endif
