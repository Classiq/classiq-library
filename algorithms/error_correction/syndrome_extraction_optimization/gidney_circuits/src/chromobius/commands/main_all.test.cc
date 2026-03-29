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

#include "chromobius/commands/main_all.test.h"

#include "gtest/gtest.h"

#include "chromobius/test_util.test.h"

using namespace chromobius;

std::string chromobius::result_of_running_main(const std::vector<std::string> args, const std::string &input) {
    std::vector<const char *> argv;
    argv.push_back("TEST_PROCESS");
    for (const auto &a : args) {
        argv.push_back(a.c_str());
    }
    RaiiTempNamedFile inp;
    RaiiTempNamedFile out;
    argv.push_back("--in");
    argv.push_back(inp.path.c_str());
    argv.push_back("--out");
    argv.push_back(out.path.c_str());
    FILE *f = fopen(inp.path.c_str(), "w");
    if (f == nullptr || fwrite(input.data(), 1, input.size(), f) != input.size()) {
        throw std::invalid_argument("Failed to write input.");
    }
    fclose(f);
    if (chromobius::main((int)argv.size(), argv.data()) != EXIT_SUCCESS) {
        throw std::invalid_argument("Returned not EXIT_SUCCESS");
    }
    f = fopen(out.path.c_str(), "rb");
    if (f == nullptr) {
        throw std::invalid_argument("Failed to read output.");
    }
    std::string s;
    while (true) {
        int i = getc(f);
        if (i == EOF) {
            break;
        }
        s.push_back((char)i);
    }
    return s;
}

TEST(main_all, unknown_command) {
    ASSERT_THROW({ result_of_running_main({"UNKNOWN_COMMAND"}, ""); }, std::invalid_argument);
}
