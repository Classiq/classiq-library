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

#include "chromobius/commands/main_all.test.h"
#include "chromobius/test_util.test.h"

using namespace chromobius;

TEST(main_predict, basic) {
    RaiiTempNamedFile dem;
    FILE *f = fopen(dem.path.c_str(), "w");
    fprintf(f, "%s", R"DEM(
        error(0.1) D0 L0
        error(0.1) D0 D1 L1
        error(0.1) D1 L2
        detector(0, 0, 0, 0) D0
        detector(0, 0, 0, 1) D1
    )DEM");
    fclose(f);
    auto stdout_content = result_of_running_main(
        {"predict", "--dem", dem.path, "--in_format", "dets", "--out_format", "dets"},
        R"stdin(shot
shot D0
shot D1
shot D0 D1)stdin");
    ASSERT_EQ(stdout_content, R"stdout(shot
shot L0
shot L2
shot L1
)stdout");
}
