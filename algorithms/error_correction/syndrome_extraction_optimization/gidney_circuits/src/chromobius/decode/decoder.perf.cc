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

#include "chromobius/decode/decoder.h"

#include <span>

#include "chromobius/util.perf.h"
#include "stim.h"

using namespace chromobius;

FILE *open_test_data_file(const char *name) {
    std::vector<std::string> directories_to_check = {
        "test_data/",
        "../test_data/",
        "../../test_data/",
    };
    for (const auto &d : directories_to_check) {
        std::string path = d + name;
        FILE *f = fopen((d + name).c_str(), "r");
        if (f != nullptr) {
            return f;
        }
    }
    throw std::invalid_argument("Failed to find test data file " + std::string(name));
}

BENCHMARK(configure_midout_color_code_d25_r100_p1000) {
    FILE *f = open_test_data_file("midout_color_code_d25_r100_p1000.stim");
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, true, false, 0, false, false);

    size_t k = 0;
    benchmark_go([&]() {
        Decoder d = Decoder::from_dem(src_dem, DecoderConfigOptions{});
        k += d.mobius_dem.instructions.size();
        k += d.matcher_edge_buf.size();
        k += d.atomic_errors.size();
        k += d.drag_graph.mmm.size();
    }).goal_millis(1800);
    if (k == 1) {
        std::cerr << "data dependence";
    }
}

BENCHMARK(configure_midout_color_code_d9_r36_p1000) {
    FILE *f = open_test_data_file("midout_color_code_d9_r36_p1000.stim");
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, true, false, 0, false, false);

    size_t k = 0;
    benchmark_go([&]() {
        Decoder d = Decoder::from_dem(src_dem, DecoderConfigOptions{});
        k += d.mobius_dem.instructions.size();
        k += d.matcher_edge_buf.size();
        k += d.atomic_errors.size();
        k += d.drag_graph.mmm.size();
    }).goal_millis(60);
    if (k == 1) {
        std::cerr << "data dependence";
    }
}

BENCHMARK(configure_midout_color_code_d5_r10_p1000) {
    FILE *f = open_test_data_file("midout_color_code_d5_r10_p1000.stim");
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, true, false, 0, false, false);

    size_t k = 0;
    benchmark_go([&]() {
        Decoder d = Decoder::from_dem(src_dem, DecoderConfigOptions{});
        k += d.mobius_dem.instructions.size();
        k += d.matcher_edge_buf.size();
        k += d.atomic_errors.size();
        k += d.drag_graph.mmm.size();
    }).goal_millis(3.4);
    if (k == 1) {
        std::cerr << "data dependence";
    }
}

BENCHMARK(decode_midout_color_code_d5_r10_p1000) {
    FILE *f = open_test_data_file("midout_color_code_d5_r10_p1000.stim");
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, true, false, 0, false, false);
    Decoder decoder = Decoder::from_dem(src_dem, DecoderConfigOptions{});

    size_t num_shots = 1024;
    std::mt19937_64 rng{0};
    auto sample = stim::sample_batch_detection_events<64>(src_circuit, num_shots, rng);
    auto &dets = sample.first;
    auto &obs_actual = sample.second;
    dets = dets.transposed();
    obs_actual = obs_actual.transposed();
    size_t num_dets = 0;
    for (size_t k = 0; k < num_shots; k++) {
        num_dets += dets[k].popcnt();
    }

    size_t mistakes = 0;
    benchmark_go([&]() {
        for (size_t k = 0; k < num_shots; k++) {
            std::span<uint8_t> det_data{dets[k].u8, dets[k].u8 + dets.num_minor_u8_padded()};
            auto obs_predicted = decoder.decode_detection_events(det_data);
            mistakes += obs_actual[k].u64[0] != obs_predicted;
        }
    })
        .goal_millis(4.5)
        .show_rate("shots", num_shots)
        .show_rate("dets", num_dets);
    if (mistakes == 1) {
        std::cerr << "data dependence";
    }
}

BENCHMARK(decode_midout_color_code_d9_r36_p1000) {
    FILE *f = open_test_data_file("midout_color_code_d9_r36_p1000.stim");
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, true, false, 0, false, false);
    Decoder decoder = Decoder::from_dem(src_dem, DecoderConfigOptions{});

    size_t num_shots = 1024;
    std::mt19937_64 rng{0};
    auto sample = stim::sample_batch_detection_events<64>(src_circuit, num_shots, rng);
    auto &dets = sample.first;
    auto &obs_actual = sample.second;
    dets = dets.transposed();
    obs_actual = obs_actual.transposed();
    size_t num_dets = 0;
    for (size_t k = 0; k < num_shots; k++) {
        num_dets += dets[k].popcnt();
    }

    size_t mistakes = 0;
    benchmark_go([&]() {
        for (size_t k = 0; k < num_shots; k++) {
            std::span<uint8_t> det_data{dets[k].u8, dets[k].u8 + dets.num_minor_u8_padded()};
            auto obs_predicted = decoder.decode_detection_events(det_data);
            mistakes += obs_actual[k].u64[0] != obs_predicted;
        }
    })
        .goal_millis(90)
        .show_rate("shots", num_shots)
        .show_rate("dets", num_dets);
    if (mistakes == 1) {
        std::cerr << "data dependence";
    }
}

BENCHMARK(decode_midout_color_code_d25_r100_p1000) {
    FILE *f = open_test_data_file("midout_color_code_d25_r100_p1000.stim");
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, true, false, 0, false, false);
    Decoder decoder = Decoder::from_dem(src_dem, DecoderConfigOptions{});
    size_t num_shots = 128;

    std::mt19937_64 rng{0};
    auto sample = stim::sample_batch_detection_events<64>(src_circuit, num_shots, rng);
    auto &dets = sample.first;
    auto &obs_actual = sample.second;
    dets = dets.transposed();
    obs_actual = obs_actual.transposed();
    size_t num_dets = 0;
    for (size_t k = 0; k < num_shots; k++) {
        num_dets += dets[k].popcnt();
    }

    size_t mistakes = 0;
    benchmark_go([&]() {
        for (size_t k = 0; k < num_shots; k++) {
            std::span<uint8_t> det_data{dets[k].u8, dets[k].u8 + dets.num_minor_u8_padded()};
            auto obs_predicted = decoder.decode_detection_events(det_data);
            mistakes += obs_actual[k].u64[0] != obs_predicted;
        }
    })
        .goal_millis(420)
        .show_rate("shots", num_shots)
        .show_rate("dets", num_dets);
    if (mistakes == 1) {
        std::cerr << "data dependence";
    }
}
