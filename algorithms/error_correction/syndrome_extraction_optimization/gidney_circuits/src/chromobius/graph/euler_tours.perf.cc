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

#include "chromobius/graph/euler_tours.h"

#include "chromobius/util.perf.h"
#include "stim.h"

using namespace chromobius;

BENCHMARK(solve_euler_tours_n10000) {
    std::mt19937_64 rng{0};
    std::vector<int64_t> edges;
    for (size_t k = 0; k < 2000; k++) {
        node_offset_int a;
        node_offset_int b;
        node_offset_int c;
        do {
            a = rng() % 9999 + 1;
            b = rng() % 9999 + 1;
            c = rng() % 9999 + 1;
        } while (a == b || b == c || a == c);
        edges.push_back(a);
        edges.push_back(b);
        edges.push_back(b);
        edges.push_back(c);
        edges.push_back(a);
        edges.push_back(c);
    }
    std::shuffle(edges.begin(), edges.end(), rng);
    EulerTourGraph g(10000);

    size_t n = 0;
    benchmark_go([&]() {
        g.iter_euler_tours_of_interleaved_edge_list(edges, {}, [&](std::span<const node_offset_int> cycle) {
            n += cycle.size();
        });
    })
        .goal_micros(230)
        .show_rate("edges", edges.size());
    if (n == 1) {
        std::cerr << "data dependence";
    }
}
