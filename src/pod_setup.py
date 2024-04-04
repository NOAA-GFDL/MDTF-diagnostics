"""Classes for POD setup routines previously located in data_manager.DataSourceBase
"""
import logging
import os
import io
from pathlib import Path
import subprocess

from src import cli, util
import dataclasses as dc
from distutils.spawn import find_executable

_log = logging.getLogger(__name__)


class PodBaseClass(metaclass=util.MDTFABCMeta):
    """Base class for POD setup methods
    """

    def parse_pod_settings_file(self, code_root: str):
        pass

    def setup_pod(self, config: util.NameSpace,
                  model_paths: util.ModelDataPathManager,
                  case_list: dict):
        pass

    def setup_var(self, pod, v):
        pass


class PodObject(util.MDTFObjectBase, util.PODLoggerMixin, PodBaseClass):
    """Class to hold pod information"""
    # name: str  Class atts inherited from MDTFObjectBase
    # _id
    # _parent: object
    # status: ObjectStatus
    pod_dims = dict()
    pod_data = dict()
    pod_vars = dict()
    pod_settings = dict()
    multi_case_dict = dict()  # populated with case_info entries in enviroment_manager
    overwrite: bool = False
    # explict 'program' attribute in settings
    _interpreters = dict
    runtime_requirements: util.NameSpace
    driver: str = ""
    program: str = ""
    pod_env_vars: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict)
    log_file: io.IOBase = dc.field(default=None, init=False)
    nc_largefile: bool = False
    bash_exec: str
    global_env_vars: dict

    def __init__(self, name: str, runtime_config: util.NameSpace):
        self.name = name
        self._id = None
        # define global environment variables: those that apply to the entire POD
        self.pod_env_vars = os.environ.copy()
        self.pod_env_vars['RGB'] = os.path.join(runtime_config.CODE_ROOT, 'shared', 'rgb')
        self.pod_env_vars['CONDA_ROOT'] = os.path.expandvars(runtime_config.conda_root)
        self.pod_env_vars['CONDA_ENV_ROOT'] = os.path.expandvars(runtime_config.conda_env_root)
        if any(runtime_config.micromamba_exe):
            self.pod_env_vars['MICROMAMBA_EXE'] = runtime_config.micromamba_exe
        else:
            self.pod_env_vars['MICROMAMBA_EXE'] = ""
        # globally enforce non-interactive matplotlib backend
        # see https://matplotlib.org/3.2.2/tutorials/introductory/usage.html#what-is-a-backend
        self.pod_env_vars['MPLBACKEND'] = "Agg"
        self._interpreters = {'.py': 'python', '.ncl': 'ncl', '.R': 'Rscript'}
        self.nc_largefile = runtime_config.large_file
        self.bash_exec = find_executable('bash')
        # Initialize the POD path object and define the POD output paths
        # Don't need a new working directory since one is created when the model data directories are initialized
        self.paths = util.PodPathManager(runtime_config,
                                         env=self.pod_env_vars,
                                         new_work_dir=False)
        self.paths.setup_pod_paths(self.name)
        util.MDTFObjectBase.__init__(self, name=self.name, _parent=None)

    # Explicitly invoke MDTFObjectBase post_init and init methods so that _id and other inherited
    # attributes are initialized correctly. Calling super()__init__ causes and error in the _id definition
    def __post_init__(self, *args, **kwargs):
        util.MDTFObjectBase.__post_init__(self)
        # set up log (PODLoggerMixin)
        self.init_log(log_dir=self.paths.POD_WORK_DIR)

    @property
    def failed(self):
        return self.status == util.ObjectStatus.FAILED

    @property
    def active(self):
        return self.status == util.ObjectStatus.ACTIVE

    @property
    def _log_name(self):
        # POD loggers sit in a subtree of the DataSource logger distinct from
        # the DataKey loggers; the two subtrees are distinguished by class name
        _log_name = f"{self.name}_{self._id}".replace('.', '_')
        return f"{self.__class__.__name__}.{_log_name}"

    @property
    def _children(self):
        # property required by MDTFObjectBase
        return self.multi_case_dict.values()

    @property
    def full_name(self):
        return f"<#{self._id}:{self.name}>"

    def close_log_file(self, log=True):
        if self.log_file is not None:
            if log:
                self.log_file.write(self.format_log(children=False))
            self.log_file.close()

    def iter_case_names(self):
        """Iterator returning :c
        """
        yield self.multi_case_dict.keys()

    def parse_pod_settings_file(self, code_root: str) -> util.NameSpace:
        """Parse the POD settings file"""
        settings_file_query = Path(code_root, 'diagnostics', self.name).glob('*settings.*')
        settings_file_path = str([p for p in settings_file_query][0])
        # Use wildcard to support settings file in yaml and jsonc format
        settings_dict = cli.parse_config_file(settings_file_path)
        return util.NameSpace.fromDict({k: settings_dict[k] for k in settings_dict.keys()})

    def verify_pod_settings(self):
        """Verify that the POD settings file has the required entries"""
        required_settings = {"driver": str, "long_name": "", "convention": "",
                             "runtime_requirements": list}
        value = []
        try:
            value = [i for i in required_settings if i in self.pod_settings
                     and isinstance(self.pod_settings[i], type(required_settings[i]))]
        except Exception as exc:
            raise util.PodConfigError("Caught Exception: required setting %s not in pod setting file %s",
                                      value[0]) from exc

        def verify_runtime_reqs(runtime_reqs: dict):
            for k, v in runtime_reqs.items():
                if any(v):
                    pod_env = k
                    break
                
            pod_pkgs = runtime_reqs[pod_env]

            if "python" not in pod_env:
                env_name = '_MDTF_' + pod_env.upper() + '_base'
            else:
                env_name = '_MDTF_' + pod_env.lower() + '_base'

            conda_env_root = self.pod_env_vars['CONDA_ENV_ROOT']
            e = os.path.join(conda_env_root,  env_name)

            env_dir = util.resolve_path(e,
                                        env_vars=self.pod_env_vars,
                                        log=self.log)
            assert os.path.isdir(env_dir), self.log.error(f'%s not found.', env_dir)

            if pod_env.lower != "python3":
                pass
            else:
                self.log.info(f"Checking {e} for {self.name} package requirements")
                if os.path.exists(os.path.join(conda_root, "bin/conda")):
                    args = [os.path.join(conda_root, "bin/conda"),
                            'list',
                            '-n',
                            env_name]
                elif os.path.exists(self.pod_env_vars['MICROMAMBA_EXE']):
                    args = [self.pod_env_vars['MICROMAMBA_EXE'],
                            'list',
                            '-n',
                            env_name]
                else:
                    raise util.PodConfigError('Could not find conda or micromamba executable')

                p1 = subprocess.run(args,
                                    universal_newlines=True,
                                    bufsize=1,
                                    capture_output=True,
                                    text=True,
                                    env=self.pod_env_vars
                                    )
                # verify that pod package names are substrings of at least one package installed
                # in the pod environment
                output = p1.stdout.splitlines()
                for p in pod_pkgs:
                    has_pkgs = [o for o in output if p.lower() in o.lower()]
                    if not any(has_pkgs):
                        self.log.error(f'Package {p} not found in POD environment {pod_env}')

        try:
            verify_runtime_reqs(self.pod_settings['runtime_requirements'])
        except Exception as exc:
            raise util.PodConfigError('POD runtime requirements not defined in specified Conda environment') \
                from exc

    def get_pod_settings(self, pod_settings_dict: util.NameSpace):
        self.pod_settings = util.NameSpace.toDict(pod_settings_dict.settings)

    def get_pod_data(self, pod_settings: util.NameSpace):
        if hasattr(pod_settings, 'data'):
            self.pod_data = util.NameSpace.toDict(pod_settings.data)
        else:
            self.log.debug("The data attribute is undefined in '%s' settings file. "
                           "Using attributes defined separately for each variable",
                           self.name)

    def get_pod_dims(self, pod_settings: util.NameSpace):
        self.pod_dims = util.NameSpace.toDict(pod_settings.dimensions)

    def get_pod_vars(self, pod_settings: util.NameSpace):
        self.pod_vars = util.NameSpace.toDict(pod_settings.varlist)

    def query_files_in_time_range(self, startdate, enddate):
        pass

    def append_pod_env_vars(self, pod_input):
        self.global_env_vars.update(v for v in pod_input.pod_env_vars)

    def set_entry_point(self):
        """Locate the top-level driver script for the POD.

        Raises: :class:`~util.PodRuntimeError` if driver script can't be found.
        """
        self.driver = os.path.join(self.paths.POD_CODE_DIR, self.pod_settings["driver"])
        if not self.driver:
            raise util.PodRuntimeError((f"No driver script found in "
                                        f"{self.paths.POD_CODE_DIR}. Specify 'driver' in settings.jsonc."),
                                       self)
        if not os.path.isabs(self.driver):  # expand relative path
            self.driver = os.path.join(self.paths.POD_CODE_DIR, self.driver)

        self.log.debug("Setting driver script for %s to '%s'.",
                       self.full_name, self.driver)

    def set_interpreter(self, pod_settings: util.NameSpace):
        """Determine what executable should be used to run the driver script.

        .. note::
           Existence of the program on the environment's ``$PATH`` isn't checked
           until before the POD runs (see :mod:`src.environment_manager`.)
        """

        if not self.program:
            # Find ending of filename to determine the program that should be used
            _, driver_ext = os.path.splitext(pod_settings.driver)
            # Possible error: Driver file type unrecognized
            if driver_ext not in self._interpreters:
                raise util.PodRuntimeError((f"Don't know how to call a '{driver_ext}' "
                                            f"file.\nSupported programs: {list(self._interpreters.values())}"),
                                           self
                                           )
            self.program = self._interpreters[driver_ext]
            self.log.debug("Set program for %s to '%s'.",
                           self.full_name, self.program)

    def setup_pod(self, runtime_config: util.NameSpace,
                  model_paths: util.ModelDataPathManager,
                  cases: dict):
        """Update POD information from settings and runtime configuration files
        """
        # Parse the POD settings file
        pod_input = self.parse_pod_settings_file(runtime_config.CODE_ROOT)
        self.get_pod_settings(pod_input)
        self.get_pod_vars(pod_input)
        self.get_pod_data(pod_input)
        self.get_pod_dims(pod_input)
        # verify that required settings are specified,
        # and that required packages are installed in the target Conda environment
        self.verify_pod_settings()
        # append user-specified pod_env_vars to PodObject pod_env_vars dict
        if 'pod_env_vars' in self.pod_settings:
            if len(self.pod_settings['pod_env_vars']) > 0:
                for k, v in self.pod_settings['pod_env_vars'].items():
                    self.pod_env_vars[k] = v
        self.set_interpreter(pod_input.settings)
        self.runtime_requirements = pod_input.settings['runtime_requirements']
        pod_convention = self.pod_settings['convention'].lower()

        for case_name, case_dict in runtime_config.case_list.items():
            cases[case_name].read_varlist(self)
            # Translate the data if desired and the pod convention does not match the case convention
            data_convention = case_dict.convention.lower()
            if runtime_config.translate_data and pod_convention != data_convention:
                self.log.info(f'Translating POD variables from {pod_convention} to {data_convention}')
            else:
                data_convention = 'no_translation'
                self.log.info(f'POD convention and data convention are both {data_convention}. '
                              f'No data translation will be performed for case {case_name}.')
            # A 'noTranslationFieldlist' will be defined for the varlistEntry translation attribute
            cases[case_name].translate_varlist(model_paths,
                                               case_name,
                                               data_convention)

        for case_name in cases.keys():
            for v in cases[case_name].iter_children():
                # deactivate failed variables now that alternates are fully specified
                if v.last_exception is not None and not v.failed:
                    util.deactivate(v, v.last_exception, level=logging.WARNING)
            if cases[case_name].status == util.ObjectStatus.NOTSET and \
                    any(v.status == util.ObjectStatus.ACTIVE for v in cases[case_name].iter_children()):
                cases[case_name].status = util.ObjectStatus.ACTIVE
        # set MultirunDiagnostic object status to Active if all case statuses are Active
        if self.status == util.ObjectStatus.NOTSET and \
                all(case_dict.status == util.ObjectStatus.ACTIVE for case_name, case_dict in cases.items()):
            self.status = util.ObjectStatus.ACTIVE


