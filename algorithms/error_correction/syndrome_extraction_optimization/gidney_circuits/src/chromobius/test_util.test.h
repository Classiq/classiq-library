/*
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef _CHROMOBIUS_TEST_UTIL_H
#define _CHROMOBIUS_TEST_UTIL_H

#include <cstdio>
#include <string>

namespace chromobius {

FILE *open_test_data_file(const char *name);

struct RaiiTempNamedFile {
    int descriptor;
    std::string path;
    RaiiTempNamedFile();
    ~RaiiTempNamedFile();
    RaiiTempNamedFile(const std::string &contents);
    std::string read_contents();
    void write_contents(const std::string &contents);
};

}  // namespace chromobius

#endif
