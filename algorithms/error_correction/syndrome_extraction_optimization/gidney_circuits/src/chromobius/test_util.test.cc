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

#include "chromobius/test_util.test.h"

#include "gtest/gtest.h"

using namespace chromobius;

FILE *chromobius::open_test_data_file(const char *name) {
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

static void init_path(RaiiTempNamedFile &self) {
    char tmp_stdin_filename[] = "/tmp/stim_test_named_file_XXXXXX";
    self.descriptor = mkstemp(tmp_stdin_filename);
    if (self.descriptor == -1) {
        throw std::runtime_error("Failed to create temporary file.");
    }
    self.path = std::string(tmp_stdin_filename);
}

RaiiTempNamedFile::RaiiTempNamedFile() {
    init_path(*this);
}

RaiiTempNamedFile::RaiiTempNamedFile(const std::string &contents) {
    init_path(*this);
    write_contents(contents);
}

RaiiTempNamedFile::~RaiiTempNamedFile() {
    if (!path.empty()) {
        remove(path.data());
        path = "";
    }
}

std::string RaiiTempNamedFile::read_contents() {
    FILE *f = fopen(path.c_str(), "rb");
    if (f == nullptr) {
        throw std::runtime_error("Failed to open temp named file " + path);
    }
    std::string result;
    while (true) {
        int c = getc(f);
        if (c == EOF) {
            break;
        }
        result.push_back(c);
    }
    fclose(f);
    return result;
}

void RaiiTempNamedFile::write_contents(const std::string &contents) {
    FILE *f = fopen(path.c_str(), "wb");
    if (f == nullptr) {
        throw std::runtime_error("Failed to open temp named file " + path);
    }
    for (char c : contents) {
        putc(c, f);
    }
    fclose(f);
}
