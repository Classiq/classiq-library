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

#include "gtest/gtest.h"

#include "chromobius/decode/decoder.h"
#include "chromobius/test_util.test.h"

using namespace chromobius;

size_t count_mistakes_decoding_test_data_file(size_t shots, const char *name) {
    FILE *f = open_test_data_file(name);
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, true, false, 0, false, false);
    Decoder decoder = Decoder::from_dem(src_dem, DecoderConfigOptions{});
    decoder.check_invariants();

    std::mt19937_64 rng{0};
    size_t mistakes = 0;
    auto [dets, obs_actual] = stim::sample_batch_detection_events<64>(src_circuit, shots, rng);
    dets = dets.transposed();
    obs_actual = obs_actual.transposed();
    for (size_t k = 0; k < shots; k++) {
        std::span<uint8_t> det_data{dets[k].u8, dets[k].u8 + dets.num_minor_u8_padded()};
        auto obs_predicted = decoder.decode_detection_events(det_data);
        mistakes += obs_actual[k].u64[0] != obs_predicted;
    }
    return mistakes;
}

void verify_error_resilience(const char *name) {
    FILE *f = open_test_data_file(name);
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, false, false, 0, false, false);
    Decoder decoder = Decoder::from_dem(src_dem, DecoderConfigOptions{});
    size_t num_dets = (size_t)src_dem.count_detectors();

    std::set<size_t> bad_error_set;
    std::vector<size_t> bad_errors;
    stim::DemSampler<stim::MAX_BITWORD_WIDTH> sampler(src_dem, std::mt19937_64{0}, 1024);

    // Work in batches of 1024 to reduce sampling cost.
    for (size_t err_start = 0; err_start < num_dets; err_start += 1024) {
        for (size_t k = 0; k < 1024; k++) {
            size_t err_k = err_start + k;
            if (err_k < num_dets) {
                sampler.err_buffer[err_k][k] = 1;
            }
        }
        sampler.resample(true);

        auto dets = sampler.det_buffer.transposed();
        auto obs_actual = sampler.obs_buffer.transposed();
        for (size_t k = 0; k < 1024; k++) {
            size_t err_k = k + err_start;
            std::span<uint8_t> det_data{dets[k].u8, dets[k].u8 + dets.num_minor_u8_padded()};

            obsmask_int obs_predicted;
            try {
                obs_predicted = decoder.decode_detection_events(det_data);
                if (obs_actual[k].u64[0] != obs_predicted) {
                    bad_errors.push_back(err_k);
                    bad_error_set.insert(err_k);
                }
            } catch (const std::exception &ex) {
                dets.clear();
                bad_errors.push_back(err_k);
                bad_error_set.insert(err_k);
            }
        }

        sampler.err_buffer.clear();
    }

    if (!bad_errors.empty()) {
        std::set<uint64_t> included_detector_indices;
        for (size_t k = 0; k < num_dets; k++) {
            included_detector_indices.insert(k);
        }
        auto coords = src_dem.get_detector_coordinates(included_detector_indices);
        stim::DetectorErrorModel bad_dem;
        size_t err_index = 0;
        for (const auto &instruction : src_dem.instructions) {
            if (instruction.type == stim::DemInstructionType::DEM_ERROR) {
                if (bad_error_set.contains(err_index)) {
                    bad_dem.append_dem_instruction(instruction);
                }
                err_index++;
            }
        }
        auto explained = stim::ErrorMatcher::explain_errors_from_circuit(src_circuit, &bad_dem, true);
        std::stringstream ss;
        for (size_t k = 0; k < explained.size(); k++) {
            ss << "\nFailed to correct error #" << bad_errors[k] << " from " << name << ":\n";
            ss << "\n    " << bad_dem.instructions[k];
            for (auto t : bad_dem.instructions[k].target_data) {
                if (t.is_relative_detector_id()) {
                    ss << "\n    " << decoder.node_colors[t.val()];
                }
            }
            ss << "\n  " << explained[k] << "\n";
        }
        EXPECT_TRUE(bad_errors.empty()) << ss.str();
    }
}

obsmask_int decode_single(const char *name, const std::vector<uint64_t> detection_events) {
    FILE *f = open_test_data_file(name);
    stim::Circuit src_circuit = stim::Circuit::from_file(f);
    fclose(f);
    auto src_dem =
        stim::ErrorAnalyzer::circuit_to_detector_error_model(src_circuit, false, false, false, 0, false, false);
    Decoder decoder = Decoder::from_dem(src_dem, DecoderConfigOptions{});
    size_t num_dets = (size_t)src_dem.count_detectors();

    stim::simd_bits<64> dets(num_dets);
    for (const auto &d : detection_events) {
        dets[d] = 1;
    }
    std::span<uint8_t> det_data{dets.u8, dets.u8 + dets.num_u8_padded()};
    return decoder.decode_detection_events(det_data);
}

struct IntegrationTestData : public testing::TestWithParam<std::tuple<const char *, int>> {};
INSTANTIATE_TEST_SUITE_P(
    IntegrationTests,
    IntegrationTestData,
    ::testing::Values(
                std::tuple<const char *, int>{"toric_superdense_color_code_epr_d12_r5_p1000.stim", 1693},
                std::tuple<const char *, int>{"midout488_color_code_d9_r33_p1000.stim", 823},
                std::tuple<const char *, int>{"midout_color_code_d5_r10_p1000.stim", 94},
                std::tuple<const char *, int>{"midout_color_code_d9_r36_p1000.stim", 45},
                std::tuple<const char *, int>{"superdense_color_code_d5_r20_p1000.stim", 329},  // Including remnant errors reduces to 273?
                std::tuple<const char *, int>{"phenom_color_code_d5_r5_p1000.stim", 0},
                std::tuple<const char *, int>{"surface_code_d5_r5_p1000.stim", 3},
                std::tuple<const char *, int>{"rep_code_d9_transit_p10.stim", 1},
                std::tuple<const char *, int>{"rep_code_rg_d9_transit_p10.stim", 1},
                std::tuple<const char *, int>{"rep_code_rbrrr_d9_transit_p10.stim", 1},
                std::tuple<const char *, int>{"color2surface_d5_transit_p100.stim", 1},
                std::tuple<const char *, int>{"color2surface_d7_phenom_r7_p100.stim", 12}
        ));

TEST_P(IntegrationTestData, expected_failure_count) {
    auto [name, expected] = GetParam();
    auto mistakes = count_mistakes_decoding_test_data_file(8192, name);
    EXPECT_EQ(mistakes, expected) << name;
}

TEST_P(IntegrationTestData, single_error_resilience) {
    auto [name, expected] = GetParam();
    verify_error_resilience(name);
}

TEST(FixCheck, euler_tour_ordering) {
    decode_single("fix_check_1.stim", {8687, 8736, 8737, 8763, 8945, 8720});
}

TEST(FixCheck, phenom_rgb_reps_for_last_layer) {
    decode_single("fix_check_1.stim", {8915, 8914, 8890});
}
