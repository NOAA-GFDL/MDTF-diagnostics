"""
Base classes implementing logic for querying, fetching and preprocessing
model data requested by the PODs for multirun mode
(i.e., a single POD is associated with multiple data sources)
"""
import dataclasses as dc
import copy
from src import util, diagnostic, data_model

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


# defining attributes using dc.field default_factory means that all instances have a default type
# This also ensures that the same attribute object is not reused each time it is called
# Therefore, you can modify individual values in one dc.field instance without propagating the
# changes to other object instances
class MultirunVarlist(diagnostic.Varlist):
    # contents: dc.InitVar = util.MANDATORY # fields inherited from data_model.DMDataSet
    # vars: list = dc.field(init=False, default_factory=list)
    # coord_bounds: list = dc.field(init=False, default_factory=list)
    # aux_coords: list = dc.field(init=False, default_factory=list)
    pass

class MultirunDiagnostic(diagnostic.Diagnostic):
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
    varlist = MultirunVarlist = None

@util.mdtf_dataclass
class MultirunVarlistEntry(diagnostic.VarlistEntry):
    # Attributes:
    #         path_variable: Name of env var containing path to local data.
    #         dest_path: list of paths to local data
    # _id = util.MDTF_ID()           # fields inherited from core.MDTFObjectBase
    # name: str
    # _parent: object
    # log = util.MDTFObjectLogger
    # status: ObjectStatus
    # standard_name: str             # fields inherited from data_model.DMVariable
    # units: Units
    # dims: list
    # scalar_coords: list
    # modifier: str
    # use_exact_name: bool = False   # fields inherited from diagnostic.VarlistEntry
    # env_var: str = dc.field(default="", compare=False)
    # path_variable: str = dc.field(default="", compare=False)
    # dest_path: str = ""
    # requirement: VarlistEntryRequirement = dc.field(default=VarlistEntryRequirement.REQUIRED, compare=False)
    # alternates: list = dc.field(default_factory=list, compare=False)
    # translation: typing.Any = dc.field(default=None, compare=False)
    # data: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict, compare=False)
    # stage: VarlistEntryStage = dc.field(default=VarlistEntryStage.NOTSET, compare=False)
    # _deactivation_log_level = logging.INFO

    # NOTE: see <https://stackoverflow.com/questions/26467564/how-to-copy-all-attributes-of-one-python-object-to-another>
    # for why the from_parent method is used. We want attributes to correspond to an object, not the multrunvarlist
    # class
    # init attributes will belong to the instance
    def __init__(self):
        self.path_variable: list = dc.field(default_factory=list,
                                       compare=False)  # each variable will have a list of paths to files for
        # each case don't need compare methods b/c this will be a list of strings, not booleans, ints, etc...
        self.dest_path: list = dc.field(default_factory=list,
                                   compare=False)
    @classmethod
    def from_parent(self, parent):
        skip_atts = ["path_variable", "dest_path"]
        for k, v in parent.__dict__.items():
            if k not in skip_atts:
                #print(k)
                self.__dict__[k] = copy.deepcopy(v)



          # each variable will have a list of paths to files for each case
    # don't need compare methods b/c this will be a list of strings,
    # not booleans, ints, etc...
    pass



#if __name__ == "__main__":
#    print(MultirunDiagnostic.mro())