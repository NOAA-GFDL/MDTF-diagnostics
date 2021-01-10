"""Code specific to the computing environment at NOAA's Geophysical Fluid 
Dynamics Laboratory (Princeton, NJ, USA).
"""
import os
import io
import dataclasses
import shutil
import tempfile
from src import (util, core, datelabel, diagnostic, data_manager, 
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

    def parse_env_vars(self, cli_obj):
        super(GFDLMDTFFramework, self).parse_env_vars(cli_obj)
        # set temp directory according to where we're running
        if gfdl_util.running_on_PPAN():
            gfdl_tmp_dir = cli_obj.config.get('GFDL_PPAN_TEMP', '$TMPDIR')
        else:
            gfdl_tmp_dir = cli_obj.config.get('GFDL_WS_TEMP', '$TMPDIR')
        gfdl_tmp_dir = util.resolve_path(
            gfdl_tmp_dir, root_path=self.code_root, env=self.global_env_vars
        )
        if not os.path.isdir(gfdl_tmp_dir):
            gfdl_util.make_remote_dir(gfdl_tmp_dir)
        tempfile.tempdir = gfdl_tmp_dir
        os.environ['MDTF_TMPDIR'] = gfdl_tmp_dir
        self.global_env_vars['MDTF_TMPDIR'] = gfdl_tmp_dir

    def _post_parse_hook(self, cli_obj, config, paths):
        ### call parent class method
        super(GFDLMDTFFramework, self)._post_parse_hook(cli_obj, config, paths)

        self.reset_case_pod_list(cli_obj, config, paths)
        self.dry_run = config.get('dry_run', False)
        self.timeout = config.get('file_transfer_timeout', 0)
        # copy obs data from site install
        gfdl_util.fetch_obs_data(
            paths.OBS_DATA_REMOTE, paths.OBS_DATA_ROOT,
            timeout=self.timeout, dry_run=self.dry_run
        )

    def reset_case_pod_list(self, cli_obj, config, paths):
        if self.frepp_mode:
            for case in self.case_list:
                # frepp mode:only attempt PODs other instances haven't already done
                case_outdir = paths.modelPaths(case, overwrite=True)
                case_outdir = case_outdir.MODEL_OUT_DIR
                pod_list = case['pod_list']
                for p in pod_list:
                    if os.path.isdir(os.path.join(case_outdir, p)):
                        _log.info(("\tPreexisting {} in {}; "
                            "skipping b/c frepp mode").format(p, case_outdir))
                case['pod_list'] = [p for p in pod_list if not \
                    os.path.isdir(os.path.join(case_outdir, p))
                ]

    def verify_paths(self, config, p):
        keep_temp = config.get('keep_temp', False)
        # clean out WORKING_DIR if we're not keeping temp files:
        if os.path.exists(p.WORKING_DIR) and not \
            (keep_temp or p.WORKING_DIR == p.OUTPUT_DIR):
            shutil.rmtree(p.WORKING_DIR)
        util.check_dirs(p.CODE_ROOT, p.OBS_DATA_REMOTE, create=False)
        util.check_dirs(p.MODEL_DATA_ROOT, p.OBS_DATA_ROOT, p.WORKING_DIR, 
            create=True)
        # Use GCP to create OUTPUT_DIR on a volume that may be read-only
        if not os.path.exists(p.OUTPUT_DIR):
            gfdl_util.make_remote_dir(p.OUTPUT_DIR, self.timeout, self.dry_run)


# ====================================================================

@util.mdtf_dataclass
class GfdlDiagnostic(diagnostic.Diagnostic):
    """Wrapper for Diagnostic that adds writing a placeholder directory 
    (POD_OUT_DIR) to the output as a lockfile if we're running in frepp 
    cooperative mode.
    """
    # extra dataclass fields
    _has_placeholder: bool = False

    def pre_run_setup(self):
        """Extra code only applicable in frepp cooperative mode. If this code is 
        called, all the POD's model data has been generated. Write a placeholder
        directory to POD_OUT_DIR, so if frepp invokes the MDTF package again 
        while we're running, only our results will be written to the overall 
        output.
        """
        super(GfdlDiagnostic, self).pre_run_setup()

        config = core.ConfigManager()
        frepp_mode = config.get('frepp', False)
        if frepp_mode and not os.path.exists(self.POD_OUT_DIR):
            try:
                gfdl_util.make_remote_dir(self.POD_OUT_DIR)
                self._has_placeholder = True
            except Exception as exc:
                try:
                    raise util.PodRuntimeError((f"Caught exception making output "
                        f"directory at {self.POD_OUT_DIR}."), self) from exc
                except Exception as chained_exc:
                    self.exceptions.log(chained_exc)    

# ------------------------------------------------------------------------

def GfdlautoDataManager(case_dict):
    """Wrapper for dispatching DataManager based on inputs.
    """
    test_root = case_dict.get('CASE_ROOT_DIR', None)
    if not test_root:
        return GFDL_UDA_CMIP6DataSourceAttributes(case_dict)
    test_root = os.path.normpath(test_root)
    if 'pp' in os.path.basename(test_root):
        return GfdlppDataManager(case_dict)
    else:
        _log.critical(("ERROR: Couldn't determine data fetch method from input."
            "Please set '--data_manager GFDL_pp', 'GFDL_UDA_CMP6', or "
            "'GFDL_data_cmip6', depending on the source you want."))
        exit(1)

class GCPFetchMixin(data_manager.AbstractFetchMixin):
    """Mixin implementing data fetch for netcdf files on filesystems accessible
    from GFDL via GCP. Remote files are copies to a local temp directory. dmgets
    are issued for remote files on tape filesystems.
    """
    def setup_fetch(self):
        modMgr = gfdl_util.ModuleManager()
        modMgr.load('gcp')

    @property
    def tape_filesystem(self):
        return gfdl_util.is_on_tape_filesystem(self.attrs.MODEL_DATA_ROOT)

    def pre_fetch_hook(self, vars_to_fetch):
        """Issue dmget for all files we're about to fetch, if those files are
        on a tape filesystem.
        """
        if self.tape_filesystem:
            paths = set([])
            for var in vars_to_fetch:
                for data_key in self.iter_data_keys(var):
                    paths.update(self.remote_data(data_key))

            _log.info(f"Start dmget of {len(paths)} files.")
            util.run_command(['dmget','-t','-v'] + list(paths),
                timeout= len(paths) * self.file_transfer_timeout,
                dry_run=self.dry_run
            ) 
            _log.info("Successful exit of dmget.")

    def _get_fetch_method(self, method='auto'):
        _methods = {
            'gcp': {'command': ['gcp', '--sync', '-v', '-cd'], 'site':'gfdl:'},
            'cp':  {'command': ['cp'], 'site':''},
            'ln':  {'command': ['ln', '-fs'], 'site':''}
        }
        if method not in _methods:
            if self.tape_filesystem:
                method = 'gcp' # use GCP for DMF filesystems
            else:
                method = 'ln' # symlink for local files
        _log.debug("Selected fetch method '%s'.", method)
        return (_methods[method]['command'], _methods[method]['site'])

    def fetch_dataset(self, var, paths):
        """Copy files to temporary directory.
        (GCP can't copy to home dir, so always copy to a temp dir)
        """
        tmpdir = core.TempDirManager().make_tempdir()
        _log.debug("Created GCP fetch temp dir at %s.", tmpdir)
        (cp_command, smartsite) = self._get_fetch_method(self.fetch_method)
        if not util.is_iterable(paths):
            paths = (paths, )

        local_paths = []
        for path in paths:
            # exceptions caught in parent loop in data_manager.DataSourceBase
            local_path = os.path.join(tmpdir, os.path.basename(path))
            _log.info(f"\tFetching {path[len(self.attrs.MODEL_DATA_ROOT):]}")
            util.run_command(cp_command + [
                smartsite + path, 
                # gcp requires trailing slash, ln ignores it
                smartsite + tmpdir + os.sep
            ], 
                timeout=self.file_transfer_timeout, 
                dry_run=self.dry_run
            )
            local_paths.append(local_path)
        return local_paths


class GFDL_GCP_FileDataSourceBase(
    data_manager.OnTheFlyDirectoryHierarchyQueryMixin, 
    GCPFetchMixin, 
    data_manager.DataframeQueryDataSourceBase
):
    """Base class for DataSources that access data on GFDL's internal filesystems
    using GCP, and which may be invoked via frepp.
    """
    _DiagnosticClass = GfdlDiagnostic
    _PreprocessorClass = preprocessor.MDTFDataPreprocessor

    _FileRegexClass = util.abstract_attribute()
    _DirectoryRegex = util.abstract_attribute()
    _AttributesClass = util.abstract_attribute()

    def __init__(self, case_dict):
        self.catalog = None
        super(GFDL_GCP_FileDataSourceBase, self).__init__(case_dict)

        config = core.ConfigManager()
        self.fetch_method = 'auto'
        self.frepp_mode = config.get('frepp', False)
        self.dry_run = config.get('dry_run', False)
        self.file_transfer_timeout = config.get('file_transfer_timeout', 0)

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

@util.mdtf_dataclass
class GFDL_UDA_CMIP6DataSourceAttributes(data_manager.CMIP6DataSourceAttributes):
    def __post_init__(self, model=None, experiment=None):
        self.MODEL_DATA_ROOT = os.sep + os.path.join('uda', 'CMIP6')
        super(GFDL_UDA_CMIP6DataSourceAttributes, self).__post_init__(model, experiment)

class Gfdludacmip6DataManager(
    data_manager.CMIP6ExperimentSelectionMixin, 
    GFDL_GCP_FileDataSourceBase
):
    """DataSource for accessing CMIP6 data stored on spinning disk at /uda/CMIP6.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _DirectoryRegex = cmip6.drs_directory_regex
    _AttributesClass = GFDL_UDA_CMIP6DataSourceAttributes


@util.mdtf_dataclass
class GFDL_archive_CMIP6DataSourceAttributes(data_manager.CMIP6DataSourceAttributes):
    def __post_init__(self, model=None, experiment=None):
        self.MODEL_DATA_ROOT = os.sep + os.path.join('archive','pcmdi','repo','CMIP6')
        super(GFDL_archive_CMIP6DataSourceAttributes, self).__post_init__(model, experiment)

class Gfdlarchivecmip6DataManager(
    data_manager.CMIP6ExperimentSelectionMixin, 
    GFDL_GCP_FileDataSourceBase
):
    """DataSource for accessing more extensive set of CMIP6 data on DMF tape-backed
    storage at /archive/pcmdi/repo/CMIP6.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _DirectoryRegex = cmip6.drs_directory_regex
    _AttributesClass = GFDL_archive_CMIP6DataSourceAttributes


@util.mdtf_dataclass
class GFDL_data_CMIP6DataSourceAttributes(data_manager.CMIP6DataSourceAttributes):
    def __post_init__(self, model=None, experiment=None):
        self.MODEL_DATA_ROOT = os.sep + os.path.join('data_cmip6', 'CMIP6')
        super(GFDL_data_CMIP6DataSourceAttributes, self).__post_init__(model, experiment)

class Gfdldatacmip6DataManager(
    data_manager.CMIP6ExperimentSelectionMixin, 
    GFDL_GCP_FileDataSourceBase
):
    """DataSource for accessing pre-publication CMIP6 data on /data_cmip6.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _DirectoryRegex = cmip6.drs_directory_regex
    _AttributesClass = GFDL_data_CMIP6DataSourceAttributes

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
        'frequency': datelabel.FXDateFrequency, 'chunk_freq': datelabel.FXDateFrequency
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
        'start_date': datelabel.FXDateMin, 'end_date': datelabel.FXDateMax,
        'frequency': datelabel.FXDateFrequency, 'chunk_freq': datelabel.FXDateFrequency
    }
)
pp_path_regex = util.ChainedRegexPattern(
    # try the first regex, and if no match, try second
    _pp_ts_regex, _pp_static_regex,
    input_field="remote_path",
    match_error_filter=pp_ignore_regex
)
@util.regex_dataclass(pp_path_regex)
@util.mdtf_dataclass
class PPTimeseriesDataFile():
    """Dataclass describing catalog entries for /pp/ directory timeseries data.
    """
    component: str = ""
    frequency: datelabel.DateFrequency = None
    chunk_freq: datelabel.DateFrequency = None
    start_date: datelabel.Date = None
    end_date: datelabel.Date = None
    variable: str = ""
    remote_path: str = util.MANDATORY
    date_range: datelabel.DateRange = dataclasses.field(init=False)

    def __post_init__(self, *args):
        if isinstance(self.frequency, str):
            self.frequency = datelabel.DateFrequency(self.frequency)
        if self.start_date == datelabel.FXDateMin \
            and self.end_date == datelabel.FXDateMax:
            # Assume we're dealing with static/fx-frequency data, so use special 
            # placeholder values
            self.date_range = datelabel.FXDateRange
            if not self.frequency.is_static:
                raise util.DataclassParseError(("Inconsistent filename parse: "
                    f"cannot determine if '{self.remote_path}' represents static data."))
        else:
            self.date_range = datelabel.DateRange(self.start_date, self.end_date)
            if self.frequency.is_static:
                raise util.DataclassParseError(("Inconsistent filename parse: "
                    f"cannot determine if '{self.remote_path}' represents static data."))

@util.mdtf_dataclass
class PPDataSourceAttributes(data_manager.DataSourceAttributesBase):
    """Data-source-specific attributes for the DataSource corresponding to 
    model data in the /pp/ directory hierarchy.
    """
    MODEL_DATA_ROOT: str = ""

    def __post_init__(self):
        """Validate user input.
        """
        super(PPDataSourceAttributes, self).__post_init__()
        config = core.ConfigManager()
        # set MODEL_DATA_ROOT
        if not self.MODEL_DATA_ROOT and config.CASE_ROOT_DIR:
            _log.debug(
                "MODEL_DATA_ROOT not supplied, using CASE_ROOT_DIR = '%s'.",
                config.CASE_ROOT_DIR
            )
            self.MODEL_DATA_ROOT = config.CASE_ROOT_DIR
        # verify model data root dir exists
        if not os.path.isdir(self.MODEL_DATA_ROOT):
            _log.critical("Data directory MODEL_DATA_ROOT = '%s' not found.",
                self.MODEL_DATA_ROOT)
            exit(1)

class GfdlppDataManager(GFDL_GCP_FileDataSourceBase):
    _FileRegexClass = PPTimeseriesDataFile
    _DirectoryRegex = pp_dir_regex
    _AttributesClass = PPDataSourceAttributes

    # map "name" field in VarlistEntry's query_attrs() to "variable" field here
    _query_attrs_synonyms = {'name': 'variable'}

    daterange_col = "date_range"
    # Catalog columns whose values must be the same for all variables.
    expt_cols = tuple()
    # Catalog columns whose values must be the same for each POD.
    pod_expt_cols = ('component', )
    # Catalog columns whose values must "be the same for each variable", ie are 
    # irrelevant but must be constrained to a unique value.
    var_expt_cols = ("chunk_freq", )

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'MODEL_DATA_ROOT'))
        return self.attrs.MODEL_DATA_ROOT

    @staticmethod
    def _filter_column(df, col_name, func, obj_name):
        values = list(df[col_name].drop_duplicates())
        if len(values) <= 1:
            # unique value, no need to filter
            return df
        filter_val = func(values)
        _log.debug("Selected experiment attribute %s='%s' for %s (out of %s).", 
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
        def _heuristic_tiebreaker(str_list):
            def _heuristic_tiebreaker_sub(strs):
                min_len = min(len(s.split('_')) for s in strs)
                strs2 = [s for s in strs if (len(s.split('_')) == min_len)]
                if len(strs2) == 1:
                    return strs2[0]
                else:
                    return min(strs2, key=len)

            cmip_list = [s for s in str_list if ('cmip' in s.lower())]
            if cmip_list:
                return _heuristic_tiebreaker_sub(cmip_list)
            else:
                return _heuristic_tiebreaker_sub(str_list)

        df = self._filter_column(df, 'component', _heuristic_tiebreaker, obj.name)
        return df

    def resolve_var_expt(self, df, obj):
        """Disambiguate arbitrary experiment attributes on a per-variable basis:
 
        - Take the shortest chunk_frequency, to minimize transferring data that's
            outside of the query date range.
        """
        df = self._filter_column_min(df, obj.name, 'chunk_freq')
        return df

# ------------------------------------------------------------------------

class GfdlvirtualenvEnvironmentManager(
    environment_manager.VirtualenvEnvironmentManager
    ):
    # Use module files to switch execution environments, as defined on 
    # GFDL workstations and PP/AN cluster.

    def __init__(self):
        _ = gfdl_util.ModuleManager()
        super(GfdlvirtualenvEnvironmentManager, self).__init__()

    # manual-coded logic like this is not scalable
    def set_pod_env(self, pod):
        langs = [s.lower() for s in pod.runtime_requirements]
        if pod.name == 'convective_transition_diag':
            pod.env = 'py_convective_transition_diag'
        elif pod.name == 'MJO_suite':
            pod.env = 'ncl_MJO_suite'
        elif ('r' in langs) or ('rscript' in langs):
            pod.env = 'r_default'
        elif 'ncl' in langs:
            pod.env = 'ncl'
        else:
            pod.env = 'py_default'

    # this is totally not scalable
    _module_lookup = {
        'ncl': ['ncl'],
        'r_default': ['r'],
        'py_default': ['python'],
        'py_convective_transition_diag': ['python', 'ncl'],
        'ncl_MJO_suite': ['python', 'ncl']
    }

    def create_environment(self, env_name):
        modMgr = gfdl_util.ModuleManager()
        modMgr.load(self._module_lookup[env_name])
        super(GfdlvirtualenvEnvironmentManager, \
            self).create_environment(env_name)

    def activate_env_commands(self, env_name):
        modMgr = gfdl_util.ModuleManager()
        mod_list = modMgr.load_commands(self._module_lookup[env_name])
        return ['source $MODULESHOME/init/bash'] \
            + mod_list \
            + super(GfdlvirtualenvEnvironmentManager, self).activate_env_commands(env_name)

    def deactivate_env_commands(self, env_name):
        modMgr = gfdl_util.ModuleManager()
        mod_list = modMgr.unload_commands(self._module_lookup[env_name])
        return super(GfdlvirtualenvEnvironmentManager, \
            self).deactivate_env_commands(env_name) + mod_list

    def tear_down(self):
        super(GfdlvirtualenvEnvironmentManager, self).tear_down()
        modMgr = gfdl_util.ModuleManager()
        modMgr.revert_state()

class GfdlcondaEnvironmentManager(environment_manager.CondaEnvironmentManager):
    # Use mdteam's anaconda2
    def _call_conda_create(self, env_name):
        raise Exception(("Trying to create conda env {} "
            "in read-only mdteam account.").format(env_name)
        )

# ------------------------------------------------------------------------

class GFDLHTMLPodOutputManager(output_manager.HTMLPodOutputManager):
    def __init__(self, pod, output_mgr):
        super(GFDLHTMLPodOutputManager, self).__init__(pod, output_mgr)
        self.frepp_mode = output_mgr.frepp_mode

    def make_output(self):
        """Only run output steps (including logging error on index.html) 
        if POD ran on this invocation.
        """
        if not self.frepp_mode:
            super(GFDLHTMLPodOutputManager, self).make_output()
        elif self._pod._has_placeholder:
            _log.debug('POD %s has frepp placeholder, generating output.', 
                self._pod.name)
            super(GFDLHTMLPodOutputManager, self).make_output()
        else: 
            _log.debug('POD %s does not have frepp placeholder; not generating output.', 
                self._pod.name)

class GFDLHTMLOutputManager(output_manager.HTMLOutputManager):
    _PodOutputManagerClass = GFDLHTMLPodOutputManager

    def __init__(self, case):
        config = core.ConfigManager()
        try:
            self.frepp_mode = case.frepp_mode
            self.dry_run = config.get('dry_run', False)
            self.file_transfer_timeout = config.get('file_transfer_timeout', 0)
        except (AttributeError, KeyError) as exc:
            _log.exception(f"Caught {repr(exc)}.")

        super(GFDLHTMLOutputManager, self).__init__(case)

    def make_html(self, case, cleanup=False):
        """Never cleanup html if we're in frepp_mode, since framework may run 
        later when another component finishes. Instead just append current
        progress to CASE_TEMP_HTML.
        """
        prev_html = os.path.join(self.OUT_DIR, self._html_file_name)
        if self.frepp_mode and os.path.exists(prev_html):
            _log.debug("Found previous HTML at %s; appending.", self.OUT_DIR)
            with io.open(prev_html, 'r', encoding='utf-8') as f1:
                contents = f1.read()
            contents = contents.split('<!--CUT-->')
            assert len(contents) == 3
            contents = contents[1]

            if os.path.exists(self.CASE_TEMP_HTML):
                mode = 'a'
            else:
                _log.warning("No file at %s.", self.CASE_TEMP_HTML)
                mode = 'w'
            with io.open(self.CASE_TEMP_HTML, mode, encoding='utf-8') as f2:
                f2.write(contents)
        super(GFDLHTMLOutputManager, self).make_html(
            case, cleanup=(not self.frepp_mode)
        )

    @property
    def _tarball_file_path(self):
        paths = core.PathManager()
        assert hasattr(self, 'WK_DIR')
        file_name = self.WK_DIR + '.tar'
        return os.path.join(paths.WORKING_DIR, file_name)

    def make_tar_file(self, case):
        """Make the tar file locally in WK_DIR and gcp to destination,
        since OUT_DIR might be mounted read-only.
        """
        paths = core.PathManager()
        out_path = super(GFDLHTMLOutputManager, self).make_tar_file(case)
        _, file_name = os.path.split(out_path)
        tar_dest_path = os.path.join(paths.OUTPUT_DIR, file_name)
        gfdl_util.gcp_wrapper(out_path, tar_dest_path)
        return tar_dest_path

    def copy_to_output(self, case):
        """Use gcp for transfer, since OUTPUT_DIR might be mounted read-only.
        Also has special logic to handle frepp_mode.
        """
        if self.WK_DIR == self.OUT_DIR:
            return # no copying needed
        if self.frepp_mode:
            # only copy PODs that ran, whether they succeeded or not
            for pod in case.pods.values():
                if pod._has_placeholder:
                    gfdl_util.gcp_wrapper(pod.POD_WK_DIR, pod.POD_OUT_DIR)
            # copy all case-level files
            _log.debug("Copying case-level files in %s", self.WK_DIR)
            for f in os.listdir(self.WK_DIR):
                if os.path.isfile(os.path.join(self.WK_DIR, f)):
                    _log.debug("Found case-level file %s", f)
                    gfdl_util.gcp_wrapper(
                        os.path.join(self.WK_DIR, f), self.OUT_DIR,
                    )
        else:
            # copy everything at once
            if os.path.exists(self.OUT_DIR):
                if self.overwrite:
                    try:
                        _log.error('%s exists, attempting to remove.', self.OUT_DIR)
                        shutil.rmtree(self.OUT_DIR)
                    except OSError:
                        # gcp will not overwrite dirs, so forced to save under
                        # a different name despite overwrite=True
                        _log.error(("Couldn't remove %s (probably mounted read"
                            "-only); will rename new directory."), self.OUT_DIR)
                else:
                    _log.error("%s exists; will rename new directory.", self.OUT_DIR)
            try:
                if os.path.exists(self.OUT_DIR):
                    # check again, since rmtree() might have succeeded
                    self.OUT_DIR, version = \
                        util.bump_version(self.OUT_DIR)
                    new_wkdir, _ = \
                        util.bump_version(self.WK_DIR, new_v=version)
                    _log.debug("Move %s to %s", self.WK_DIR, new_wkdir)
                    shutil.move(self.WK_DIR, new_wkdir)
                    self.WK_DIR = new_wkdir
                gfdl_util.gcp_wrapper(self.WK_DIR, self.OUT_DIR)
            except Exception:
                raise # only delete MODEL_WK_DIR if copied successfully
            _log.debug('Transfer succeeded; deleting directory %s', self.WK_DIR)
            shutil.rmtree(self.WK_DIR)
