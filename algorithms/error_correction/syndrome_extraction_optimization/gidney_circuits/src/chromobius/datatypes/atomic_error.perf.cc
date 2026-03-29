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

#include "chromobius/util.perf.h"
#include "stim.h"

using namespace chromobius;

BENCHMARK(sort3) {
    std::vector<node_offset_int> data;
    std::mt19937_64 rng{0};
    for (size_t k = 0; k < 999; k++) {
        data.push_back((node_offset_int)rng());
    }

    size_t v0 = 0;
    size_t v1 = 0;
    size_t v2 = 0;
    benchmark_go([&]() {
        for (size_t k = 0; k < data.size(); k += 3) {
            auto abc = sort3(data[k], data[k + 1], data[k + 2]);
            v0 += abc[0];
            v1 ^= abc[1];
            v2 += abc[2];
        }
    })
        .goal_nanos(150)
        .show_rate("Constructions", data.size() / 3);
    if (v0 + v1 + v2 == 1) {
        std::cerr << "data dependence";
    }
}

BENCHMARK(sort3_known_max) {
    std::vector<node_offset_int> data;
    std::mt19937_64 rng{0};
    for (size_t k = 0; k < 999; k++) {
        data.push_back((node_offset_int)rng());
    }

    size_t v0 = 0;
    size_t v1 = 0;
    size_t v2 = 0;
    benchmark_go([&]() {
        for (size_t k = 0; k < data.size(); k += 3) {
            auto e2 = sort3(data[k], UINT32_MAX, data[k + 1]);
            v0 += e2[0];
            v1 ^= e2[1];
            v2 += e2[2];
        }
    })
        .goal_nanos(100)
        .show_rate("Constructions", data.size() / 3);
    if (v0 + v1 + v2 == 1) {
        std::cerr << "data dependence";
    }
}
