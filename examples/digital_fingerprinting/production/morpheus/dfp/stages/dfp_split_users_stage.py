# Copyright (c) 2022, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import typing

import numpy as np
import srf
from srf.core import operators as ops

import cudf

from morpheus.config import Config
from morpheus.pipeline.single_port_stage import SinglePortStage
from morpheus.pipeline.stream_pair import StreamPair

from ..messages.multi_dfp_message import DFPMessageMeta
from ..utils.logging_timer import log_time

logger = logging.getLogger("morpheus.{}".format(__name__))


class DFPSplitUsersStage(SinglePortStage):

    def __init__(self,
                 c: Config,
                 include_generic: bool,
                 include_individual: bool,
                 skip_users: typing.List[str] = None,
                 only_users: typing.List[str] = None):
        super().__init__(c)

        self._include_generic = include_generic
        self._include_individual = include_individual
        self._skip_users = skip_users if skip_users is not None else []
        self._only_users = only_users if only_users is not None else []

        # Map of user ids to total number of messages. Keeps indexes monotonic and increasing per user
        self._user_index_map: typing.Dict[str, int] = {}

    @property
    def name(self) -> str:
        return "dfp-split-users"

    def supports_cpp_node(self):
        return False

    def accepted_types(self) -> typing.Tuple:
        return (cudf.DataFrame, )

    def extract_users(self, message: cudf.DataFrame):
        if (message is None):
            return []

        with log_time(logger.debug) as log_info:

            if (isinstance(message, cudf.DataFrame)):
                # Convert to pandas because cudf is slow at this
                message = message.to_pandas()

            split_dataframes: typing.Dict[str, cudf.DataFrame] = {}

            # If we are skipping users, do that here
            if (len(self._skip_users) > 0):
                message = message[~message[self._config.ae.userid_column_name].isin(self._skip_users)]

            if (len(self._only_users) > 0):
                message = message[message[self._config.ae.userid_column_name].isin(self._only_users)]

            # Split up the dataframes
            if (self._include_generic):
                split_dataframes[self._config.ae.fallback_username] = message

            if (self._include_individual):

                split_dataframes.update(
                    {username: user_df
                     for username, user_df in message.groupby("username", sort=False)})

            output_messages: typing.List[DFPMessageMeta] = []

            for user_id in sorted(split_dataframes.keys()):

                if (user_id in self._skip_users):
                    continue

                user_df = split_dataframes[user_id]

                current_user_count = self._user_index_map.get(user_id, 0)

                # Reset the index so that users see monotonically increasing indexes
                user_df.index = range(current_user_count, current_user_count + len(user_df))
                self._user_index_map[user_id] = current_user_count + len(user_df)

                output_messages.append(DFPMessageMeta(df=user_df, user_id=user_id))

                # logger.debug("Emitting dataframe for user '%s'. Start: %s, End: %s, Count: %s",
                #              user,
                #              df_user[self._config.ae.timestamp_column_name].min(),
                #              df_user[self._config.ae.timestamp_column_name].max(),
                #              df_user[self._config.ae.timestamp_column_name].count())

            rows_per_user = [len(x.df) for x in output_messages]

            if (len(output_messages) > 0):
                log_info.set_log(
                    ("Batch split users complete. Input: %s rows from %s to %s. "
                     "Output: %s users, rows/user min: %s, max: %s, avg: %.2f. Duration: {duration:.2f} ms"),
                    len(message),
                    message[self._config.ae.timestamp_column_name].min(),
                    message[self._config.ae.timestamp_column_name].max(),
                    len(rows_per_user),
                    np.min(rows_per_user),
                    np.max(rows_per_user),
                    np.mean(rows_per_user),
                )

            return output_messages

    def _build_single(self, builder: srf.Builder, input_stream: StreamPair) -> StreamPair:

        def node_fn(obs: srf.Observable, sub: srf.Subscriber):
            obs.pipe(ops.map(self.extract_users), ops.flatten()).subscribe(sub)

        stream = builder.make_node_full(self.unique_name, node_fn)
        builder.make_edge(input_stream[0], stream)

        return stream, DFPMessageMeta
