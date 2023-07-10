"""Implementation classes for model data query/fetch functionality, selected by
the user via ``--data_manager``; see :doc:`ref_data_sources` and
:doc:`fmwk_datasources`.
"""
import abc
import os
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
    varlist: varlist_util.Varlist = None

    def __init__(self, case_name: str, case_dict: util.NameSpace, parent):
        # _id = util.MDTF_ID()        # attrs inherited from util.logs.MDTFObjectBase
        # name: str
        # _parent: object
        # log = util.MDTFObjectLogger
        # status: util.ObjectStatus
        # initialize MDTF logging object associated with this case
        super().__init__(
            self, name=case_name, _parent=parent
        )
        # set up log (CaseLoggerMixin)
        self.init_log(log_dir=parent.MODEL_WK_DIR)
        self.convention = case_dict.convention

    @property
    def _children(self):
        """Iterable of the multirun varlist that is associated with the data source object
        """
        yield from self.varlist.iter_vars()

    def get_varlist(self, parent):
        return varlist_util.Varlist.from_struct(parent)
    def query_dataset(self, var):
        """Find all rows of the catalog matching relevant attributes of the
            DataSource and of the variable (:class:`~diagnostic.VarlistEntry`).
            Group these by experiments, and for each experiment make the corresponding
            :class:`DataFrameDataKey` and store it in var's *data* attribute.
            Specifically, the *data* attribute is a dict mapping experiments
            (labeled by experiment_keys) to data found for that variable
            by this query (labeled by the DataKeys).
            Finally, verify that only a single file was found for each case.
        """
        query_df = self._query_catalog(var)
        # assign set of sets of catalog row indices to var's data attr
        # filter out empty entries = queries that failed.
        expt_groups = query_df.groupby(
            by=(lambda idx: self.col_spec.expt_key(query_df, idx))
        )
        var.data = util.ConsistentDict()
        for expt_key, group in expt_groups:
            group = self.check_group_daterange(group, expt_key=expt_key, log=var.log)
            if group.empty:
                var.log.debug('Expt_key %s eliminated by _check_group_daterange',
                              expt_key)
                continue
            group = self._query_group_hook(group)
            if group.empty:
                var.log.debug('Expt_key %s eliminated by _query_group_hook', expt_key)
                continue
            d_key = self.data_key(group, expt_key=expt_key)
            var.log.debug('Query found <expt_key=%s, %s> for %s',
                          expt_key, d_key, var.full_name)
            var.data[expt_key] = d_key

            if not isinstance(var.associated_files, dict):
                var.associated_files = {}

            # Query for associated files - if the object contains a
            # `query_associated_fields` method, we call it here. This is currently
            # implemented for the gfdl `GFDL_GCP_FileDataSourceBase`, but any
            # class that inherits ` DataframeQueryDataSourceBase` can define this
            # method to populate the `VarlistEntry.associated_files` attribute.
            # Otherwise, this attribute is set to an empty dictionary here.
            if not hasattr(self, "query_associated_files") or not var.associated_files:
                continue
            try:
                var.associated_files[expt_key] = self.query_associated_files(d_key)
            except Exception as exc:
                var.log.debug(f"Unable to query associated files: {exc}")
        for d_key in var.data.values():
            if len(d_key.value) != 1:
                self._query_error_handler(
                    "Query found multiple files when one was expected:",
                    d_key, log=var.log
                )


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









