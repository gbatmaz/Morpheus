/**
 * SPDX-FileCopyrightText: Copyright (c) 2021-2022, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#pragma once

#include "morpheus/objects/data_table.hpp"  // for IDataTable
#include "morpheus/objects/table_info.hpp"

#include <cudf/types.hpp>      // for size_type
#include <pybind11/pytypes.h>  // for object

namespace morpheus {
/****** Component public implementations *******************/
/****** PyDataTable****************************************/

/**
 * @addtogroup objects
 * @{
 * @file
 */

/**
 * TODO(Documentation)
 */
struct PyDataTable : public IDataTable
{
    /**
     * @brief Construct a new Py Data Table object
     *
     * @param py_table
     */
    PyDataTable(pybind11::object &&py_table);
    ~PyDataTable();

    /**
     * @brief cuDF table rows count
     *
     * @return cudf::size_type
     */
    cudf::size_type count() const override;

    /**
     * Get cuDF table info
     *
     * @return TableInfo
     */
    TableInfo get_info() const override;

    /**
     * Get data table as python object
     *
     * @return pybind11::object
     */
    const pybind11::object &get_py_object() const override;

  private:
    pybind11::object m_py_table;
};
/** @} */  // end of group
}  // namespace morpheus
