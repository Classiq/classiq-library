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

#include "chromobius/decode/decoder.h"
#include "chromobius/pybind/sinter_compat.pybind.h"

#include <pybind11/iostream.h>
#include <pybind11/numpy.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>

#include "stim.h"

struct CompiledDecoder {
    chromobius::Decoder decoder;
    uint64_t num_detectors;
    uint64_t num_detector_bytes;
    uint64_t num_observable_bytes;
    std::vector<chromobius::obsmask_int> result_buffer;

    static CompiledDecoder from_dem(const pybind11::object &dem) {
        auto type_name = pybind11::str(dem.get_type());
        if (!type_name.contains("stim.") || !type_name.contains(".DetectorErrorModel")) {
            throw std::invalid_argument("dem must be a stim.DetectorErrorModel.");
        }
        auto dem_str = pybind11::cast<std::string>(pybind11::str(dem));
        stim::DetectorErrorModel converted_dem = stim::DetectorErrorModel(dem_str.c_str());
        auto decoder = chromobius::Decoder::from_dem(converted_dem, chromobius::DecoderConfigOptions{});
        auto num_dets = converted_dem.count_detectors();
        return CompiledDecoder{
            .decoder = std::move(decoder),
            .num_detectors = num_dets,
            .num_detector_bytes = (num_dets + 7) / 8,
            .num_observable_bytes = (converted_dem.count_observables() + 7) / 8,
            .result_buffer = {},
        };
    }

    pybind11::object predict_obs_flips_from_dets_bit_packed(const pybind11::object &dets_obj) {
        if (!pybind11::isinstance<pybind11::array_t<uint8_t>>(dets_obj)) {
            throw std::invalid_argument("Expected bit packed detection event data, but dets.dtype wasn't np.uint8.");
        }

        const pybind11::array_t<uint8_t> &dets = pybind11::cast<pybind11::array_t<uint8_t>>(dets_obj);
        size_t num_shots;
        size_t shot_stride;
        size_t det_shape;
        if (dets.ndim() == 2) {
            num_shots = dets.shape(0);
            shot_stride = dets.strides(0);
            det_shape = dets.shape(1);
            if (dets.strides(1) != 1) {
                std::stringstream ss;
                ss << "Bit packed shot data must be contiguous in memory, but dets.stride[1] wasn't equal to 1.\n";
                ss << "It was " << dets.strides(1) << ".";
                throw std::invalid_argument(ss.str());
            }
        } else if (dets.ndim() == 1) {
            num_shots = 1;
            shot_stride = 0;
            det_shape = dets.shape(0);
        } else {
            throw std::invalid_argument("dets.shape not in [1, 2]");
        }

        if (det_shape != num_detector_bytes) {
            std::stringstream ss;
            ss << "Expected dets.shape[1]=" << dets.shape(1);
            ss << " == num_detector_bytes=" << num_detector_bytes;
            ss << " because dets.shape == 2 and dets.dtype==np.uint8 indicating bit packed shots.";
            throw std::invalid_argument(ss.str());
        }

        result_buffer.clear();
        for (size_t shot = 0; shot < num_shots; shot++) {
            const uint8_t *data = dets.data() + shot_stride * shot;
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
        if (dets.ndim() == 2) {
            return pybind11::array_t<uint8_t>(
                {(pybind11::ssize_t)num_shots, (pybind11::ssize_t)num_observable_bytes},
                {(pybind11::ssize_t)num_observable_bytes, (pybind11::ssize_t)1},
                buffer,
                free_when_done);
        } else {
            return pybind11::array_t<uint8_t>(
                {(pybind11::ssize_t)num_observable_bytes},
                {(pybind11::ssize_t)1},
                buffer,
                free_when_done);
        }
    }
};

PYBIND11_MODULE(chromobius, m) {
    m.attr("__version__") = "0.0.dev0";
    m.doc() = R"pbdoc(
        chromobius: A fast implementation of the mobius color code decoder.
    )pbdoc";

    chromobius::pybind_sinter_compat(m);

    auto compiled_decoder = pybind11::class_<CompiledDecoder>(
        m,
        "CompiledDecoder",
        stim::clean_doc_string(R"DOC(
            A chromobius decoder ready to predict observable flips from detection events.

            Example:
                >>> import stim
                >>> import chromobius

                >>> dem = stim.Circuit('''
                ...     X_ERROR(0.1) 0 1 2 3 4 5 6 7
                ...     MPP Z0*Z1*Z2 Z1*Z2*Z3 Z2*Z3*Z4 Z3*Z4*Z5
                ...     DETECTOR(0, 0, 0, 1) rec[-4]
                ...     DETECTOR(1, 0, 0, 2) rec[-3]
                ...     DETECTOR(2, 0, 0, 0) rec[-2]
                ...     DETECTOR(3, 0, 0, 1) rec[-1]
                ...     M 0
                ...     OBSERVABLE_INCLUDE(0) rec[-1]
                ... ''').detector_error_model()

                >>> decoder = chromobius.CompiledDecoder.from_dem(dem)
        )DOC")
            .data());

    compiled_decoder.def(
        "predict_obs_flips_from_dets_bit_packed",
        &CompiledDecoder::predict_obs_flips_from_dets_bit_packed,
        pybind11::arg("dets"),
        stim::clean_doc_string(R"DOC(
            @signature def predict_obs_flips_from_dets_bit_packed(dets: np.ndarray) -> np.ndarray:
            Predicts observable flips from detection events.

            Args:
                dets: A bit packed numpy array of detection event data. The array can either
                    be 1-dimensional (a single shot to decode) or 2-dimensional (multiple
                    shots to decode, with the first axis being the shot axis and the second
                    axis being the detection event byte axis).

                    The array's dtype must be np.uint8. If you have an array of dtype
                    np.bool_, you have data that's not bit packed. You can pack it by
                    using `np.packbits(array, bitorder='little')`. But ideally you
                    should attempt to never have unpacked data in the first place,
                    since it's 8x larger which can be a large performance loss. For
                    example, stim's sampler methods all have a `bit_packed=True` argument
                    that cause them to return bit packed data.

            Returns:
                A bit packed numpy array of observable flip data. The array will have
                the same number of dimensions as the dets argument.

                If dets is a 1D array, then the result has:
                    shape = (math.ceil(num_obs / 8),)
                    dtype = np.uint8
                If dets is a 2D array, then the result has:
                    shape = (dets.shape[0], math.ceil(num_obs / 8),)
                    dtype = np.uint8

                To determine if the observable with index k was flipped in shot s, compute:
                    `bool((result[s, k // 8] >> (k % 8)) & 1)`

            Example:
                >>> import stim
                >>> import chromobius
                >>> import numpy as np

                >>> repetition_color_code = stim.Circuit('''
                ...     # Apply noise.
                ...     X_ERROR(0.1) 0 1 2 3 4 5 6 7
                ...     # Measure three-body stabilizers to catch errors.
                ...     MPP Z0*Z1*Z2 Z1*Z2*Z3 Z2*Z3*Z4 Z3*Z4*Z5 Z4*Z5*Z6 Z5*Z6*Z7
                ...
                ...     # Annotate detectors, with a coloring in the 4th coordinate.
                ...     DETECTOR(0, 0, 0, 2) rec[-6]
                ...     DETECTOR(1, 0, 0, 0) rec[-5]
                ...     DETECTOR(2, 0, 0, 1) rec[-4]
                ...     DETECTOR(3, 0, 0, 2) rec[-3]
                ...     DETECTOR(4, 0, 0, 0) rec[-2]
                ...     DETECTOR(5, 0, 0, 1) rec[-1]
                ...
                ...     # Check on the message.
                ...     M 0
                ...     OBSERVABLE_INCLUDE(0) rec[-1]
                ... ''')

                >>> # Sample the circuit.
                >>> shots = 4096
                >>> sampler = repetition_color_code.compile_detector_sampler()
                >>> dets, actual_obs_flips = sampler.sample(
                ...     shots=shots,
                ...     separate_observables=True,
                ...     bit_packed=True,
                ... )

                >>> # Decode with Chromobius.
                >>> dem = repetition_color_code.detector_error_model()
                >>> decoder = chromobius.compile_decoder_for_dem(dem)
                >>> predicted_flips = decoder.predict_obs_flips_from_dets_bit_packed(dets)

                >>> # Count mistakes.
                >>> differences = np.any(predicted_flips != actual_obs_flips, axis=1)
                >>> mistakes = np.count_nonzero(differences)
                >>> assert mistakes < shots / 5
        )DOC")
            .data());

    m.def(
        "compile_decoder_for_dem",
        &CompiledDecoder::from_dem,
        pybind11::arg("dem"),
        stim::clean_doc_string(R"DOC(
            @signature def compile_decoder_for_dem(dem: stim.DetectorErrorModel) -> chromobius.CompiledDecoder:
            Compiles a decoder for a stim detector error model.

            Args:
                dem: A stim detector error model. The detector error model must satisfy:
                    1. Basis+Color annotations. Every detector that appears in an error
                        must specify coordinate data including a fourth coordinate. The 4th
                        coordinate indicates the basis and color of the detector with the
                        convention:
                            0 = Red X
                            1 = Green X
                            2 = Blue X
                            3 = Red Z
                            4 = Green Z
                            5 = Blue Z
                    2. Rainbow triplets. Bulk errors with three symptoms in one basis should
                        have one symptom of each color. Errors with three symptoms that
                        repeat a color will cause an exception unless they can be decomposed
                        into other basic errors.
                    3. Movable excitations. It needs to be possible to combine bulk errors
                        to form simpler errors with one or two symptoms that can be used to
                        move or destroy excitations. If bulk errors don't have this
                        property, decoding will fail when attempting to lift a solution
                        from the matcher requires dragging an excitation along a path but
                        there's no way to move the excitation along that path.
                    4. Matchable-avoids-color. In parts of the dem that correspond to a
                        matchable code, at least one of the colors must be avoided.
                        Otherwise the matcher may be given a problem that can be solved
                        locally, but when lifting it needs to be solved non-locally.

            Returns:
                A decoder object that can be used to predict observable flips from
                detection event samples.

            Example:
                >>> import stim
                >>> import chromobius

                >>> dem = stim.Circuit('''
                ...     X_ERROR(0.1) 0 1 2 3 4 5 6 7
                ...     MPP Z0*Z1*Z2 Z1*Z2*Z3 Z2*Z3*Z4 Z3*Z4*Z5
                ...     DETECTOR(0, 0, 0, 1) rec[-4]
                ...     DETECTOR(1, 0, 0, 2) rec[-3]
                ...     DETECTOR(2, 0, 0, 0) rec[-2]
                ...     DETECTOR(3, 0, 0, 1) rec[-1]
                ...     M 0
                ...     OBSERVABLE_INCLUDE(0) rec[-1]
                ... ''').detector_error_model()

                >>> decoder = chromobius.compile_decoder_for_dem(dem)
        )DOC")
            .data());

    compiled_decoder.def_static(
        "from_dem",
        &CompiledDecoder::from_dem,
        pybind11::arg("dem"),
        stim::clean_doc_string(R"DOC(
            @signature def from_dem(dem: stim.DetectorErrorModel) -> chromobius.CompiledDecoder:
            Compiles a decoder for a stim detector error model.

            Args:
                dem: A stim detector error model. The detector error model must satisfy:
                    1. Basis+Color annotations. Every detector that appears in an error
                        must specify coordinate data including a fourth coordinate. The 4th
                        coordinate indicates the basis and color of the detector with the
                        convention:
                            0 = Red X
                            1 = Green X
                            2 = Blue X
                            3 = Red Z
                            4 = Green Z
                            5 = Blue Z
                    2. Rainbow triplets. Bulk errors with three symptoms in one basis should
                        have one symptom of each color. Errors with three symptoms that
                        repeat a color will cause an exception unless they can be decomposed
                        into other basic errors.
                    3. Movable excitations. It needs to be possible to combine bulk errors
                        to form simpler errors with one or two symptoms that can be used to
                        move or destroy excitations. If bulk errors don't have this
                        property, decoding will fail when attempting to lift a solution
                        from the matcher requires dragging an excitation along a path but
                        there's no way to move the excitation along that path.
                    4. Matchable-avoids-color. In parts of the dem that correspond to a
                        matchable code, at least one of the colors must be avoided.
                        Otherwise the matcher may be given a problem that can be solved
                        locally, but when lifting it needs to be solved non-locally.

            Returns:
                A decoder object that can be used to predict observable flips from
                detection event samples.

            Example:
                >>> import stim
                >>> import chromobius

                >>> dem = stim.Circuit('''
                ...     X_ERROR(0.1) 0 1 2 3 4 5 6 7
                ...     MPP Z0*Z1*Z2 Z1*Z2*Z3 Z2*Z3*Z4 Z3*Z4*Z5
                ...     DETECTOR(0, 0, 0, 1) rec[-4]
                ...     DETECTOR(1, 0, 0, 2) rec[-3]
                ...     DETECTOR(2, 0, 0, 0) rec[-2]
                ...     DETECTOR(3, 0, 0, 1) rec[-1]
                ...     M 0
                ...     OBSERVABLE_INCLUDE(0) rec[-1]
                ... ''').detector_error_model()

                >>> decoder = chromobius.CompiledDecoder.from_dem(dem)
        )DOC")
            .data());
}
