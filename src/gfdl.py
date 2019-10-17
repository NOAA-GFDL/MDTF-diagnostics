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
from collections import defaultdict
import datelabel
import util
from data_manager import DataManager, DataQueryFailure
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
            ds = util.DataSet(**(match.groupdict()))
            ds.remote_resource = os.path.join(self.root_dir, path)
            (ds.dir, ds.file) = os.path.split(path)
            del ds.component2
            ds.date_range = datelabel.DateRange(ds.start_date, ds.end_date)
            ds.date_freq = datelabel.DateFrequency(ds.date_freq)
            ds.chunk_freq = datelabel.DateFrequency(ds.chunk_freq)
            return ds
        else:
            raise ValueError("Can't parse {}.".format(path))

    def search_pp_path(self, name_in_model, date_freq, component=None):
        """Search a /pp/ directory for files containing a variable.

        At GFDL, data may be archived on a slow tape filesystem, so we attempt
        to speed up the search process relative to :func:`util.find_files`. The 
        only unknowns are the <component> the variable is assigned to and its 
        <chunk_freq> (which will differ from experiment to experiment). 

        Args:
            name_in_model (:obj:`str`): Name of variable to search for, in model's
                naming convention.
            date_freq (:obj:`str`): Desired output frequency.
            component (:obj:`str`, optional): Model component for vairable, if
                known ahead of time.

        Returns: :obj:`list` of :obj:`str`: paths of files found matching search
            criteria. Paths are relative to /pp/ root directory.

        Raises: :exception:`~data_manager.DataManager.DataQueryFailure` if 
            no files matching criteria are found.
        """
        candidate_dirs = []
        if not component:
            cmpts = [d for d in os.listdir(self.root_dir) if not d.startswith('.')]
        else:
            cmpts = [component]
        suffix_query = '.{}.nc'.format(name_in_model)
        for component in cmpts:
            subdir_rel = os.path.join(component, 'ts', date_freq)
            subdir_abs = os.path.join(self.root_dir, subdir_rel)
            if not os.path.exists(subdir_abs):
                continue
            chunk_freqs = [d for d in os.listdir(subdir_abs) if not d.startswith('.')]
            for freq in chunk_freqs:
                # '-quit' means we return immediately when first file is found. 
                # Arguments compatible with BSD (=macs) 'find'.
                paths = util.run_command([
                    'find', os.path.join(subdir_abs, freq), '-name', \
                        '*'+suffix_query, '-print', '-quit'
                ])
                if paths:
                    candidate_dirs.append(os.path.join(subdir_rel, freq))
        if not candidate_dirs:
            raise Exception('No {} files with freq={} found in {}'.format(
                name_in_model, date_freq, self.root_dir))

        files = []
        for d in candidate_dirs:
            files.extend( \
                [os.path.join(d, f) \
                for f in os.listdir(os.path.join(self.root_dir, d)) \
                if f.endswith(suffix_query)] \
            )
        return files

    def query_dataset(self, dataset):
        """Populate remote_resource attribute with list of candidate files.

        Specifically, if a <component> and <chunk_freq> subdirectory has all the
        requested data, return paths to all files we *would* need in that 
        subdirectory. The decision of which <component> and <chunk_freq> to use
        is made in :meth:`~gfdl.GfdlppDataManager.plan_data_fetching` 
        because it requires comparing the files found for *all* requested datasets.
        """
        print "query for {} @ {}".format(dataset.name_in_model, 
            dataset.date_freq.format_frepp())
        dataset.remote_resource = []
        try:
            if 'component' in dataset:
                files = self.search_pp_path( \
                    dataset.name_in_model, dataset.date_freq.format_frepp(), \
                    dataset.component)
            else:
                files = self.search_pp_path( \
                    dataset.name_in_model, dataset.date_freq.format_frepp())
        except Exception as ex:
            raise DataQueryFailure(dataset, str(ex)) # reraise with full dataset
        files = [self.parse_pp_path(f) for f in files]

        candidate_dirs = {f.dir for f in files}
        for d in candidate_dirs:
            try:
                remote_range = datelabel.DateRange( \
                    [f.date_range for f in files if (f.dir == d)])
            except ValueError:
                # Date range of remote files doesn't contain analysis range or 
                # is noncontiguous; should probably log an error
                continue
            if remote_range.contains(dataset.date_range):
                dataset.remote_resource.extend(
                    [f for f in files \
                    if (f.dir == d and f.date_range in dataset.date_range)]
                )
        if not dataset.remote_resource:
            raise DataQueryFailure(dataset, 
                "Couldn't cover date range {} with files in {}".format(
                    dataset.date_range, self.root_dir))

    def plan_data_fetching(self):
        """Filter files on model component and chunk frequency.
        """
        cmpts = self._select_model_component(self.iter_vars())
        print "Components selected: ", cmpts
        for var in self.iter_vars():
            cmpt = self._heuristic_component_tiebreaker( \
                {f.component for f in var.remote_resource if (f.component in cmpts)} \
            )
            # take shortest chunk frequency (revisit?)
            chunk_freq = min(f.chunk_freq \
                for f in var.remote_resource if (f.component == cmpt))
            var.remote_resource = [f for f in var.remote_resource \
                if (f.chunk_freq == chunk_freq and f.component == cmpt)]
            assert var.remote_resource # shouldn't have eliminated everything
        # don't return files, instead fetch_dataset iterates through vars
        return None
        # return super(GfdlppDataManager, self).plan_data_fetching()

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

    def _select_model_component(self, datasets):
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
        for idx, ds in enumerate(datasets):
            for ds_file in ds.remote_resource:
                d[ds_file.component].add(idx)
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
        # return os.path.getmtime(dataset.local_resource) \
        #     >= os.path.getmtime(dataset.remote_resource)

    def fetch_dataset(self, ds_var, method='auto', dry_run=False):
        """Copy files to temporary directory and combine chunks.
        """
        (cp_command, smartsite) = self._determine_fetch_method(method)
        if len(ds_var.remote_resource) == 1:
            # one chunk, no need to ncrcat
            for f in ds_var.remote_resource:
                util.run_command( \
                    cp_command + [
                        smartsite + os.path.join(self.root_dir, f.remote_resource), 
                        ds_var.local_resource
                ])
        else:
            paths = util.PathManager()
            ds_var.nohash_tempdir = paths.make_tempdir(new_dir=ds_var.tempdir())
            chunks = []
            # TODO: Do something intelligent with logging, caught OSErrors
            for f in ds_var.remote_resource:
                print "copying {} to {}".format(f.remote_resource, ds_var.nohash_tempdir)
                util.run_command(cp_command + [
                    smartsite + os.path.join(self.root_dir, f.remote_resource), 
                    # gcp requires trailing slash, ln ignores it
                    smartsite + ds_var.nohash_tempdir + os.sep
                ]) 
                chunks.append(f.file)
            # ncrcat will error instead of creating destination directories
            dest_dir, _ = os.path.split(ds_var.local_resource)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            # not running in shell, so can't use glob expansion.
            util.run_command(['ncrcat', '-O'] + chunks + [ds_var.local_resource], 
                cwd=ds_var.nohash_tempdir)
            # TODO: trim ncrcat'ed files to actual time period
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

    def process_fetched_data(self):
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
