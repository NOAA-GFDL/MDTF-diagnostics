"""Implementation classes for model data query
"""
import io
import dataclasses
from src import util, varlist_util

import logging

_log = logging.getLogger(__name__)

# RegexPattern that matches any string (path) that doesn't end with ".nc".
ignore_non_nc_regex = util.RegexPattern(r".*(?<!\.nc)")


class DataSourceBase(util.MDTFObjectBase, util.CaseLoggerMixin):
    """DataSource for handling POD sample model data for multirun cases stored on a local filesystem.
    """
    # _FileRegexClass = SampleDataFile # fields inherited from SampleLocalFileDataSource
    # _AttributesClass = SampleDataAttributes
    # col_spec = sampleLocalFileDataSource_col_spec
    convention: str
    query: dict
    date_range: util.DateRange = dataclasses.field(init=False)
    varlist: varlist_util.Varlist = None
    log_file: io.IOBase = dataclasses.field(default=None, init=False)
    env_vars: util.WormDict
    query: dict = dict(frequency="",
                       path="",
                       standard_name="",
                       realm=""
                       )

    def __init__(self, case_name: str,
                 case_dict: dict,
                 path_obj: util.ModelDataPathManager,
                 parent: None):
        # _id = util.MDTF_ID()        # attrs inherited from util.logs.MDTFObjectBase
        # name: str
        # _parent: object
        # log = util.MDTFObjectLogger
        # status: util.ObjectStatus

        # initialize MDTF logging object associated with this case
        util.MDTFObjectBase.__init__(self, name=case_name, _parent=parent)
        # set up log (CaseLoggerMixin)
        self.init_log(log_dir=path_obj.WORK_DIR)
        # configure case-specific env vars
        self.env_vars = util.WormDict.from_struct({
            k: case_dict[k] for k in ("startdate", "enddate", "convention")
        })
        self.env_vars.update({"CASENAME": case_name})
        optional_case_attrs = {'realm', 'frequency'}
        for att in optional_case_attrs:
            if case_dict.get(att, None) is not None:
                self.query[att] = case_dict[att]

    @property
    def _children(self):
        """Iterable of the multirun varlist that is associated with the data source object
        """
        yield from self.varlist.iter_vars()

    def iter_vars_only(self, active=None):
        yield from self.varlist.iter_vars_only(active=active)

    def read_varlist(self, parent, append_vars: bool = False):
        self.varlist = varlist_util.Varlist.from_struct(parent, append_vars)

    def set_date_range(self, startdate: str, enddate: str):
        self.date_range = util.DateRange(start=startdate, end=enddate)

    def set_query(self, var: varlist_util.VarlistEntry, path_regex: str):
        if self.query['frequency'] == '':
            if var.is_static:
                freq = "fx"
            else:
                freq = var.T.frequency

            if not isinstance(freq, str):
                freq = freq.format_local()
            if freq == 'hr':
                freq = '1hr'
            self.query['frequency'] = freq

        var_id = var.name
        standard_name = var.standard_name
        if self.query['realm'] == '':
            self.query['realm'] = var.realm
        if var.translation is not None:
            #var_id = var.translation.name
            standard_name = var.translation.standard_name
            if any(var.translation.alternate_standard_names):
                standard_name = [var.translation.standard_name] + var.translation.alternate_standard_names

        # define initial query dictionary with variable settings requirements that do not change if
        # the variable is translated
        self.query['path'] = path_regex
        self.query['standard_name'] = standard_name


    def translate_varlist(self,
                          var: varlist_util.VarlistEntry,
                          model_paths: util.ModelDataPathManager,
                          case_name: str,
                          from_convention: str,
                          to_convention: str):

        self.varlist.setup_var(model_paths,
                               case_name,
                               var,
                               from_convention,
                               to_convention,
                               self.date_range)


# instantiate the class maker so that the convention-specific classes can be instantiated using
# the convention string specification associated with each case
data_source = util.ClassMaker()


@data_source.maker
class CMIPDataSource(DataSourceBase):
    """DataSource for handling POD sample model data for multirun cases stored on a local filesystem.
    """
    # _FileRegexClass = SampleDataFile # fields inherited from SampleLocalFileDataSource
    # _AttributesClass = SampleDataAttributes
    # col_spec = sampleLocalFileDataSource_col_spec
    # varlist = diagnostic.varlist
    convention: str = "CMIP"

    def set_query(self, var: varlist_util.VarlistEntry, path_regex: str):
        super().set_query(var, path_regex)
        return


@data_source.maker
class CESMDataSource(DataSourceBase):
    """DataSource for handling POD sample model data for multirun cases stored on a local filesystem.
    """
    # _FileRegexClass = SampleDataFile # fields inherited from SampleLocalFileDataSource
    # _AttributesClass = SampleDataAttributes
    # col_spec = sampleLocalFileDataSource_col_spec
    # varlist = diagnostic.varlist
    convention: str = "CESM"

    def set_query(self, var: varlist_util.VarlistEntry, path_regex: str):
        super().set_query(var, path_regex)
        return


@data_source.maker
class GFDLDataSource(DataSourceBase):
    """DataSource for handling POD sample model data for multirun cases stored on a local filesystem.
    """
    # _FileRegexClass = SampleDataFile # fields inherited from SampleLocalFileDataSource
    # _AttributesClass = SampleDataAttributes
    # col_spec = sampleLocalFileDataSource_col_spec
    # varlist = diagnostic.varlist
    convention: str = "GFDL"

    def set_query(self, var: varlist_util.VarlistEntry, path_regex: str):
        super().set_query(var, path_regex)
        # this is hacky, but prevents the framework from grabbing from ice_1x1deg
        if self.query['realm'] == 'seaIce*':
            self.query['realm'] = 'ice'
        return
