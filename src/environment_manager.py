f"""Classes which setup software dependencies for the PODs and which execute the
PODs' code.
"""

import os
import io
import abc
import dataclasses
from distutils.spawn import find_executable
import signal
import typing
import subprocess
from src import util
import yaml

import logging
_log = logging.getLogger(__name__)


class AbstractEnvironmentManager(abc.ABC):
    """Abstract interface for EnvironmentManager classes. The EnvironmentManager
    is responsible for setting up the runtime environment for a POD's third-party
    software dependencies (language versions, libraries, etc.) before execution
    and doing any associated cleanup after execution.
    """
    def __init__(self, log=_log):
        self.log = log  # log to case's logger

    @abc.abstractmethod
    def create_environment(self, env_name):
        """Install or otherwise create the POD runtime environment identified by
        *env_name*, which can be an arbitrary object describing the environment.
        """
        pass

    @abc.abstractmethod
    def get_pod_env(self, pod):
        """Assign an environment identifier (of the same type as the *env_name*
        arguments) to a *pod* based on the requirements and other declarative
        information from its settings.jsonc file.

        Args:
            pod (:class:`~src.pod_setup:PODObject`): POD object whose runtime
                environment needs to be determined.

        Returns:
            Environment identifier to be passed as *env_name* to other
            methods of the EnvironmentManager.
        """
        pass

    @abc.abstractmethod
    def activate_env_commands(self, env_name):
        """Generate shell commands needed to activate/set up the environment
        before the POD executes.

        Args:
            env_name: Identifier corresponding to the environment to activate.

        Returns:
            List of strings, one per command, corresponding to the shell commands
            needed to activate or set up the runtime environment within the POD's
            execution environment (e.g., child subprocess) created by the
            RuntimeManager.
        """
        pass

    @abc.abstractmethod
    def deactivate_env_commands(self, env_name):
        """Generate shell commands needed to deactivate/clean up the environment
        after the POD has finished executing.

        Args:
            env_name: Identifier corresponding to the environment to deactivate.

        Returns:
            List of strings, one per command, corresponding to the shell commands
            needed to deactivate or tear down the runtime environment within the
            POD's execution environment (e.g., child subprocess) created by the
            RuntimeManager.
        """
        pass

    @abc.abstractmethod
    def destroy_environment(self, env_name):
        """Uninstall or otherwise remove the POD runtime environment identified by
        *env_name*, which can be an arbitrary object describing the environment.
        """
        pass

    def tear_down(self):
        """Performs any cleanup specific to the EnvironmentManager itself. Called
        once, after all PODs have executed.
        """
        pass


class NullEnvironmentManager(AbstractEnvironmentManager):
    """EnvironmentManager class which does nothing; intended as a dummy setting
    for building framework test harnesses.
    """
    def create_environment(self, env_name):
        """No-op."""
        pass

    def destroy_environment(self, env_name):
        """No-op."""
        pass

    def get_pod_env(self, pod):
        """No-op."""
        pass

    def activate_env_commands(self, env_name):
        """No-op."""
        return []

    def deactivate_env_commands(self, env_name):
        """No-op."""
        return []


class CondaEnvironmentManager(AbstractEnvironmentManager):
    """:class:`AbstractEnvironmentManager` that uses the conda package manager
    to define and switch runtime environments.
    """
    env_name_prefix = '_MDTF_'  # our envs start with this string to avoid conflicts
    code_root: str = ""
    conda_dir: str = ""
    env_list: list = []
    conda_exe: str = "" 
    log: logging.log

    def __init__(self, config: util.NameSpace, log):
        self.code_root = config.CODE_ROOT
        self.conda_dir = os.path.join(self.code_root, 'src', 'conda')
        self.log = log
        for file_ in os.listdir(self.conda_dir):
            if file_.endswith('.yml'):
                name, _ = os.path.splitext(file_)
                self.env_list.append(name.split('env_')[-1])

        # find conda executable
        # conda_init for bash defines conda as a shell function; will get error
        # if we try to call the conda executable directly
        if any(config.micromamba_exe):
            cmd = (f"{self.conda_dir}/micromamba_init.sh --micromamba_root {config.conda_root}"
                   f" --micromamba_exe {config.micromamba_exe}")
        else:
            cmd = f"{self.conda_dir}/conda_init.sh {config.conda_root}"

        try:
            conda_info = util.run_shell_command(
                cmd,
                log=log
            )
            for line in conda_info:
                key, val = line.split('=')
                if key == '_CONDA_EXE':
                    self.conda_exe = val
                    assert os.path.exists(self.conda_exe)
                elif key == '_CONDA_ROOT':
                    self.conda_root = val
        except Exception as exc:
            raise util.PodRuntimeError("Can't find conda.") from exc

        # find where environments are installed
        self.conda_env_root = config.conda_env_root
        if not os.path.isdir(self.conda_env_root):
            self.log.log.warning("Conda env directory '%s' not found; creating.",
                             self.conda_env_root)
            os.makedirs(self.conda_env_root)  # recursive mkdir if needed
        else:
            # only true in default anaconda install, may need to fix
            self.conda_env_root = os.path.join(self.conda_root, 'envs')

    def create_environment(self, env_name):
        # check to see if conda env exists, and if not, try to create it
        conda_prefix = os.path.join(self.conda_env_root, env_name)
        if not os.path.exists(conda_prefix):
            self.log.log.warning(("Conda env '%s' not found (grepped for '%s'); "
                                  "continuing."), env_name, conda_prefix)

    def _call_conda_create(self, env_name):
        if env_name.startswith(self.env_name_prefix):
            short_name = env_name[(len(self.env_name_prefix)+1):]
        else:
            short_name = env_name
        path = f"{self.conda_dir}/env_{short_name}.yml"
        if not os.path.exists(path):
            self.log.log.error("Can't find %s", path)
        else:
            conda_prefix = os.path.join(self.conda_env_root, env_name)
            self.log.log.info("Creating conda env '%s' in '%s'.", env_name, conda_prefix)
        cmd = (
            f'source {self.conda_dir}/conda_init.sh {self.conda_root} && '
            f'{self.conda_exe} env create --force -q -p "{conda_prefix}" -f "{path}"'
        )
        try:
            _ = util.run_shell_command(cmd, log=self.log)
        except Exception:
            raise

    def create_all_environments(self):
        try:
            cmd = (f'{self.conda_dir}/conda_env_setup.sh -c "{self.conda_exe}" '
                   f'-d "{self.conda_env_root}" --all'
                   )
            _ = util.run_shell_command(cmd, log=self.log)
        except Exception:
            raise

    def destroy_environment(self, env_name):
        pass

    def get_pod_env(self, pod):
        if pod.name in self.env_list:
            # env created specifically for this POD
            return self.env_name_prefix + pod.name
        else:
            langs = [s.lower() for s in pod.runtime_requirements]
            if ('r' in langs) or ('rscript' in langs):
                return self.env_name_prefix + 'R_base'
            elif 'ncl' in langs:
                return self.env_name_prefix + 'NCL_base'
            elif 'python3' in langs:
                return self.env_name_prefix + 'python3_base'
            else:
                pod.log.error("Can't find environment providing %s",
                    pod.runtime_requirements)

    def activate_env_commands(self, env_name):
        """Source conda_init.sh to set things that aren't set b/c we aren't
        in an interactive shell.
        """
        # conda_init for bash defines conda as a shell function; will get error
        # if we try to call the conda executable directly
        conda_prefix = os.path.join(self.conda_env_root, env_name)
        if os.path.split(self.conda_exe)[-1] == 'micromamba':
            return [
                f'source {self.conda_dir}/micromamba_init.sh --micromamba_exe {self.conda_exe}'
                f' --micromamba_root {self.conda_root}',
                f'micromamba activate {conda_prefix}'
            ]
        else:
            return [
                f'source {self.conda_dir}/conda_init.sh {self.conda_root}',
                f'conda activate {conda_prefix}'
            ]

    def deactivate_env_commands(self, env_name):
        return []

# ============================================================================


class AbstractRuntimeManager(abc.ABC):
    """Interface for RuntimeManager classes. The RuntimeManager is responsible
    for managing the actual execution of the PODs.
    """
    @abc.abstractmethod
    def setup(self):
        """Performs any initialization tasks
        """
        pass

    @abc.abstractmethod
    def run(self, cases: dict, log: logging.log):
        pass

    @abc.abstractmethod
    def tear_down(self): pass


@util.mdtf_dataclass
class SubprocessRuntimePODWrapper:
    """Wrapper for :class:`diagnostic.multirunDiagnostic` that adds fields and methods
    used by :class:`SubprocessRuntimeManager`.
    """
    pod: typing.Any = util.MANDATORY
    env: typing.Any = None
    env_vars: dict = dataclasses.field(default_factory=dict)
    process: typing.Any = dataclasses.field(default=None, init=False)

    def __init__(self, pod):
        self.pod = pod
        self.env_vars = dict()

    def set_pod_env_vars(self, pod, cases: dict):
        """Sets all environment variables for the POD: paths and names of each
        variable and coordinate. Raise a :class:`~src.util.exceptions.WormKeyError`
        if any of these definitions conflict.
        """
        pod.pod_env_vars.update({
            "POD_HOME": pod.paths.POD_CODE_DIR,  # location of POD's code
            "OBS_DATA": pod.paths.POD_OBS_DATA,  # POD's observational data
            "WORK_DIR": pod.paths.POD_WORK_DIR,  # POD's subdir within working directory
            "DATADIR": pod.paths.POD_WORK_DIR  # synonym so we don't need to change docs
        })

        for case_name, case_dict in cases.items():
            for var in case_dict.iter_children(status_neq=util.ObjectStatus.ACTIVE):
                # define env vars for varlist entries without data. Name collisions
                # are OK in this case.
                try:
                    self.env_vars.update(var.env_vars)
                except util.WormKeyError:
                    continue

    def pre_run_setup(self, cases: dict, catalog_file: str):
        self.pod.log_file = io.open(
            os.path.join(self.pod.paths.POD_WORK_DIR, self.pod.name+".log"),
            'w', encoding='utf-8'
        )
        self.pod.log_file.write(
            util.mdtf_log_header(f"MDTF {self.pod.name} DIAGNOSTIC LOG")
        )

        self.pod.log.info('### Starting %s', self.pod.full_name)
        try:
            self.set_pod_env_vars(self.pod, cases)
            self.pod.set_entry_point()
        except Exception as exc:
            raise util.PodRuntimeError("Caught exception during pre_run_setup",
                                       self) from exc
        self.pod.log.info("%s will run using '%s' from conda env '%s'.",
                          self.pod.full_name, self.pod.program, self.env)

        self.pod.log.debug("%s", self.pod.format_log(children=False))
    #    self.pod._log_handler.reset_buffer()
        self.write_case_env_file(cases, catalog_file)
        self.setup_env_vars()

    def setup_env_vars(self):
        def _envvar_format(x):
            # environment variables must be strings
            if isinstance(x, str):
                return x
            elif isinstance(x, bool):
                return '1' if x else '0'
            else:
                return str(x)

        skip_items = ['enddate', 'startdate', 'CASENAME']  # Omit per-case environment variables
        self.env_vars = {k: _envvar_format(v)
                         for k, v in self.pod.pod_env_vars.items() if k not in skip_items}

        # append varlist env vars for backwards compatibility with single-run PODs
        if len(self.pod.multicase_dict['CASE_LIST']) == 1:
            for case_name, case_info in self.pod.multicase_dict['CASE_LIST'].items():
                for k, v in case_info.items():
                    self.env_vars[k] = v

        env_list = [f"  {k}: {v}" for k, v in self.env_vars.items()]
        self.pod.log_file.write("\n")
        self.pod.log_file.write("\n".join(["### Shell env vars: "] + sorted(env_list)))
        self.pod.log_file.write("\n\n")

    def write_case_env_file(self, case_list: dict, catalog_file: str):
        out_file = os.path.join(self.pod.paths.POD_WORK_DIR, 'case_info.yml')
        self.pod.pod_env_vars["case_env_file"] = out_file
        case_info = dict()
        case_info['CATALOG_FILE'] = catalog_file
        case_info['CASE_LIST'] = dict()
        assert os.path.isfile(case_info['CATALOG_FILE']), 'CATALOG_FILE json not found in WORK_DIR'
        for case_name, case in case_list.items():
            case_info['CASE_LIST'][case_name] = {k: v
                                                 for k, v in case.env_vars.items()}
            
            # append case environment vars
            for v in case.iter_vars_only(active=True):
                for kk, vv in v.env_vars.items():
                    if v.name.lower() + '_var' in kk.lower():
                        case_info['CASE_LIST'][case_name][kk] = v.name
                    elif v.name.lower() + '_file' in kk.lower():
                        case_info['CASE_LIST'][case_name][kk] = v.dest_path
                    else:
                        case_info['CASE_LIST'][case_name][kk] = vv
                # append env_vars for alternates
                if len(v.alternates) > 0:
                    for alt in v.alternates:
                        if hasattr(alt, 'env_vars'):
                            for kk, vv in alt.env_vars.items():
                                if alt.name.lower() + '_var' in kk.lower():
                                    case_info['CASE_LIST'][case_name][kk] = alt.name
                                elif alt.name.lower() + '_file' in kk.lower():
                                    case_info['CASE_LIST'][case_name][kk] = alt.dest_path
                                else:
                                    case_info['CASE_LIST'][case_name][kk] = vv

        f = open(out_file, 'w+')
        assert os.path.isfile(out_file), f"Could not find case env file {out_file}"
        yaml.dump(case_info, f, allow_unicode=True, default_flow_style=False)
        self.pod.multicase_dict = case_info
        f.close()

    def setup_exception_handler(self, exc):
        chained_exc = util.chain_exc(exc, f"preparing to run {self.pod.full_name}.",
                                     util.PodRuntimeError)
        self.pod.deactivate(chained_exc)
        self.tear_down()
        raise exc  # include in production, or just for debugging?

    def run_commands(self):
        """Produces the shell command(s) to run the POD.
        """
        output_name = self.pod.driver.rstrip(".ipynb") + "_ipynb"
        if self.pod.program == 'jupyter':
            return [f"/usr/bin/env {self.pod.program} nbconvert --to html" +\
                    f" --output-dir='{self.pod.pod_env_vars['WORK_DIR']}' --output {output_name} --execute {self.pod.driver}"]
        else:
            return [f"/usr/bin/env {self.pod.program} {self.pod.driver}"]

    def run_msg(self):
        """Log message when execution starts.
        """
        return (f"Running {os.path.basename(self.pod.driver)} for "
                f"{self.pod.full_name}.")

    def validate_commands(self):
        """Produces the shell command(s) to validate the POD's runtime environment
        (ie, check for all requested third-party module dependencies.)
        Dependencies are passed as arguments to the shell script
        ``src/validate_environment.sh``, which is invoked in the POD's subprocess
        before the POD is run.

        Returns:
            (:py:obj:`str`): Command-line invocation to validate the POD's
                runtime environment.
        """
        paths = self.pod.paths
        command_path = os.path.join(paths.CODE_ROOT,
                                    'src', 'validate_environment.sh')
        reqs = self.pod.runtime_requirements
        command = [
            command_path,
            ' -v',
            ' -p '.join([''] + list(reqs)),
            ' -z '.join([''] + list(self.pod.pod_env_vars)),
            ' -a '.join([''] + reqs.get('python', [])),
            ' -b '.join([''] + reqs.get('ncl', [])),
            ' -c '.join([''] + reqs.get('Rscript', []))
        ]
        return [''.join(command).replace('(','\(').replace(')','\)')]

    def runtime_exception_handler(self, exc):
        """Handler which is called if an exception is raised during the POD's
        execution (including setup and clean up).
        """
        chained_exc = util.chain_exc(exc, f"running {self.pod.full_name}.",
                                     util.PodExecutionError)
        self.pod.deactivate(chained_exc)
        self.tear_down()
        raise exc  # include in production, or just for debugging?

    def tear_down(self, retcode=None):
        # just to be safe
        if self.process is not None:
            if hasattr(self.process, 'retcode'):
                retcode = self.process.returncode
            try:
                self.process.kill()
            except ProcessLookupError:
                pass
            self.process = None

        log_str = ""
        if self.pod.status != util.ObjectStatus.INACTIVE:
            if retcode == 0:
                log_str = f"{self.pod.full_name} exited successfully (code={retcode})."
                self.pod.log.info(log_str)
            elif retcode is None:
                log_str = f"{self.pod.full_name} exited without specifying a return code\n (not " \
                          f"necessarily a failure; this information just wasn't provided\n" \
                          f"to the subprocess manager when the POD completed).\n"
                self.pod.log.info(log_str)
            elif self.pod.failed:
                log_str = f"{self.pod.full_name} exited abnormally with pod status FAILED."
                self.pod.log.info(log_str)
            else:
                log_str = f"{self.pod.full_name} exited abnormally (code={retcode})."
                exc = util.PodExecutionError(log_str)
                self.pod.deactivate(exc)

        if self.pod.log_file is not None:
            self.pod.log_file.write(80 * '-' + '\n')
            self.pod.log_file.write(log_str + '\n')
            self.pod.log_file.flush()  # redundant?

        if not self.pod.failed:
            self.pod.status = util.ObjectStatus.INACTIVE

        # elapsed = timeit.default_timer() - start_time
        # print(pod+" Elapsed time ",elapsed)


class SubprocessRuntimeManager(AbstractRuntimeManager):
    """RuntimeManager class that runs each POD in a child subprocess spawned on
    the local machine. Resource allocation is delegated to the local machine's
    kernel's scheduler.
    """
    _PodWrapperClass = SubprocessRuntimePODWrapper
    _EnvironmentManagerClass = CondaEnvironmentManager
    pods: list = []
    bash_exec: str = ""
    no_preprocessing: bool = False
    catalog_file: str = ""

    def __init__(self, pod_dict: dict, config: util.NameSpace, _log: logging.log):
        # transfer all pods, even failed ones, because we need to call their
        self.pods = [self._PodWrapperClass(p) for p in pod_dict.values()]
        # init object-level logger
        self.env_mgr = self._EnvironmentManagerClass(config, log=_log)

        # Need to run bash explicitly because 'conda activate' sources
        # env vars (can't do that in posix sh). tcsh could also work.
        self.bash_exec = find_executable('bash')

        self.no_preprocessing = not(config.get('run_pp', False))
        if self.no_preprocessing:
            self.catalog_file = config.get('DATA_CATALOG')
        else:
            self.catalog_file = os.path.join(config.get('OUTPUT_DIR'), 'MDTF_postprocessed_data.json')

    def iter_active_pods(self):
        """Generator iterating over all wrapped pods which are currently active,
        i.e. which haven't been skipped due to requirement errors.
        """
        yield from filter((lambda p: p.pod.active), self.pods)

    def setup(self):
        for p in self.iter_active_pods():
            p.env = self.env_mgr.get_pod_env(p.pod)
        envs = set([p.env for p in self.pods if p.env])
        for env in envs:
            self.env_mgr.create_environment(env)

    def spawn_subprocess(self, p, env_vars_base):
        run_cmds = p.validate_commands() + p.run_commands()
        commands = self.env_mgr.activate_env_commands(p.env) \
            + run_cmds \
            + self.env_mgr.deactivate_env_commands(p.env)
        p.pod.log.info('\t'+p.run_msg())
        # '&&' so we abort if any command in the sequence fails.
        commands = ' && '.join([s for s in commands if s])

        assert os.path.isdir(p.pod.paths.POD_WORK_DIR)
        env_vars = env_vars_base.copy()
        env_vars.update(p.env_vars)
        env_vars.update(p.pod.pod_env_vars)
        # Need to run bash explicitly because 'conda activate' sources
        # env vars (can't do that in posix sh). tcsh could also work.
        return subprocess.Popen(
            commands,
            shell=True, executable=self.bash_exec,
            env=env_vars, cwd=p.pod.paths.POD_WORK_DIR,
            stdout=p.pod.log_file, stderr=p.pod.log_file,
            universal_newlines=True, bufsize=1
        )

    def run(self, cases: dict, _log):
        # Call cleanup method if we're killed
        signal.signal(signal.SIGTERM, self.runtime_terminate)
        signal.signal(signal.SIGINT, self.runtime_terminate)

        pod_list = [p for p in self.iter_active_pods()]
        if not pod_list:
            _log.log.error('%s: no PODs met data requirements; returning',
                           self.__class__.__name__)
            return

        env_vars_base = os.environ.copy()
        for podwrapper in pod_list:
            podwrapper.pod.log.info('%s: run %s.', self.__class__.__name__, podwrapper.pod.full_name)
            try:
                podwrapper.pre_run_setup(cases, self.catalog_file)
            except Exception as exc:
                podwrapper.setup_exception_handler(exc)
                continue
            try:
                podwrapper.pod.log_file.write(f"### Start execution of {podwrapper.pod.full_name}\n")
                podwrapper.pod.log_file.write(80 * '-' + '\n')
                podwrapper.pod.log_file.flush()
                podwrapper.process = self.spawn_subprocess(podwrapper, env_vars_base)
            except Exception as exc:
                podwrapper.runtime_exception_handler(exc)
                continue
        # should use asyncio, instead wait for each process
        # to terminate and close all log files
        # TODO: stderr gets eaten with current setup; possible to do a proper
        # tee if procs are run with asyncio? https://stackoverflow.com/a/59041913
        for p in self.pods:
            if p.process is not None:
                p.process.wait()
            p.tear_down()
        _log.log.info('%s: completed all PODs.', self.__class__.__name__)
        self.tear_down()

    def tear_down(self):
        # cleanup all envs that were defined, just to be safe
        envs = set([p.env for p in self.pods if p.env])
        for env in envs:
            self.env_mgr.destroy_environment(env)
        self.env_mgr.tear_down()

    def runtime_terminate(self, signum=None):
        """Handler called in the event that POD execution was halted abnormally,
        by receiving  ``SIGINT`` or ``SIGTERM``.
        """
        # try to clean up everything
        for p in self.pods:
            util.signal_logger(self.__class__.__name__, signum, log=p.pod.log)
            p.tear_down()
            p.pod.close_log_file(log=True)

        self.tear_down()
        util.exit_handler(code=1)
