/**
 * SPDX-FileCopyrightText: Copyright (c) 2022, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "pass_thru.hpp"

#include <pybind11/pybind11.h>
#include <pysrf/utils.hpp>  // for pysrf::import

#include <exception>

namespace morpheus_example {

PassThruStage::PassThruStage() : PythonNode(base_t::op_factory_from_sub_fn(build_operator())) {}

PassThruStage::subscribe_fn_t PassThruStage::build_operator()
{
    return [this](rxcpp::observable<sink_type_t> input, rxcpp::subscriber<source_type_t> output) {
        return input.subscribe(
            rxcpp::make_observer<sink_type_t>([this, &output](sink_type_t x) { output.on_next(std::move(x)); },
                                              [&](std::exception_ptr error_ptr) { output.on_error(error_ptr); },
                                              [&]() { output.on_completed(); }));
    };
}

std::shared_ptr<srf::segment::Object<PassThruStage>> PassThruStageInterfaceProxy::init(srf::segment::Builder& builder,
                                                                                       const std::string& name)
{
    return builder.construct_object<PassThruStage>(name);
}

namespace py = pybind11;

// Define the pybind11 module m.
PYBIND11_MODULE(morpheus_example, m)
{
    srf::pysrf::import(m, "morpheus._lib.messages");

    py::class_<srf::segment::Object<PassThruStage>,
               srf::segment::ObjectProperties,
               std::shared_ptr<srf::segment::Object<PassThruStage>>>(m, "PassThruStage", py::multiple_inheritance())
        .def(py::init<>(&PassThruStageInterfaceProxy::init), py::arg("builder"), py::arg("name"));
}

}  // namespace morpheus_example
