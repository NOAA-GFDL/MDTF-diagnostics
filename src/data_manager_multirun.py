"""
Base classes implementing logic for querying, fetching and preprocessing
model data requested by the PODs for multirun mode
(i.e., a single POD is associated with multiple data sources)
"""
import os
import abc
import collections
import dataclasses as dc
import glob
import signal
import textwrap
import typing
from abc import ABC

from src import util, core, diagnostic, xr_parser, preprocessor, data_manager
import pandas as pd
import intake_esm

import logging

_log = logging.getLogger(__name__)


class MultirunDataSourceBase(data_manager.DataSourceBase, core.MDTFObjectBase, util.CaseLoggerMixin,
                             data_manager.AbstractDataSource, metaclass=util.MDTFABCMeta):
    """Base class for handling multirun data needs. Executes query for
    requested model data against the remote data sources, fetches the required
    data locally, preprocesses it, and performs cleanup/formatting of the POD's
    output.
    """

    def __init__(self, case_dict, parent):
        super().__init__(case_dict)
        pass


class MultirunDataframeQueryDataSourceBase(MultirunDataSourceBase, data_manager.DataframeQueryDataSourceBase,
                                           metaclass=util.MDTFABCMeta):
    """DataSource which queries a data catalog made available as a pandas
    DataFrame, and includes logic for selecting experiment based on column values.
    """

    def __init__(self, case_dict, parent):
        super(data_manager.DataframeQueryDataSourceBase, self).__init__(case_dict, parent)
        pass
