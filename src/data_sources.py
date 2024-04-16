"""Implementation classes for model data query
"""
import os
import io
import dataclasses
from src import util, cmip6, varlist_util

import logging
_log = logging.getLogger(__name__)

# RegexPattern that matches any string (path) that doesn't end with ".nc".
ignore_non_nc_regex = util.RegexPattern(r".*(?<!\.nc)")

sample_data_regex = util.RegexPattern(
    r"""
        (?P<sample_dataset>\S+)/    # first directory: model name
        (?P<frequency>\w+)/         # subdirectory: data frequency
        # file name = model name + variable name + frequency
        (?P=sample_dataset)\.(?P<variable>\w+)\.(?P=frequency)\.nc
    """,
    input_field="remote_path",
    match_error_filter=ignore_non_nc_regex
)


@util.regex_dataclass(sample_data_regex)
class SampleDataFile:
    """Dataclass describing catalog entries for sample model data files.
    """
    sample_dataset: str = util.MANDATORY
    frequency: util.DateFrequency = util.MANDATORY
    variable: str = util.MANDATORY
    remote_path: str = util.MANDATORY


@util.mdtf_dataclass
class DataSourceAttributesBase:
    """Class defining attributes that any DataSource needs to specify:

    - *CASENAME*: User-supplied label to identify output of this run of the
      package.
    - *FIRSTYR*, *LASTYR*, *date_range*: Analysis period, specified as a closed
      interval (i.e. running from 1 Jan of FIRSTYR through 31 Dec of LASTYR).
    - *CASE_ROOT_DIR*: Root directory containing input model data. Different
      DataSources may interpret this differently.
    - *convention*: name of the variable naming convention used by the source of
      model data.
    """
    CASENAME: str = util.MANDATORY
    FIRSTYR: str = util.MANDATORY
    LASTYR: str = util.MANDATORY
    date_range: util.DateRange = dataclasses.field(init=False)
    CASE_ROOT_DIR: str = ""

    log: dataclasses.InitVar = _log

    def _set_case_root_dir(self, log=_log):
        config = {}
        if not self.CASE_ROOT_DIR and config.CASE_ROOT_DIR:
            log.debug("Using global CASE_ROOT_DIR = '%s'.", config.CASE_ROOT_DIR)
            self.CASE_ROOT_DIR = config.CASE_ROOT_DIR
        # verify case root dir exists
        if not os.path.isdir(self.CASE_ROOT_DIR):
            log.critical("Data directory CASE_ROOT_DIR = '%s' not found.",
                         self.CASE_ROOT_DIR)
            util.exit_handler(code=1)

    def __post_init__(self, log=_log):
        self._set_case_root_dir(log=log)
        self.date_range = util.DateRange(self.FIRSTYR, self.LASTYR)


class DataSourceBase(util.MDTFObjectBase, util.CaseLoggerMixin):
    """DataSource for handling POD sample model data for multirun cases stored on a local filesystem.
    """
    # _FileRegexClass = SampleDataFile # fields inherited from SampleLocalFileDataSource
    # _AttributesClass = SampleDataAttributes
    # col_spec = sampleLocalFileDataSource_col_spec
    convention: str
    date_range: util.DateRange = dataclasses.field(init=False)
    varlist: varlist_util.Varlist = None
    log_file: io.IOBase = dataclasses.field(default=None, init=False)
    env_vars: util.WormDict()

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

    @property
    def _children(self):
        """Iterable of the multirun varlist that is associated with the data source object
        """
        yield from self.varlist.iter_vars()

    def iter_vars_only(self, active=None):
        yield from self.varlist.iter_vars_only(active=active)

    def read_varlist(self, parent):
        self.varlist = varlist_util.Varlist.from_struct(parent)

    def set_date_range(self, startdate: str, enddate: str):
        self.date_range = util.DateRange(start=startdate, end=enddate)

    def translate_varlist(self,
                          model_paths: util.ModelDataPathManager,
                          case_name: str,
                          to_convention: str):
        for v in self.varlist.iter_vars():
            self.varlist.setup_var(model_paths, case_name, v, to_convention, self.date_range)


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


@data_source.maker
class CESMDataSource(DataSourceBase):
    """DataSource for handling POD sample model data for multirun cases stored on a local filesystem.
    """
    # _FileRegexClass = SampleDataFile # fields inherited from SampleLocalFileDataSource
    # _AttributesClass = SampleDataAttributes
    # col_spec = sampleLocalFileDataSource_col_spec
    # varlist = diagnostic.varlist
    convention: str = "CESM"


@data_source.maker
class GFDLDataSource(DataSourceBase):
    """DataSource for handling POD sample model data for multirun cases stored on a local filesystem.
    """
    # _FileRegexClass = SampleDataFile # fields inherited from SampleLocalFileDataSource
    # _AttributesClass = SampleDataAttributes
    # col_spec = sampleLocalFileDataSource_col_spec
    # varlist = diagnostic.varlist
    convention: str = "GFDL"


dummy_regex = util.RegexPattern(
    r"""(?P<dummy_group>.*) # match everything; RegexPattern needs >= 1 named groups
    """,
    input_field="remote_path",
    match_error_filter=ignore_non_nc_regex
)


@util.regex_dataclass(dummy_regex)
class GlobbedDataFile:
    """Applies a trivial regex to the paths returned by the glob."""
    dummy_group: str = util.MANDATORY
    remote_path: str = util.MANDATORY



    #def to_file_glob_tuple(self):
    #    return dm.FileGlobTuple(
    #        name=self.full_name, glob=self.glob,
    #        attrs={
    #            'glob_id': self.glob_id,
    #            'pod_name': self.pod_name, 'name': self.name
    #        }
    #    )





@util.mdtf_dataclass
class CMIP6DataSourceAttributes(DataSourceAttributesBase):
    # CASENAME: str          # fields inherited from DataSourceAttributesBase
    # FIRSTYR: str
    # LASTYR: str
    # date_range: util.DateRange
    # CASE_ROOT_DIR: str
    # log: dataclasses.InitVar = _log
    convention: str = "CMIP" # hard-code naming convention
    activity_id: str = ""
    institution_id: str = ""
    source_id: str = ""
    experiment_id: str = ""
    variant_label: str = ""
    grid_label: str = ""
    version_date: str = ""
    model: dataclasses.InitVar = ""      # synonym for source_id
    experiment: dataclasses.InitVar = "" # synonym for experiment_id
    CATALOG_DIR: str = dataclasses.field(init=False)

    def __post_init__(self, log=_log, model=None, experiment=None):
        super(CMIP6DataSourceAttributes, self).__post_init__(log=log)
        config = {}
        cv = cmip6.CMIP6_CVs()

        def _init_x_from_y(source, dest):
            if not getattr(self, dest, ""):
                try:
                    source_val = getattr(self, source, "")
                    if not source_val:
                        raise KeyError()
                    dest_val = cv.lookup_single(source_val, source, dest)
                    log.debug("Set %s='%s' based on %s='%s'.",
                        dest, dest_val, source, source_val)
                    setattr(self, dest, dest_val)
                except KeyError:
                    log.debug("Couldn't set %s from %s='%s'.",
                              dest, source, source_val)
                    setattr(self, dest, "")

        if not self.CASE_ROOT_DIR and config.CASE_ROOT_DIR:
            log.debug("Using global CASE_ROOT_DIR = '%s'.", config.CASE_ROOT_DIR)
            self.CASE_ROOT_DIR = config.CASE_ROOT_DIR
        # verify case root dir exists
        if not os.path.isdir(self.CASE_ROOT_DIR):
            log.critical("Data directory CASE_ROOT_DIR = '%s' not found.",
                self.CASE_ROOT_DIR)
            util.exit_handler(code=1)

        # should really fix this at the level of CLI flag synonyms
        if model and not self.source_id:
            self.source_id = model
        if experiment and not self.experiment_id:
            self.experiment_id = experiment

        # validate non-empty field values
        for field in dataclasses.fields(self):
            val = getattr(self, field.name, "")
            if not val:
                continue
            try:
                if not cv.is_in_cv(field.name, val):
                    log.error(("Supplied value '%s' for '%s' is not recognized by "
                        "the CMIP6 CV. Continuing, but queries will probably fail."),
                        val, field.name)
            except KeyError:
                # raised if not a valid CMIP6 CV category
                continue
        # currently no inter-field consistency checks: happens implicitly, since
        # set_experiment will find zero experiments.

        # Attempt to determine first few fields of DRS, to avoid having to crawl
        # entire DRS structure
        _init_x_from_y('experiment_id', 'activity_id')
        _init_x_from_y('source_id', 'institution_id')
        _init_x_from_y('institution_id', 'source_id')
        # TODO: multi-column lookups
        # set CATALOG_DIR to be further down the hierarchy if possible, to
        # avoid having to crawl entire DRS strcture; CASE_ROOT_DIR remains the
        # root of the DRS hierarchy
        new_root = self.CASE_ROOT_DIR
        for drs_attr in ("activity_id", "institution_id", "source_id", "experiment_id"):
            drs_val = getattr(self, drs_attr, "")
            if not drs_val:
                break
            new_root = os.path.join(new_root, drs_val)
        if not os.path.isdir(new_root):
            log.error("Data directory '%s' not found; starting crawl at '%s'.",
                new_root, self.CASE_ROOT_DIR)
            self.CATALOG_DIR = self.CASE_ROOT_DIR
        else:
            self.CATALOG_DIR = new_root









