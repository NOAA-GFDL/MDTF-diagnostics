from __future__ import absolute_import, division, print_function, unicode_literals
import os
import io
from src import six
import re
import shutil
if os.name == 'posix' and six.PY2:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
else:
    import subprocess
from collections import defaultdict, namedtuple
from itertools import chain
from operator import attrgetter, itemgetter
from abc import ABCMeta, abstractmethod, abstractproperty
from src import datelabel
from src import util
from src import util_mdtf
import src.conflict_resolution as choose
from src import cmip6
from src.data_manager import DataSet, DataManager, DataAccessError
from src.environment_manager import VirtualenvEnvironmentManager, CondaEnvironmentManager
from src.shared_diagnostic import Diagnostic, PodRequirementFailure
from src.netcdf_helper import NcoNetcdfHelper # only option currently implemented

class ModuleManager(util.Singleton):
    _current_module_versions = {
        'python2':   'python/2.7.12',
        # most recent version common to analysis and workstations; use conda anyway
        'python3':   'python/3.4.3',
        'ncl':      'ncarg/6.5.0',
        'r':        'R/3.4.4',
        'anaconda': 'anaconda2/5.1',
        'gcp':      'gcp/2.3',
        # install nco in conda environment, rather than using GFDL module
        # 'nco':      'nco/4.5.4', # 4.7.6 still broken on workstations
        'netcdf':   'netcdf/4.2'
    }

    def __init__(self):
        if 'MODULESHOME' not in os.environ:
            # could set from module --version
            raise OSError(("Unable to determine how modules are handled "
                "on this host."))
        _ = os.environ.setdefault('LOADEDMODULES', '')

        # capture the modules the user has already loaded once, when we start up,
        # so that we can restore back to this state in revert_state()
        self.user_modules = set(self._list())
        self.modules_i_loaded = set()

    def _module(self, *args):
        # based on $MODULESHOME/init/python.py
        if isinstance(args[0], list): # if we're passed explicit list, unpack it
            args = args[0]
        cmd = '{}/bin/modulecmd'.format(os.environ['MODULESHOME'])
        proc = subprocess.Popen([cmd, 'python'] + args, stdout=subprocess.PIPE)
        (output, error) = proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=proc.returncode, 
                cmd=' '.join([cmd, 'python'] + args), output=error)
        exec(output)

    def _parse_names(self, *module_names):
        return [m if ('/' in m) else self._current_module_versions[m] \
            for m in module_names]

    def load(self, *module_names):
        """Wrapper for module load.
        """
        mod_names = self._parse_names(*module_names)
        for mod_name in mod_names:
            if mod_name not in self.modules_i_loaded:
                self.modules_i_loaded.add(mod_name)
                self._module(['load', mod_name])

    def load_commands(self, *module_names):
        return ['module load {}'.format(m) \
            for m in self._parse_names(*module_names)]

    def unload(self, *module_names):
        """Wrapper for module unload.
        """
        mod_names = self._parse_names(*module_names)
        for mod_name in mod_names:
            if mod_name in self.modules_i_loaded:
                self.modules_i_loaded.discard(mod_name)
                self._module(['unload', mod_name])

    def unload_commands(self, *module_names):
        return ['module unload {}'.format(m) \
            for m in self._parse_names(*module_names)]

    def _list(self):
        """Wrapper for module list.
        """
        return os.environ['LOADEDMODULES'].split(':')
    
    def revert_state(self):
        mods_to_unload = self.modules_i_loaded.difference(self.user_modules)
        for mod in mods_to_unload:
            self._module(['unload', mod])
        # User's modules may have been unloaded if we loaded a different version
        for mod in self.user_modules:
            self._module(['load', mod])
        assert set(self._list()) == self.user_modules


class GfdlDiagnostic(Diagnostic):
    """Wrapper for Diagnostic that adds writing a placeholder directory to the
    output as a lockfile if we're running in frepp cooperative mode.
    """
    def __init__(self, pod_name, verbose=0):
        super(GfdlDiagnostic, self).__init__(pod_name, verbose)
        self._has_placeholder = False

    def setUp(self, verbose=0):
        config = util_mdtf.ConfigManager()
        try:
            super(GfdlDiagnostic, self).setUp(verbose)
            make_remote_dir(
                self.POD_OUT_DIR,
                timeout=config.config.get('file_transfer_timeout', 0),
                dry_run=config.config.get('dry_run', False)
            )
            self._has_placeholder = True
        except PodRequirementFailure:
            raise

    def tearDown(self, verbose=0):
        # only run teardown (including logging error on index.html) if POD ran
        if self._has_placeholder:
            super(GfdlDiagnostic, self).tearDown(verbose)

class GfdlvirtualenvEnvironmentManager(VirtualenvEnvironmentManager):
    # Use module files to switch execution environments, as defined on 
    # GFDL workstations and PP/AN cluster.

    def __init__(self, verbose=0):
        _ = ModuleManager()
        super(GfdlvirtualenvEnvironmentManager, self).__init__(verbose)

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
        modMgr = ModuleManager()
        modMgr.load(self._module_lookup[env_name])
        super(GfdlvirtualenvEnvironmentManager, \
            self).create_environment(env_name)

    def activate_env_commands(self, env_name):
        modMgr = ModuleManager()
        mod_list = modMgr.load_commands(self._module_lookup[env_name])
        return ['source $MODULESHOME/init/bash'] \
            + mod_list \
            + super(GfdlvirtualenvEnvironmentManager, self).activate_env_commands(env_name)

    def deactivate_env_commands(self, env_name):
        modMgr = ModuleManager()
        mod_list = modMgr.unload_commands(self._module_lookup[env_name])
        return super(GfdlvirtualenvEnvironmentManager, \
            self).deactivate_env_commands(env_name) + mod_list

    def tearDown(self):
        super(GfdlvirtualenvEnvironmentManager, self).tearDown()
        modMgr = ModuleManager()
        modMgr.revert_state()

class GfdlcondaEnvironmentManager(CondaEnvironmentManager):
    # Use mdteam's anaconda2
    def _call_conda_create(self, env_name):
        raise Exception(("Trying to create conda env {} "
            "in read-only mdteam account.").format(env_name)
        )


def GfdlautoDataManager(case_dict, DateFreqMixin=None):
    """Wrapper for dispatching DataManager based on inputs.
    """
    test_root = case_dict.get('CASE_ROOT_DIR', None)
    if not test_root:
        return Gfdludacmip6DataManager(case_dict, DateFreqMixin)
    test_root = os.path.normpath(test_root)
    if 'pp' in os.path.basename(test_root):
        return GfdlppDataManager(case_dict, DateFreqMixin)
    else:
        print(("ERROR: Couldn't determine data fetch method from input."
            "Please set '--data_manager GFDL_pp', 'GFDL_UDA_CMP6', or "
            "'GFDL_data_cmip6', depending on the source you want."))
        exit()


class GfdlarchiveDataManager(six.with_metaclass(ABCMeta, DataManager)):
    def __init__(self, case_dict, DateFreqMixin=None):
        # load required modules
        modMgr = ModuleManager()
        modMgr.load('gcp') # should refactor

        config = util_mdtf.ConfigManager()
        config.config.netcdf_helper = 'NcoNetcdfHelper' # HACK for now
        super(GfdlarchiveDataManager, self).__init__(case_dict, DateFreqMixin)

        assert ('CASE_ROOT_DIR' in case_dict)
        if not os.path.isdir(case_dict['CASE_ROOT_DIR']):
            raise DataAccessError(None, 
                "Can't access CASE_ROOT_DIR = '{}'".format(case_dict['CASE_ROOT_DIR']))
        self.root_dir = case_dict['CASE_ROOT_DIR']
        self.tape_filesystem = is_on_tape_filesystem(self.root_dir)

        self.frepp_mode = config.config.get('frepp', False)
        if self.frepp_mode:
            self.overwrite = True
            # flag to not overwrite config and .tar: want overwrite for frepp
            self.file_overwrite = True
            # if overwrite=False, WK_DIR & OUT_DIR will have been set to a 
            # unique name in parent's init. Set it back so it will be overwritten.
            d = config.paths.modelPaths(self, overwrite=True)
            self.MODEL_WK_DIR = d.MODEL_WK_DIR
            self.MODEL_OUT_DIR = d.MODEL_OUT_DIR

    DataKey = namedtuple('DataKey', ['name_in_model', 'date_freq'])  
    def dataset_key(self, dataset):
        return self.DataKey(
            name_in_model=dataset.name_in_model, 
            date_freq=str(dataset.date_freq)
        )

    @abstractmethod
    def undecided_key(self, dataset):
        pass

    @abstractmethod
    def parse_relative_path(self, subdir, filename):
        pass

    def _listdir(self, dir_):
        # print("\t\tDEBUG: listdir on ...{}".format(dir_[len(self.root_dir):]))
        return os.listdir(dir_)

    def _list_filtered_subdirs(self, dirs_in, subdir_filter=None):
        subdir_filter = util.coerce_to_iter(subdir_filter)
        found_dirs = []
        for dir_ in dirs_in:
            found_subdirs = {d for d \
                in self._listdir(os.path.join(self.root_dir, dir_)) \
                if not (d.startswith('.') or d.endswith('.nc'))
            }
            if subdir_filter:
                found_subdirs = found_subdirs.intersection(subdir_filter)
            if not found_subdirs:
                print("\tCouldn't find subdirs (in {}) at {}, skipping".format(
                    subdir_filter, os.path.join(self.root_dir, dir_)
                ))
                continue
            found_dirs.extend([
                os.path.join(dir_, subdir_) for subdir_ in found_subdirs \
                if os.path.isdir(os.path.join(self.root_dir, dir_, subdir_))
            ])
        return found_dirs

    @abstractmethod
    def subdirectory_filters(self):
        pass

    def _query_data(self):
        """XXX UPDATE DOCSTRING 
        Populate _remote_data attribute with list of candidate files.

        Specifically, if a <component> and <chunk_freq> subdirectory has all the
        requested data, return paths to all files we *would* need in that 
        subdirectory. The decision of which <component> and <chunk_freq> to use
        is made in :meth:`~gfdl.GfdlppDataManager.plan_data_fetching` 
        because it requires comparing the files found for *all* requested datasets.
        """
        self._component_map = defaultdict(list)

        # match files ending in .nc only if they aren't of the form .tile#.nc
        # (negative lookback) 
        regex_no_tiles = re.compile(r".*(?<!\.tile\d)\.nc$")

        pathlist = ['']
        for filter_ in self.subdirectory_filters():
            pathlist = self._list_filtered_subdirs(pathlist, filter_)
        for dir_ in pathlist:
            file_lookup = defaultdict(list)
            dir_contents = self._listdir(os.path.join(self.root_dir, dir_))
            dir_contents = list(filter(regex_no_tiles.search, dir_contents))
            files = []
            for f in dir_contents:
                try:
                    files.append(self.parse_relative_path(dir_, f))
                except ValueError as exc:
                    print('\tDEBUG:', exc)
                    #print('\t\tDEBUG: ', exc, '\n\t\t', os.path.join(self.root_dir, dir_), f)
                    continue
            for ds in files:
                data_key = self.dataset_key(ds)
                file_lookup[data_key].append(ds)
            for data_key in self.data_keys:
                if data_key not in file_lookup:
                    continue
                try:
                    # method throws ValueError if ranges aren't contiguous
                    files_date_range = datelabel.DateRange.from_contiguous_span(
                        *[f.date_range for f in file_lookup[data_key]]
                    )
                except ValueError:
                    # Date range of remote files doesn't contain analysis range or 
                    # is noncontiguous; should probably log an error
                    continue
                if not files_date_range.contains(self.date_range):
                    # should log warning
                    continue
                for ds in file_lookup[data_key]:
                    if ds.date_range in self.date_range:
                        d_key = self.dataset_key(ds)
                        assert data_key == d_key
                        u_key = self.undecided_key(ds)
                        self.data_files[data_key].update([u_key])
                        self._component_map[u_key, data_key].append(ds)

    def query_dataset(self, dataset):
        # all the work done by _query_data
        pass

    @abstractmethod
    def _decide_allowed_components(self):
        pass

    def plan_data_fetch_hook(self):
        """Filter files on model component and chunk frequency.
        """
        d_to_u_dict = self._decide_allowed_components()
        for data_key in self.data_keys:
            u_key = d_to_u_dict[data_key]
            print("Selected {} for {} @ {}".format(
                u_key, data_key.name_in_model, data_key.date_freq)
            )
            # check we didn't eliminate everything:
            assert self._component_map[u_key, data_key] 
            self.data_files[data_key] = self._component_map[u_key, data_key]

        paths = set()
        for data_key in self.data_keys:
            for f in self.data_files[data_key]:
                paths.add(f._remote_data)
        if self.tape_filesystem:
            print("start dmget of {} files".format(len(paths)))
            util.run_command(['dmget','-t','-v'] + list(paths),
                timeout= len(paths) * self.file_transfer_timeout,
                dry_run=self.dry_run
            ) 
            print("end dmget")

    def local_data_is_current(self, dataset):
        """Test whether data is current based on filesystem modification dates.

        TODO:
            - Throw an error if local copy has been modified after remote copy. 
            - Handle case where local data involves processing of remote data, like
                ncrcat'ing. Copy raw remote files to temp directory if we need to 
                process?
            - gcp --sync does this already.

        """
        return False
        # return os.path.getmtime(dataset._local_data) \
        #     >= os.path.getmtime(dataset._remote_data)

    def remote_data_list(self):
        """Process list of requested data to make data fetching efficient.
        """
        return sorted(list(self.data_keys), key=lambda dk: repr(dk))

    def _fetch_exception_handler(self, exc):
        print(exc)
        # iterating over the keys themselves, so that will be what's passed 
        # in the exception
        for pod in self.data_pods[exc.dataset]:
            print("\tSkipping pod {} due to data fetch error.".format(pod.name))
            pod.skipped = exc

    def fetch_dataset(self, d_key, method='auto'):
        """Copy files to temporary directory and combine chunks.
        """
        # pylint: disable=maybe-no-member
        (cp_command, smartsite) = self._determine_fetch_method(method)
        dest_path = self.local_path(d_key)
        dest_dir = os.path.dirname(dest_path)
        # ncrcat will error instead of creating destination directories
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        # GCP can't copy to home dir, so always copy to temp
        tmpdirs = util_mdtf.TempDirManager()
        work_dir = tmpdirs.make_tempdir(hash_obj = d_key)
        remote_files = sorted( # cast from set to list so we can go in chrono order
            list(self.data_files[d_key]), key=lambda ds: ds.date_range.start
            ) 

        # copy remote files
        # TODO: Do something intelligent with logging, caught OSErrors
        for f in remote_files:
            print("\tcopying ...{} to {}".format(
                f._remote_data[len(self.root_dir):], work_dir
            ))
            util.run_command(cp_command + [
                smartsite + f._remote_data, 
                # gcp requires trailing slash, ln ignores it
                smartsite + work_dir + os.sep
            ], 
                timeout=self.file_transfer_timeout, 
                dry_run=self.dry_run
            )

        # ----------------------------------------
        # Processing of copied files: TODO: refactor individual steps into 
        # separate functions 

        # set axis names from header info
        # only look at first file; if other chunks for same var differ, NCO will
        # raise error when we try to concat them
        file_name = os.path.basename(remote_files[0]._remote_data)
        var_name = remote_files[0].name_in_model
        file_axes = self.nc_get_axes_attributes(
            var_name,
            in_file=file_name, cwd=work_dir, dry_run=self.dry_run
        )
        for fax, fax_attrs in iter(file_axes.items()):
            # update DataSets with axis info - need to loop since multiple PODs
            # may reference this file (warning will be repeated; TODO fix that)
            error_flag = 0
            for var in self.data_keys[d_key]: 
                if fax in var.axes:
                    # file's axis in list of case's axis names; check their
                    # axis attributes match if they're both defined
                    if 'axis' in fax_attrs and 'axis' in var.axes[fax] \
                        and fax_attrs['axis'].lower() != var.axes[fax]['axis'].lower() \
                        and error_flag != 1:
                        print(("\tWarning: unexpected axis attribute for {0} in "
                            "{1} (found {2}, {3} convention is {4})").format(
                                fax, file_name, fax_attrs['axis'], 
                                self.convention, var.axes[fax]['axis']
                        ))
                        error_flag = 1
                    var.axes[fax]['MDTF_set_from_axis'] = False
                else: 
                    # file has different axis name, try to match by attribute
                    for vax, vax_attrs in iter(var.axes.items()):
                        if 'axis' not in fax_attrs or 'axis' not in vax_attrs:
                            continue
                        elif vax_attrs['axis'].lower() == fax_attrs['axis'].lower():
                            # matched axis attributes: log warning & reassign
                            if error_flag != 2:
                                print(("\tWarning: unexpected {0} axis name in {1} "
                                    "(found {2}, {3} convention is {4})").format(
                                        fax_attrs['axis'], file_name, fax, 
                                        self.convention, vax
                                ))
                                error_flag = 2
                            # only update so we don't overwrite the envvar name
                            var.axes[fax] = vax_attrs.copy()
                            var.axes[fax].update(fax_attrs)
                            var.axes[fax]['MDTF_set_from_axis'] = True
                            del var.axes[vax]
                            break
                    else:
                        # get here if we didn't hit 'break' above -- give up
                        if error_flag != 3:
                            print(("\tWarning: unable to assign {0} axis "
                                "in {1}.").format(fax, file_name))
                            error_flag = 3

        # crop time axis to requested range
        # do this *before* combining chunks to reduce disk activity
        for vax, vax_attrs in iter(var.axes.items()):
            if 'axis' not in vax_attrs or vax_attrs['axis'].lower() != 't':
                continue
            else:
                time_var_name = vax
                break
        else:
            print("\tCan't determine time axis for {}.".format(file_name))
            time_var_name = 'time' # will probably give KeyError
        trim_count = 0
        for f in remote_files:
            file_name = os.path.basename(f._remote_data)
            if not self.date_range.overlaps(f.date_range):
                print(("\tWarning: {} has dates {} outside of requested "
                    "range {}.").format(file_name, f.date_range, self.date_range))
                continue
            if not self.date_range.contains(f.date_range):
                # file overlaps analysis range but is not strictly contained
                # in it means we need to trim either start or end or both
                trimmed_range = f.date_range.intersection(
                    self.date_range,
                    precision=f.date_range.precision
                )
                print("\ttrimming '{}' of {} from {} to {}".format(
                    time_var_name, file_name, f.date_range, trimmed_range))
                trim_count = trim_count + 1
                self.nc_crop_time_axis(
                    time_var_name, trimmed_range, 
                    in_file=file_name, cwd=work_dir, dry_run=self.dry_run
                )
        if trim_count > 2:
            print("trimmed {} files!".format(trim_count))
            raise AssertionError()

        # cat chunks to destination, if more than one
        if len(remote_files) > 1:
            # not running in shell, so can't use glob expansion.
            print("\tcatting {} chunks to {}".format(
                d_key.name_in_model, dest_path
            ))
            chunks = [os.path.basename(f._remote_data) for f in remote_files]
            self.nc_cat_chunks(chunks, dest_path, 
                cwd=work_dir, dry_run=self.dry_run
            )
        else:
            f = util.coerce_from_iter(remote_files)
            file_name = os.path.basename(f._remote_data)
            print("\tsymlinking {} to {}".format(d_key.name_in_model, dest_path))
            util.run_command(['ln', '-fs', \
                os.path.join(work_dir, file_name), dest_path],
                dry_run=self.dry_run
            ) 
        # temp files cleaned up by data_manager.tearDown

    def _determine_fetch_method(self, method='auto'):
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
        return (_methods[method]['command'], _methods[method]['site'])

    def process_fetched_data_hook(self):
        pass

    def _make_html(self, cleanup=False):
        # never cleanup html if we're in frepp_mode, since framework may run 
        # later when another component finishes. Instead just append current
        # progress to TEMP_HTML.
        prev_html = os.path.join(self.MODEL_OUT_DIR, 'index.html')
        if self.frepp_mode and os.path.exists(prev_html):
            print("\tDEBUG: Appending previous index.html at {}".format(prev_html))
            with io.open(prev_html, 'r', encoding='utf-8') as f1:
                contents = f1.read()
            contents = contents.split('<!--CUT-->')
            assert len(contents) == 3
            contents = contents[1]

            if os.path.exists(self.TEMP_HTML):
                mode = 'a'
            else:
                print("\tWARNING: No file at {}.".format(self.TEMP_HTML))
                mode = 'w'
            with io.open(self.TEMP_HTML, mode, encoding='utf-8') as f2:
                f2.write(contents)
        super(GfdlarchiveDataManager, self)._make_html(
            cleanup=(not self.frepp_mode)
        )

    def _make_tar_file(self, tar_dest_dir):
        # make locally in WORKING_DIR and gcp to destination,
        # since OUTPUT_DIR might be mounted read-only
        config = util_mdtf.ConfigManager()
        out_file = super(GfdlarchiveDataManager, self)._make_tar_file(
            config.paths.WORKING_DIR
        )
        gcp_wrapper(
            out_file, tar_dest_dir,
            timeout=self.file_transfer_timeout, dry_run=self.dry_run
        )
        _, file_ = os.path.split(out_file)
        return os.path.join(tar_dest_dir, file_)

    def _copy_to_output(self):
        # use gcp, since OUTPUT_DIR might be mounted read-only
        if self.MODEL_WK_DIR == self.MODEL_OUT_DIR:
            return # no copying needed
        if self.frepp_mode:
            # only copy PODs that ran, whether they succeeded or not
            for pod in self.pods:
                if pod._has_placeholder:
                    gcp_wrapper(
                        pod.POD_WK_DIR, 
                        pod.POD_OUT_DIR,
                        timeout=self.file_transfer_timeout, dry_run=self.dry_run
                    )
            # copy all case-level files
            print("\tDEBUG: files in {}".format(self.MODEL_WK_DIR))
            for f in os.listdir(self.MODEL_WK_DIR):
                print("\t\tDEBUG: found {}".format(f))
                if os.path.isfile(os.path.join(self.MODEL_WK_DIR, f)):
                    print("\t\tDEBUG: found {}".format(f))
                    gcp_wrapper(
                        os.path.join(self.MODEL_WK_DIR, f), 
                        self.MODEL_OUT_DIR,
                        timeout=self.file_transfer_timeout, dry_run=self.dry_run
                    )
        else:
            # copy everything at once
            if os.path.exists(self.MODEL_OUT_DIR):
                if self.overwrite:
                    try:
                        print('Error: {} exists, attempting to remove.'.format(
                            self.MODEL_OUT_DIR))
                        shutil.rmtree(self.MODEL_OUT_DIR)
                    except OSError:
                        # gcp will not overwrite dirs, so forced to save under
                        # a different name despite overwrite=True
                        print(("Error: couldn't remove {} (probably mounted read"
                            "-only); will rename new directory.").format(
                            self.MODEL_OUT_DIR))
                else:
                    print("Error: {} exists; will rename new directory.".format(
                        self.MODEL_OUT_DIR))
            try:
                if os.path.exists(self.MODEL_OUT_DIR):
                    # check again, since rmtree() might have succeeded
                    self.MODEL_OUT_DIR, version = \
                        util_mdtf.bump_version(self.MODEL_OUT_DIR)
                    new_wkdir, _ = \
                        util_mdtf.bump_version(self.MODEL_WK_DIR, new_v=version)
                    print("\tDEBUG: move {} to {}".format(self.MODEL_WK_DIR, new_wkdir))
                    shutil.move(self.MODEL_WK_DIR, new_wkdir)
                    self.MODEL_WK_DIR = new_wkdir
                gcp_wrapper(
                    self.MODEL_WK_DIR, self.MODEL_OUT_DIR, 
                    timeout=self.file_transfer_timeout,
                    dry_run=self.dry_run
                )
            except Exception:
                raise # only delete MODEL_WK_DIR if copied successfully
            shutil.rmtree(self.MODEL_WK_DIR)


class GfdlppDataManager(GfdlarchiveDataManager):
    def __init__(self, case_dict, DateFreqMixin=None):
        # assign explicitly else linter complains
        self.component = None
        self.data_freq = None
        self.chunk_freq = None
        super(GfdlppDataManager, self).__init__(case_dict, DateFreqMixin)

    UndecidedKey = namedtuple('ComponentKey', ['component', 'chunk_freq'])
    def undecided_key(self, dataset):
        return self.UndecidedKey(
            component=dataset.component, 
            chunk_freq=str(dataset.chunk_freq)
        )

    _pp_ts_regex = re.compile(r"""
            /?                      # maybe initial separator
            (?P<component>\w+)/     # component name
            ts/                     # timeseries;
            (?P<date_freq>\w+)/     # ts freq
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
    
    def parse_relative_path(self, subdir, filename):
        rel_path = os.path.join(subdir, filename)
        match = re.match(self._pp_ts_regex, rel_path)
        if match:
            #if match.group('component') != match.group('component2'):
            #    raise ValueError("Can't parse {}.".format(rel_path))
            ds = DataSet(**(match.groupdict()))
            del ds.component2
            ds._remote_data = os.path.join(self.root_dir, rel_path)
            ds.date_range = datelabel.DateRange(ds.start_date, ds.end_date)
            ds.date_freq = self.DateFreq(ds.date_freq)
            ds.chunk_freq = self.DateFreq(ds.chunk_freq)
            return ds
        # match failed, try static file regex instead
        match = re.match(self._pp_static_regex, rel_path)
        if match:
            md = match.groupdict()
            md['start_date'] = None
            md['end_date'] = None
            md['name_in_model'] = None # TODO: handle better
            ds = DataSet(**md)
            del ds.component2
            ds._remote_data = os.path.join(self.root_dir, rel_path)
            ds.date_range = None
            ds.date_freq = self.DateFreq('static')
            ds.chunk_freq = self.DateFreq('static')
            return ds
        raise ValueError("Can't parse {}, skipping.".format(rel_path))

    def subdirectory_filters(self):
        return [self.component, 'ts', frepp_freq(self.data_freq), 
                frepp_freq(self.chunk_freq)]
                
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

    def _decide_allowed_components(self):
        choices = dict.fromkeys(self.data_files)
        cmpt_choices = choose.minimum_cover(
            self.data_files,
            attrgetter('component'),
            self._heuristic_component_tiebreaker
        )
        for data_key, cmpt in iter(cmpt_choices.items()):
            # take shortest chunk frequency (revisit?)
            chunk_freq = min(u_key.chunk_freq \
                for u_key in self.data_files[data_key] \
                if u_key.component == cmpt)
            choices[data_key] = self.UndecidedKey(component=cmpt, chunk_freq=str(chunk_freq))
        return choices

class Gfdlcmip6abcDataManager(six.with_metaclass(ABCMeta, GfdlarchiveDataManager)):
    def __init__(self, case_dict, DateFreqMixin=None):
        # set root_dir
        # from experiment and model, determine institution and mip
        # set realization code = 'r1i1p1f1' unless specified
        cmip = cmip6.CMIP6_CVs()
        if 'activity_id' not in case_dict:
            if 'experiment_id' in case_dict:
                key = case_dict['experiment_id']
            elif 'experiment' in case_dict:
                key = case_dict['experiment']
            else:
                raise Exception("Can't determine experiment.")
        self.experiment_id = key
        self.activity_id = cmip.lookup(key, 'experiment_id', 'activity_id')
        if 'institution_id' not in case_dict:
            if 'source_id' in case_dict:
                key = case_dict['source_id']
            elif 'model' in case_dict:
                key = case_dict['model']
            else:
                raise Exception("Can't determine model/source.")
        self.source_id = key
        self.institution_id = cmip.lookup(key, 'source_id', 'institution_id')
        if 'member_id' not in case_dict:
            self.member_id = 'r1i1p1f1'
        case_dict['CASE_ROOT_DIR'] = os.path.join(
            self._cmip6_root, self.activity_id, self.institution_id, 
            self.source_id, self.experiment_id, self.member_id)
        # assign explicitly else linter complains
        self.data_freq = None
        self.table_id = None
        self.grid_label = None
        self.version_date = None
        super(Gfdlcmip6abcDataManager, self).__init__(
            case_dict, DateFreqMixin=cmip6.CMIP6DateFrequency
        )
        if 'data_freq' in self.__dict__:
            self.table_id = cmip.table_id_from_freq(self.data_freq)

    @abstractmethod # note: only using this as a property
    def _cmip6_root(self):
        pass

    # also need to determine table?
    UndecidedKey = namedtuple('UndecidedKey', 
        ['table_id', 'grid_label', 'version_date'])
    def undecided_key(self, dataset):
        return self.UndecidedKey(
            table_id=str(dataset.table_id),
            grid_label=dataset.grid_label, 
            version_date=str(dataset.version_date)
        )

    def parse_relative_path(self, subdir, filename):
        d = cmip6.parse_DRS_path(
            os.path.join(self.root_dir, subdir)[len(self._cmip6_root):],
            filename
        )
        d['name_in_model'] = d['variable_id']
        ds = DataSet(**d)
        ds._remote_data = os.path.join(self.root_dir, subdir, filename)
        return ds

    def subdirectory_filters(self):
        return [self.table_id, None, # variable_id
            self.grid_label, self.version_date]

    @staticmethod
    def _cmip6_table_tiebreaker(str_list):
        # no suffix or qualifier, if possible
        tbls = [cmip6.parse_mip_table_id(t) for t in str_list]
        tbls = [t for t in tbls if (not t['spatial_avg'] and not t['region'] \
            and t['temporal_avg'] == 'interval')]
        if not tbls:
            raise Exception('Need to refine table_id more carefully')
        tbls = min(tbls, key=lambda t: len(t['table_prefix']))
        return tbls['table_id']

    @staticmethod
    def _cmip6_grid_tiebreaker(str_list):
        # no suffix or qualifier, if possible
        grids = [cmip6.parse_grid_label(g) for g in str_list]
        grids = [g for g in grids if (
            not g['spatial_avg'] and not g['region']
        )]
        if not grids:
            raise Exception('Need to refine grid_label more carefully')
        grids = min(grids, key=itemgetter('grid_number'))
        return grids['grid_label']

    def _decide_allowed_components(self):
        tables = choose.minimum_cover(
            self.data_files,
            attrgetter('table_id'), 
            self._cmip6_table_tiebreaker
        )
        dkeys_for_each_pod = list(self.data_pods.inverse().values())
        grid_lbl = choose.all_same_if_possible(
            self.data_files,
            dkeys_for_each_pod,
            attrgetter('grid_label'), 
            self._cmip6_grid_tiebreaker
            )
        version_date = choose.require_all_same(
            self.data_files,
            attrgetter('version_date'),
            lambda dates: str(max(datelabel.Date(dt) for dt in dates))
            )
        choices = dict.fromkeys(self.data_files)
        for data_key in choices:
            choices[data_key] = self.UndecidedKey(
                table_id=str(tables[data_key]), 
                grid_label=grid_lbl[data_key], 
                version_date=version_date[data_key]
            )
        return choices

class Gfdludacmip6DataManager(Gfdlcmip6abcDataManager):
    _cmip6_root = os.sep + os.path.join('archive','pcmdi','repo','CMIP6')

class Gfdldatacmip6DataManager(Gfdlcmip6abcDataManager):
    # Kris says /data_cmip6 used to stage pre-publication data, so shouldn't
    # be used as a data source unless explicitly requested by user
    _cmip6_root = os.sep + os.path.join('data_cmip6','CMIP6')


def gcp_wrapper(source_path, dest_dir, timeout=0, dry_run=False):
    modMgr = ModuleManager()
    modMgr.load('gcp')
    source_path = os.path.normpath(source_path)
    dest_dir = os.path.normpath(dest_dir)
    # gcp requires trailing slash, ln ignores it
    if os.path.isdir(source_path):
        source = ['-r', 'gfdl:' + source_path + os.sep]
        # gcp /A/B/ /C/D/ will result in /C/D/B, so need to specify parent dir
        dest = ['gfdl:' + os.path.dirname(dest_dir) + os.sep]
    else:
        source = ['gfdl:' + source_path]
        dest = ['gfdl:' + dest_dir + os.sep]
    print('\tDEBUG: GCP {} -> {}'.format(source[-1], dest[-1]))
    util.run_command(
        ['gcp', '--sync', '-v', '-cd'] + source + dest,
        timeout=timeout, 
        dry_run=dry_run
    )

def make_remote_dir(dest_dir, timeout=None, dry_run=None):
    try:
        os.makedirs(dest_dir)
    except OSError:
        # use GCP for this because output dir might be on a read-only filesystem.
        # apparently trying to test this with os.access is less robust than 
        # just catching the error
        config = util_mdtf.ConfigManager()
        tmpdirs = util_mdtf.TempDirManager()
        work_dir = tmpdirs.make_tempdir()
        if timeout is None:
            timeout = config.config.get('file_transfer_timeout', 0)
        if dry_run is None:
            dry_run = config.config.get('dry_run', False)
        work_dir = os.path.join(work_dir, os.path.basename(dest_dir))
        os.makedirs(work_dir)
        gcp_wrapper(work_dir, dest_dir, timeout=timeout, dry_run=dry_run)

def running_on_PPAN():
    """Return true if current host is in the PPAN cluster."""
    host = os.uname()[1].split('.')[0]
    return (re.match(r"(pp|an)\d{3}", host) is not None)

def is_on_tape_filesystem(path):
    # handle eg. /arch0 et al as well as /archive.
    return any(os.path.realpath(path).startswith(s) \
        for s in ['/arch', '/ptmp', '/work'])

def frepp_freq(date_freq):
    # logic as written would give errors for 1yr chunks (?)
    if date_freq is None:
        return date_freq
    assert isinstance(date_freq, datelabel.DateFrequency)
    if date_freq.unit == 'hr' or date_freq.quantity != 1:
        return date_freq.format()
    else:
        # weekly not used in frepp
        _frepp_dict = {
            'yr': 'annual',
            'season': 'seasonal',
            'mo': 'monthly',
            'day': 'daily',
            'hr': 'hourly'
        }
        return _frepp_dict[date_freq.unit]

frepp_translate = {
    'in_data_dir': 'root_dir', # /pp/ directory
    'descriptor': 'CASENAME',
    'out_dir': 'OUTPUT_DIR',
    'WORKDIR': 'WORKING_DIR',
    'yr1': 'FIRSTYR',
    'yr2': 'LASTYR'
}

def parse_frepp_stub(frepp_stub):
    """Converts the frepp arguments to a Python dictionary.

    See `<https://wiki.gfdl.noaa.gov/index.php/FRE_User_Documentation#Automated_creation_of_diagnostic_figures>`__.

    Returns: :py:obj:`dict` of frepp parameters.
    """
    # parse arguments and relabel keys
    d = {}
    regex = re.compile(r"""
        \s*set[ ]     # initial whitespace, then 'set' followed by 1 space
        (?P<key>\w+)  # key is simple token, no problem
        \s+=?\s*      # separator is any whitespace, with 0 or 1 "=" signs
        (?P<value>    # want to capture all characters to end of line, so:
            [^=#\s]   # first character = any non-separator, or '#' for comments
            .*        # capture everything between first and last chars
            [^\s]     # last char = non-whitespace.
            |[^=#\s]\b) # separate case for when value is a single character.
        \s*$          # remainder of line must be whitespace.
        """, re.VERBOSE)
    for line in frepp_stub.splitlines():
        print("line = '{}'".format(line))
        match = re.match(regex, line)
        if match:
            if match.group('key') in frepp_translate:
                key = frepp_translate[match.group('key')]
            else:
                key = match.group('key')
            d[key] = match.group('value')

    # cast from string
    for int_key in ['FIRSTYR', 'LASTYR', 'verbose']:
        if int_key in d:
            d[int_key] = int(d[int_key])
    for bool_key in ['make_variab_tar', 'test_mode']:
        if bool_key in d:
            d[bool_key] = bool(d[bool_key])

    d['frepp'] = (d != {})
    return d
