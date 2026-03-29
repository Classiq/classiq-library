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

#include "chromobius/commands/main_benchmark.h"

#include <chrono>

#include "chromobius/decode/decoder.h"
#include "stim.h"

using namespace chromobius;

int chromobius::main_benchmark(int argc, const char **argv) {
    auto time_config_starts = std::chrono::steady_clock::now();

    stim::check_for_unknown_arguments(
        {
            "--in",
            "--in_format",
            "--in_includes_appended_observables",
            "--obs_in",
            "--obs_in_format",
            "--out",
            "--dem",
        },
        {},
        "benchmark",
        argc,
        argv);

    FILE *shots_in = stim::find_open_file_argument("--in", stdin, "rb", argc, argv);
    FILE *obs_in = nullptr;
    if (stim::find_argument("--obs_in", argc, argv) != nullptr) {
        obs_in = stim::find_open_file_argument("--obs_in", nullptr, "rb", argc, argv);
    }
    FILE *stats_out = stim::find_open_file_argument("--out", stdout, "wb", argc, argv);
    FILE *dem_file = stim::find_open_file_argument("--dem", nullptr, "rb", argc, argv);
    stim::FileFormatData shots_in_format =
        stim::find_enum_argument("--in_format", "01", stim::format_name_to_enum_map(), argc, argv);
    stim::FileFormatData obs_in_format =
        stim::find_enum_argument("--obs_in_format", "01", stim::format_name_to_enum_map(), argc, argv);
    bool append_obs = stim::find_bool_argument("--in_includes_appended_observables", argc, argv);
    if (!append_obs && obs_in == nullptr) {
        throw std::invalid_argument("Must specify --in_includes_appended_observables or --obs_in.");
    }

    stim::DetectorErrorModel dem = stim::DetectorErrorModel::from_file(dem_file);
    fclose(dem_file);
    auto num_obs = dem.count_observables();
    auto num_dets = dem.count_detectors();

    std::unique_ptr<stim::MeasureRecordReader<stim::MAX_BITWORD_WIDTH>> obs_reader;
    if (obs_in != nullptr) {
        obs_reader = stim::MeasureRecordReader<stim::MAX_BITWORD_WIDTH>::make(obs_in, obs_in_format.id, 0, 0, num_obs);
    }
    auto reader = stim::MeasureRecordReader<stim::MAX_BITWORD_WIDTH>::make(
        shots_in, shots_in_format.id, 0, num_dets, append_obs * num_obs);

    size_t num_mistakes = 0;
    size_t num_shots = 0;
    uint64_t num_detection_events = 0;

    auto decoder = Decoder::from_dem(dem, DecoderConfigOptions{});
    stim::simd_bits<stim::MAX_BITWORD_WIDTH> buf_dets(reader->bits_per_record());
    stim::simd_bits<stim::MAX_BITWORD_WIDTH> buf_obs(num_obs);
    auto time_config_ends_decoding_starts = std::chrono::steady_clock::now();

    while (reader->start_and_read_entire_record(buf_dets)) {
        if (obs_reader == nullptr) {
            for (size_t k = 0; k < num_obs; k++) {
                buf_obs[k] = buf_dets[num_dets + k];
                buf_dets[num_dets + k] = 0;
            }
        } else if (!obs_reader->start_and_read_entire_record(buf_obs)) {
            throw std::invalid_argument("Obs data ended before shot data ended.");
        }
        num_detection_events += buf_dets.popcnt();
        auto prediction =
            decoder.decode_detection_events({buf_dets.u8, buf_dets.u8 + buf_dets.num_u8_padded()});
        if (buf_obs.u64[0] != prediction) {
            num_mistakes++;
        }
        num_shots++;
    }

    auto time_decoding_ends = std::chrono::steady_clock::now();
    auto decoding_microseconds = (double)std::chrono::duration_cast<std::chrono::microseconds>(
                                     time_decoding_ends - time_config_ends_decoding_starts)
                                     .count();
    auto config_microseconds = (double)std::chrono::duration_cast<std::chrono::microseconds>(
                                   time_config_ends_decoding_starts - time_config_starts)
                                   .count();

    auto total_detectors = (uint64_t)num_dets * (uint64_t)num_shots;
    std::stringstream output;
    output << "                                num_shots = " << num_shots << "\n";
    output << "                             num_mistakes = " << num_mistakes << "\n";
    output << "                        mistakes_per_shot = "
           << (num_shots ? (double)num_mistakes / (double)num_shots : 0) << "\n";
    output << "\n";
    output << "                     num_detection_events = " << num_detection_events << "\n";
    output << "                   num_detectors_per_shot = " << num_dets << "\n";
    output << "                       detection_fraction = " << ((double)num_detection_events / (double)total_detectors)
           << "\n";
    output << "\n";
    output << "                            setup_seconds = " << (config_microseconds / 1000000) << "\n";
    output << "                         decoding_seconds = " << (decoding_microseconds / 1000000) << "\n";
    output << "           decoding_microseconds_per_shot = " << (decoding_microseconds / num_shots) << "\n";
    output << "decoding_microseconds_per_detection_event = " << (decoding_microseconds / num_detection_events) << "\n";
    fprintf(stats_out, "%s", output.str().c_str());
    if (stats_out != stdout) {
        fclose(stats_out);
    }
    if (shots_in != stdin) {
        fclose(shots_in);
    }
    if (obs_in != nullptr) {
        fclose(obs_in);
    }

    return EXIT_SUCCESS;
}
