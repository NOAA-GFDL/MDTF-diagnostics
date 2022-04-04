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

from src import util, core, diagnostic, xr_parser, preprocessor, data_manager, data_model
import pandas as pd
import intake_esm

import logging

_log = logging.getLogger(__name__)


# METHOD RESOLUTION ORDER (MRO): What order will classes inherit in MultirunDataSourceBase
# (and other classes with multiple base classes)?
# Python3 uses C3 linearization algorithm (https://en.wikipedia.org/wiki/C3_linearization):
# L[C] = C + merge of linearization of parents of C and list of parents of C
# in the order they are inherited from left to right.
# super() returns proxy objects: objects with the ability to dispatch to methods of other objects via delegation.
# Technically, super is a class overriding the __getattribute__ method.
# Instances of super are proxy objects providing access to the methods in the MRO.
# General format is:
# super(cls, instance-or-subclass).method(*args, **kw)
# You can get the MRO of a class by running print(class.mro())
class MultirunDataSourceBase(data_manager.DataSourceBase, core.MDTFObjectBase, util.CaseLoggerMixin,
                             data_manager.AbstractDataSource, metaclass=util.MDTFABCMeta):
    """Base class for handling multirun data needs. Executes query for
    requested model data against the remote data sources, fetches the required
    data locally, preprocesses it, and performs cleanup/formatting of the POD's
    output.
    """

    def __init__(self, case_dict, parent):
        super(self).__init__(case_dict, parent)
        print("MultirunDataSourceBase")

# MRO: [<class '__main__.MultirunDataframeQueryDataSourceBase'>
# <class '__main__.MultirunDataSourceBase'>
# <class 'src.data_manager.DataframeQueryDataSourceBase'>
# <class 'src.data_manager.DataSourceBase'>
# <class 'src.core.MDTFObjectBase'>
# <class 'src.util.logs.CaseLoggerMixin'>
# <class 'src.util.logs._CaseAndPODHandlerMixin'>
# <class 'src.util.logs.MDTFObjectLoggerMixinBase'>
# <class 'src.data_manager.AbstractDataSource'>
# <class 'src.data_manager.AbstractQueryMixin'>
# <class 'src.data_manager.AbstractFetchMixin'>
# <class 'abc.ABC'>
# <class 'object'>]
class MultirunDataframeQueryDataSourceBase(MultirunDataSourceBase, data_manager.DataframeQueryDataSourceBase,
                                           metaclass=util.MDTFABCMeta):
    """DataSource which queries a data catalog made available as a pandas
    DataFrame, and includes logic for selecting experiment based on column values.
    """

    def __init__(self, case_dict, parent):
        # note that in python3, you do NOT need to include the enclosing class as the first argument to super()
        # e.g., super(MultirunDataframeQueryDataSourceBase,self)
        # here, the code calls the super class's init method, which is MultiRunDataSourceBase's init method
        super(self).__init__(case_dict, parent)
        print("MultirunDataframeQuerySourceBase")

# [<class '__main__.MultirunLocalFileDataSource'>,
# <class '__main__.MultirunDataframeQueryDataSourceBase'>,
# <class '__main__.MultirunDataSourceBase'>,
# <class 'src.data_manager.LocalFileDataSource'>...
# ]
class MultirunLocalFileDataSource(MultirunDataframeQueryDataSourceBase, data_manager.LocalFileDataSource):
    pass

class MultirunVarlist(diagnostic.Varlist, data_model.DMDataSet):
    pass

class MultirunDiagnostic(diagnostic.Varlist, diagnostic.diagnostic, core.MDTFObjectBase, util.PODLoggerMixin):
    # _id = util.MDTF_ID()           # fields inherited from core.MDTFObjectBase
    # name: str
    # _parent: object
    # log = util.MDTFObjectLogger
    # status: ObjectStatus
    # long_name: str = ""  # fields inherited from diagnostic.diagnostic
    # description: str = ""
    # convention: str = "CF"
    # realm: str = ""
    # driver: str = ""
    # program: str = ""
    # runtime_requirements: dict = dc.field(default_factory=dict)
    # pod_env_vars: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict)
    # log_file: io.IOBase = dc.field(default=None, init=False)
    # nc_largefile: bool = False
    # varlist: Varlist = None
    # preprocessor: typing.Any = dc.field(default=None, compare=False)
    # POD_CODE_DIR = ""
    # POD_OBS_DATA = ""
    # POD_WK_DIR = ""
    # POD_OUT_DIR = ""
    # _deactivation_log_level = logging.ERROR
    #  _interpreters = {'.py': 'python', '.ncl': 'ncl', '.R': 'Rscript'}
    pass



#if __name__ == "__main__":
#   print(MultirunLocalFileDataSource.mro())
