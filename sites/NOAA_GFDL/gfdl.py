"""Code specific to the computing environment at NOAA's Geophysical Fluid 
Dynamics Laboratory (Princeton, NJ, USA).
"""
import os
import io
import abc
import collections
import operator as op
import re
import shutil
import subprocess
import typing
from src import (util, core, datelabel, diagnostic, data_manager, 
    preprocessor, environment_manager, output_manager)
from sites.NOAA_GFDL import gfdl_util
import src.conflict_resolution as choose

import logging
_log = logging.getLogger(__name__)

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

        if not self._has_placeholder:
            config = core.ConfigManager()
            try:
                gfdl_util.make_remote_dir(self.POD_OUT_DIR)
                self._has_placeholder = True
            except Exception as exc:
                try:
                    raise util.PodRuntimeError(self, (f"Caught exception "
                        f"making output directory at {self.POD_OUT_DIR}.")) from exc
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
        return gfdl_util.is_on_tape_filesystem(self.MODEL_DATA_ROOT)

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
        tmpdirs = core.TempDirManager()
        # assign temp directory by case/DataSource attributes
        tmpdir = tmpdirs.make_tempdir(hash_obj = self.attrs)
        _log.debug("Created GCP fetch temp dir at %s.", tmpdir)
        (cp_command, smartsite) = self._get_fetch_method(self.fetch_method)
        if not util.is_iterable(paths):
            paths = (paths, )

        for path in paths:
            # exceptions caught in parent loop in data_manager.DataSourceBase
            local_path = os.path.join(tmpdir, os.path.basename(path))
            _log.info(f"\tfetching {path[len(self.MODEL_DATA_ROOT):]}")
            util.run_command(cp_command + [
                smartsite + path, 
                # gcp requires trailing slash, ln ignores it
                smartsite + tmpdir + os.sep
            ], 
                timeout=self.file_transfer_timeout, 
                dry_run=self.dry_run
            )
            var.local_data.append(local_path)

class GFDLCMIP6LocalFileDataSource(
    data_manager.OnTheFlyDirectoryHierarchyQueryMixin, 
    GCPFetchMixin, 
    data_manager.DataframeQueryDataSource
):
    _FileRegexClass = data_manager.CMIP6DataSourceFile
    _AttributesClass = data_manager.CMIP6DataSourceAttributes
    _DiagnosticClass = GfdlDiagnostic
    _PreprocessorClass = preprocessor.MDTFDataPreprocessor

    # following column groups the same as in data_manager.CMIP6LocalFileDataSource

    daterange_col = "date_range"
    # Catalog columns whose values must be the same for all variables.
    expt_cols = (
        "activity_id", "institution_id", "source_id", "experiment_id",
        "variant_label", "version_date",
        # derived columns
        "region", "spatial_avg", 'realization_index', 'initialization_index', 
        'physics_index', 'forcing_index'
    )
    # Catalog columns whose values must be the same for each POD.
    pod_expt_cols = ('grid_label',
        # derived columns
        'regrid', 'grid_number'
    )
    # Catalog columns whose values must "be the same for each variable", ie are 
    # irrelevant but must be constrained to a unique value.
    var_expt_cols = ("table_id", )

    def __init__(self, case_dict):
        self.catalog = None
        super(GFDLCMIP6LocalFileDataSource, self).__init__(case_dict)

        config = core.ConfigManager()
        self.fetch_method = 'auto'
        self.frepp_mode = config.get('frepp', False)
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
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'CATALOG_DIR'))
        return self.attrs.CATALOG_DIR

@util.mdtf_dataclass
class GFDL_UDA_CMIP6DataSourceAttributes(data_manager.CMIP6DataSourceAttributes):
    def __post_init__(self, model=None, experiment=None):
        self.MODEL_DATA_ROOT = os.sep + os.path.join('uda', 'CMIP6')
        super(GFDL_UDA_CMIP6DataSourceAttributes, self).__post_init__(model, experiment)

class Gfdludacmip6DataManager(GFDLCMIP6LocalFileDataSource):
    _AttributesClass = GFDL_UDA_CMIP6DataSourceAttributes

@util.mdtf_dataclass
class GFDL_data_CMIP6DataSourceAttributes(data_manager.CMIP6DataSourceAttributes):
    def __post_init__(self, model=None, experiment=None):
        # Kris says /data_cmip6 used to stage pre-publication data, so shouldn't
        # be used as a data source unless explicitly requested by user
        self.MODEL_DATA_ROOT = os.sep + os.path.join('data_cmip6', 'CMIP6')
        super(GFDL_data_CMIP6DataSourceAttributes, self).__post_init__(model, experiment)

class Gfdldatacmip6DataManager(GFDLCMIP6LocalFileDataSource):
    _AttributesClass = GFDL_data_CMIP6DataSourceAttributes


_pp_ts_regex = re.compile(r"""
        /?                      # maybe initial separator
        (?P<component>\w+)/     # component name
        ts/                     # timeseries;
        (?P<frequency>\w+)/     # ts freq
        (?P<chunk_freq>\w+)/    # data chunk length   
        (?P<component2>\w+)\.        # component name (again)
        (?P<start_date>\d+)-(?P<end_date>\d+)\.   # file's date range
        (?P<name_in_model>\w+)\.       # field name
        nc                      # netCDF file extension
    """, re.VERBOSE)
_pp_static_regex = re.compile(r"""
        /?                      # maybe initial separator
        (?P<component>\w+)/     # component name 
        (?P<component2>\w+)     # component name (again)
        \.static\.nc             # static frequency, netCDF file extension                
    """, re.VERBOSE)

class GfdlppDataManager(
    data_manager.OnTheFlyDirectoryHierarchyQueryMixin, 
    GCPFetchMixin, 
    data_manager.DataframeQueryDataSource
):
    _FileRegexClass = NotImplementedError()
    _AttributesClass = NotImplementedError()
    _DiagnosticClass = GfdlDiagnostic
    _PreprocessorClass = preprocessor.MDTFDataPreprocessor

    def parse_relative_path(self, subdir, filename):
        rel_path = os.path.join(subdir, filename)
        path_d = {
            'case_name': self.case_name,
            'remote_path': os.path.join(self.data_root_dir, rel_path),
            'local_path': util.NOTSET
        }
        match = re.match(self._pp_ts_regex, rel_path)
        if match:
            md = match.groupdict()
            md['date_range'] = datelabel.DateRange(md['start_date'], md['end_date'])
            md = util.filter_dataclass(md, self.FileDataSet)
            return self.FileDataSet(**md, **path_d)
        # match failed, try static file regex instead
        match = re.match(self._pp_static_regex, rel_path)
        if match:
            md = match.groupdict()
            md['start_date'] = datelabel.FXDateMin
            md['end_date'] = datelabel.FXDateMax
            md['date_range'] = datelabel.FXDateRange
            # TODO: fix this: static vars combined in one file;
            # must extract them in preprocessor
            md['name_in_model'] = util.NOTSET 
            md = util.filter_dataclass(md, self.FileDataSet)
            return self.FileDataSet(**md, **path_d)
        raise ValueError("Can't parse {}, skipping.".format(rel_path))

    def subdirectory_filters(self):
        return [self.component, 'ts', gfdl_util.frepp_freq(self.data_freq), 
                gfdl_util.frepp_freq(self.chunk_freq)]
                
    @staticmethod
    def _heuristic_component_tiebreaker(str_list):
        """Determine experiment component(s) from heuristics.

        1. If we're passed multiple components, select those containing 'cmip'.

        2. If that selects multiple components, break the tie by selecting the 
            component with the fewest words (separated by '_'), or, failing that, 
            the shortest overall name.

        Args:
            str_list (:py:obj:`list` of :py:obj:`str`:): list of component names.

        Returns: :py:obj:`str`: name of component that breaks the tie.
        """
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

    def select_undetermined(self):
        d_to_u = dict.fromkeys(self.data_keys)
        for d_key in d_to_u:
            d_to_u[d_key] = {f.to_UndeterminedKey() for f in self.data_files[d_key]}
        choices = dict.fromkeys(self.data_keys)
        cmpt_choices = choose.minimum_cover(
            d_to_u,
            op.attrgetter('component'),
            self._heuristic_component_tiebreaker
        )
        for d_key, cmpt in iter(cmpt_choices.items()):
            # take shortest chunk frequency (revisit?)
            chunk_freq = min(u_key.chunk_freq for u_key in d_to_u[d_key] \
                if u_key.component == cmpt)
            choices[d_key] = self.UndeterminedKey(
                component=cmpt, chunk_freq=str(chunk_freq))
        return choices

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



class GFDLHTMLPodOutputManager(output_manager.HTMLPodOutputManager):
    def __init__(self, pod, code_root, case_wk_dir):
        """Only run output steps (including logging error on index.html) 
        if POD ran on this invocation.
        """
        if pod._has_placeholder:
            _log.debug('POD %s has placeholder, generating output.', pod.name)
            super(GFDLHTMLPodOutputManager, self).__init__(pod, code_root, case_wk_dir)
        else: 
            _log.debug('POD %s does not have placeholder; not generating output.', 
                pod.name)

class GFDLHTMLOutputManager(output_manager.HTMLOutputManager):
    _PodOutputManagerClass = GFDLHTMLPodOutputManager

    def __init__(self, case):
        config = core.ConfigManager()
        try:
            self.frepp_mode = case.frepp_mode
            self.file_transfer_timeout = config['file_transfer_timeout']
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
