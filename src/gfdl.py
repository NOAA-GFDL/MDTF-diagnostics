import os
import sys
import re
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
else:
    import subprocess
from collections import defaultdict, namedtuple
from itertools import chain
from operator import attrgetter, itemgetter
from abc import ABCMeta, abstractmethod
import datelabel
import util
import conflict_resolution as choose
import cmip6
from data_manager import DataSet, DataManager, DataQueryFailure
from environment_manager import VirtualenvEnvironmentManager, CondaEnvironmentManager
from shared_diagnostic import Diagnostic, PodRequirementFailure
from netcdf_helper import NcoNetcdfHelper # only option currently implemented

class ModuleManager(util.Singleton):
    _current_module_versions = {
        'python':   'python/2.7.12',
        'ncl':      'ncarg/6.5.0',
        'r':        'R/3.4.4',
        'anaconda': 'anaconda2/5.1',
        'gcp':      'gcp/2.3',
        'nco':      'nco/4.5.4', # avoid bug in 4.7.6 module on workstations
        'netcdf':   'netcdf/4.2'
    }

    def __init__(self):
        if 'MODULESHOME' not in os.environ:
            # could set from module --version
            raise OSError('Unable to determine how modules are handled on this host.')
        if not os.environ.has_key('LOADEDMODULES'):
            os.environ['LOADEDMODULES'] = ''

        # capture the modules the user has already loaded once, when we start up,
        # so that we can restore back to this state in revert_state()
        self.user_modules = set(self._list())
        self.modules_i_loaded = set()

    def _module(self, *args):
        # based on $MODULESHOME/init/python.py
        if type(args[0]) == type([]):
            args = args[0]
        else:
            args = list(args)
        cmd = '{}/bin/modulecmd'.format(os.environ['MODULESHOME'])
        proc = subprocess.Popen([cmd, 'python'] + args, stdout=subprocess.PIPE)
        (output, error) = proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=proc.returncode, 
                cmd=' '.join([cmd, 'python'] + args), output=error)
        exec output

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
        return ['module load {}'.format(m) for m in self._parse_names(*module_names)]

    def unload(self, *module_names):
        """Wrapper for module unload.
        """
        mod_names = self._parse_names(*module_names)
        for mod_name in mod_names:
            if mod_name in self.modules_i_loaded:
                self.modules_i_loaded.discard(mod_name)
                self._module(['unload', mod_name])

    def unload_commands(self, *module_names):
        return ['module unload {}'.format(m) for m in self._parse_names(*module_names)]

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
    # hack because we can't pass config to init easily
    _config = None

    def __init__(self, pod_name, verbose=0):
        super(GfdlDiagnostic, self).__init__(pod_name, verbose)
        self._has_placeholder = False

    def setUp(self, verbose=0):
        try:
            super(GfdlDiagnostic, self).setUp(verbose)
            make_placeholder_dir(
                self.name, 
                util.get_from_config('OUTPUT_DIR', self._config, section='paths'),
                timeout=util.get_from_config('file_transfer_timeout', self._config),
                dry_run=util.get_from_config('dry_run', self._config)
            )
            self._has_placeholder = True
        except PodRequirementFailure:
            raise

class GfdlvirtualenvEnvironmentManager(VirtualenvEnvironmentManager):
    # Use module files to switch execution environments, as defined on 
    # GFDL workstations and PP/AN cluster.

    def __init__(self, config, verbose=0):
        _ = ModuleManager()
        super(GfdlvirtualenvEnvironmentManager, self).__init__(config, verbose)

    # manual-coded logic like this is not scalable
    def set_pod_env(self, pod):
        keys = [s.lower() for s in pod.required_programs]
        if pod.name == 'convective_transition_diag':
            pod.env = 'py_convective_transition_diag'
        elif pod.name == 'MJO_suite':
            pod.env = 'ncl_MJO_suite'
        elif ('r' in keys) or ('rscript' in keys):
            pod.env = 'r_default'
        elif 'ncl' in keys:
            pod.env = 'ncl'
        else:
            pod.env = 'py_default'

    # this is totally not scalable
    _module_lookup = {
        'ncl': ['ncl'],
        'r_default': ['r'],
        'py_default': ['python'],
        'py_convective_transition_diag': ['python', 'ncl'],
        'ncl_MJO_suite': ['ncl', 'nco']
    }

    def create_environment(self, env_name):
        modMgr = ModuleManager()
        modMgr.load(self._module_lookup[env_name])
        super(GfdlvirtualenvEnvironmentManager, \
            self).create_environment(env_name)

    def activate_env_commands(self, pod):
        modMgr = ModuleManager()
        mod_list = modMgr.load_commands(self._module_lookup[pod.env])
        return ['source $MODULESHOME/init/bash'] \
            + mod_list \
            + super(GfdlvirtualenvEnvironmentManager, self).activate_env_commands(pod)

    def deactivate_env_commands(self, pod):
        modMgr = ModuleManager()
        mod_list = modMgr.unload_commands(self._module_lookup[pod.env])
        return super(GfdlvirtualenvEnvironmentManager, \
            self).deactivate_env_commands(pod) + mod_list

    def tearDown(self):
        super(GfdlvirtualenvEnvironmentManager, self).tearDown()
        modMgr = ModuleManager()
        modMgr.revert_state()

class GfdlcondaEnvironmentManager(CondaEnvironmentManager):
    # Use mdteam's anaconda2
    def __init__(self, config, verbose=0):
        super(GfdlcondaEnvironmentManager, self).__init__(config, verbose)

    def _call_conda_create(self, env_name):
        raise Exception(
            'Trying to create conda env {} in read-only mdteam account.'.format(env_name)
        )

    def activate_env_commands(self, pod):
        """Workaround conda activate in non-interactive shell.
        Ref: 
        https://github.com/conda/conda/issues/7980#issuecomment-536369736
        """
        conda_prefix = os.path.join(self.conda_env_root, pod.env)
        return [
            'source {}/bin/activate {}'.format(self.conda_root, conda_prefix)
        ]


def GfdlautoDataManager(case_dict, config={}, DateFreqMixin=None):
    """Wrapper for dispatching DataManager based on inputs.
    """
    drs_partial_directory_regex = re.compile(r"""
        .*CMIP6
        (/(?P<activity_id>\w+))?
        (/(?P<institution_id>[a-zA-Z0-9_-]+))?
        (/(?P<source_id>[a-zA-Z0-9_-]+))?
        (/(?P<experiment_id>[a-zA-Z0-9_-]+))?
        (/(?P<member_id>\w+))?
        (/(?P<table_id>\w+))?
        (/(?P<variable_id>\w+))?
        (/(?P<grid_label>\w+))?
        (/v(?P<version_date>\d+))?
        /?                      # maybe final separator
    """, re.VERBOSE)

    if 'root_dir' in case_dict \
        and os.path.normpath(case_dict['root_dir']).endswith(os.sep+'pp'):
        return GfdlppDataManager(case_dict, config, DateFreqMixin)
    elif ('experiment_id' in case_dict or 'experiment' in case_dict) \
        and ('source_id' in case_dict or 'model' in case_dict):
        return Gfdludacmip6DataManager(case_dict, config, DateFreqMixin)
    elif 'root_dir' in case_dict and 'CMIP6' in case_dict['root_dir']:
        match = re.match(drs_partial_directory_regex, case_dict['root_dir'])
        if match:
            case_dict.update(match.groupdict())
        return Gfdludacmip6DataManager(case_dict, config, DateFreqMixin)
    elif 'root_dir' in case_dict:
        return GfdlppDataManager(case_dict, config, DateFreqMixin)
    else:
        raise Exception("Don't know how to dispatch DataManager based on input.")


class GfdlarchiveDataManager(DataManager):
    __metaclass__ = ABCMeta
    def __init__(self, case_dict, config={}, DateFreqMixin=None):
        # load required modules
        modMgr = ModuleManager()
        modMgr.load('gcp', 'nco') # should refactor
        config['settings']['netcdf_helper'] = 'NcoNetcdfHelper'
        self.coop_mode = config['settings']['frepp']

        super(GfdlarchiveDataManager, self).__init__(case_dict, config, DateFreqMixin)
        assert ('root_dir' in case_dict)
        assert os.path.isdir(case_dict['root_dir'])
        self.root_dir = case_dict['root_dir']

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
        # print "\t\tDEBUG: listdir on ...{}".format(dir_[len(self.root_dir):])
        return os.listdir(dir_)

    def _list_filtered_subdirs(self, dirs_in, subdir_filter=None):
        subdir_filter = util.coerce_to_collection(subdir_filter, set)
        found_dirs = []
        for dir_ in dirs_in:
            found_subdirs = {d for d \
                in self._listdir(os.path.join(self.root_dir, dir_)) \
                if not (d.startswith('.') or d.endswith('.nc'))
            }
            if subdir_filter:
                found_subdirs = found_subdirs.intersection(subdir_filter)
            if not found_subdirs:
                print "\tCouldn't find subdirs (in {}) at {}, skipping".format(
                    subdir_filter, os.path.join(self.root_dir, dir_)
                )
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
                    print '\tDEBUG:', exc
                    #print '\t\tDEBUG: ', exc, '\n\t\t', os.path.join(self.root_dir, dir_), f
                    continue
            for ds in files:
                data_key = self.dataset_key(ds)
                file_lookup[data_key].append(ds)
            for data_key in self.data_keys:
                if data_key not in file_lookup:
                    continue
                try:
                    files_date_range = datelabel.DateRange( \
                        [f.date_range for f in file_lookup[data_key]])
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
            print "Selected {} for {} @ {}".format(
                u_key, data_key.name_in_model, data_key.date_freq)

            # check we didn't eliminate everything:
            assert self._component_map[u_key, data_key] 
            self.data_files[data_key] = self._component_map[u_key, data_key]

        paths = set()
        for data_key in self.data_keys:
            for f in self.data_files[data_key]:
                paths.add(f._remote_data)
        print "start dmget of {} files".format(len(paths))
        util.run_command(['dmget','-t','-v'] + list(paths),
            timeout=(len(paths)/2)*self.file_transfer_timeout,
            dry_run=self.dry_run
        ) 
        print "end dmget"

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
        return sorted(self.data_keys.keys())

    def _fetch_exception_handler(self, exc):
        print exc
        # iterating over the keys themselves, so that will be what's passed 
        # in the exception
        for pod in self.data_pods[exc.dataset]:
            print "\tSkipping pod {} due to data fetch error.".format(pod.name)
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
        paths = util.PathManager()
        work_dir = paths.make_tempdir(hash_obj = d_key)
        remote_files = sorted( # cast from set to list so we can go in chrono order
            list(self.data_files[d_key]), key=lambda ds: ds.date_range.start
            ) 

        # copy remote files
        # TODO: Do something intelligent with logging, caught OSErrors
        for f in remote_files:
            print "\tcopying ...{} to {}".format(
                f._remote_data[len(self.root_dir):], work_dir)
            util.run_command(cp_command + [
                smartsite + f._remote_data, 
                # gcp requires trailing slash, ln ignores it
                smartsite + work_dir + os.sep
            ], 
                timeout=self.file_transfer_timeout, 
                dry_run=self.dry_run
            ) 

        # crop time axis to requested range
        translate = util.VariableTranslator()
        time_var_name = translate.fromCF(self.convention, 'time_coord')
        trim_count = 0
        for f in remote_files:
            trimmed_range = f.date_range.intersection(
                self.date_range, 
                precision=f.date_range.start.precision
            )
            if trimmed_range != f.date_range:
                file_name = os.path.basename(f._remote_data)
                print "\ttrimming '{}' of {} from {} to {}".format(
                    time_var_name, file_name, f.date_range, trimmed_range)
                trim_count = trim_count + 1
                self.nc_crop_time_axis(
                    time_var_name, trimmed_range, file_name, 
                    working_dir=work_dir, 
                    dry_run=self.dry_run
                )
        assert trim_count <= 2

        # cat chunks to destination, if more than one
        if len(remote_files) > 1:
            # not running in shell, so can't use glob expansion.
            print "\tcatting {} chunks to {}".format(
                d_key.name_in_model, dest_path)
            chunks = [os.path.basename(f._remote_data) for f in remote_files]
            self.nc_cat_chunks(chunks, dest_path, 
                working_dir=work_dir,
                dry_run=self.dry_run
            )
        else:
            f = util.coerce_from_collection(remote_files)
            file_name = os.path.basename(f._remote_data)
            print "\tsymlinking {} to {}".format(d_key.name_in_model, dest_path)
            util.run_command(['ln', '-fs', \
                os.path.join(work_dir, file_name), dest_path],
                dry_run=self.dry_run
            ) 
        # temp files cleaned up by data_manager.tearDown

    def _determine_fetch_method(self, method='auto'):
        _methods = {
            'gcp': {'command': ['gcp', '-sync', '-v', '-cd'], 'site':'gfdl:'},
            'cp':  {'command': ['cp'], 'site':''},
            'ln':  {'command': ['ln', '-fs'], 'site':''}
        }
        if method not in _methods:
            if any(self.root_dir.startswith(s) for s in ['/arch', '/ptmp', '/work']):
                method = 'gcp' # use GCP for DMF filesystems
            else:
                method = 'ln' # symlink for local files
        return (_methods[method]['command'], _methods[method]['site'])

    def process_fetched_data_hook(self):
        pass

    def _make_html(self, cleanup=False):
        paths = util.PathManager()
        prev_html = os.path.join(self.MODEL_OUT_DIR, os.path.basename(self.TEMP_HTML))
        if paths.OUTPUT_DIR == paths.WORKING_DIR \
            and self.coop_mode and os.path.exists(prev_html):
            # should just run cat in a shell
            with open(prev_html, 'r') as f1:
                contents = f1.read()
                if os.path.exists(self.TEMP_HTML):
                    with open(self.TEMP_HTML, 'a') as f2:
                        f2.write(contents)
                else:
                    with open(self.TEMP_HTML, 'w') as f2:
                        f2.write(contents)

        super(GfdlarchiveDataManager, self)._make_html(cleanup)

    def _copy_to_output(self):
        # pylint: disable=maybe-no-member
        # use gcp, since OUTPUT_DIR might be mounted read-only
        paths = util.PathManager()
        if paths.OUTPUT_DIR == paths.WORKING_DIR:
            return # no copying needed
        if self.coop_mode:
            # only copy PODs that ran, whether they succeeded or not
            for pod in self.pods:
                if pod._has_placeholder:
                    gcp_wrapper(
                        pod.POD_WK_DIR, 
                        self.MODEL_OUT_DIR,
                        timeout=self.file_transfer_timeout, dry_run=self.dry_run
                    )
            # copy all case-level files
            for f in os.path.listdir(self.MODEL_WK_DIR):
                if os.path.isfile(f):
                    gcp_wrapper(
                        os.path.join(self.MODEL_WK_DIR, f), 
                        self.MODEL_OUT_DIR,
                        timeout=self.file_transfer_timeout, dry_run=self.dry_run
                    )
        else:
            # copy everything at once
            gcp_wrapper(
                self.MODEL_WK_DIR, 
                paths.OUTPUT_DIR,
                timeout=self.file_transfer_timeout, dry_run=self.dry_run
            )


class GfdlppDataManager(GfdlarchiveDataManager):
    def __init__(self, case_dict, config={}, DateFreqMixin=None):
        super(GfdlppDataManager, self).__init__(case_dict, config, DateFreqMixin)
        for attr in ['component', 'data_freq', 'chunk_freq']:
            if attr not in self.__dict__:
                self.__setattr__(attr, None)

    UndecidedKey = namedtuple('ComponentKey', ['component', 'chunk_freq'])
    def undecided_key(self, dataset):
        return self.UndecidedKey(
            component=dataset.component, 
            chunk_freq=str(dataset.chunk_freq)
        )

    def parse_relative_path(self, subdir, filename):
        rel_path = os.path.join(subdir, filename)
        match = re.match(r"""
            /?                      # maybe initial separator
            (?P<component>\w+)/     # component name
            ts/                     # timeseries; TODO: handle time averages (not needed now)
            (?P<date_freq>\w+)/     # ts freq
            (?P<chunk_freq>\w+)/    # data chunk length   
            (?P<component2>\w+)\.        # component name (again)
            (?P<start_date>\d+)-(?P<end_date>\d+)\.   # file's date range
            (?P<name_in_model>\w+)\.       # field name
            nc                      # netCDF file extension
        """, rel_path, re.VERBOSE)
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
        else:
            raise ValueError("Can't parse {}, skipping.".format(rel_path))

    def subdirectory_filters(self):
        # pylint: disable=maybe-no-member
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
            str_list (:obj:`list` of :obj:`str`:): list of component names.

        Returns: :obj:`str`: name of component that breaks the tie.
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
        choices = dict.fromkeys(self.data_files.keys())
        cmpt_choices = choose.minimum_cover(
            self.data_files,
            attrgetter('component'),
            self._heuristic_component_tiebreaker
        )
        for data_key, cmpt in cmpt_choices.iteritems():
            # take shortest chunk frequency (revisit?)
            chunk_freq = min(u_key.chunk_freq \
                for u_key in self.data_files[data_key] \
                if u_key.component == cmpt)
            choices[data_key] = self.UndecidedKey(component=cmpt, chunk_freq=str(chunk_freq))
        return choices

class Gfdludacmip6DataManager(GfdlarchiveDataManager):
    def __init__(self, case_dict, config={}, DateFreqMixin=None):
        # set root_dir
        # from experiment and model, determine institution and mip
        # set realization code = 'r1i1p1f1' unless specified
        self._uda_root = os.sep + os.path.join('archive','pcmdi','repo','CMIP6')
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
        case_dict['root_dir'] = os.path.join(
            self._uda_root, self.activity_id, self.institution_id, 
            self.source_id, self.experiment_id, self.member_id)
        super(Gfdludacmip6DataManager, self).__init__(
            case_dict, config, DateFreqMixin=cmip6.CMIP6DateFrequency)
        for attr in ['data_freq', 'table_id', 'grid_label', 'version_date']:
            if attr not in self.__dict__:
                self.__setattr__(attr, None)
        if 'data_freq' in self.__dict__:
            self.table_id = cmip.table_id_from_freq(self.data_freq)

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
            os.path.join(self.root_dir, subdir)[len(self._uda_root):],
            filename
        )
        d['name_in_model'] = d['variable_id']
        ds = DataSet(**d)
        ds._remote_data = os.path.join(self.root_dir, subdir, filename)
        return ds

    def subdirectory_filters(self):
        # pylint: disable=maybe-no-member
        return [self.table_id, None, # variable_id
            self.grid_label, self.version_date]

    @staticmethod
    def _cmip6_table_tiebreaker(str_list):
        # no suffix or qualifier, if possible
        tbls = [cmip6.parse_mip_table_id(t) for t in str_list]
        tbls = [t for t in tbls if (
            not t['spatial_avg'] and not t['region'] and t['temporal_avg'] == 'interval'
        )]
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
        dkeys_for_each_pod = self.data_pods.inverse().values()
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
        choices = dict.fromkeys(self.data_files.keys())
        for data_key in choices:
            choices[data_key] = self.UndecidedKey(
                table_id=str(tables[data_key]), 
                grid_label=grid_lbl[data_key], 
                version_date=version_date[data_key]
            )
        return choices

def gcp_wrapper(source_path, dest_dir, timeout=0, dry_run=False):
    modMgr = ModuleManager()
    modMgr.load('gcp')
    # gcp requires trailing slash, ln ignores it
    if os.path.isdir(source_path):
        source = ['-r', 'gfdl:' + os.path.normpath(source_path) + os.sep]
    else:
        source = ['gfdl:' + os.path.normpath(source_path)]
    dest = ['gfdl:' + dest_dir + os.sep]
    util.run_command(
        ['gcp', '-sync', '-v', '-cd'] + source + dest,
        timeout=timeout, 
        dry_run=dry_run
    )

def make_placeholder_dir(dir_name, dest_root_dir, timeout=0, dry_run=False):
    try:
        os.mkdir(os.path.join(dest_root_dir, dir_name))
    except OSError:
        # use GCP for this because output dir might be on a read-only filesystem.
        # apparently trying to test this with os.access is less robust than 
        # just catching the error
        paths = util.PathManager()
        work_dir = paths.make_tempdir()
        work_dir = os.path.join(work_dir, dir_name)
        os.makedirs(work_dir)
        gcp_wrapper(work_dir, dest_root_dir, timeout=timeout, dry_run=dry_run)

def running_on_PPAN():
    """Return true if current host is in the PPAN cluster."""
    host = os.uname()[1].split('.')[0]
    return (re.match(r"(pp|an)\d{3}", host) is not None)

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

    See `https://wiki.gfdl.noaa.gov/index.php/FRE_User_Documentation#Automated_creation_of_diagnostic_figures`_.

    Returns: :obj:`dict` of frepp parameters.
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
        print "line = '{}'".format(line)
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
