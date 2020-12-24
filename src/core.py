"""Common functions and classes used in multiple places in the MDTF code. 
"""
import os
import sys
import io
import collections
import copy
import dataclasses as dc
import re
import glob
import shutil
import signal
import string
import tempfile
import traceback
from src import util, cli, mdtf_info, data_model, xr_util
import cfunits

import logging
_log = logging.getLogger(__name__)

class MDTFFramework(object):
    def __init__(self, cli_obj):
        # print('\tDEBUG: argv = {}'.format(sys.argv[1:]))
        self.code_root = cli_obj.code_root
        self.pod_list = []
        self.case_list = []
        self.cases = []
        self.global_env_vars = dict()
        try:
            # load pod data
            pod_info_tuple = mdtf_info.load_pod_settings(self.code_root)
            # load log config
            log_config = cli.read_config_file(
                self.code_root, "logging.jsonc", site=cli_obj.site
            )
            self.configure(cli_obj, pod_info_tuple, log_config)
        except Exception as exc:
            wrapped_exc = traceback.TracebackException.from_exception(exc)
            _log.critical("Framework caught exception %s", repr(exc))
            print(''.join(wrapped_exc.format()))
        
    def configure(self, cli_obj, pod_info_tuple, log_config):
        """Wrapper for all configuration done based on CLI arguments.
        """
        self._cli_post_parse_hook(cli_obj)
        self.dispatch_classes(cli_obj)
        self.parse_mdtf_args(cli_obj, pod_info_tuple)
        # init singletons
        config = ConfigManager(cli_obj, pod_info_tuple, 
            self.global_env_vars, self.case_list, log_config)
        paths = PathManager(cli_obj)
        self.verify_paths(config, paths)
        _ = TempDirManager(paths.WORKING_DIR)
        _ = VariableTranslator(self.code_root)

        # config should be read-only from here on
        self._post_parse_hook(cli_obj, config, paths)
        self._print_config(cli_obj, config, paths)

    def _cli_post_parse_hook(self, cli_obj):
        # gives subclasses the ability to customize CLI handler after parsing
        # although most of the work done by parse_mdtf_args
        if cli_obj.config.get('dry_run', False):
            cli_obj.config['test_mode'] = True

    def dispatch_classes(self, cli_obj):
        def _dispatch(setting):
            return cli_obj.imports[setting]

        self.DataSource = _dispatch('data_manager')
        self.EnvironmentManager = _dispatch('environment_manager')
        self.RuntimeManager = _dispatch('runtime_manager')
        self.OutputManager = _dispatch('output_manager')

    @staticmethod
    def _populate_from_cli(cli_obj, group_nm, target_d=None):
        if target_d is None:
            target_d = dict()
        for arg in cli_obj.iter_group_actions(subcommand=None, group=group_nm):
            key = arg.dest
            val = cli_obj.config.get(key, None)
            if val: # assign nonempty items only
                target_d[key] = val
        return target_d

    def parse_mdtf_args(self, cli_obj, pod_info_tuple):
        """Parse script options returned by the CLI. For greater customizability,
        most of the functionality is spun out into sub-methods.
        """
        self.parse_env_vars(cli_obj)
        self.parse_pod_list(cli_obj, pod_info_tuple)
        self.parse_case_list(cli_obj)

    def parse_env_vars(self, cli_obj):
        # don't think PODs use global env vars?
        # self.env_vars = self._populate_from_cli(cli_obj, 'PATHS', self.env_vars)
        self.global_env_vars['RGB'] = os.path.join(self.code_root,'src','rgb')
        # globally enforce non-interactive matplotlib backend
        # see https://matplotlib.org/3.2.2/tutorials/introductory/usage.html#what-is-a-backend
        self.global_env_vars['MPLBACKEND'] = "Agg"

    def parse_pod_list(self, cli_obj, pod_info_tuple):
        pod_data = pod_info_tuple.pod_data
        all_realms = pod_info_tuple.sorted_lists.get('realms', [])
        pod_realms = pod_info_tuple.realm_data

        args = util.to_iter(cli_obj.config.pop('pods', []), set)
        if 'example' in args or 'examples' in args:
            self.pod_list = [p for p in pod_data if p.startswith('example')]
        elif 'all' in args:
            self.pod_list = [p for p in pod_data if not p.startswith('example')]
        else:
            # specify pods by realm
            realms = args.intersection(all_realms)
            args = args.difference(all_realms) # remainder
            for key in pod_realms:
                if util.to_iter(key, set).issubset(realms):
                    self.pod_list.extend(pod_realms[key])
            # specify pods by name
            pods = args.intersection(set(pod_data))
            self.pod_list.extend(list(pods))
            for arg in args.difference(set(pod_data)): # remainder:
                print("WARNING: Didn't recognize POD {}, ignoring".format(arg))
            # exclude examples
            self.pod_list = [p for p in pod_data if not p.startswith('example')]
        if not self.pod_list:
            _log.critical(("ERROR: no PODs selected to be run. Do `./mdtf info pods`"
                " for a list of available PODs, and check your -p/--pods argument."
                f"\nReceived --pods = {str(list(args))}"))
            exit(1)

    def parse_case_list(self, cli_obj):
        d = cli_obj.config # abbreviate
        if 'CASENAME' in d and d['CASENAME']:
            # defined case from CLI
            cli_d = self._populate_from_cli(cli_obj, 'MODEL')
            if 'CASE_ROOT_DIR' not in cli_d and d.get('root_dir', None): 
                # CASE_ROOT was set positionally
                cli_d['CASE_ROOT_DIR'] = d['root_dir']
            case_list_in = [cli_d]
        else:
            case_list_in = util.to_iter(cli_obj.file_case_list)
        case_list = []
        for i, case_d in enumerate(case_list_in):
            case_list.append(self.parse_case(i, case_d, cli_obj))
        self.case_list = [case for case in case_list if case]
        if not self.case_list:
            _log.critical(("ERROR: no valid entries in case_list. Please specify "
                "model run information.\nReceived:"
                f"\n{util.pretty_print_json(case_list_in)}"))
            exit(1)

    def parse_case(self, n, d, cli_obj):
        # really need to move this into init of DataManager
        if 'CASE_ROOT_DIR' not in d and 'root_dir' in d:
            d['CASE_ROOT_DIR'] = d.pop('root_dir')
        case_convention = d.get('convention', '')
        if case_convention:
            d['convention'] = case_convention

        if not ('CASENAME' in d or ('model' in d and 'experiment' in d)):
            _log.warning(("Need to specify either CASENAME or model/experiment "
                "in caselist entry %s, skipping."), n+1)
            return None
        _ = d.setdefault('model', d.get('convention', ''))
        _ = d.setdefault('experiment', '')
        _ = d.setdefault('CASENAME', '{}_{}'.format(d['model'], d['experiment']))

        for field in ['FIRSTYR', 'LASTYR', 'convention']:
            if not d.get(field, None):
                _log.warning(("No value set for %s in caselist entry %s, "
                    "skipping."), field, n+1)
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

    def verify_paths(self, config, p):
        # needs to be here, instead of PathManager, because we subclass it in 
        # NOAA_GFDL
        keep_temp = config.get('keep_temp', False)
        # clean out WORKING_DIR if we're not keeping temp files:
        if os.path.exists(p.WORKING_DIR) and not \
            (keep_temp or p.WORKING_DIR == p.OUTPUT_DIR):
            shutil.rmtree(p.WORKING_DIR)
        util.check_dirs(p.CODE_ROOT, p.OBS_DATA_ROOT, create=False)
        util.check_dirs(p.MODEL_DATA_ROOT, p.WORKING_DIR, p.OUTPUT_DIR,
            create=True)

    def _post_parse_hook(self, cli_obj, config, paths):
        # init other services
        pass

    def _print_config(self, cli_obj, config, paths):
        # make config nested dict for backwards compatibility
        # this is all temporary
        d = dict()
        for n, case in enumerate(self.case_list):
            key = 'case_list({})'.format(n)
            d[key] = case
        # d['pod_list'] = self.pod_list
        d['paths'] = paths.toDict()
        d['paths'].pop('_unittest', None)
        d['settings'] = dict()
        all_groups = set(arg_gp.title for arg_gp in \
            cli_obj.iter_arg_groups(subcommand=None))
        settings_gps = all_groups.difference(
            ('parser','PATHS','MODEL','DIAGNOSTICS'))
        for group in settings_gps:
            d['settings'] = self._populate_from_cli(cli_obj, group, d['settings'])
        d['settings'] = {k:v for k,v in d['settings'].items() \
            if k not in d['paths']}
        d['env_vars'] = config.global_env_vars
        print('DEBUG: SETTINGS:')
        print(util.pretty_print_json(d))

    # --------------------------------------------------------------------

    def run_case(self, case_name, case_d):
        _log.info(f"Framework: initialize {case_name}")
        case = self.DataSource(case_d)
        case.setup()
        self.cases.append(case)

        _log.info(f'Framework: request data for {case_name}')
        case.request_data()

        _log.info(f'Framework: run {case_name}')
        run_mgr = self.RuntimeManager(case.pods, self.EnvironmentManager)
        run_mgr.setup()
        run_mgr.run()
        run_mgr.tear_down()
        self.OutputManager(case)
        return any(p.failed for p in case.pods.values())

    def main(self, foo=None):
        failed = False
        _log.info("\n======= Starting %s", __file__)
        # only run first case in list until dependence on env vars cleaned up
        for d in self.case_list[0:1]:
            case_name = d.get('CASENAME', '')
            failed = failed or self.run_case(case_name, d)

        tempdirs = TempDirManager()
        tempdirs.cleanup()
        print_summary(self)
        return (1 if failed else 0)


class ConfigManager(util.Singleton, util.NameSpace):
    def __init__(self, cli_obj=None, pod_info_tuple=None, global_env_vars=None, 
        case_list=None, log_config=None, unittest=False):
        self.update(cli_obj.config)
        if pod_info_tuple is None:
            self.pod_data = dict()
        else:
            self.pod_data = pod_info_tuple.pod_data
        if global_env_vars is None:
            self.global_env_vars = dict()
        else:
            self.global_env_vars = global_env_vars
        self.log_config = log_config
        # copy srializable version of parsed settings, in order to write 
        # backup config file
        self.backup_config = copy.deepcopy(cli_obj.config) 
        self.backup_config['case_list'] = copy.deepcopy(case_list)


class PathManager(util.Singleton, util.NameSpace):
    """:class:`~util.Singleton` holding root paths for the MDTF code. These are
    set in the ``paths`` section of ``defaults.jsonc``.
    """
    def __init__(self, cli_obj=None, env=None, unittest=False):
        self.CODE_ROOT = cli_obj.code_root
        self._unittest = unittest
        if not self._unittest:
            assert os.path.isdir(self.CODE_ROOT)

        d = cli_obj.config
        # set by CLI settings that have "parse_type": "path" in JSON entry
        cli_paths = [act.dest for act in cli_obj.iter_actions() \
            if isinstance(act, cli.PathAction)]
        if not cli_paths:
            _log.warning("Didn't get list of paths from CLI.")
        for key in cli_paths:
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
            name = case.name
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
        return d


class TempDirManager(util.Singleton):
    _prefix = 'MDTF_temp_'

    def __init__(self, temp_root=None, unittest=False):
        self._unittest = unittest
        if not temp_root:
            temp_root = tempfile.gettempdir()
        if not self._unittest:
            assert os.path.isdir(temp_root)
        self._root = temp_root
        self._dirs = []

        # delete temp files if we're killed
        signal.signal(signal.SIGTERM, self.tempdir_cleanup_handler)
        signal.signal(signal.SIGINT, self.tempdir_cleanup_handler)

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
        _log.debug("Cleaning up temp dir %s", path)
        shutil.rmtree(path)

    def cleanup(self):
        config = ConfigManager()
        if not config.get('keep_temp', False):
            for d in self._dirs:
                self.rm_tempdir(d)

    def tempdir_cleanup_handler(self, signum=None, frame=None):
        # delete temp files
        util.signal_logger(self.__class__.__name__, signum, frame)
        self.cleanup()

# --------------------------------------------------------------------

@util.mdtf_dataclass
class TranslatedVarlistEntry(data_model.DMVariable):
    """Class returned by VarlistTranslator.lookup_variable(). Marks some 
    attributes inherited from DMVariable as participating in 
    DataSource.query_dataset().
    """
    # to be more correct, we should probably have VarlistTranslator return a
    # DMVariable, which is converted to this type on assignment to the
    # VarlistEntry, since metadata fields are specific to the VarlistEntry
    # implementation
    convention: str = util.MANDATORY
    name: str = \
        dc.field(default=util.MANDATORY, metadata={'query': True})
    standard_name: str = \
        dc.field(default=util.MANDATORY, metadata={'query': True})
    units: cfunits.Units = util.MANDATORY
    # axes_set: frozenset = dc.field(default_factory=frozenset)
    scalar_coords: list = \
        dc.field(init=False, default_factory=list, metadata={'query': True})

@util.mdtf_dataclass
class FieldlistEntry(object):
    """Class corresponding to an entry in a fieldlist file.
    """
    name: str = util.MANDATORY           # = name according to this convention
    standard_name: str = util.MANDATORY  # = CF conventions standard name
    units: str = util.MANDATORY          # = units according to this convention
    axes_set: frozenset = dc.field(default_factory=frozenset)
    ndim: dc.InitVar = 4
    scalar_coord_templates: dict = dc.field(default_factory=dict)

    def __post_init__(self, ndim=4):
        if not self.axes_set:
            if ndim == 4:
                self.axes_set = ('T', 'Z', 'Y', 'X')
            elif ndim == 3:
                self.axes_set = ('T', 'Y', 'X')
            elif ndim == 2:
                self.axes_set = ('Y', 'X')
            elif ndim == 1:
                self.axes_set = ('T')
        self.axes_set = frozenset(
            data_model.DMAxis.from_struct(x) for x in self.axes_set
        )
        self.scalar_coord_templates = {
            data_model.DMAxis.from_struct(k): v for k,v \
                in self.scalar_coord_templates.items()
        }
        
@util.mdtf_dataclass
class Fieldlist():
    """Class corresponding to a single variable naming convention (single file
    in src/data/fieldlist_*.jsonc).
    """
    name: str = util.MANDATORY
    axes: dict = dc.field(default_factory=dict)
    entries: util.WormDict = dc.field(default_factory=util.WormDict)
    lut: util.WormDict = dc.field(default_factory=util.WormDict)
    other: dict = dc.field(default_factory=dict)

    @classmethod
    def from_struct(cls, d):
        lut_temp = collections.defaultdict(util.WormDict)

        def _process_one(section_name):
            # build two-stage lookup table -- should just make FieldlistEntry 
            # hashable
            section_d = d.pop(section_name, dict())
            for k,v in section_d.items():
                entry = FieldlistEntry(name=k, **v)
                d['entries'][k] = entry
                lut_temp[entry.standard_name][entry.axes_set] = entry

        d['axes'] = {
            data_model.DMAxis.from_struct(v['axis']): \
                data_model.coordinate_from_struct(v, name=k) \
            for k,v in d['axes'].items() 
        }
        d['entries'] = util.WormDict()
        d['lut'] = util.WormDict()
        _process_one('aux_coords')
        _process_one('variables')
        d['lut'].update(lut_temp)
        return cls(**d)

    def to_CF(self, name):
        """FieldlistEntry for the variable having the given name in this convention.
        """
        return self.entries[name]

    def to_CF_name(self, name):
        """Like :meth:`to_CF`, but only return the CF standard name, given the 
        name in this convention.
        """
        return self.to_CF(name).standard_name

    def from_CF(self, standard_name, axes_set=None):
        """Look up FieldlistEntry corresponding to the given standard name,
        optionally providing an axes_set to resolve ambiguity.

        TODO: this is a hacky implementation; FieldlistEntry needs to be 
        expanded with more ways to uniquely identify variable (eg cell methods).
        """
        if standard_name not in self.lut:
            raise KeyError((f"Standard name '{standard_name}' not defined in "
                f"convention '{self.name}'."))
        lut1 = self.lut[standard_name] # abbreviate
        if axes_set is None:
            entries = tuple(lut1.values())
            if len(entries) > 1:
                raise ValueError((f"Variable name in convention '{self.name}' "
                    f"not uniquely determined by standard name '{standard_name}'."))
            return entries[0]
        else:
            axes_set = frozenset(axes_set)
            if axes_set not in lut1:
                raise KeyError((f"Queried standard name '{standard_name}' with an "
                    f"unexpected set of axes {axes_set} not in convention "
                    f"'{self.name}'."))
            return lut1[axes_set]

    def from_CF_name(self, standard_name, axes_set=None):
        """Like :meth:`from_CF`, but only return the variable's name in this 
        convention.
        """
        return self.from_CF(standard_name, axes_set=axes_set).name

    def lookup_axis(self, ax):
        if not isinstance(ax, data_model.DMAxis):
            ax = data_model.DMAxis.from_struct(ax)
        return self.axes.get(ax, None)

    def lookup_variable(self, var):
        """Returns TranslatedVarlistEntry instance, with populated axes."""
        fl_entry = self.from_CF(var.standard_name, var.phys_axes_set)
        coords = {ax: self.lookup_axis(ax) for ax in fl_entry.axes_set}
        for c in var.scalar_coords:
            coords[c.axis].value = c.value
        return util.coerce_to_dataclass(
            fl_entry, TranslatedVarlistEntry, 
            coords=tuple(coords.values()), convention=self.name
        )

    def translate(self, var):
        """Return a TranslatedVarlistEntry with translated names, units, 
        etc. for var. Includes logic to translate and rename scalar coords/slices,
        e.g. VarlistEntry for 'ua' (4D) @ 500mb could produce a 
        TranslatedVarlistEntry for 'u500' (3D), depending on naming convention.
        """
        fl_entry = self.from_CF(var.standard_name, var.phys_axes_set)
        conv_var = self.lookup_variable(var)

        if len(var.scalar_coords) > 1:
            raise NotImplementedError()
        elif len(var.scalar_coords) == 1:
            # change name in convention, since we're dealing with a slice
            c = var.scalar_coords[0]
            if c.axis not in fl_entry.scalar_coord_templates:
                raise ValueError((f"Don't know how to name {c.axis} slice of "
                    f"{fl_entry.name}."
                ))
            # construct convention's name for this variable on a level
            name_template = fl_entry.scalar_coord_templates[c.axis]
            conv_ax = self.lookup_axis(c.axis)
            value_in_conv = c.value \
                * xr_util.conversion_factor(c.units, conv_ax.units)
            new_name = name_template.format(value=int(value_in_conv))
            if xr_util.are_units_equal(c.units, conv_ax.units):
                _log.debug("Renaming %s %s %s slice of varlist entry '%s' to '%s'.",
                    c.value, c.units, c.axis, var.name, new_name)
            else:
                _log.debug(("Renaming %s slice of varlist entry '%s' to '%s' "
                    "(@ %s %s = %s %s)."),
                    c.axis, var.name, new_name, c.value, c.units, 
                    value_in_conv, conv_ax.units)
            conv_var.name = new_name
        return conv_var


class VariableTranslator(util.Singleton):
    """:class:`~util.Singleton` containing information for different variable 
    naming conventions. These are defined in the src/data/fieldlist_*.jsonc 
    files.
    """
    def __init__(self, code_root=None, unittest=False):
        self._unittest = unittest
        self.conventions = util.WormDict()
        self.aliases = util.WormDict()
        if unittest:
            # value not used, when we're testing will mock out call to read_json
            # below with actual translation table to use for test
            config_files = []
        else:
            glob_pattern = os.path.join(
                code_root, 'src', 'data', 'fieldlist_*.jsonc'
            )
            config_files = glob.glob(glob_pattern)
        for f in config_files:
            try:
                d = util.read_json(f)
                self.add_convention(d)
            except Exception as exc:
                _log.exception("Caught exception loading fieldlist file %s: %s", 
                    f, repr(exc))
                continue

    def add_convention(self, d):
        conv_name = d['name']
        _log.debug("Adding variable name convention '%s'", conv_name)
        for model in d.pop('models', []):
            self.aliases[model] = conv_name
        self.conventions[conv_name] = Fieldlist.from_struct(d)

    def get_convention_name(self, conv_name):
        """Return the Fieldlist object itself, if we want to do lots of lookups
        and want to keep code uncluttered.
        """
        if conv_name in self.conventions:
            return conv_name
        if conv_name in self.aliases:
            _log.debug("Using convention '%s' based on alias '%s'.",
                self.aliases[conv_name], conv_name)
            return self.aliases[conv_name]
        _log.error("Unrecognized variable name convention '%s'.", 
            conv_name)
        raise KeyError(conv_name)

    def get_convention(self, conv_name):
        """Return the Fieldlist object itself, if we want to do lots of lookups
        and want to keep code uncluttered.
        """
        conv_name = self.get_convention_name(conv_name)
        return self.conventions[conv_name]

    def _fieldlist_method(self, conv_name, method_name, *args, **kwargs):
        meth = getattr(self.get_convention(conv_name), method_name)
        return meth(*args, **kwargs)

    def to_CF(self, conv_name, name):
        return self._fieldlist_method(conv_name, 'to_CF', name)

    def to_CF_name(self, conv_name, name):
        return self._fieldlist_method(conv_name, 'to_CF_name', name)

    def from_CF(self, conv_name, standard_name, axes_set=None):
        return self._fieldlist_method(conv_name, 'from_CF', 
            standard_name, axes_set=axes_set)

    def from_CF_name(self, conv_name, standard_name, axes_set=None):
        return self._fieldlist_method(conv_name, 'from_CF_name', 
            standard_name, axes_set=axes_set)

    def lookup_axis(self, conv_name, axis):
        return self._fieldlist_method(conv_name, 'lookup_axis', axis)

    def lookup_variable(self, conv_name, var):
        return self._fieldlist_method(conv_name, 'lookup_variable', var)

    def translate(self, conv_name, var):
        return self._fieldlist_method(conv_name, 'translate', var)

# --------------------------------------------------------------------

def print_summary(fmwk):
    def summary_info_tuple(case):
        """Debug information; will clean this up.
        """
        if not hasattr(case, 'pods') or not case.pods:
            return (
                ['dummy sentinel string'], [],
                getattr(case, 'MODEL_OUT_DIR', '<ERROR: dir not created.>')
            )
        else:
            return (
                [p_name for p_name, p in case.pods.items() if p.failed],
                [p_name for p_name, p in case.pods.items() if not p.failed],
                getattr(case, 'MODEL_OUT_DIR', '<ERROR: dir not created.>')
            )

    d = {c.name: summary_info_tuple(c) for c in fmwk.cases}
    failed = any(len(tup[0]) > 0 for tup in d.values())
    print('\n' + (80 * '-'))
    if failed:
        print(f"Exiting with errors from {__file__}")
        for case_name, tup in d.items():
            print(f"Summary for {case_name}:")
            if tup[0][0] == 'dummy sentinel string':
                print('\tAn error occurred in setup. No PODs were run.')
            else:
                if tup[1]:
                    print((f"\tThe following PODs exited cleanly: "
                        f"{', '.join(tup[1])}"))
                if tup[0]:
                    print((f"\tThe following PODs raised errors: "
                        f"{', '.join(tup[0])}"))
            print(f"\tOutput written to {tup[2]}")
    else:
        print(f"Exiting normally from {__file__}")
        for case_name, tup in d.items():
            print(f"Summary for {case_name}:")
            print(f"\tAll PODs exited cleanly.")
            print(f"\tOutput written to {tup[2]}")
