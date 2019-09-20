import os
import sys
import re
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except (ImportError, ModuleNotFoundError):
        import subprocess
else:
    import subprocess
from collections import defaultdict
import datelabel
from util import Singleton, find_files, BiDict
from data_manager import DataManager
from environment_manager import VirtualenvEnvironmentManager, CondaEnvironmentManager

_current_module_versions = {
    'python':   'python/2.7.12',
    'ncl':      'ncarg/6.5.0',
    'r':        'R/3.4.4',
    'anaconda': 'anaconda2/5.1',
    'gcp':      'gcp/2.3',
    'nco':      'nco/4.7.6',
    'netcdf':   'netcdf/4.2'
}

class ModuleManager(Singleton):
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
        modMgr = ModuleManager()
        super(GfdlvirtualenvEnvironmentManager, self).__init__(config, verbose)

    def create_environment(self, env_name):
        modMgr = ModuleManager()
        modMgr.load(_current_module_versions[env_name])
        super(GfdlvirtualenvEnvironmentManager, \
            self).create_environment(env_name)

    def activate_env_command(self, pod):
        mod_name = _current_module_versions[pod.env]
        parent_cmd = super(GfdlvirtualenvEnvironmentManager, \
            self).activate_env_command(pod)
        return 'module load {} && {}'.format(mod_name, parent_cmd)

    def deactivate_env_command(self, pod):
        mod_name = _current_module_versions[pod.env]
        parent_cmd = super(GfdlvirtualenvEnvironmentManager, \
            self).deactivate_env_command(pod)
        return '{} && module unload {}'.format(parent_cmd, mod_name)

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
    def __init__(self, root_dir, case_dict, config={}, verbose=0):
        super(GfdlppDataManager, self).__init__(case_dict, config, verbose)
        assert os.path.isdir(root_dir)
        self.root_dir = root_dir

        # load required modules
        modMgr = ModuleManager()
        modMgr.load(_current_module_versions['gcp'])
        modMgr.load(_current_module_versions['nco'])

    def parse_pp_path(self, path):
        ts_regex = re.compile(r"""
            (?P<component>\w+)/        # component name
            ts/                     
            (?P<date_freq>\w+)/        # ts freq
            (?P<chunk_freq>\w+)/        
            (?P<component2>\w+)\.        # component name (again)
            (?P<start_date>\d+)-(?P<end_date>\d+)\.   # d ate range
            (?P<field_name>\w+)\.       # field name
            nc       
        """, re.VERBOSE)
        # TODO: handle time averages (not needed now)
        match = re.match(ts_regex, path)
        if match:
            assert match.group('component') == match.group('component2')
            ds = DataSet(**match.groupdict())
            ds.remote_resource = path
            (ds.dir, ds.file) = os.path.split(path)
            ds.date_range = datelabel.DateRange(ds.start_date, ds.end_date)
            ds.date_freq = datelabel.DateFrequency(ds.date_freq)
            ds.chunk_freq = datelabel.DateFrequency(ds.chunk_freq)
            return ds
        else:
            raise ValueError

    def query_dataset(self, dataset):
        if 'component' in dataset:
            component = dataset.component
        else:
            component = '*'
        pattern = '{}/ts/{}/*.{}.nc'.format(
            component, dataset.date_freq.format_frepp(), dataset.name
        )
        files = find_files(self.root_dir, pattern)
        if not files:
            raise DataQueryFailure(dataset, 'No files found in {}'.format(self.root_dir))
        
        dataset.remote_resource = []
        dir_dict = defaultdict(list)
        for f in files:
            ds = self.parse_pp_path(f)
            dir_dict[ds.dir].append(ds)
        for ds_dir in dir_dict.values():
            try:
                remote_range = datelabel.DateRange([ds.date_range for ds in ds_dir])
            except ValueError:
                # Something's messed up with remote files if we get here
                # should probably log an error
                continue
            if remote_range.contains(dataset.date_range):
                dataset.remote_resource.extend(
                    [ds for ds in ds_dir if (ds.date_range in dataset.date_range)]
                )
        
        if not dataset.remote_resource:
            raise DataQueryFailure(dataset, 
                "Couldn't cover date range {} with files in {}".format(
                    datset.date_range, self.root_dir))

    def _optimize_data_fetching(self, datasets):
        cmpts = self._select_model_component(datasets):
        for ds in datasets:
            ds_list = [d for d in ds.remote_resource if (d.component in cmpts)]
            # take longest chunk frequency (revisit?)
            chunk_freq = max({d.chunk_freq for d in ds_list})
            ds.remote_resource = [d for d in ds_list if (d.chunk_freq == chunk_freq)]
            assert ds.remote_resource # shouldn't have eliminated everything

    def _select_model_component(self, datasets):
        """Determine experiment component(s) from heuristics.

        1. Pick all data from the same component if possible, and from as few
            components if not. See `https://en.wikipedia.org/wiki/Set_cover_problem`_ 
            and `http://www.martinbroadhurst.com/greedy-set-cover-in-python.html`_.

        2. If multiple components satisfy (1) equally well, select those
            containing 'cmip'.

        3. If we still have multiple components satisfying (1) and (2), break the
            tie by selecting the one with the fewest words (separated by '_'), 
            or, failing that, the shortest overall name.

        Args:
            dataset (:obj:`list` of :class:`~data_manager.DataManager.DataSet`):

        Returns: :obj:`list` of :obj:`str`: name(s) of model components to use.

        Raises: AssertionError if problem is unsatisfiable. This indicates some
            error in the input data.
        """
        def _heuristic_tiebreaker(str_list):
            cmip_list = [s for s in str_list if ('cmip' in s.lower())]
            if cmip_list:
                return _heuristic_tiebreaker_sub(cmip_list)
            else:
                return _heuristic_tiebreaker_sub(str_list)

        def _heuristic_tiebreaker_sub(str_list):
            min_len = min(len(s.split('_')) for s in str_list)
            str_list2 = [s for s in str_list if (len(s.split('_')) == min_len)]
            if len(str_list2) == 1:
                return str_list2
            else:
                return min(str_list2, key=len)

        d = defaultdict(set)
        for idx, ds in enumerate(datasets):
            d[ds.component].add(idx)
        all_idx = set(range(len(datasets)))
        assert set(e for s in d.values() for e in s) == all_idx

        covered_idx = set()
        cover = []
        while covered_idx != all_idx:
            # max() with key=... only returns one entry if there are duplicates
            # so we need to do two passes in order to call our tiebreaker logic
            max_uncovered = max(len(val - covered_idx) for val in d.values())
            cmpt_to_add = _heuristic_tiebreaker(
                [key for key,val in d.iteritems() \
                    if (len(val - covered_idx) == max_uncovered)]
            )
            cover.append(cmpt_to_add)
            covered_idx.update(d[cmpt_to_add])
        assert cover # is not empty
        return cover




def parse_frepp_stub(frepp_stub):
    """Converts the frepp arguments to a Python dictionary.

    See `https://wiki.gfdl.noaa.gov/index.php/FRE_User_Documentation#Automated_creation_of_diagnostic_figures`_.

    Returns: :obj:`dict` of frepp parameters.
    """
    frepp_translate = {
        'in_data_dir': 'MODEL_DATA_ROOT',
        'descriptor': 'CASENAME',
        'out_dir': 'OUTPUT_DIR',
        'WORKDIR': 'WORKING_DIR',
        'yr1': 'FIRSTYR',
        'yr2': 'LASTYR'
    }
    # parse arguments and relabel keys
    d = {}
    # look for "set ", match token, skip spaces or "=", then match string of 
    # characters to end of line
    regex = r"\s*set (\w+)\s+=?\s*([^=#\s]\b|[^=#\s].*[^\s])\s*$"
    for line in frepp_stub.splitlines():
        print "line = '{}'".format(line)
        match = re.match(regex, line)
        if match:
            if match.group(1) in frepp_translate:
                key = frepp_translate[match.group(1)]
            else:
                key = match.group(1)
            d[key] = match.group(2)

    # cast from string
    for int_key in ['FIRSTYR', 'LASTYR', 'verbose']:
        if int_key in d:
            d[int_key] = int(d[int_key])
    for bool_key in ['make_variab_tar', 'test_mode']:
        if bool_key in d:
            d[bool_key] = bool(d[bool_key])

    d['frepp_mode'] = ('MODEL_DATA_ROOT' in d)
    return d