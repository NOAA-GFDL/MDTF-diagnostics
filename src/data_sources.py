"""Implementation classes for the model data query/fetch functionality
implemented in src/data_manager.py, selected by the user via  ``--data_manager``.
"""
import os
import collections
import dataclasses
from src import util, core, diagnostic, xr_parser, preprocessor, cmip6
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
    # log: dataclasses.InitVar = _log
    sample_dataset: str = ""

    def _set_case_root_dir(self, log=_log):
        """Additional logic to set CASE_ROOT_DIR from MODEL_DATA_ROOT.
        """
        config = core.ConfigManager()
        paths = core.PathManager()
        if not self.CASE_ROOT_DIR and config.CASE_ROOT_DIR:
            log.debug("Using global CASE_ROOT_DIR = '%s'.", config.CASE_ROOT_DIR)
            self.CASE_ROOT_DIR = config.CASE_ROOT_DIR
        if not self.CASE_ROOT_DIR:
            model_root = getattr(paths, 'MODEL_DATA_ROOT', None)
            log.debug("Setting CASE_ROOT_DIR to MODEL_DATA_ROOT = '%s'.", model_root)
            self.CASE_ROOT_DIR = model_root
        # verify CASE_ROOT_DIR exists
        if not os.path.isdir(self.CASE_ROOT_DIR):
            log.critical("Data directory CASE_ROOT_DIR = '%s' not found.",
                self.CASE_ROOT_DIR)
            util.exit_handler(code=1)

    def __post_init__(self, log=_log):
        """Validate user input.
        """
        super(SampleDataAttributes, self).__post_init__(log=log)
        # set sample_dataset
        if not self.sample_dataset and self.CASENAME:
            log.debug(
                "'sample_dataset' not supplied, using CASENAME = '%s'.",
                self.CASENAME
            )
            self.sample_dataset = self.CASENAME
        # verify chosen subdirectory exists
        if not os.path.isdir(
            os.path.join(self.CASE_ROOT_DIR, self.sample_dataset)
        ):
            log.critical(
                "Sample dataset '%s' not found in CASE_ROOT_DIR = '%s'.",
                self.sample_dataset, self.CASE_ROOT_DIR)
            util.exit_handler(code=1)

sampleLocalFileDataSource_col_spec = dm.DataframeQueryColumnSpec(
    # Catalog columns whose values must be the same for all variables.
    expt_cols = dm.DataFrameQueryColumnGroup(["sample_dataset"])
)

class SampleLocalFileDataSource(dm.SingleLocalFileDataSource):
    """DataSource for handling POD sample model data stored on a local filesystem.
    """
    _FileRegexClass = SampleDataFile
    _AttributesClass = SampleDataAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = preprocessor.SampleDataPreprocessor
    col_spec = sampleLocalFileDataSource_col_spec

    # map "name" field in VarlistEntry's query_attrs() to "variable" field here
    _query_attrs_synonyms = {'name': 'variable'}

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'CASE_ROOT_DIR'))
        return self.attrs.CASE_ROOT_DIR

# ----------------------------------------------------------------------------

class MetadataRewriteParser(xr_parser.DefaultDatasetParser):
    """After loading and parsing the metadata on dataset *ds* but before
    applying the preprocessing functions, update attrs on *ds* with the new
    metadata values that were specified in :class:`ExplicitFileDataSource`\'s
    config file.
    """
    def __init__(self, data_mgr, pod):
        assert isinstance(data_mgr, ExplicitFileDataSource)
        super(MetadataRewriteParser, self).__init__(data_mgr, pod)

        self.guess_names = True # needed since names will be un-translated
        self.id_lut = dict()

    def setup(self, data_mgr, pod):
        """Make a lookup table to map :class:`~diagnostic.VarlistEntry` IDs to
        the set of metadata that we need to alter.

        If user has provided the name of variable used by the data files (via the
        ``var_name`` attribute), set that as the translated variable name.
        Otherwise, variables are untranslated, and we use the herusitics in
        :meth:`xr_parser.DefaultDatasetParser.guess_dependent_var` to determine
        the name.
        """
        super(MetadataRewriteParser, self).setup(data_mgr, pod)

        for var in pod.iter_children():
            # set user-supplied translated name
            # note: currently have to do this here, rather than in setup_var(),
            # because query for this data source relies on the *un*translated
            # name (ie, the POD's name for the var) being set in the translated
            # name attribute.
            if pod.name in data_mgr._config \
                and var.name in data_mgr._config[pod.name]:
                translated_name = data_mgr._config[pod.name][var.name].var_name
                if translated_name:
                    var.translation.name = translated_name
                    var.log.debug(("Set translated name of %s to user-specified "
                        "value '%s'."), var.full_name, translated_name)

            # add var's info to lookup table of metadata changes
            new_metadata = util.ConsistentDict()
            for d_key in var.data.values():
                idxs = list(d_key.value)
                glob_ids = data_mgr.df['glob_id'].loc[idxs].to_list()
                for id_ in glob_ids:
                    entry = data_mgr.config_by_id[id_]
                    new_metadata.update(entry.metadata)
            self.id_lut[var._id] = new_metadata

    def _post_normalize_hook(self, var, ds):
        """After loading the metadata on dataset *ds* but before
        reconciling it with the record, update attrs with the new
        metadata values that were specified in :class:`ExplicitFileDataSource`\'s
        config file.

        Normal operation is to set the changed attrs on the VarlistEntry
        translation, and then have these overwrite attrs in *ds* in the inherited
        :meth:`xr_parser.DefaultDatasetParser.reconcile_variable` method. If
        the user set the ``--disable-preprocessor`` flag, this is skipped, so
        instead we set the attrs directly on *ds*.
        """
        tv_name = var.translation.name # abbreviate
        assert tv_name in ds # should have been validated by xr_parser
        ds_attrs = ds[tv_name].attrs # abbreviate
        for k, v in self.id_lut[var._id].items():
            if k in ds_attrs and v is not xr_parser.ATTR_NOT_FOUND:
                if v != ds_attrs[k]:
                    var.log.info(("Changing the value of the '%s' attribute of "
                        "variable '%s' from '%s' to user-requested value '%s'."),
                        k, var.name, ds_attrs[k], v,
                        tags=(util.ObjectLogTag.NC_HISTORY, util.ObjectLogTag.BANNER)
                    )
                else:
                    var.log.debug(("The '%s' attribute of variable '%s' already "
                        "has the user-requested value '%s'; not changing."),
                        k, var.name, v,
                        tags=util.ObjectLogTag.BANNER
                    )
            else:
                var.log.debug(("Attribute '%s' of variable '%s' is undefined; "
                    "setting to user-requested value '%s'."),
                    k, var.name, v,
                    tags=(util.ObjectLogTag.NC_HISTORY, util.ObjectLogTag.BANNER)
                )

            v = str(v) # xarray attrs are all strings
            ds_attrs[k] = v
            if k in ('standard_name', 'units'):
                # already logged what we're doing, so update supported attrs on
                # translated var itself in addition to setting directly on ds
                setattr(var.translation, k, v)

class MetadataRewritePreprocessor(preprocessor.DaskMultiFilePreprocessor):
    """Subclass :class:`~preprocessor.DaskMultiFilePreprocessor` in order to
    look up and apply edits to metadata that are stored in
    :class:`ExplicitFileDataSourceConfigEntry` objects in the \config_by_id
    attribute of :class:`ExplicitFileDataSource`.
    """
    _file_preproc_functions = []
    _XarrayParserClass = MetadataRewriteParser

    @property
    def _functions(self):
        config = core.ConfigManager()
        if config.get('disable_preprocessor', False):
            return (
                preprocessor.CropDateRangeFunction,
                preprocessor.RenameVariablesFunction
            )
        else:
            # Add ApplyScaleAndOffsetFunction to functions used by parent class
            return (
                preprocessor.CropDateRangeFunction,
                preprocessor.ApplyScaleAndOffsetFunction,
                preprocessor.PrecipRateToFluxFunction,
                preprocessor.ConvertUnitsFunction,
                preprocessor.ExtractLevelFunction,
                preprocessor.RenameVariablesFunction
            )

dummy_regex = util.RegexPattern(
    r"""(?P<dummy_group>.*) # match everything; RegexPattern needs >= 1 named groups
    """,
    input_field="remote_path",
    match_error_filter=ignore_non_nc_regex
)
@util.regex_dataclass(dummy_regex)
class GlobbedDataFile():
    """Applies a trivial regex to the paths returned by the glob."""
    dummy_group: str = util.MANDATORY
    remote_path: str = util.MANDATORY

@util.mdtf_dataclass
class ExplicitFileDataSourceConfigEntry():
    glob_id: util.MDTF_ID = None
    pod_name: str = util.MANDATORY
    name: str = util.MANDATORY
    glob: str = util.MANDATORY
    var_name: str = ""
    metadata: dict = dataclasses.field(default_factory=dict)
    _has_user_metadata: bool = None

    def __post_init__(self):
        if self.glob_id is None:
            self.glob_id = util.MDTF_ID() # assign unique ID #
        if self._has_user_metadata is None:
            self._has_user_metadata = bool(self.metadata)

    @property
    def full_name(self):
        return '<' + self.pod_name+ '.' + self.name + '>'

    @classmethod
    def from_struct(cls, pod_name, var_name, v_data):
        # "var_name" in arguments is the name given to the variable by the POD;
        # name_in_data is the user-specified name of the variable in the files
        if isinstance(v_data, dict):
            glob = v_data.get('files', "")
            name_in_data = v_data.get('var_name', "")
            metadata = v_data.get('metadata', dict())
            _has_user_metadata = ('metadata' in v_data)
        else:
            glob = v_data
            name_in_data = ""
            metadata = dict()
            _has_user_metadata = False
        return cls(
            pod_name=pod_name, name=var_name, glob=glob,
            var_name=name_in_data, metadata=metadata,
            _has_user_metadata=_has_user_metadata
        )

    def to_file_glob_tuple(self):
        return dm.FileGlobTuple(
            name=self.full_name, glob=self.glob,
            attrs={
                'glob_id': self.glob_id,
                'pod_name': self.pod_name, 'name': self.name
            }
        )

@util.mdtf_dataclass
class ExplicitFileDataAttributes(dm.DataSourceAttributesBase):
    # CASENAME: str          # fields inherited from dm.DataSourceAttributesBase
    # FIRSTYR: str
    # LASTYR: str
    # date_range: util.DateRange
    # CASE_ROOT_DIR: str
    # convention: str
    # log: dataclasses.InitVar = _log
    config_file: str = None

    def __post_init__(self, log=_log):
        """Validate user input.
        """
        super(ExplicitFileDataAttributes, self).__post_init__(log=log)

        config = core.ConfigManager()
        if not self.config_file:
            self.config_file = config.get('config_file', '')
        if not self.config_file:
            log.critical(("No configuration file found for ExplicitFileDataSource "
                "(--config-file)."))
            util.exit_handler(code=1)

        if self.convention != core._NO_TRANSLATION_CONVENTION:
            log.debug("Received incompatible convention '%s'; setting to '%s'.",
                self.convention, core._NO_TRANSLATION_CONVENTION)
            self.convention = core._NO_TRANSLATION_CONVENTION

explicitFileDataSource_col_spec = dm.DataframeQueryColumnSpec(
    # Catalog columns whose values must be the same for all variables.
    expt_cols = dm.DataFrameQueryColumnGroup([])
)

class ExplicitFileDataSource(
    dm.OnTheFlyGlobQueryMixin, dm.LocalFetchMixin, dm.DataframeQueryDataSourceBase
):
    """DataSource for dealing data in a regular directory hierarchy on a
    locally mounted filesystem. Assumes data for each variable may be split into
    several files according to date, with the dates present in their filenames.
    """
    _FileRegexClass = GlobbedDataFile
    _AttributesClass = ExplicitFileDataAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = MetadataRewritePreprocessor
    col_spec = explicitFileDataSource_col_spec

    expt_key_cols = tuple()
    expt_cols = expt_key_cols

    def __init__(self, case_dict, parent):
        self.catalog = None
        self._config = collections.defaultdict(dict)
        self.config_by_id = dict()
        self._has_user_metadata = None

        super(ExplicitFileDataSource, self).__init__(case_dict, parent)

        # Read config file; parse contents into ExplicitFileDataSourceConfigEntry
        # objects and store in self.config_by_id
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'config_file'))
        config = util.read_json(self.attrs.config_file, log=self.log)
        self.parse_config(config)

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'CASE_ROOT_DIR'))
        return self.attrs.CASE_ROOT_DIR

    def parse_config(self, config_d):
        """Parse contents of JSON config file into a list of
        :class`ExplicitFileDataSourceConfigEntry` objects.
        """
        # store contents in ConfigManager so they can be backed up in output
        # (HTMLOutputManager.backup_config_files())
        config = core.ConfigManager()
        config._configs['data_source_config'] = core.ConfigTuple(
            name='data_source_config',
            backup_filename='ExplicitFileDataSource_config.json',
            contents=config_d
        )

        # parse contents
        for pod_name, v_dict in config_d.items():
            for v_name, v_data in v_dict.items():
                entry = ExplicitFileDataSourceConfigEntry.from_struct(
                    pod_name, v_name, v_data)
                self._config[pod_name][v_name] = entry
                self.config_by_id[entry.glob_id] = entry
        # don't bother to validate here -- if we didn't specify files for all
        # vars it'll manifest as a failed query & be logged as error there.

        # set overwrite_metadata flag if needed
        self._has_user_metadata = any(
            x._has_user_metadata for x in self.config_by_id.values()
        )
        if self._has_user_metadata and \
            not config.get('overwrite_file_metadata', False):
            self.log.warning(("Requesting metadata edits in ExplicitFileDataSource "
                "implies the use of the --overwrite-file-metadata flag. Input "
                "file metadata will be overwritten."),
                tags=util.ObjectLogTag.BANNER
            )
            config['overwrite_file_metadata'] = True

    def iter_globs(self):
        """Iterator returning :class:`FileGlobTuple` instances. The generated
        catalog contains the union of the files found by each of the globs.
        """
        for entry in self.config_by_id.values():
            yield entry.to_file_glob_tuple()

# ----------------------------------------------------------------------------

@util.mdtf_dataclass
class CMIP6DataSourceAttributes(dm.DataSourceAttributesBase):
    # CASENAME: str          # fields inherited from dm.DataSourceAttributesBase
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
        config = core.ConfigManager()
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

cmip6LocalFileDataSource_col_spec = dm.DataframeQueryColumnSpec(
    # Catalog columns whose values must be the same for all variables.
    expt_cols = dm.DataFrameQueryColumnGroup(
        ["activity_id", "institution_id", "source_id", "experiment_id",
        "variant_label", "version_date"],
        # columns whose values are derived from those above
        ["region", "spatial_avg", 'realization_index', 'initialization_index',
        'physics_index', 'forcing_index']
    ),
    # Catalog columns whose values must be the same for each POD.
    pod_expt_cols = dm.DataFrameQueryColumnGroup(
        ['grid_label'],
        # columns whose values are derived from those above
        ['regrid', 'grid_number']
    ),
    # Catalog columns whose values must "be the same for each variable", ie are
    # irrelevant but must be constrained to a unique value.
    var_expt_cols = dm.DataFrameQueryColumnGroup(["table_id"]),
    daterange_col = "date_range"
)

class CMIP6ExperimentSelectionMixin():
    """Encapsulate attributes and logic used for CMIP6 experiment disambiguation
    so that it can be reused in DataSources with different parents (eg. different
    FetchMixins for different data fetch protocols.)

    Assumes inheritance from DataframeQueryDataSourceBase -- should enforce this.
    """
    # map "name" field in VarlistEntry's query_attrs() to "variable_id" field here
    _query_attrs_synonyms = {'name': 'variable_id'}

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
        obj.log.debug("Selected experiment attribute '%s'='%s' for %s.",
            col_name, df[col_name].iloc[0], obj.name)
        return df

class CMIP6LocalFileDataSource(CMIP6ExperimentSelectionMixin, dm.LocalFileDataSource):
    """DataSource for handling model data named following the CMIP6 DRS and
    stored on a local filesystem.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _DirectoryRegex = cmip6.drs_directory_regex
    _AttributesClass = CMIP6DataSourceAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = preprocessor.DefaultPreprocessor
    col_spec = cmip6LocalFileDataSource_col_spec
    _convention = "CMIP" # hard-code naming convention

