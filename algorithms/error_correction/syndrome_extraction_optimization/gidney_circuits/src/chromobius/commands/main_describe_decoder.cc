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

#include "chromobius/commands/main_describe_decoder.h"

#include "chromobius/decode/decoder.h"
#include "stim.h"

using namespace chromobius;

int chromobius::main_describe_decoder(int argc, const char **argv) {
    stim::check_for_unknown_arguments(
        {
            "--in",
            "--out",
            "--circuit",
        },
        {},
        "describe_decoder",
        argc,
        argv);

    auto out_file = stim::find_output_stream_argument("--out", true, argc, argv);
    auto &out = out_file.stream();

    stim::DetectorErrorModel dem;

    if (stim::find_argument("--circuit", argc, argv) != nullptr) {
        FILE *circuit_in = stim::find_open_file_argument("--circuit", nullptr, "rb", argc, argv);
        auto circuit = stim::Circuit::from_file(circuit_in);
        fclose(circuit_in);
        dem = stim::ErrorAnalyzer::circuit_to_detector_error_model(circuit, false, true, false, true, false, false);
    } else {
        FILE *dem_in = stim::find_open_file_argument("--in", stdin, "rb", argc, argv);
        dem = stim::DetectorErrorModel::from_file(dem_in);
        fclose(dem_in);
    }

    auto decoder = Decoder::from_dem(dem, DecoderConfigOptions{.include_coords_in_mobius_dem=true});
    out << decoder;
    out << "\n";
    return EXIT_SUCCESS;
}
