"""Definition of the MDTF framework main loop and classes implementing basic,
supporting functionality.
"""
import os
import sys
import abc
import collections
import copy
import dataclasses as dc
import glob
import shutil
import signal
import tempfile
import traceback
import typing
from src import util, cli, mdtf_info, data_model, units
from src.units import Units

import logging
_log = logging.getLogger(__name__)




@util.mdtf_dataclass
class MDTFObjectBase(metaclass=util.MDTFABCMeta):
    """Base class providing shared functionality for the object hierarchy, which is:

    - The framework itself (:class:`MDTFFramework`);
    - :class:`~data_manager.DataSourceBase`\s belonging to a run of the package;
    - :class:`~diagnostic.Diagnostic`\s (PODs) belonging to a
      :class:`~data_manager.DataSourceBase`;
    - :class:`~diagnostic.VarlistEntry`\s (requested model variables) belonging
      to a :class:`~diagnostic.Diagnostic`.
    """
    _id: util.MDTF_ID = None
    name: str = util.MANDATORY
    _parent: typing.Any = dc.field(default=util.MANDATORY, compare=False)
    status: ObjectStatus = dc.field(default=ObjectStatus.NOTSET, compare=False)

    def __post_init__(self):
        if self._id is None:
            # assign unique ID # so that we don't need to rely on names being unique
            self._id = util.MDTF_ID()
        # init object-level logger
        self.log = util.MDTFObjectLogger.get_logger(self._log_name)

    # the @property decorator allows us to attach code to designated attribute, such as getter and setter methods
    @property
    def _log_name(self):
        if self._parent is None:
            return util.OBJ_LOG_ROOT # framework: root of tree
        else:
            _log_name = f"{self.name}_{self._id}".replace('.', '_')
            return f"{self._parent._log_name}.{_log_name}"

    @property
    def full_name(self):
        return f"<#{self._id}:{self._parent.name}.{self.name}>"

    def __hash__(self):
        return self._id.__hash__()

    @property
    def failed(self):
        return self.status == ObjectStatus.FAILED # abbreviate

    @property
    def active(self):
        return self.status == ObjectStatus.ACTIVE # abbreviate

    @property
    @abc.abstractmethod
    def _children(self):
        """Iterable of child objects associated with this object."""
        pass

    # This is a figurative "birth" routine that generates an object full of child objects
    def iter_children(self, child_type=None, status=None, status_neq=None):
        """Generator iterating over child objects associated with this object.

        Args:
            child_type: None or Type `type`; default None. If None, iterates over
            all child objects regardless of their type
            status: None or :class:`ObjectStatus`, default None. If None,
                iterates over all child objects, regardless of status. If a
                :class:`ObjectStatus` value is passed, only iterates over
                child objects with that status.
            status_neq: None or :class:`ObjectStatus`, default None. If set,
                iterates over child objects which *don't* have the given status.
                If *status* is set, this setting is ignored.
        """
        iter_ = self._children
        if child_type is not None:  # return the iter_ elements that match a specified child_type
            iter_ = filter((lambda x: isinstance(x, child_type)), iter_)
        if status is not None:  # return the iter_ elements that match the specified status
            iter_ = filter((lambda x: x.status == status), iter_)
        elif status_neq is not None:  # return the iter elements that do NOT match status_neq
            iter_ = filter((lambda x: x.status != status_neq), iter_)
        yield from iter_

    def child_deactivation_handler(self, child, exc):
        # needs to test for child_type
        pass

    def child_status_update(self, exc=None):
        if next(self.iter_children(), None) is None:
            # should never get here (no children of any status), because this
            # method should only be called by children
            raise ValueError(f"Children misconfigured for {self.full_name}.")

        # if all children have failed, deactivate self
        if not self.failed and \
            next(self.iter_children(status_neq=ObjectStatus.FAILED), None) is None:
            self.deactivate(util.ChildFailureEvent(self), level=None)

    # level at which to log deactivation events
    _deactivation_log_level = logging.ERROR

    def deactivate(self, exc, level=None):
        # always log exceptions, even if we've already failed
        self.log.store_exception(exc)

        if not (self.failed or self.status == ObjectStatus.SUCCEEDED):
            # only need to log and update on status change for still-active objs
            if level is None:
                level = self._deactivation_log_level # default level for child class
            self.log.log(level, "Deactivated %s due to %r.", self.full_name, exc)

            # update status on self
            self.status = ObjectStatus.FAILED
            if self._parent is not None:
                # call handler on parent, which may change parent and/or siblings
                self._parent.child_deactivation_handler(self, exc)
                self._parent.child_status_update()
            # update children (deactivate all)
            for obj in self.iter_children(status_neq=ObjectStatus.FAILED):
                obj.deactivate(util.PropagatedEvent(exc=exc, parent=self), level=None)

# -----------------------------------------------------------------------------


ConfigTuple = collections.namedtuple(
    'ConfigTuple', 'name backup_filename contents'
)
ConfigTuple.__doc__ = """
    Class wrapping general structs used for configuration.
"""


class ConfigManager(util.Singleton, util.NameSpace):
    def __init__(self, cli_obj=None, pod_info_tuple=None, global_env_vars=None,
                 case_d=None, log_config=None, unittest=False):
        self._unittest = unittest
        self._configs = dict()
        if self._unittest:
            self.pod_data = dict()
        else:
            # normal code path
            self.pod_data = pod_info_tuple.pod_data
            self.update(cli_obj.config)  # the update method is a Python built-in that adds items from
            # an iterable or another dictionary to a dictionary
            backup_config = self.backup_config(cli_obj, case_d)
            self._configs[backup_config.name] = backup_config
            self._configs['log_config'] = ConfigTuple(
                name='log_config',
                backup_filename=None,
                contents=log_config
            )
        if global_env_vars is None:
            self.global_env_vars = dict()
        else:
            self.global_env_vars = global_env_vars

    def backup_config(self, cli_obj, case_d):
        """Copy serializable version of parsed settings, in order to write
        backup config file.
        """
        d = copy.deepcopy(cli_obj.config)
        d = {k:v for k,v in d.items() if not k.endswith('_is_default_')}
        d['case_list'] = copy.deepcopy(case_d)
        return ConfigTuple(
            name='backup_config',
            backup_filename='config_save.json',
            contents=d
        )





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
        util.signal_logger(self.__class__.__name__, signum, frame, log=_log)
        self.cleanup()

# ---------------------------------------------------------------------------


class MDTFFramework(MDTFObjectBase):
    def __init__(self, cli_obj):
        super(MDTFFramework, self).__init__(
            name=self.__class__.__name__,
            _parent=None,
            status=ObjectStatus.ACTIVE
        )
        self.code_root = cli_obj.code_root
        self.pod_list = []
        self.cases = dict()
        self.global_env_vars = dict()
        self.multirun = False
        self.preprocess_data = True
        self.pods = dict()
        try:
            # load pod data
            pod_info_tuple = mdtf_info.load_pod_settings(self.code_root)
            # load log config
            log_config = cli.read_config_file(
                self.code_root, "logging.jsonc", site=cli_obj.site
            )
            self.configure(cli_obj, pod_info_tuple, log_config)
        except Exception as exc:
            tb_exc = traceback.TracebackException(*(sys.exc_info()))
            _log.critical("Framework caught exception %r", exc)
            print(''.join(tb_exc.format()))
            util.exit_handler(code=1)

    @property
    def _children(self):
        """Iterable of child objects associated with this object."""
        if self.multirun:
            return self.pods.values()
        else:
            return self.cases.values()

    @property
    def full_name(self):
        return self.name

    def configure(self, cli_obj, pod_info_tuple, log_config):
        """Wrapper for all configuration done based on CLI arguments.
        """
        self._cli_post_parse_hook(cli_obj)
        self.dispatch_classes(cli_obj)
        self.parse_mdtf_args(cli_obj, pod_info_tuple)
        # init singletons
        config = ConfigManager(cli_obj, pod_info_tuple,
            self.global_env_vars, self.cases, log_config)
        paths = PathManager(cli_obj)
        self.verify_paths(config, paths)
        _ = TempDirManager(paths.TEMP_DIR_ROOT, self.global_env_vars)
        translate = VariableTranslator(self.code_root)
        translate.read_conventions(self.code_root)

        # config should be read-only from here on
        self._post_parse_hook(cli_obj, config, paths)
        self._print_config(cli_obj, config, paths)

    def _cli_post_parse_hook(self, cli_obj):
        # gives subclasses the ability to customize CLI handler after parsing
        # although most of the work done by parse_mdtf_args
        pass

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
            if val:  # assign nonempty items only
                target_d[key] = val
        return target_d

    def parse_mdtf_args(self, cli_obj, pod_info_tuple):
        """Parse script options returned by the CLI. For greater customizability,
        most of the functionality is spun out into sub-methods.
        """
        self.parse_flags(cli_obj)
        self.parse_env_vars(cli_obj)

        if not cli_obj.config.get('pod_list'):
            # pod_list is a separate object from the case_list in multirun mode
            _log.info("pod_list not defined separately from case_list."
                      "Will parse pod_list from cases case_list if present, or use PODs designated by"
                      "--all (default) or --example cli args")
            pod_list = cli_obj.config.pop('pods', [])
            self.pod_list = self.parse_pod_list(pod_list, pod_info_tuple)
        else:
            self.pod_list = cli_obj.config.get('pod_list')

        self.parse_case_list(cli_obj, pod_info_tuple)

    def parse_flags(self, cli_obj):
        if cli_obj.config.get('dry_run', False):
            cli_obj.config['test_mode'] = True

        if cli_obj.config.get('disable_preprocessor', False):
            _log.warning(("User disabled metadata checks and unit conversion in "
                          "preprocessor."),  extra={'tags': {util.ObjectLogTag.BANNER}})
        if cli_obj.config.get('overwrite_file_metadata', False):
            _log.warning(("User chose to overwrite input file metadata with "
                          "framework values (convention = '%s')."),
                         cli_obj.config.get('convention', ''),
                         extra={'tags': {util.ObjectLogTag.BANNER}}
            )
        if cli_obj.config.get('data_type') == 'multi_run':
            self.multirun = True
            _log.info("Running framework in multi-run mode ")
        else:
            _log.info("Running framework in single-run mode ")

        # verify CASE_ROOT_DIR, otherwise error raised about missing caselist is not informative
        try:
            if cli_obj.config.get('CASE_ROOT_DIR', ''):
                util.check_dir(cli_obj.config['CASE_ROOT_DIR'], 'CASE_ROOT_DIR',
                               create=False)
        except Exception as exc:
            _log.fatal((f"Mis-specified input for CASE_ROOT_DIR (received "
                        f"'{cli_obj.config.get('CASE_ROOT_DIR', '')}', caught {repr(exc)}.)"))
            util.exit_handler(code=1)

        if "no_pp" in cli_obj.config.get('data_manager').lower():
            self.preprocess_data = False

    def iter_children(self, child_type=None, status=None, status_neq=None):
        return super().iter_children(child_type, status, status_neq)

    def parse_env_vars(self, cli_obj):
        # don't think PODs use global env vars?
        # self.env_vars = self._populate_from_cli(cli_obj, 'PATHS', self.env_vars)
        self.global_env_vars['RGB'] = os.path.join(self.code_root,'shared','rgb')
        # globally enforce non-interactive matplotlib backend
        # see https://matplotlib.org/3.2.2/tutorials/introductory/usage.html#what-is-a-backend
        self.global_env_vars['MPLBACKEND'] = "Agg"

    def parse_pod_list(self, pod_list, pod_info_tuple):
        pod_data = pod_info_tuple.pod_data # pod names -> contents of settings file
        args = util.to_iter(pod_list, set)
        bad_args = []
        pods = []
        for arg in args:
            if arg == 'all':
                # add all PODs except example PODs
                pods.extend([p for p in pod_data if not p.lower().startswith('example')])
            elif arg == 'example' or arg == 'examples':
                # add example PODs
                if self.multirun:
                    pods.extend([p for p in pod_data if p.lower() == 'example_multicase'])
                else:
                    pods.extend([p for p in pod_data if p.lower() == 'example'])
            elif arg in pod_info_tuple.realm_data:
                # realm_data: realm name -> list of POD names
                # add all PODs for this realm
                pods.extend(pod_info_tuple.realm_data[arg])
            elif arg in pod_data:
                # add POD by name
                pods.append(arg)
            else:
                # unrecognized argument
                _log.error("POD identifier '%s' not recognized.", arg)
                bad_args.append(arg)

        if bad_args:
            valid_args = ['all', 'examples'] \
                + pod_info_tuple.sorted_realms \
                + pod_info_tuple.sorted_pods
            _log.critical(("The following POD identifiers were not recognized: "
                           "[%s].\nRecognized identifiers are: [%s].\n(Received --pods = %s)."),
                          ', '.join(f"'{p}'" for p in bad_args),
                          ', '.join(f"'{p}'" for p in valid_args),
                          str(list(args))
                          )
            util.exit_handler(code=1)

        pods = list(set(pods)) # delete duplicates
        if not pods:
            _log.critical(("ERROR: no PODs selected to be run. Do `./mdtf info pods`"
                           " for a list of available PODs, and check your -p/--pods argument."
                           f"\nReceived --pods = {str(list(args))}"))
            util.exit_handler(code=1)
        return pods

    def set_case_pod_list(self, case, cli_obj, pod_info_tuple):
        # if pods set from CLI, overwrite pods in case list
        # already finalized self.pod-list by the time we get here
        if not cli_obj.is_default['pods'] or not case.get('pod_list', None):
            return self.pod_list
        else:
            return self.parse_pod_list(case['pod_list'], pod_info_tuple)

    def parse_case(self, n, d, cli_obj, pod_info_tuple):
        # really need to move this into init of DataManager
        if 'CASE_ROOT_DIR' not in d and 'root_dir' in d:
            d['CASE_ROOT_DIR'] = d.pop('root_dir')
        case_convention = d.get('convention', '')
        if case_convention:
            d['convention'] = case_convention

        if not ('CASENAME' in d or ('model' in d and 'experiment' in d)):
            _log.warning(("Need to specify either CASENAME or model/experiment "
                "in caselist entry #%d, skipping."), n+1)
            return None
        _ = d.setdefault('model', d.get('convention', ''))
        _ = d.setdefault('experiment', '')
        _ = d.setdefault('CASENAME', '{}_{}'.format(d['model'], d['experiment']))

        for field in ['FIRSTYR', 'LASTYR', 'convention']:
            if not d.get(field, None):
                _log.warning(("No value set for %s in caselist entry #%d, "
                              "skipping."), field, n+1)
                return None
        # if pods set from CLI, overwrite pods in case list
        d['pod_list'] = self.set_case_pod_list(d, cli_obj, pod_info_tuple)
        return d

    def parse_case_list(self, cli_obj, pod_info_tuple):
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
        self.cases = dict()
        for i, case_d in enumerate(case_list_in):
            case = self.parse_case(i, case_d, cli_obj, pod_info_tuple)
            if case:
                self.cases[case['CASENAME']] = case
        if not self.cases:
            _log.critical(("No valid entries in case_list. Please specify "
                           "model run information.\nReceived:"
                           f"\n{util.pretty_print_json(case_list_in)}"))
            util.exit_handler(code=1)



    def _post_parse_hook(self, cli_obj, config, paths):
        # init other services
        pass

    def _print_config(self, cli_obj, config, paths):
        """Log end result of parsing package settings. This is only for the user's
        benefit; a machine-readable version which is usable for
        provenance/reproducibility is saved by the OutputManager as
        ``config_save.jsonc``.
        """
        d = dict()
        for n, case in enumerate(self.iter_children()):
            key = 'case_list({})'.format(n)
            d[key] = case
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
        _log.info('PACKAGE SETTINGS:')
        _log.info(util.pretty_print_json(d))

    # --------------------------------------------------------------------

    @property
    def failed(self):
        """Overall success/failure of this run of the framework. Return True if
        any case or any POD has failed, else return False.
        """
        def _failed(obj):
            # need this workaround in case we failed early in init
            return (not hasattr(obj, 'failed')) or obj.failed

        # should be unnecessary if we've been propagating status correctly
        if self.status == ObjectStatus.FAILED or not self.cases:
            return True
        for case in self.iter_children():
            if _failed(case) or not hasattr(case, 'pods') or not case.pods:
                return True
            if any(_failed(p) for p in case.iter_children()):
                return True
        return False

    def main(self):
        new_d = dict()
        # single run mode
        if not self.multirun:
            self.cases = dict(list(self.cases.items())[0:1])
            for case_name, case_d in self.cases.items():
                _log.info("###core.py %s: initializing case '%s'.", self.full_name, case_name)
                case = self.DataSource(case_d, parent=self)
                case.setup()
                new_d[case_name] = case
            self.cases = new_d
            util.transfer_log_cache(close=True)

            for case_name, case in self.cases.items():
                if not case.failed:
                    if type(case).__name__ ==  'NoPPDataSource':
                        _log.info("### %s: Skipping Data Preprocessing for case '%s'."
                                  "Variables will not be renamed, and level extraction,"
                                  "will not be done on 4-D fields.",
                                  self.full_name, case_name)
                    else:
                        _log.info("### %s: requesting data for case '%s'.",
                                  self.full_name, case_name)
                        case.request_data()
                else:
                    _log.info(("### %s: initialization for case '%s' failed; skipping "
                               f"data request."), self.full_name, case_name)

                if not case.failed:
                    _log.info("### %s: running case '%s'.", self.full_name, case_name)
                    run_mgr = self.RuntimeManager(case, self.EnvironmentManager)
                    run_mgr.setup()
                    run_mgr.run()
                else:
                    _log.info(("### %s: Data request for case '%s' failed; skipping "
                               "execution."), self.full_name, case_name)

                out_mgr = self.OutputManager(case)
                out_mgr.make_output()
            tempdirs = TempDirManager()
            tempdirs.cleanup()
            print_summary(self)
            return 1 if self.failed else 0  # exit code
        # multirun mode
        else:
            # Import multirun methods here to avoid circular import problems
            # e.g., multirun.py inherits from diagnostic.py which inherits from core.py
            from src.diagnostic import MultirunDiagnostic, MultirunNoPPDiagnostic
            pod_dict = dict.fromkeys(self.pod_list, [])
            self.pods = pod_dict
            for pod in pod_dict.keys():
                if self.preprocess_data:
                    pod_dict[pod] = MultirunDiagnostic.from_config(pod, parent=self)
                # Initialize the pod as a MultirunDiagnostic object
                # Attach the caselist dict, and append case-specific attributes to each case object
                # Set the POD attributes including paths, pod_env_vars, and the convention
                # Append the varlist and import variable information from the pod settings file
                else:  # initialize noPP object
                    pod_dict[pod] = MultirunNoPPDiagnostic.from_config(pod, parent=self)
                # Translate varlist variables and metadata
                # Perform data preprocessing
                pod_dict[pod].setup_pod()
                # query the data
                # request the data
                util.transfer_log_cache(close=True)
                if type(pod_dict[pod]).__name__ == 'MultirunNoPPDiagnostic':
                    _log.info("### %s: Skipping Data Preprocessing for POD '%s'."
                              "Variables will not be renamed, and level extraction,"
                              "will not be done on 4-D fields.",
                              self.full_name, pod)
                else:
                    for case_name, case in pod_dict[pod].cases.items():
                        if not case.failed:
                            _log.info("### %s: requesting data for case '%s'.",
                                      self.full_name, case_name)
                            case.request_data(pod_dict[pod])
                        else:
                            _log.info(("### %s: initialization for case '%s' failed; skipping "
                                       f"data request."), self.full_name, case_name)

            if not any(p.failed for p in self.pods.values()):
                _log.info("### %s: running pods '%s'.", self.full_name, [p for p in pod_dict.keys()])
                run_mgr = self.RuntimeManager(self.pods, self.EnvironmentManager, self)
                run_mgr.setup()
                run_mgr.run(self)
            else:
                _log.info(("### %s: Data request for pod '%s' failed; skipping "
                           "execution."), self.full_name, pod)

            for p in self.pods.values():
                out_mgr = self.OutputManager(p)
                out_mgr.make_output(p)
            tempdirs = TempDirManager()
            tempdirs.cleanup()
            print_multirun_summary(self)
            return 0 if not any(v.failed for v in self.pods.values()) else 1  # exit code

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

    d = {c_name: summary_info_tuple(c) for c_name, c in fmwk.cases.items()}
    failed = any(len(tup[0]) > 0 for tup in d.values())
    _log.info('\n' + (80 * '-'))
    if failed:
        _log.info(f"Exiting with errors.")
        for case_name, tup in d.items():
            _log.info(f"Summary for {case_name}:")
            if tup[0][0] == 'dummy sentinel string':
                _log.info('\tAn error occurred in setup. No PODs were run.')
            else:
                if tup[1]:
                    _log.info((f"\tThe following PODs exited normally: "
                        f"{', '.join(tup[1])}"))
                if tup[0]:
                    _log.info((f"\tThe following PODs raised errors: "
                        f"{', '.join(tup[0])}"))
            _log.info(f"\tOutput written to {tup[2]}")
    else:
        _log.info(f"Exiting normally.")
        for case_name, tup in d.items():
            _log.info(f"Summary for {case_name}:")
            _log.info(f"\tAll PODs exited normally.")
            _log.info(f"\tOutput written to {tup[2]}")


def print_multirun_summary(fmwk):
    def summary_info_tuple(pod):
        """Debug information; will clean this up.
        """
        return (
            [p_name for p_name, p in pod.cases.items() if p.failed],
            [p_name for p_name, p in pod.cases.items() if not p.failed],
            getattr(pod, 'POD_OUT_DIR', '<ERROR: dir not created.>')
        )

    d = {p_name: summary_info_tuple(p) for p_name, p in fmwk.pods.items()}
    failed = any(len(tup[0]) > 0 for tup in d.values())
    _log.info('\n' + (80 * '-'))
    if failed:
        _log.info(f"Exiting with errors.")
        for case_name, tup in d.items():
            _log.info(f"Summary for {case_name}:")
            if tup[0][0] == 'dummy sentinel string':
                _log.info('\tAn error occurred in setup. No PODs were run.')
            else:
                if tup[1]:
                    _log.info((f"\tThe following PODs exited normally: "
                               f"{', '.join(tup[1])}"))
                if tup[0]:
                    _log.info((f"\tThe following PODs raised errors: "
                               f"{', '.join(tup[0])}"))
            _log.info(f"\tOutput written to {tup[2]}")
    else:
        _log.info(f"Exiting normally.")
        for case_name, tup in d.items():
            _log.info(f"Summary for {case_name}:")
            _log.info(f"\tAll PODs exited normally.")
            _log.info(f"\tOutput written to {tup[2]}")
        fmwk.status = ObjectStatus.SUCCEEDED
