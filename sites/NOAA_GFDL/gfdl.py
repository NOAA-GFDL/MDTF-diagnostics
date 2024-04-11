"""Code specific to the computing environment at NOAA's Geophysical Fluid
Dynamics Laboratory (Princeton, NJ, USA).
"""
import abc
import os
import io
import dataclasses
import shutil
import tempfile
import pandas as pd
from src import (util, pod_setup, data_manager, data_sources,
                 preprocessor, environment_manager, output_manager, cmip6)
from sites.NOAA_GFDL import gfdl_util

import logging
_log = logging.getLogger(__name__)


class GFDLMDTFFramework(core.MDTFFramework):
    def parse_mdtf_args(self, cli_obj, pod_info_tuple):
        super(GFDLMDTFFramework, self).parse_mdtf_args(cli_obj, pod_info_tuple)


        # set up cooperative mode -- hack to pass config settings
        self.frepp_mode = cli_obj.config.get('frepp', False)
        if self.frepp_mode:
            cli_obj.config['diagnostic'] = 'Gfdl'




# ====================================================================

class GfdlPodObject(pod_setup.PodObject):
    """Wrapper for Diagnostic that adds writing a placeholder directory
    (POD_OUT_DIR) to the output as a lockfile if we're running in frepp
    cooperative mode.
    """
    # extra dataclass fields
    _has_placeholder: bool = False
    frepp_mode: bool = False
    timeout: int = 0

    def __init__(self, name: str, runtime_config: util.NameSpace):
        """Extra code only applicable in frepp cooperative mode. If this code is
        called, all the POD's model data has been generated. Write a placeholder
        directory to POD_OUT_DIR, so if frepp invokes the MDTF package again
        while we're running, only our results will be written to the overall
        output.
        """
        super(GfdlPodObject, self).__init__(name, runtime_config)

        self.frepp_mode = runtime_config.get('frepp', False)
        self.timeout = runtime_config.get('file_transfer_timeout', 0)
        if self.frepp_mode and not os.path.exists(self.POD_OUT_DIR):
            try:
                gfdl_util.make_remote_dir(self.POD_OUT_DIR, log=self.log)
                self._has_placeholder = True
            except Exception as exc:
                chained_exc = util.chain_exc(exc, (f"Making output directory at "
                                                   f"{self.POD_OUT_DIR}."), util.PodRuntimeError)
                self.deactivate(chained_exc)

    def reset_case_pod_list(self, runtime_config):
        if self.frepp_mode:
            for case in self.iter_children():
                # frepp mode:only attempt PODs other instances haven't already done
                case_outdir = self.paths.modelPaths(case, overwrite=True)
                case_outdir = case_outdir.MODEL_OUT_DIR

    def verify_paths(self, config):
        keep_temp = config.get('keep_temp', False)
        # clean out WORKING_DIR if we're not keeping temp files:
        if os.path.exists(self.WORK_DIR) and not \
                (keep_temp or self.WORK_DIR == self.OUTPUT_DIR):
            gfdl_util.rmtree_wrapper(self.WORK_DIR)

        try:
            for dir_name, create_ in (
                    ('CODE_ROOT', False), ('OBS_DATA_REMOTE', False),
                    ('OBS_DATA_ROOT', True), ('MODEL_DATA_ROOT', True), ('WORK_DIR', True)
            ):
                util.check_dir(p, dir_name, create=create_)
        except Exception as exc:
            _log.fatal((f"Input settings for {dir_name} mis-specified (caught "
                        f"{repr(exc)}.)"))
            util.exit_handler(code=1)

        # Use GCP to create OUTPUT_DIR on a volume that may be read-only
        if not os.path.exists(p.OUTPUT_DIR):
            gfdl_util.make_remote_dir(p.OUTPUT_DIR, self.timeout, self.dry_run,
                                      log=_log)

    def parse_env_vars(self, runtime_config: util.NameSpace):
        # set temp directory according to where we're running
        if gfdl_util.running_on_PPAN():
            gfdl_tmp_dir = runtime_config.get('GFDL_PPAN_TEMP', '$TMPDIR')
        else:
            gfdl_tmp_dir = runtime_config.get('GFDL_WS_TEMP', '$TMPDIR')
        gfdl_tmp_dir = util.resolve_path(
            gfdl_tmp_dir, root_path=self.code_root, env=self.global_env_vars,
            log=_log
        )
        if not os.path.isdir(gfdl_tmp_dir):
            gfdl_util.make_remote_dir(gfdl_tmp_dir, log=_log)
        tempfile.tempdir = gfdl_tmp_dir
        os.environ['MDTF_TMPDIR'] = gfdl_tmp_dir
        self.global_env_vars['MDTF_TMPDIR'] = gfdl_tmp_dir

    def _post_parse_hook(self, config, paths):
        # call parent class method

        self.reset_case_pod_list(config, paths)
        # copy obs data from site install
        gfdl_util.fetch_obs_data(
            self.paths.OBS_DATA_REMOTE, self.paths.OBS_DATA_ROOT,
            timeout=self.timeout, log=_log
        )


# ------------------------------------------------------------------------

class GCPFetchMixin:
    """Mixin implementing data fetch for netcdf files on filesystems accessible
    from GFDL via GCP. Remote files are copies to a local temp directory. dmgets
    are issued for remote files on tape filesystems.
    """
    def setup_fetch(self):
        modMgr = gfdl_util.ModuleManager()
        modMgr.load('gcp')

    @property
    def tape_filesystem(self):
        return gfdl_util.is_on_tape_filesystem(self.attrs.CASE_ROOT_DIR)

    def pre_fetch_hook(self, vars_to_fetch):
        """Issue dmget for all files we're about to fetch, if those files are
        on a tape filesystem.
        """
        if self.tape_filesystem:
            paths = set([])
            for var in vars_to_fetch:
                for d_key in var.iter_data_keys(status=util.ObjectStatus.ACTIVE):
                    paths.update(d_key.remote_data())
                for d_key in var.iter_associated_files_keys(
                    status=util.ObjectStatus.ACTIVE
                ):
                    paths.update(d_key.remote_data())

            self.log.info(f"Start dmget of {len(paths)} files...")
            util.run_command(['dmget','-t','-v'] + list(paths),
                             timeout=len(paths) * self.timeout, log=self.log
                             )
            self.log.info("Successful exit of dmget.")

    def _get_fetch_method(self, method=None):
        _methods = {
            'gcp': {'command': ['gcp', '--sync', '-v', '-cd'], 'site':'gfdl:'},
            'cp':  {'command': ['cp'], 'site':''},
            'ln':  {'command': ['ln', '-fs'], 'site':''}
        }
        if method is None:
            method = getattr(self, "_fetch_method", 'auto')
        if method not in _methods:
            if self.tape_filesystem:
                method = 'gcp' # use GCP for DMF filesystems
            else:
                method = 'ln' # symlink for local files
        self.log.debug("Selected fetch method '%s'.", method)
        return (_methods[method]['command'], _methods[method]['site'])

    def fetch_dataset(self, var, d_key):
        """Copy files to temporary directory.
        (GCP can't copy to home dir, so always copy to a temp dir)
        """
        tmpdir = util.TempDirManager().make_tempdir()
        self.log.debug("Created GCP fetch temp dir at %s.", tmpdir)
        (cp_command, smartsite) = self._get_fetch_method(self._fetch_method)

        paths = d_key.remote_data()
        if isinstance(paths, pd.Series):
            paths = paths.to_list()
        if not util.is_iterable(paths):
            paths = (paths, )

        local_paths = []
        for path in paths:
            # exceptions caught in parent loop in data_manager.DataSourceBase
            local_path = os.path.join(tmpdir, os.path.basename(path))
            self.log.info(f"\tFetching {path[len(self.attrs.CASE_ROOT_DIR):]}")
            util.run_command(cp_command + [
                    smartsite + path,
                    # gcp requires trailing slash, ln ignores it
                    smartsite + tmpdir + os.sep
                ],
                timeout=self.timeout, dry_run=self.dry_run, log=self.log
            )
            local_paths.append(local_path)
        d_key.local_data = local_paths


class GFDL_GCP_FileDataSourceBase(ABC):
    """Base class for multirun DataSources that access data on GFDL's internal filesystems
    using GCP, and which may be invoked via frepp.
    """
    _DiagnosticClass = MultirunGfdlDiagnostic
    _PreprocessorClass = preprocessor.MultirunDefaultPreprocessor

    def __init__(self, case_dict, parent):
        super(Multirun_GFDL_GCP_FileDataSourceBase, self).__init__(case_dict, parent)
        # borrow MDTFObjectBase initialization from data_manager:~DataSourceBase
        core.MDTFObjectBase.__init__(
            self, name=case_dict['CASENAME'], _parent=parent
        )
        # default behavior when run interactively:
        # frepp_mode = False, any_components = True
        # default behavior when invoked by FRE wrapper:
        # frepp_mode = True (set to False by calling wrapper with --run_once)
        # any_components = True (set to False with --component_only)
        config = core.ConfigManager()
        self.frepp_mode = config.get('frepp', False)
        self.dry_run = config.get('dry_run', False)
        self.any_components = config.get('any_components', False)
        self.timeout = config.get('file_transfer_timeout', 0)

        if self.frepp_mode:
            paths = core.PathManager()
            self.overwrite = True
            # flag to not overwrite config and .tar: want overwrite for frepp
            self.file_overwrite = True
            # if overwrite=False, WK_DIR & OUT_DIR will have been set to a
            # unique name in parent's init. Set it back so it will be overwritten.
            d = paths.model_paths(self, overwrite=True)
            self.MODEL_WK_DIR = d.MODEL_WK_DIR
            self.MODEL_OUT_DIR = d.MODEL_OUT_DIR

    @property
    def _children(self):
        """Iterable of the multirun varlist that is associated with the data source object
        """
        yield from self.varlist.iter_vars()


@util.mdtf_dataclass
class GFDL_UDA_CMIP6DataSourceAttributes(data_sources.CMIP6DataSourceAttributes):
    def __post_init__(self, log=_log, model=None, experiment=None):
        self.CASE_ROOT_DIR = os.sep + os.path.join('uda', 'CMIP6')
        super(GFDL_UDA_CMIP6DataSourceAttributes, self).__post_init__(log, model, experiment)

class Gfdludacmip6DataManager(
    data_sources.CMIP6ExperimentSelectionMixin,
    GFDL_GCP_FileDataSourceBase
):
    """DataSource for accessing CMIP6 data stored on spinning disk at /uda/CMIP6.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _DirectoryRegex = cmip6.drs_directory_regex
    _AttributesClass = GFDL_UDA_CMIP6DataSourceAttributes
    _fetch_method = "cp"  # copy locally instead of symlink due to NFS hanging


@util.mdtf_dataclass
class GFDL_archive_CMIP6DataSourceAttributes(data_sources.CMIP6DataSourceAttributes):
    def __post_init__(self, log=_log, model=None, experiment=None):
        self.CASE_ROOT_DIR = os.sep + os.path.join('archive','pcmdi','repo','CMIP6')
        super(GFDL_archive_CMIP6DataSourceAttributes, self).__post_init__(log, model, experiment)

class Gfdlarchivecmip6DataManager(
    data_sources.CMIP6ExperimentSelectionMixin,
    GFDL_GCP_FileDataSourceBase
):
    """DataSource for accessing more extensive set of CMIP6 data on DMF tape-backed
    storage at /archive/pcmdi/repo/CMIP6.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _DirectoryRegex = cmip6.drs_directory_regex
    _AttributesClass = GFDL_archive_CMIP6DataSourceAttributes
    _fetch_method = "gcp"


@util.mdtf_dataclass
class GFDL_data_CMIP6DataSourceAttributes(data_sources.CMIP6DataSourceAttributes):
    def __post_init__(self, log=_log, model=None, experiment=None):
        self.CASE_ROOT_DIR = os.sep + os.path.join('data_cmip6', 'CMIP6')
        super(GFDL_data_CMIP6DataSourceAttributes, self).__post_init__(log, model, experiment)

class Gfdldatacmip6DataManager(
    data_sources.CMIP6ExperimentSelectionMixin,
    GFDL_GCP_FileDataSourceBase
):
    """DataSource for accessing pre-publication CMIP6 data on /data_cmip6.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _DirectoryRegex = cmip6.drs_directory_regex
    _AttributesClass = GFDL_data_CMIP6DataSourceAttributes
    _fetch_method = "gcp"

# RegexPattern that matches any string (path) that doesn't end with ".nc".
_ignore_non_nc_regex = util.RegexPattern(r".*(?<!\.nc)")
# match files ending in .nc only if they aren't of the form .tile#.nc
# (negative lookback)
_ignore_tiles_regex = util.RegexPattern(r".*\.tile\d\.nc$")
# match any paths corresponding to time average data (/av/), since currently
# we only deal with timeseries data (/ts/)
_ignore_time_avg_regex = util.RegexPattern(r"/?([a-zA-Z0-9_-]+)/av/\S*")
# RegexPattern matching any of the above -- description of files that are OK
# to silently ignore during /pp/ directory crawl
pp_ignore_regex = util.ChainedRegexPattern(
    _ignore_time_avg_regex, _ignore_tiles_regex, _ignore_non_nc_regex
)

# can't combine these with the path regexes (below) since static dir regex should
# only be used with static files
_pp_dir_regex = util.RegexPattern(r"""
        /?                      # maybe initial separator
        (?P<component>[a-zA-Z0-9_-]+)/     # component name
        ts/                     # timeseries;
        (?P<frequency>\w+)/     # ts freq
        (?P<chunk_freq>\w+)     # data chunk length
    """
)
_pp_static_dir_regex = util.RegexPattern(r"""
        /?                      # maybe initial separator
        (?P<component>[a-zA-Z0-9_-]+)     # component name
    """,
                                         defaults={
                                             'frequency': util.FXDateFrequency,
                                             'chunk_freq': util.FXDateFrequency
                                         }
)
pp_dir_regex = util.ChainedRegexPattern(
    # try the first regex, and if no match, try second
    _pp_dir_regex, _pp_static_dir_regex
)

_pp_ts_regex = util.RegexPattern(r"""
        /?                      # maybe initial separator
        (?P<component>[a-zA-Z0-9_-]+)/     # component name
        ts/                     # timeseries;
        (?P<frequency>\w+)/     # ts freq
        (?P<chunk_freq>\w+)/    # data chunk length
        (?P=component)\.        # component name (again)
        (?P<start_date>\d+)-(?P<end_date>\d+)\.   # file's date range
        (?P<variable>[a-zA-Z0-9_-]+)\.       # field name
        nc                      # netCDF file extension
    """
                                 )
_pp_static_regex = util.RegexPattern(r"""
        /?                      # maybe initial separator
        (?P<component>[a-zA-Z0-9_-]+)/     # component name
        (?P=component)     # component name (again)
        \.static\.nc             # static frequency, netCDF file extension
    """,
                                     defaults={
                                         'variable': 'static',
                                         'start_date': util.FXDateMin, 'end_date': util.FXDateMax,
                                         'frequency': util.FXDateFrequency, 'chunk_freq': util.FXDateFrequency
                                     }
                                     )
pp_path_regex = util.ChainedRegexPattern(
    # try the first regex, and if no match, try second
    _pp_ts_regex, _pp_static_regex,
    input_field="remote_path",
    match_error_filter=pp_ignore_regex
)


@util.regex_dataclass(pp_path_regex)
class PPTimeseriesDataFile():
    """Dataclass describing catalog entries for /pp/ directory timeseries data.
    """
    component: str = ""
    frequency: util.DateFrequency = None
    chunk_freq: util.DateFrequency = None
    start_date: util.Date = None
    end_date: util.Date = None
    variable: str = ""
    remote_path: str = util.MANDATORY
    date_range: util.DateRange = dataclasses.field(init=False)

    def __post_init__(self, *args):
        if isinstance(self.frequency, str):
            self.frequency = util.DateFrequency(self.frequency)
        if self.start_date == util.FXDateMin \
            and self.end_date == util.FXDateMax:
            # Assume we're dealing with static/fx-frequency data, so use special
            # placeholder values
            self.date_range = util.FXDateRange
            if not self.frequency.is_static:
                raise util.DataclassParseError(("Inconsistent filename parse: "
                    f"cannot determine if '{self.remote_path}' represents static data."))
        else:
            self.date_range = util.DateRange(self.start_date, self.end_date)
            if self.frequency.is_static:
                raise util.DataclassParseError(("Inconsistent filename parse: "
                                                f"cannot determine if '{self.remote_path}' represents static data."))


@util.mdtf_dataclass
class PPDataSourceAttributes(data_manager.DataSourceAttributesBase):
    """Data-source-specific attributes for the DataSource corresponding to
    model data in the /pp/ directory hierarchy.
    """
    # CASENAME: str          # fields inherited from dm.DataSourceAttributesBase
    # FIRSTYR: str
    # LASTYR: str
    # date_range: util.DateRange
    # CASE_ROOT_DIR: str
    # convention: str

    convention: str = "GFDL"
    CASE_ROOT_DIR: str = ""
    component: str = ""
    # chunk_freq: util.DateFrequency = None # THIS IS THE PROBLEM LINE FOPR THE GFDL SITE BUILD!!!

    #  This method overrides dataclass.mdtf_dataclass._old_post_init.
    # _old_post_init has the parms *args, and **kwargs. Excluding these parms
    # from the super().__post_init__() call, therefore, caused an error that 1
    # positional argument (self) was specified, but 2 were given during the self.atts definition
    # in data_manager.DataSourceBase.__init__()
    # I resolved the problem (I think) using the example here:
    # https://stackoverflow.com/questions/66995998/how-can-i-take-the-variable-from-the-parent-class-constructor-and-use-it-in-the
    # after another post stated that an error like this could be caused by class override issues.
    def __post_init__(self, *args, **kwargs):
        """Validate user input.
        """
        super(PPDataSourceAttributes, self).__post_init__(*args, **kwargs)
        config = core.ConfigManager()


gfdlppDataManager_any_components_col_spec = data_manager.DataframeQueryColumnSpec(
    # Catalog columns whose values must be the same for all variables.
    expt_cols=data_manager.DataFrameQueryColumnGroup([]),
    pod_expt_cols=data_manager.DataFrameQueryColumnGroup([]),
    var_expt_cols=data_manager.DataFrameQueryColumnGroup(['chunk_freq', 'component']),
    daterange_col="date_range"
)

gfdlppDataManager_same_components_col_spec = data_manager.DataframeQueryColumnSpec(
    # Catalog columns whose values must be the same for all variables.
    expt_cols=data_manager.DataFrameQueryColumnGroup([]),
    pod_expt_cols=data_manager.DataFrameQueryColumnGroup(['component']),
    var_expt_cols=data_manager.DataFrameQueryColumnGroup(['chunk_freq']),
    daterange_col="date_range"
)


class GfdlppDataManager(GFDL_GCP_FileDataSourceBase):
    # extends GFDL_GCP_FileDataSourceBase
    _FileRegexClass = PPTimeseriesDataFile
    _DirectoryRegex = pp_dir_regex
    _AttributesClass = PPDataSourceAttributes


    # map "name" field in VarlistEntry's query_attrs() to "variable" field of
    # PPTimeseriesDataFile
    _query_attrs_synonyms = {'name': 'variable'}

    def __init__(self, case_dict, parent):
        super(GfdlppDataManager, self).__init__(case_dict, parent)
        # default behavior when run interactively:
        # frepp_mode = False, any_components = True
        # default behavior when invoked by FRE wrapper:
        # frepp_mode = True (set to False by calling wrapper with --run_once)
        # any_components = True (set to False with --component_only)
        config = core.ConfigManager()
        self.frepp_mode = config.get('frepp', False)
        self.any_components = config.get('any_components', False)


    def query_associated_files(self, d_key):
        """Infers static file from variable's component and assigns data key
        to the associated_files property"""
        df = self.df
        component = df.iloc[[d_key.value[0]]]["component"].values[0]
        group = df.loc[(df["component"] == component) & (df["variable"] == "static")]
        if len(group) == 1:
            result = self.data_key(group, expt_key=d_key.expt_key)
        else:
            result = None
        return result

    @property
    def var_expt_key_cols(self):
        """Catalog columns whose values must "be the same for each variable", ie
        are irrelevant but must be constrained to a unique value.
        """
        # if we aren't restricted to one component, use all components regardless
        # of frepp_mode. This is the default behavior when called from the FRE
        # wrapper.
        if self.any_components:
            return 'chunk_freq', 'component'
        else:
            return 'chunk_freq'

    # these have to be supersets of their *_key_cols counterparts; for this use
    # case they're all just the same set of attributes.
    @property
    def expt_cols(self): return self.expt_key_cols

    @property
    def pod_expt_cols(self): return self.pod_expt_key_cols

    @property
    def var_expt_cols(self): return self.var_expt_key_cols

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'CASE_ROOT_DIR'))
        return self.attrs.CASE_ROOT_DIR

    def _filter_column(self, df, col_name, func, obj_name, preferred=None):
        values = list(df[col_name].drop_duplicates())
        if len(values) <= 1:
            # unique value, no need to filter
            return df
        args = {"preferred": preferred} if preferred is not None else {}
        filter_val = func(values, **args)
        self.log.debug("Selected experiment attribute %s='%s' for %s (out of %s).",
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
        variables.
        """
        # no-op since no attributes in this category
        return df

    def resolve_pod_expt(self, df, obj):
        """Disambiguate experiment attributes that must be the same for all
        variables for each POD:

        - Select the model component name according to the following heuristics:
            i) select component names containing 'cmip' (case-insensitive). ii)
            if that selects multiple components, break the tie by selecting the
            component with the fewest words (separated by '_'), or, failing that,
            the shortest overall name.
        """
        def _heuristic_tiebreaker(str_list, preferred=None):
            """Internal function to resolve multiple possible attributes"""

            def _heuristic_tiebreaker_sub(strs):
                """sub-function to selected the shortest attribute"""
                min_len = min(len(s.split('_')) for s in strs)
                strs2 = [s for s in strs if (len(s.split('_')) == min_len)]
                if len(strs2) == 1:
                    return strs2[0]
                else:
                    return min(strs2, key=len)

            # filter by the preferred list if provided
            if preferred is not None:
                assert isinstance(preferred, list)
                str_list = [x for x in preferred if x in str_list]

                # select the first matching value from the preferred list
                if len(str_list) >= 1:
                    str_list = [str_list[0]]

            # determine if any of the attributes contain the text `cmip`
            cmip_list = [s for s in str_list if ('cmip' in s.lower())]

            # give preference to attributes that contain the substring `cmip`
            if cmip_list:
                return _heuristic_tiebreaker_sub(cmip_list)

            # otherwise, select the shortest attribute
            else:
                return _heuristic_tiebreaker_sub(str_list)

        if 'component' in self.col_spec.pod_expt_cols.cols:

            # loop over pods and get the preferred components
            preferred = []
            for pod in self.pods.values():
                for var in pod.varlist.vars:
                    _component = var.component
                    if len(_component) > 0:
                        _component = str(_component).split(",")
                        preferred = preferred + _component

            # find the intersection of preferred components
            if len(preferred) > 0:
                # preserves preference order
                preferred = list(dict.fromkeys(preferred))
            else:
                preferred = None

            # filter the dataframe of possible components
            df = self._filter_column(df, 'expt_key', _heuristic_tiebreaker, obj.name, preferred=preferred)

        # otherwise no-op
        return df

    def resolve_var_expt(self, df, obj):
        """Disambiguate arbitrary experiment attributes on a per-variable basis:

        - Take the shortest chunk_frequency, to minimize transferring data that's
            outside of the query date range.
        """
        df = self._filter_column_min(df, obj.name, 'chunk_freq')

        # if a preferred component is specified, select it at the var level
        if 'component' in self.col_spec.var_expt_cols.cols:
            col_name = 'component'
            if obj.component is not None:
                preferred = obj.component.split(",")
                for comp in preferred:
                    _df = df[df["component"] == comp]
                    if len(_df) > 0:
                        df = _df
                        break

            # select the first entry
            df = df.sort_values(col_name).iloc[[0]]

            self.log.debug("Selected experiment attribute '%s'='%s' for %s.",
                           col_name, df[col_name].iloc[0], obj.name)

        return df


class GfdlAutoDataManager(object):
    """Wrapper for dispatching DataManager based on user input. If CASE_ROOT_DIR
    ends in "pp", use :class:`GfdlppDataManager`, otherwise use CMIP6 data on
    /uda via :class:`Gfdludacmip6DataManager`.
    """
    # Note, object is explicitly defined as a parameter for Python 2/3
    # compatibility reasons; omitting object in Python2 yields "old-style" classes
    # All classes are "new-style" in Python3 by default.
    # TODO: Since WE DO NOT SUPPORT PYTHON2, remove object parm and verify that it doesn't destroy everything
    def __new__(cls, case_dict, parent, *args, **kwargs):
        """Dispatch DataManager instance creation based on the contents of
        case_dict."""
        config = core.ConfigManager()
        dir_ = case_dict.get('CASE_ROOT_DIR', config.CASE_ROOT_DIR)
        if 'pp' in os.path.basename(os.path.normpath(dir_)):
            dispatched_cls = GfdlppDataManager
        else:
            dispatched_cls = Gfdludacmip6DataManager
            # could use more careful logic here, but for now assume CMIP6 on
            # /uda as a fallback

        _log.debug("%s: Dispatched DataManager to %s.",
                   cls.__name__, dispatched_cls.__name__)
        obj = dispatched_cls.__new__(dispatched_cls)
        obj.__init__(case_dict, parent)
        return obj

    def __init__(self, *args, **kwargs):
        pass

class GfdlcondaEnvironmentManager(environment_manager.CondaEnvironmentManager):
    # Use miniconda3 in the mdtf role account
    def _call_conda_create(self, env_name):
        raise Exception(("Trying to create conda env {} "
            "in read-only mdtf role account.").format(env_name)
        )

# ------------------------------------------------------------------------


