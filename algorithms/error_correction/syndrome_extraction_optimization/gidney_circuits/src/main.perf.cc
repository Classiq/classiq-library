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

#include <cmath>
#include <iostream>

#include "chromobius/util.perf.h"
#include "stim.h"

RegisteredBenchmark *running_benchmark = nullptr;
std::vector<RegisteredBenchmark> *all_registered_benchmarks_data = nullptr;
uint64_t registry_initialized = 0;

/// Describe quantity as an SI-prefixed value with two significant figures.
std::string si2(double val) {
    char unit = ' ';
    if (val < 1) {
        if (val < 1) {
            val *= 1000;
            unit = 'm';
        }
        if (val < 1) {
            val *= 1000;
            unit = 'u';
        }
        if (val < 1) {
            val *= 1000;
            unit = 'n';
        }
        if (val < 1) {
            val *= 1000;
            unit = 'p';
        }
    } else {
        if (val > 1000) {
            val /= 1000;
            unit = 'k';
        }
        if (val > 1000) {
            val /= 1000;
            unit = 'M';
        }
        if (val > 1000) {
            val /= 1000;
            unit = 'G';
        }
        if (val > 1000) {
            val /= 1000;
            unit = 'T';
        }
    }
    std::stringstream ss;
    if (1 <= val && val < 10) {
        ss << (size_t)val << '.' << ((size_t)(val * 10) % 10);
    } else if (10 <= val && val < 100) {
        ss << ' ' << (size_t)val;
    } else if (100 <= val && val < 1000) {
        ss << (size_t)(val / 10) * 10;
    } else {
        ss << val;
    }
    ss << ' ' << unit;
    return ss.str();
}

static std::vector<const char *> known_arguments{"--only", "--target_seconds"};

void find_benchmarks(const std::string &filter, std::vector<RegisteredBenchmark> &out) {
    bool found = false;

    if (!filter.empty() && filter[filter.size() - 1] == '*') {
        std::string start = filter.substr(0, filter.size() - 1);
        for (const auto &benchmark : *all_registered_benchmarks_data) {
            if (benchmark.name.substr(0, start.size()) == start) {
                out.push_back(benchmark);
                found = true;
            }
        }
    } else {
        for (const auto &benchmark : *all_registered_benchmarks_data) {
            if (benchmark.name == filter) {
                out.push_back(benchmark);
                found = true;
            }
        }
    }

    if (!found) {
        std::cerr << "No benchmark matching filter '" << filter << "'. Available benchmarks are:\n";
        for (auto &benchmark : *all_registered_benchmarks_data) {
            std::cerr << "    " << benchmark.name << "\n";
        }
        exit(EXIT_FAILURE);
    }
}

double BENCHMARK_CONFIG_TARGET_SECONDS = 0.5;

int main(int argc, const char **argv) {
    stim::check_for_unknown_arguments(known_arguments, {}, nullptr, argc, argv);
    const char *only = stim::find_argument("--only", argc, argv);
    BENCHMARK_CONFIG_TARGET_SECONDS = stim::find_float_argument("--target_seconds", 0.5, 0, 10000, argc, argv);

    std::vector<RegisteredBenchmark> chosen_benchmarks;
    if (only == nullptr) {
        chosen_benchmarks = *all_registered_benchmarks_data;
    } else {
        std::string filter_text = only;
        std::vector<std::string> filters{};
        size_t s = 0;
        for (size_t k = 0;; k++) {
            if (only[k] == ',' || only[k] == '\0') {
                filters.push_back(filter_text.substr(s, k - s));
                s = k + 1;
            }
            if (only[k] == '\0') {
                break;
            }
        }

        if (filters.empty()) {
            std::cerr << "No filters specified.\n";
            exit(EXIT_FAILURE);
        }

        for (const auto &filter : filters) {
            find_benchmarks(filter, chosen_benchmarks);
        }
    }

    for (auto &benchmark : chosen_benchmarks) {
        running_benchmark = &benchmark;
        benchmark.func();
        for (const auto &result : benchmark.results) {
            double actual_seconds_per_rep = result.total_seconds / result.total_reps;
            if (result.goal_seconds != -1) {
                int deviation = (int)round((log(result.goal_seconds) - log(actual_seconds_per_rep)) / (log(10) / 10.0));
                std::cout << "[";
                for (int k = -20; k <= 20; k++) {
                    if ((k < deviation && k < 0) || (k > deviation && k > 0)) {
                        std::cout << '.';
                    } else if (k == deviation) {
                        std::cout << '*';
                    } else if (k == 0) {
                        std::cout << '|';
                    } else if (deviation < 0) {
                        std::cout << '<';
                    } else {
                        std::cout << '>';
                    }
                }
                std::cout << "] ";
                std::cout << si2(actual_seconds_per_rep) << "s";
                std::cout << " (vs " << si2(result.goal_seconds) << "s) ";
            } else {
                std::cout << si2(actual_seconds_per_rep) << "s ";
            }
            for (const auto &e : result.marginal_rates) {
                const auto &multiplier = e.second;
                const auto &unit = e.first;
                std::cout << "(" << si2(result.total_reps / result.total_seconds * multiplier) << unit << "/s) ";
            }
            std::cout << benchmark.name << "\n";
            if (benchmark.results.empty()) {
                std::cerr << "`benchmark_go` was not called from BENCH(" << benchmark.name << ")";
                exit(EXIT_FAILURE);
            }
        }
    }

    if (all_registered_benchmarks_data != nullptr) {
        delete all_registered_benchmarks_data;
        all_registered_benchmarks_data = nullptr;
    }
    return 0;
}
