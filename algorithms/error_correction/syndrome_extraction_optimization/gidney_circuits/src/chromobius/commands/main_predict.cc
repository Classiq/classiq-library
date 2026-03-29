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

#include "chromobius/commands/main_predict.h"

#include "chromobius/decode/decoder.h"
#include "stim.h"

using namespace chromobius;

int chromobius::main_predict(int argc, const char **argv) {
    stim::check_for_unknown_arguments(
        {
            "--in",
            "--in_format",
            "--in_includes_appended_observables",
            "--out",
            "--out_format",
            "--dem",
        },
        {},
        "predict",
        argc,
        argv);

    FILE *shots_in = stim::find_open_file_argument("--in", stdin, "rb", argc, argv);
    FILE *predictions_out = stim::find_open_file_argument("--out", stdout, "wb", argc, argv);
    FILE *dem_file = stim::find_open_file_argument("--dem", nullptr, "rb", argc, argv);
    stim::FileFormatData shots_in_format =
        stim::find_enum_argument("--in_format", "b8", stim::format_name_to_enum_map(), argc, argv);
    stim::FileFormatData predictions_out_format =
        stim::find_enum_argument("--out_format", "01", stim::format_name_to_enum_map(), argc, argv);
    bool append_obs = stim::find_bool_argument("--in_includes_appended_observables", argc, argv);

    stim::DetectorErrorModel dem = stim::DetectorErrorModel::from_file(dem_file);
    fclose(dem_file);
    auto decoder = Decoder::from_dem(dem, DecoderConfigOptions{});

    size_t num_dets = dem.count_detectors();
    size_t num_obs = dem.count_observables();
    auto reader = stim::MeasureRecordReader<stim::MAX_BITWORD_WIDTH>::make(
        shots_in, shots_in_format.id, 0, dem.count_detectors(), append_obs * num_obs);
    auto writer = stim::MeasureRecordWriter::make(predictions_out, predictions_out_format.id);
    writer->begin_result_type('L');

    stim::simd_bits<stim::MAX_BITWORD_WIDTH> buf_dets(reader->bits_per_record());
    while (reader->start_and_read_entire_record(buf_dets)) {
        if (append_obs) {
            for (size_t k = 0; k < num_obs; k++) {
                buf_dets[num_dets + k] = 0;
            }
        }
        auto prediction =
            decoder.decode_detection_events({buf_dets.u8, buf_dets.u8 + buf_dets.num_u8_padded()});
        for (size_t k = 0; k < num_obs; k++) {
            writer->write_bit((prediction >> k) & 1);
        }
        writer->write_end();
        buf_dets.clear();
    }

    if (predictions_out != stdout) {
        fclose(predictions_out);
    }
    if (shots_in != stdin) {
        fclose(shots_in);
    }

    return EXIT_SUCCESS;
}
