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

#include "chromobius/commands/main_all.h"

#include "chromobius/commands/main_benchmark.h"
#include "chromobius/commands/main_describe_decoder.h"
#include "chromobius/commands/main_predict.h"
#include "stim.h"

using namespace chromobius;

int chromobius::main(int argc, const char **argv) {
    const char *command = "";
    if (argc >= 2) {
        command = argv[1];
    }
    const char *help = R"HELP(

Available chromobius commands:

    # Print usage information.
    chromobius help

    # Predict observable flips from detection event data.
    chromobius predict \
        [--dem FILEPATH] \                     # where to read detector error model from
        [--in] \                               # where to read detection event data (defaults to stdin)
        [--in_format 01|b8|...] \              # format of input detection event data
        [--in_includes_appended_observables] \ # if set, input data includes observables as extra detectors to ignore
        [--out FILEPATH] \                     # where to write predictions to (defaults to stdout)
        [--out_format 01|b8|...]               # format to use when writing predictions

    # Print accuracy and timing statistics collected while decoding.
    chromobius benchmark
        [--dem FILEPATH] \                     # where to read detector error model from
        [--in] \                               # where to read detection event data (defaults to stdin)
        [--in_format 01|b8|...] \              # format of input detection event data
        [--in_includes_appended_observables] \ # if set, observables are extra detectors in detection event data
        [--obs_in FILEPATH] \                  # if set, observables are read from a separate file
        [--obs_in_format 01|b8|...] \          # format of separate observable data
        [--out FILEPATH]                       # where to write results (defaults to stdout)

    # Describes the internal representations used to decode a given dem or circuit.
    chromobius describe_decoder \
        [--in] \           # where to read a detector error model from (defaults to stdin)
        [--circuit] \      # where to read a circuit from (overrides --in)
        [--out FILEPATH]   # where to write output (defaults to stdout)
)HELP";

    if (strcmp(command, "describe_decoder") == 0) {
        return main_describe_decoder(argc, argv);
    }
    if (strcmp(command, "predict") == 0) {
        return main_predict(argc, argv);
    }
    if (strcmp(command, "benchmark") == 0) {
        return main_benchmark(argc, argv);
    }
    if (strcmp(command, "help") == 0 || strcmp(command, "--help") == 0 || strcmp(command, "-help") == 0 ||
        strcmp(command, "-h") == 0) {
        std::cout << help;
        return EXIT_SUCCESS;
    }

    std::stringstream ss;
    if (command[0] == '\0') {
        ss << "Specify a chromobius command to run.\n";
    } else {
        ss << "Unrecognized chromobius command '" << command << "'.\n";
    }
    ss << help;
    throw std::invalid_argument(ss.str());
}
