"""Common functions and classes used in multiple places in the MDTF code. 
"""
import os
import io
import re
import glob
import shutil
import string
import tempfile
from src import util, cli

class MDTFConfigurer(object):
    def __init__(self, code_root=None, cli_rel_path=None):
        """Set up CLI; parse and store arguments
        """
        # print('\tDEBUG: argv = {}'.format(sys.argv[1:]))
        assert code_root # singleton, so this method should only be called once
        self.code_root = code_root
        self.pod_list = []
        self.case_list = []
        self.global_env_vars = dict()

        cli_obj = cli.FrameworkCLIHandler(code_root, cli_rel_path)
        self._cli_pre_parse_hook(cli_obj)
        cli_obj.parse_cli()
        self._cli_post_parse_hook(cli_obj)
        # load pod data
        pod_info_tuple = cli.load_pod_settings(code_root)
        self.pod_data = pod_info_tuple.pod_data
        self.all_realms = pod_info_tuple.sorted_lists.get('realms', [])
        self.pod_realms = pod_info_tuple.realm_data
        self.parse_mdtf_args(cli_obj)
        # init singletons
        config = ConfigManager(cli_obj, self.pod_data, self.case_list, 
            self.global_env_vars)
        paths = PathManager(code_root, cli_obj)
        self.verify_paths(config, paths)
        # use WORKING_DIR for temp data
        _ = TempDirManager(paths.WORKING_DIR)
        _ = VariableTranslator(code_root)

        # config should be read-only from here on
        self._post_parse_hook(cli_obj, config, paths)
        self._print_config(cli_obj, config, paths)

    def _cli_pre_parse_hook(self, cli_obj):
        # gives subclasses the ability to customize CLI handler before parsing
        # although most of the work done by parse_mdtf_args
        pass

    def _cli_post_parse_hook(self, cli_obj):
        # gives subclasses the ability to customize CLI handler after parsing
        # although most of the work done by parse_mdtf_args
        if cli_obj.config.get('dry_run', False):
            cli_obj.config['test_mode'] = True

    @staticmethod
    def _populate_from_cli(cli_obj, group_nm, target_d=None):
        if target_d is None:
            target_d = dict()
        for key, val in cli_obj.iteritems_cli(group_nm):
            if val: # assign nonempty items only
                target_d[key] = val
        return target_d

    def parse_mdtf_args(self, cli_obj):
        """Parse script options returned by the CLI. For greater customizability,
        most of the functionality is spun out into sub-methods.
        """
        self.parse_env_vars(cli_obj)
        self.parse_pod_list(cli_obj)
        self.parse_case_list(cli_obj)

    def parse_env_vars(self, cli_obj):
        # don't think PODs use global env vars?
        # self.env_vars = self._populate_from_cli(cli_obj, 'PATHS', self.env_vars)
        self.global_env_vars['RGB'] = os.path.join(self.code_root,'src','rgb')
        # globally enforce non-interactive matplotlib backend
        # see https://matplotlib.org/3.2.2/tutorials/introductory/usage.html#what-is-a-backend
        self.global_env_vars['MPLBACKEND'] = "Agg"

    def parse_pod_list(self, cli_obj):
        args = util.to_iter(cli_obj.config.pop('pods', []), set)
        if 'example' in args or 'examples' in args:
            self.pod_list = [pod for pod in self.pod_data \
                if pod.startswith('example')]
        elif 'all' in args:
            self.pod_list = [pod for pod in self.pod_data \
                if not pod.startswith('example')]
        else:
            # specify pods by realm
            realms = args.intersection(set(self.all_realms))
            args = args.difference(set(self.all_realms)) # remainder
            for key in self.pod_realms:
                if util.to_iter(key, set).issubset(realms):
                    self.pod_list.extend(self.pod_realms[key])
            # specify pods by name
            pods = args.intersection(set(self.pod_data))
            self.pod_list.extend(list(pods))
            for arg in args.difference(set(self.pod_data)): # remainder:
                print("WARNING: Didn't recognize POD {}, ignoring".format(arg))
            # exclude examples
            self.pod_list = [pod for pod in self.pod_list \
                if not pod.startswith('example')]
        if not self.pod_list:
            print(("WARNING: no PODs selected to be run. Do `./mdtf info pods`"
            " for a list of available PODs, and check your -p/--pods argument."))
            print('Received --pods = {}'.format(list(args)))
            exit()

    def parse_case_list(self, cli_obj):
        case_list_in = util.to_iter(cli_obj.case_list)
        cli_d = self._populate_from_cli(cli_obj, 'MODEL')
        if 'CASE_ROOT_DIR' not in cli_d and cli_obj.config.get('root_dir', None): 
            # CASE_ROOT was set positionally
            cli_d['CASE_ROOT_DIR'] = cli_obj.config['root_dir']
        if not case_list_in:
            case_list_in = [cli_d]
        case_list = []
        for case_tup in enumerate(case_list_in):
            case_list.append(self.parse_case(case_tup, cli_d, cli_obj))
        self.case_list = [case for case in case_list if case is not None]
        if not self.case_list:
            print("ERROR: no valid entries in case_list. Please specify model run information.")
            print('Received:')
            print(util.pretty_print_json(case_list_in))
            exit(1)

    def parse_case(self, case_tup, cli_d, cli_obj):
        n, d = case_tup
        if 'CASE_ROOT_DIR' not in d and 'root_dir' in d:
            d['CASE_ROOT_DIR'] = d.pop('root_dir')
        case_convention = d.get('convention', '')
        d.update(cli_d)
        if case_convention:
            d['convention'] = case_convention

        if not ('CASENAME' in d or ('model' in d and 'experiment' in d)):
            print(("WARNING: Need to specify either CASENAME or model/experiment "
                "in caselist entry {}, skipping.").format(n+1))
            return None
        _ = d.setdefault('model', d.get('convention', ''))
        _ = d.setdefault('experiment', '')
        _ = d.setdefault('CASENAME', '{}_{}'.format(d['model'], d['experiment']))

        for field in ['FIRSTYR', 'LASTYR', 'convention']:
            if not d.get(field, None):
                print(("WARNING: No value set for {} in caselist entry {}, "
                    "skipping.").format(field, n+1))
                return None
        # if pods set from CLI, overwrite pods in case list
        d['pod_list'] = self.set_case_pod_list(d, cli_obj)
        return d

    def set_case_pod_list(self, case, cli_obj):
        # if pods set from CLI, overwrite pods in case list
        # already finalized self.pod-list by the time we get here
        if not cli_obj.is_default['pods'] or not case.get('pod_list', None):
            return self.pod_list
        else:
            return case['pod_list']

    def _post_parse_hook(self, cli_obj, config, paths):
        # init other services
        pass

    def verify_paths(self, config, p):
        keep_temp = config.get('keep_temp', False)
        # clean out WORKING_DIR if we're not keeping temp files:
        if os.path.exists(p.WORKING_DIR) and not \
            (keep_temp or p.WORKING_DIR == p.OUTPUT_DIR):
            shutil.rmtree(p.WORKING_DIR)
        util.check_dirs(p.CODE_ROOT, p.OBS_DATA_ROOT, create=False)
        util.check_dirs(p.MODEL_DATA_ROOT, p.WORKING_DIR, p.OUTPUT_DIR,
            create=True)

    def _print_config(self, cli_obj, config, paths):
        # make config nested dict for backwards compatibility
        # this is all temporary
        d = dict()
        for n, case in enumerate(config.case_list):
            key = 'case_list({})'.format(n)
            d[key] = case
        # d['pod_list'] = self.pod_list
        d['paths'] = paths.toDict()
        d['paths'].pop('_unittest', None)
        d['settings'] = dict()
        settings_gps = set(cli_obj.parser_groups).difference(
            set(['parser','PATHS','MODEL','DIAGNOSTICS'])
        )
        for group in settings_gps:
            d['settings'] = self._populate_from_cli(cli_obj, group, d['settings'])
        d['settings'] = {k:v for k,v in iter(d['settings'].items()) \
            if k not in d['paths']}
        d['env_vars'] = config.global_env_vars
        print('DEBUG: SETTINGS:')
        print(util.pretty_print_json(d))


class ConfigManager(util.Singleton, util.NameSpace):
    def __init__(self, cli_obj=None, pod_data=None, case_list=None, 
        global_env_vars=None, unittest=False):
        self.update(cli_obj.config)
        self.pods = pod_data
        self.case_list = case_list
        self.global_env_vars = global_env_vars


class PathManager(util.Singleton, util.NameSpace):
    """:class:`~util.Singleton` holding root paths for the MDTF code. These are
    set in the ``paths`` section of ``defaults.jsonc``.
    """
    def __init__(self, code_root=None, cli_obj=None, env=None, unittest=False):
        self.CODE_ROOT = code_root
        if not self._unittest:
            assert os.path.isdir(self.CODE_ROOT)

        d = cli_obj.config
        # set by CLI settings that have "parse_type": "path" in JSON entry
        paths_to_parse = cli_obj.custom_types.get('path', [])
        if not paths_to_parse:
            print("Warning: didn't get list of paths from CLI.")
        for key in paths_to_parse:
            self[key] = self._init_path(key, d, env=env)
            if key in d:
                d[key] = self[key]

        # set following explictly: redundant, but keeps linter from complaining
        self.OBS_DATA_ROOT = self._init_path('OBS_DATA_ROOT', d, env=env)
        self.MODEL_DATA_ROOT = self._init_path('MODEL_DATA_ROOT', d, env=env)
        self.WORKING_DIR = self._init_path('WORKING_DIR', d, env=env)
        self.OUTPUT_DIR = self._init_path('OUTPUT_DIR', d, env=env)

        if not self.WORKING_DIR:
            self.WORKING_DIR = self.OUTPUT_DIR

    def _init_path(self, key, d, env=None):
        if self._unittest: # use in unit testing only
            return 'TEST_'+key
        else:
            # need to check existence in case we're being called directly
            assert key in d, 'Error: {} not initialized.'.format(key)
            return util.resolve_path(
                util.from_iter(d[key]), root_path=self.CODE_ROOT, env=env
            )

    def model_paths(self, case, overwrite=False):
        d = util.NameSpace()
        if isinstance(case, dict):
            name = case['CASENAME']
            yr1 = case['FIRSTYR']
            yr2 = case['LASTYR']
        else:
            name = case.case_name
            yr1 = case.attrs.date_range.start.format(precision=1)
            yr2 = case.attrs.date_range.end.format(precision=1)
        case_wk_dir = 'MDTF_{}_{}_{}'.format(name, yr1, yr2)
        d.MODEL_DATA_DIR = os.path.join(self.MODEL_DATA_ROOT, name)
        d.MODEL_WK_DIR = os.path.join(self.WORKING_DIR, case_wk_dir)
        d.MODEL_OUT_DIR = os.path.join(self.OUTPUT_DIR, case_wk_dir)
        if not overwrite:
            # bump both WK_DIR and OUT_DIR to same version because name of 
            # former may be preserved when we copy to latter, depending on 
            # copy method
            d.MODEL_WK_DIR, ver = util.bump_version(
                d.MODEL_WK_DIR, extra_dirs=[self.OUTPUT_DIR])
            d.MODEL_OUT_DIR, _ = util.bump_version(d.MODEL_OUT_DIR, new_v=ver)
        return d

    def pod_paths(self, pod, case):
        d = util.NameSpace()
        d.POD_CODE_DIR = os.path.join(self.CODE_ROOT, 'diagnostics', pod.name)
        d.POD_OBS_DATA = os.path.join(self.OBS_DATA_ROOT, pod.name)
        d.POD_WK_DIR = os.path.join(case.MODEL_WK_DIR, pod.name)
        d.POD_OUT_DIR = os.path.join(case.MODEL_OUT_DIR, pod.name)
        d.DATADIR = d.POD_WK_DIR # synonym so we don't need to change docs
        d.TEMP_HTML = case.TEMP_HTML
        return d


class TempDirManager(util.Singleton):
    _prefix = 'MDTF_temp_'

    def __init__(self, temp_root=None):
        if not temp_root:
            temp_root = tempfile.gettempdir()
        assert os.path.isdir(temp_root)
        self._root = temp_root
        self._dirs = []

    def make_tempdir(self, hash_obj=None):
        if hash_obj is None:
            new_dir = tempfile.mkdtemp(prefix=self._prefix, dir=self._root)
        elif isinstance(hash_obj, str):
            new_dir = os.path.join(self._root, self._prefix+hash_obj)
        else:
            # nicer-looking hash representation
            hash_ = hex(hash(hash_obj))[2:]
            assert isinstance(hash_, str)
            new_dir = os.path.join(self._root, self._prefix+hash_)
        if not os.path.isdir(new_dir):
            os.makedirs(new_dir)
        assert new_dir not in self._dirs
        self._dirs.append(new_dir)
        return new_dir

    def rm_tempdir(self, path):
        assert path in self._dirs
        self._dirs.remove(path)
        print("\tDEBUG: cleanup temp dir {}".format(path))
        shutil.rmtree(path)

    def cleanup(self):
        for d in self._dirs:
            self.rm_tempdir(d)

class ConventionError(Exception):
    pass

class VariableTranslator(util.Singleton):
    def __init__(self, code_root=None, unittest=False, verbose=0):
        if unittest:
            # value not used, when we're testing will mock out call to read_json
            # below with actual translation table to use for test
            config_files = ['dummy_filename']
        else:
            glob_pattern = os.path.join(
                code_root, 'src', 'fieldlist_*.jsonc'
            )
            config_files = glob.glob(glob_pattern)
        # always have CF-compliant option, which does no translation
        self.axes = {
            'CF': {
                "lon" : {"axis" : "X", "MDTF_envvar" : "lon_coord"},
                "lat" : {"axis" : "Y", "MDTF_envvar" : "lat_coord"},
                "lev" : {"axis" : "Z", "MDTF_envvar" : "lev_coord"},
                "time" : {"axis" : "T", "MDTF_envvar" : "time_coord"}
        }}
        self.variables = {'CF': dict()}
        self.units = {'CF': dict()}
        for f in config_files:
            d = util.read_json(f)
            for conv in util.to_iter(d['convention_name']):
                if verbose > 0: 
                    print('XXX found ', conv)
                if conv in self.variables:
                    print(f"ERROR: convention {conv} defined in {f} already exists")
                    raise ConventionError

                self.axes[conv] = d.get('axes', dict())
                self.variables[conv] = util.MultiMap(d.get('var_names', dict()))
                self.units[conv] = util.MultiMap(d.get('units', dict()))

    def to_CF(self, convention, v_name):
        if convention == 'CF': 
            return v_name
        assert convention in self.variables, \
            f"Variable name translation doesn't recognize {convention}."
        inv_lookup = self.variables[convention].inverse()
        try:
            return util.from_iter(inv_lookup[v_name])
        except KeyError:
            print(f"ERROR: name {v_name} not defined for convention {convention}.")
            raise
    
    def from_CF(self, convention, v_name):
        if convention == 'CF': 
            return v_name
        assert convention in self.variables, \
            f"Variable name translation doesn't recognize {convention}."
        try:
            return self.variables[convention].get_(v_name)
        except KeyError:
            print(f"ERROR: name {v_name} not defined for convention {convention}.")
            raise
