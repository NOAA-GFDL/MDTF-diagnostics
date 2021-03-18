"""Implementation classes for the model data query/fetch functionality 
implemented in src/data_manager.py, selected by the user via  ``--data_manager``.
"""
import os
import dataclasses
from src import util, core, diagnostic, preprocessor, cmip6
from src import data_manager as dm
import pandas as pd

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
@util.mdtf_dataclass
class SampleDataFile():
    """Dataclass describing catalog entries for sample model data files.
    """
    sample_dataset: str = util.MANDATORY
    frequency: util.DateFrequency = util.MANDATORY
    variable: str = util.MANDATORY
    remote_path: str = util.MANDATORY

@util.mdtf_dataclass
class SampleDataAttributes(dm.DataSourceAttributesBase):
    """Data-source-specific attributes for the DataSource providing sample model
    data.
    """
    # CASENAME: str          # fields inherited from dm.DataSourceAttributesBase
    # FIRSTYR: str
    # LASTYR: str
    # date_range: util.DateRange
    # CASE_ROOT_DIR: str
    # convention: str
    sample_dataset: str = ""

    def _set_case_root_dir(self):
        """Additional logic to set CASE_ROOT_DIR from MODEL_DATA_ROOT.
        """
        config = core.ConfigManager()
        paths = core.PathManager()
        if not self.CASE_ROOT_DIR and config.CASE_ROOT_DIR:
            _log.debug("Using global CASE_ROOT_DIR = '%s'.", config.CASE_ROOT_DIR)
            self.CASE_ROOT_DIR = config.CASE_ROOT_DIR
        if not self.CASE_ROOT_DIR:
            model_root = getattr(paths, 'MODEL_DATA_ROOT', None)
            _log.debug("Setting CASE_ROOT_DIR to MODEL_DATA_ROOT = '%s'.", model_root)
            self.CASE_ROOT_DIR = model_root
        # verify CASE_ROOT_DIR exists
        if not os.path.isdir(self.CASE_ROOT_DIR):
            _log.critical("Data directory CASE_ROOT_DIR = '%s' not found.",
                self.CASE_ROOT_DIR)
            exit(1)

    def __post_init__(self):
        """Validate user input.
        """
        super(SampleDataAttributes, self).__post_init__()
        # set sample_dataset
        if not self.sample_dataset and self.CASENAME:
            _log.debug(
                "'sample_dataset' not supplied, using CASENAME = '%s'.",
                self.CASENAME
            )
            self.sample_dataset = self.CASENAME
        # verify chosen subdirectory exists
        if not os.path.isdir(
            os.path.join(self.CASE_ROOT_DIR, self.sample_dataset)
        ):
            _log.critical(
                "Sample dataset '%s' not found in CASE_ROOT_DIR = '%s'.",
                self.sample_dataset, self.CASE_ROOT_DIR)
            exit(1)


class SampleLocalFileDataSource(dm.SingleLocalFileDataSource):
    """DataSource for handling POD sample model data stored on a local filesystem.
    """
    _FileRegexClass = SampleDataFile
    _AttributesClass = SampleDataAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = preprocessor.SampleDataPreprocessor

    # Catalog columns whose values must be the same for all variables.
    expt_key_cols = ("sample_dataset", )
    expt_cols = expt_key_cols

    # map "name" field in VarlistEntry's query_attrs() to "variable" field here
    _query_attrs_synonyms = {'name': 'variable'}

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'CASE_ROOT_DIR'))
        return self.attrs.CASE_ROOT_DIR

# ----------------------------------------------------------------------------

@util.mdtf_dataclass
class CMIP6DataSourceAttributes(dm.DataSourceAttributesBase):
    # CASENAME: str          # fields inherited from dm.DataSourceAttributesBase
    # FIRSTYR: str
    # LASTYR: str
    # date_range: util.DateRange
    # CASE_ROOT_DIR: str
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

    def __post_init__(self, model=None, experiment=None):
        super(CMIP6DataSourceAttributes, self).__post_init__()
        cv = cmip6.CMIP6_CVs()

        def _init_x_from_y(source, dest):
            if not getattr(self, dest, ""):
                try:
                    source_val = getattr(self, source, "")
                    if not source_val:
                        raise KeyError()
                    dest_val = cv.lookup_single(source_val, source, dest)
                    _log.debug("Set %s='%s' based on %s='%s'.", 
                        dest, dest_val, source, source_val)
                    setattr(self, dest, dest_val)
                except KeyError:
                    _log.debug("Couldn't set %s from %s='%s'.", 
                        dest, source, source_val)
                    setattr(self, dest, "")

        if self.convention != "CMIP":
            _log.debug("Received incompatible convention '%s'; setting to 'CMIP.", 
                self.convention)
            self.convention = "CMIP"

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
                    _log.error(("Supplied value '%s' for '%s' is not recognized by "
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
            _log.error("Data directory '%s' not found; starting crawl at '%s'.",
                new_root, self.CASE_ROOT_DIR)
            self.CATALOG_DIR = self.CASE_ROOT_DIR
        else:
            self.CATALOG_DIR = new_root

class CMIP6ExperimentSelectionMixin():
    """Encapsulate attributes and logic used for CMIP6 experiment disambiguation
    so that it can be reused in DataSources with different parents (eg. different
    FetchMixins for different data fetch protocols.)

    Assumes inheritance from DataframeQueryDataSourceBase -- should enforce this.
    """
    # map "name" field in VarlistEntry's query_attrs() to "variable_id" field here
    _query_attrs_synonyms = {'name': 'variable_id'}

    daterange_col = "date_range"
    # Catalog columns whose values must be the same for all variables.
    expt_key_cols = (
        "activity_id", "institution_id", "source_id", "experiment_id",
        "variant_label", "version_date"
    )
    expt_cols = expt_key_cols + (
        # columns whose values are derived from those in expt_key_cols
        "region", "spatial_avg", 'realization_index', 'initialization_index', 
        'physics_index', 'forcing_index'
    )
    # Catalog columns whose values must be the same for each POD.
    pod_expt_key_cols = ('grid_label',)
    pod_expt_cols = pod_expt_key_cols + (
        # columns whose values are derived from those in pod_expt_key_cols
        'regrid', 'grid_number'
    )
    # Catalog columns whose values must "be the same for each variable", ie are 
    # irrelevant but must be constrained to a unique value.
    var_expt_key_cols = ("table_id", )
    var_expt_cols = var_expt_key_cols

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'CATALOG_DIR'))
        return self.attrs.CATALOG_DIR

    def _query_group_hook(self, group_df):
        """Eliminate regional (Antarctic/Greenland) and spatially averaged data
        from consideration for data fetch, since no POD currently makes use of
        data of this type.
        """
        has_region = not (group_df['region'].isnull().all())
        has_spatial_avg = not (group_df['spatial_avg'].isnull().all())
        if not has_region and not has_spatial_avg:
            # correct values, pass this group through
            return group_df
        else:
            # return empty DataFrame to signify failure
            if has_region:
                _log.debug("Eliminating expt_key for regional data (%s).", 
                    group_df['region'].drop_duplicates().to_list())
            elif has_spatial_avg:
                _log.debug("Eliminating expt_key for spatially averaged data (%s).", 
                    group_df['spatial_avg'].drop_duplicates().to_list())
            return pd.DataFrame(columns=group_df.columns)

    @staticmethod
    def _filter_column(df, col_name, func, obj_name):
        values = list(df[col_name].drop_duplicates())
        if len(values) <= 1:
            # unique value, no need to filter
            return df
        filter_val = func(values)
        _log.debug("Selected experiment attribute '%s'='%s' for %s (out of %s).", 
            col_name, filter_val, obj_name, values)
        return df[df[col_name] == filter_val]

    def _filter_column_min(self, df, obj_name, *col_names):
        for c in col_names:
            df = self._filter_column(df, c, min, obj_name=obj_name)
        return df

    def _filter_column_max(self, df, obj_name, *col_names):
        for c in col_names:
            df = self._filter_column(df, c, max, obj_name=obj_name)
        return df

    def resolve_expt(self, df, obj):
        """Disambiguate experiment attributes that must be the same for all 
        variables in this case: 
 
        - If variant_id (realization, forcing, etc.) not specified by user, 
            choose the lowest-numbered variant
        - If version_date not set by user, choose the most recent revision
        """
        # If multiple ensemble/forcing members, choose lowest-numbered one
        df = self._filter_column_min(df, obj.name,
            'realization_index', 'initialization_index', 'physics_index', 'forcing_index'
        )
        # use most recent version_date
        df = self._filter_column_max(df, obj.name, 'version_date')
        return df

    def resolve_pod_expt(self, df, obj):
        """Disambiguate experiment attributes that must be the same for all 
        variables for each POD:
 
        - Prefer regridded to native-grid data (questionable)
        - If multiple regriddings available, pick the lowest-numbered one
        """
        # prefer regridded data
        if any(df['regrid'] == 'r'):
            df = df[df['regrid'] == 'r']
        # if multiple regriddings, choose the lowest-numbered one
        df = self._filter_column_min(df, obj.name, 'grid_number')
        return df

    def resolve_var_expt(self, df, obj):
        """Disambiguate arbitrary experiment attributes on a per-variable basis:
 
        - If the same variable appears in multiple MIP tables, select the first
            MIP table in alphabetical order.
        """
        # TODO: minimize number of MIP tables
        col_name = 'table_id'
        # select first MIP table (out of available options) by alpha order
        # NB need to pass list to iloc to get a pd.DataFrame instead of pd.Series
        df = df.sort_values(col_name).iloc[[0]]
        _log.debug("Selected experiment attribute '%s'='%s' for %s.", 
            col_name, df[col_name].iloc[0], obj.name)
        return df

class CMIP6LocalFileDataSource(
    CMIP6ExperimentSelectionMixin, dm.LocalFileDataSource
):
    """DataSource for handling model data named following the CMIP6 DRS and 
    stored on a local filesystem.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _DirectoryRegex = cmip6.drs_directory_regex
    _AttributesClass = CMIP6DataSourceAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = preprocessor.MDTFDataPreprocessor

