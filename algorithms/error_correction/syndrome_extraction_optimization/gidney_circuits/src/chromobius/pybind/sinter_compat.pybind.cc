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

#include "chromobius.h"
#include "chromobius/pybind/sinter_compat.pybind.h"

#include <pybind11/iostream.h>
#include <pybind11/numpy.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>

#include "stim.h"

struct ChromobiusSinterCompiledDecoder {
    chromobius::Decoder decoder;
    uint64_t num_detectors;
    uint64_t num_detector_bytes;
    uint64_t num_observable_bytes;
    std::vector<chromobius::obsmask_int> result_buffer;

    pybind11::array_t<uint8_t> decode_shots_bit_packed(
        const pybind11::array_t<uint8_t> &bit_packed_detection_event_data) {
        assert(bit_packed_detection_event_data.ndim() == 2);
        assert(bit_packed_detection_event_data.strides(1) == 1);
        assert(bit_packed_detection_event_data.shape(1) == num_detector_bytes);
        size_t stride = bit_packed_detection_event_data.strides(0);
        size_t num_shots = bit_packed_detection_event_data.shape(0);

        // Predict each shot.
        result_buffer.clear();
        for (size_t shot = 0; shot < num_shots; shot++) {
            const uint8_t *data = bit_packed_detection_event_data.data() + stride * shot;

            // Predict.
            chromobius::obsmask_int prediction =
                decoder.decode_detection_events({data, data + num_detector_bytes});
            result_buffer.push_back(prediction);
        }

        // Write predictions into output numpy array.
        uint8_t *buffer = new uint8_t[num_observable_bytes * num_shots];
        size_t offset = 0;
        for (chromobius::obsmask_int obs : result_buffer) {
            for (size_t k = 0; k < num_observable_bytes; k++) {
                buffer[offset++] = obs & 255;
                obs >>= 8;
            }
        }
        pybind11::capsule free_when_done(buffer, [](void *f) {
            delete[] reinterpret_cast<uint8_t *>(f);
        });
        return pybind11::array_t<uint8_t>(
            {(pybind11::ssize_t)num_shots, (pybind11::ssize_t)num_observable_bytes},
            {(pybind11::ssize_t)num_observable_bytes, (pybind11::ssize_t)1},
            buffer,
            free_when_done);
    }
};

enum SubDecoder : uint8_t {
    SUB_DECODER_PYMATCHING = 0,
};

struct ChromobiusSinterDecoder {
    SubDecoder sub_decoder;
    ChromobiusSinterDecoder(SubDecoder sub_decoder) : sub_decoder(sub_decoder) {
    }

    bool operator==(const ChromobiusSinterDecoder &other) const {
        return true;
    }
    bool operator!=(const ChromobiusSinterDecoder &other) const {
        return !(*this == other);
    }

    chromobius::DecoderConfigOptions get_options() const {
        chromobius::DecoderConfigOptions options;
        return options;
    }

    void decode_via_files(
        uint64_t num_shots,
        uint64_t num_dets,
        uint64_t num_obs,
        const pybind11::object &dem_path,
        const pybind11::object &dets_b8_in_path,
        const pybind11::object &obs_predictions_b8_out_path,
        const pybind11::object &tmp_dir) {
        auto dem_path_str = pybind11::cast<std::string>(pybind11::str(dem_path));
        auto dets_b8_in_path_str = pybind11::cast<std::string>(pybind11::str(dets_b8_in_path));
        auto obs_predictions_b8_out_path_str = pybind11::cast<std::string>(pybind11::str(obs_predictions_b8_out_path));

        FILE *f_dem = fopen(dem_path_str.c_str(), "r");
        stim::DetectorErrorModel dem = stim::DetectorErrorModel::from_file(f_dem);
        fclose(f_dem);

        stim::RaiiFile dets_in(dets_b8_in_path_str.c_str(), "rb");
        stim::RaiiFile obs_out(obs_predictions_b8_out_path_str.c_str(), "wb");

        auto reader =
            stim::MeasureRecordReader<stim::MAX_BITWORD_WIDTH>::make(dets_in.f, stim::SampleFormat::SAMPLE_FORMAT_B8, 0, num_dets, 0);
        auto writer = stim::MeasureRecordWriter::make(obs_out.f, stim::SampleFormat::SAMPLE_FORMAT_B8);

        auto decoder = chromobius::Decoder::from_dem(dem, get_options());

        stim::SparseShot sparse_shot;
        stim::simd_bits<stim::MAX_BITWORD_WIDTH> dets(num_dets);
        for (size_t shot = 0; shot < num_shots; shot++) {
            reader->start_and_read_entire_record(dets);
            auto result = decoder.decode_detection_events({dets.u8, dets.u8 + dets.num_u8_padded()});
            writer->begin_result_type('L');
            for (size_t k = 0; k < num_obs; k++) {
                writer->write_bit((result >> k) & 1);
            }
            writer->write_end();
        }
    }

    ChromobiusSinterCompiledDecoder compile_decoder_for_dem(const pybind11::object &dem) {
        auto dem_str = pybind11::cast<std::string>(pybind11::str(dem));
        stim::DetectorErrorModel converted_dem = stim::DetectorErrorModel(dem_str.c_str());
        auto decoder = chromobius::Decoder::from_dem(converted_dem, get_options());
        auto num_dets = converted_dem.count_detectors();
        return ChromobiusSinterCompiledDecoder{
            .decoder = std::move(decoder),
            .num_detectors = num_dets,
            .num_detector_bytes = (num_dets + 7) / 8,
            .num_observable_bytes = (converted_dem.count_observables() + 7) / 8,
            .result_buffer = {},
        };
    }
};

void chromobius::pybind_sinter_compat(pybind11::module &m) {
    auto sinter_decoder = pybind11::class_<ChromobiusSinterDecoder>(
        m,
        "_ChromobiusSinterDecoder",
        stim::clean_doc_string(R"DOC(
            An object that implements the sinter.Decoder API.
        )DOC")
            .data());

    auto sinter_compiled_decoder = pybind11::class_<ChromobiusSinterCompiledDecoder>(
        m,
        "_ChromobiusSinterCompiledDecoder",
        stim::clean_doc_string(R"DOC(
            An object that implements the sinter.CompiledDecoder API.
        )DOC")
            .data());

    sinter_decoder.def(pybind11::pickle(
        [](const ChromobiusSinterDecoder &self) -> pybind11::object {
            return pybind11::cast((uint8_t)self.sub_decoder);
        },
        [](const pybind11::object &obj) -> ChromobiusSinterDecoder {
            return ChromobiusSinterDecoder((SubDecoder)pybind11::cast<uint8_t>(obj));
        }));
    sinter_decoder.def(pybind11::self == pybind11::self);
    sinter_decoder.def(pybind11::self != pybind11::self);

    sinter_decoder.def(
        pybind11::init([](uint8_t sub_decoder) -> ChromobiusSinterDecoder {
            return ChromobiusSinterDecoder((SubDecoder)sub_decoder);
        }),
        stim::clean_doc_string(R"DOC(
            Creates a chromobius.ChromobiusSinterDecoder.
        )DOC")
            .data());

    sinter_decoder.def(
        "decode_via_files",
        &ChromobiusSinterDecoder::decode_via_files,
        pybind11::kw_only(),
        pybind11::arg("num_shots"),
        pybind11::arg("num_dets"),
        pybind11::arg("num_obs"),
        pybind11::arg("dem_path"),
        pybind11::arg("dets_b8_in_path"),
        pybind11::arg("obs_predictions_b8_out_path"),
        pybind11::arg("tmp_dir"),
        stim::clean_doc_string(R"DOC(
            Decodes data on disk, to disk.
        )DOC")
            .data());

    sinter_decoder.def(
        "compile_decoder_for_dem",
        &ChromobiusSinterDecoder::compile_decoder_for_dem,
        pybind11::kw_only(),
        pybind11::arg("dem"),
        stim::clean_doc_string(R"DOC(
            Creates a chromobius decoder preconfigured for the given detector error model.
        )DOC")
            .data());

    sinter_compiled_decoder.def(
        "decode_shots_bit_packed",
        &ChromobiusSinterCompiledDecoder::decode_shots_bit_packed,
        pybind11::kw_only(),
        pybind11::arg("bit_packed_detection_event_data"),
        stim::clean_doc_string(R"DOC(
            Predicts observable flips from the given detection events.
        )DOC")
            .data());

    m.def(
        "sinter_decoders",
        []() -> pybind11::object {
            auto result = pybind11::dict();
            result["chromobius"] = ChromobiusSinterDecoder(SubDecoder::SUB_DECODER_PYMATCHING);
            return result;
        },
        stim::clean_doc_string(R"DOC(
            @signature def sinter_decoders() -> dict[str, sinter.Decoder]:
            A dictionary describing chromobius to sinter.

            Giving the result of this function to the `custom_decoders` argument of
            `sinter.collect` will tell sinter about the decoder 'chromobius'. On the
            command line, the equivalent argument is
            `--custom_decoders 'chromobius:sinter_decoders'`.

            Returns:
                The dict `{'chromobius': <an object compatible with sinter.Decoder>}`.
        )DOC")
            .data());
}
