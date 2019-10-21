import os
import sys
import re
import tempfile
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
else:
    import subprocess
from collections import defaultdict, namedtuple
import datelabel
import util
from data_manager import DataManager, DataQueryFailure
from environment_manager import VirtualenvEnvironmentManager, CondaEnvironmentManager
from netcdf_helper import NcoNetcdfHelper # only option currently implemented

_current_module_versions = {
    'python':   'python/2.7.12',
    'ncl':      'ncarg/6.5.0',
    'r':        'R/3.4.4',
    'anaconda': 'anaconda2/5.1',
    'gcp':      'gcp/2.3',
    'nco':      'nco/4.7.6',
    'netcdf':   'netcdf/4.2'
}

class ModuleManager(util.Singleton):
    def __init__(self):
        if 'MODULESHOME' not in os.environ:
            # could set from module --version
            raise OSError('Unable to determine how modules are handled on this host.')
        if not os.environ.has_key('LOADEDMODULES'):
            os.environ['LOADEDMODULES'] = ''

        # capture the modules the user has already loaded once, when we start up,
        # so that we can restore back to this state in revert_state()
        self.user_modules = set(self.list())
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

    def load(self, module_name):
        """Wrapper for module load.
        """
        self.modules_i_loaded.add(module_name)
        self._module(['load', module_name])

    def unload(self, module_name):
        """Wrapper for module unload.
        """
        self.modules_i_loaded.discard(module_name)
        self._module(['unload', module_name])

    def list(self):
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
        assert set(self.list()) == self.user_modules


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
    def _module_lookup(self, env_name):
        _lookup = {
            'ncl': ['ncl'],
            'r_default': ['r'],
            'py_default': ['python'],
            'py_convective_transition_diag': ['python', 'ncl'],
            'ncl_MJO_suite': ['ncl', 'nco']
        }
        return [_current_module_versions[m] for m in _lookup[env_name]]

    def create_environment(self, env_name):
        modMgr = ModuleManager()
        for mod in self._module_lookup(env_name):
            modMgr.load(mod)
        super(GfdlvirtualenvEnvironmentManager, \
            self).create_environment(env_name)

    def activate_env_commands(self, pod):
        mod_list = ['module load {}'.format(m) for m in self._module_lookup(pod.env)]
        return ['source $MODULESHOME/init/bash'] \
            + mod_list \
            + super(GfdlvirtualenvEnvironmentManager, self).activate_env_commands(pod)

    def deactivate_env_commands(self, pod):
        mod_list = ['module unload {}'.format(m) for m in self._module_lookup(pod.env)]
        return super(GfdlvirtualenvEnvironmentManager, \
            self).deactivate_env_commands(pod) + mod_list

    def tearDown(self):
        super(GfdlvirtualenvEnvironmentManager, self).tearDown()
        modMgr = ModuleManager()
        modMgr.revert_state()


class GfdlcondaEnvironmentManager(CondaEnvironmentManager):
    # Use anaconda -- NOTE module not available on analysis

    def __init__(self, config, verbose=0):
        modMgr = ModuleManager()
        modMgr.load(_current_module_versions['anaconda'])
        super(GfdlcondaEnvironmentManager, self).__init__(config, verbose)

    def tearDown(self):
        super(GfdlcondaEnvironmentManager, self).tearDown()
        modMgr = ModuleManager()
        modMgr.revert_state()


class GfdlppDataManager(DataManager):
    def __init__(self, case_dict, config={}, verbose=0):
        # load required modules
        modMgr = ModuleManager()
        modMgr.load(_current_module_versions['gcp'])
        modMgr.load(_current_module_versions['nco']) # should refactor

        config['settings']['netcdf_helper'] = 'NcoNetcdfHelper'

        # if we're running on Analysis, recommended practice is to use $FTMPDIR
        # for scratch work. Setting tempfile.tempdir causes all temp directories
        # returned by util.PathManager to be in that location.
        # If we're not, assume we're on a workstation. gcp won't copy to the 
        # usual /tmp, so put temp files in a directory on /net2.
        if 'TMPDIR' in os.environ:
            tempfile.tempdir = os.environ['TMPDIR']
        elif os.path.isdir('/net2'):
            tempfile.tempdir = os.path.join('/net2', os.environ['USER'], 'tmp')
            if not os.path.isdir(tempfile.tempdir):
                os.makedirs(tempfile.tempdir)
        super(GfdlppDataManager, self).__init__(case_dict, config, verbose)
        assert ('root_dir' in case_dict)
        assert os.path.isdir(case_dict['root_dir'])
        self.root_dir = case_dict['root_dir']
        for attr in ['component', 'data_freq', 'chunk_freq']:
            if attr not in self.__dict__:
                self.__setattr__(attr, None)

    DataKey = namedtuple('DataKey', ['name_in_model', 'date_freq'])
    ComponentKey = namedtuple('ComponentKey', ['component', 'chunk_freq'])
    
    def dataset_key(self, dataset):
        return self.DataKey(
            name_in_model=dataset.name_in_model, 
            date_freq=str(dataset.date_freq)
        )

    def keys_from_dataset(self, dataset):
        return (
            self.dataset_key(dataset),
            self.ComponentKey(
                component=dataset.component, 
                chunk_freq=str(dataset.chunk_freq)
            )
        )

    def parse_pp_path(self, subdir, filename):
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
            ds = util.DataSet(**(match.groupdict()))
            del ds.component2
            ds._remote_data = os.path.join(self.root_dir, rel_path)
            ds.date_range = datelabel.DateRange(ds.start_date, ds.end_date)
            ds.date_freq = datelabel.DateFrequency(ds.date_freq)
            ds.chunk_freq = datelabel.DateFrequency(ds.chunk_freq)
            return ds
        else:
            raise ValueError("Can't parse {}, skipping.".format(rel_path))

    def _listdir(self, dir_):
        print "\t\tDEBUG: listdir on pp{}".format(dir_[len(self.root_dir):])
        return os.listdir(dir_)

    def _list_filtered_subdirs(self, dirs_in, subdir_filter=None):
        subdir_filter = util.coerce_to_collection(subdir_filter)
        found_dirs = []
        for dir_ in dirs_in:
            if not subdir_filter:
                subdir_list = [d for d \
                    in self._listdir(os.path.join(self.root_dir, dir_)) \
                    if not (d.startswith('.') or d.endswith('.nc'))
                ]
            else:
                subdir_list = subdir_filter
            found_dirs.extend([
                os.path.join(dir_, subdir_) for subdir_ in subdir_list \
                if os.path.isdir(os.path.join(self.root_dir, dir_, subdir_))
            ])
        return found_dirs

    def filtered_os_walk(self, subdir_filters):
        pathlist = ['']
        for filter_ in subdir_filters:
            pathlist = self._list_filtered_subdirs(pathlist, filter_)
        return pathlist

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

        paths = self.filtered_os_walk(
            [self.component, 'ts', frepp_freq(self.data_freq), 
                frepp_freq(self.chunk_freq)]
        )
        for dir_ in paths:
            file_lookup = defaultdict(list)
            dir_contents = self._listdir(os.path.join(self.root_dir, dir_))
            dir_contents = list(filter(regex_no_tiles.search, dir_contents))
            files = []
            for f in dir_contents:
                try:
                    files.append(self.parse_pp_path(dir_, f))
                except ValueError as exc:
                    print '\t\tDEBUG: ', exc
                    continue
            for ds in files:
                (data_key, cpt_key) = self.keys_from_dataset(ds)
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
                        (d_key, cpt_key) = self.keys_from_dataset(ds)
                        assert data_key == d_key
                        self.data_files[data_key].update([cpt_key])
                        self._component_map[cpt_key, data_key].append(ds)

    def query_dataset(self, dataset):
        # all the work done by _query_data
        pass

    def plan_data_fetch_hook(self):
        """Filter files on model component and chunk frequency.
        """
        cmpts = self._select_model_component()
        print "Components selected: ", cmpts
        for data_key in self.data_keys:
            cmpt = self._heuristic_component_tiebreaker( \
                {cpt_key.component for cpt_key in self.data_files[data_key] \
                if (cpt_key.component in cmpts)} \
            )
            # take shortest chunk frequency (revisit?)
            chunk_freq = min(cpt_key.chunk_freq \
                for cpt_key in self.data_files[data_key] \
                if cpt_key.component == cmpt)
            cpt_key = self.ComponentKey(component=cmpt, chunk_freq=chunk_freq)
            print "Selected (component, chunk) = ({}, {}) for {} @ {}".format(
                cmpt, chunk_freq, data_key.name_in_model, data_key.date_freq)

            assert self._component_map[cpt_key, data_key] # shouldn't have eliminated everything
            self.data_files[data_key] = sorted(
                self._component_map[cpt_key, data_key], 
                key=lambda ds: ds.date_range.start
            )

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

    def _select_model_component(self):
        """Determine experiment component(s) from heuristics.

        1. Pick all data from the same component if possible, and from as few
            components if not. See `https://en.wikipedia.org/wiki/Set_cover_problem`_ 
            and `http://www.martinbroadhurst.com/greedy-set-cover-in-python.html`_.

        2. If multiple components satisfy (1) equally well, use a tie-breaking 
            heuristic (:meth:`~gfdl.GfdlppDataManager._heuristic_component_tiebreaker`). 

        Args:
            datasets (iterable of :class:`~util.DataSet`): 
                Collection of all variables being requested in this DataManager.

        Returns: :obj:`list` of :obj:`str`: name(s) of model components to use.

        Raises: AssertionError if problem is unsatisfiable. This indicates some
            error in the input data.
        """
        all_idx = set()
        d = defaultdict(set)
        for idx, data_key in enumerate(self.data_files.keys()):
            for cpt_key in self.data_files[data_key]:
                d[cpt_key.component].add(idx)
            all_idx.add(idx)
        assert set(e for s in d.values() for e in s) == all_idx

        covered_idx = set()
        cover = []
        while covered_idx != all_idx:
            # max() with key=... only returns one entry if there are duplicates
            # so we need to do two passes in order to call our tiebreaker logic
            max_uncovered = max(len(val - covered_idx) for val in d.values())
            cmpt_to_add = self._heuristic_component_tiebreaker(
                [key for key,val in d.iteritems() \
                    if (len(val - covered_idx) == max_uncovered)]
            )
            cover.append(cmpt_to_add)
            covered_idx.update(d[cmpt_to_add])
        assert cover # is not empty
        return cover

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

    def fetch_dataset(self, d_key, method='auto', dry_run=False):
        """Copy files to temporary directory and combine chunks.
        """
        (cp_command, smartsite) = self._determine_fetch_method(method)
        dest_path = self.local_path(d_key)
        dest_dir, _ = os.path.split(dest_path)
        # ncrcat will error instead of creating destination directories
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        if len(self.data_files[d_key]) == 1:
            # one chunk, no need to ncrcat, copy directly
            work_dir = dest_path
        else:
            paths = util.PathManager()
            work_dir = paths.make_tempdir(hash_obj = d_key)

        # copy remote files
        # TODO: Do something intelligent with logging, caught OSErrors
        for f in self.data_files[d_key]:
            print "\tcopying pp{} to {}".format(
                f._remote_data[len(self.root_dir):], work_dir)
            if dry_run:
                continue
            util.run_command(cp_command + [
                smartsite + f._remote_data, 
                # gcp requires trailing slash, ln ignores it
                smartsite + work_dir + os.sep
            ], timeout=self.file_transfer_timeout) 

        # crop time axis to requested range
        translate = util.VariableTranslator()
        time_var_name = translate.fromCF(self.convention, 'time_coord')
        trim_count = 0
        for f in self.data_files[d_key]:
            trimmed_range = f.date_range.intersection(self.date_range)
            if trimmed_range != f.date_range:
                file_name = os.path.basename(f._remote_data)
                print "\ttrimming '{}' of {} from {} to {}".format(
                    time_var_name, file_name, f.date_range, trimmed_range)
                trim_count = trim_count + 1
                if dry_run:
                    continue
                self.nc_crop_time_axis(
                    time_var_name, trimmed_range, file_name, 
                    working_dir=work_dir)
        assert trim_count <= 2

        # cat chunks to destination, if more than one
        if len(self.data_files[d_key]) > 1:
            # not running in shell, so can't use glob expansion.
            print "\tcatting {} chunks to {}".format(
                d_key.name_in_model, dest_path)
            chunks = [os.path.basename(f._remote_data) for f in self.data_files[d_key]]
            if not dry_run:
                self.nc_cat_chunks(chunks, dest_path, working_dir=work_dir)
        # temp files cleaned up by data_manager.tearDown

    def _determine_fetch_method(self, method='auto'):
        _methods = {
            'gcp': {'command': ['gcp', '--sync', '-v', '-cd'], 'site':'gfdl:'},
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

    def _copy_to_output(self):
        # pylint: disable=maybe-no-member
        # use gcp, since OUTPUT_DIR might be mounted read-only
        paths = util.PathManager()
        if paths.OUTPUT_DIR != paths.WORKING_DIR:
            util.run_command(['gcp','-r','-v','--sync',
                'gfdl:' + self.MODEL_WK_DIR + os.sep,
                'gfdl:' + self.MODEL_OUT_DIR + os.sep
            ])

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
