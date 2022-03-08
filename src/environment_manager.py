"""Classes which setup software dependencies for the PODs and which execute the
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
from src import util, core

import logging
_log = logging.getLogger(__name__)

class AbstractEnvironmentManager(abc.ABC):
    """Abstract interface for EnvironmentManagers.
    """
    def __init__(self, log=_log):
        self.log = log # log to case's logger

    def setup(self): pass

    @abc.abstractmethod
    def create_environment(self, env_name): pass

    @abc.abstractmethod
    def get_pod_env(self, pod): pass

    @abc.abstractmethod
    def activate_env_commands(self, env_name): pass

    @abc.abstractmethod
    def deactivate_env_commands(self, env_name): pass

    @abc.abstractmethod
    def destroy_environment(self, env_name): pass

    def tear_down(self): pass

class NullEnvironmentManager(AbstractEnvironmentManager):
    """EnvironmentManager which performs no environment switching. Useful only
    as a dummy setting for building framework test harnesses.
    """
    def create_environment(self, env_name):
        pass

    def destroy_environment(self, env_name):
        pass

    def get_pod_env(self, pod):
        pass

    def activate_env_commands(self, env_name):
        return []

    def deactivate_env_commands(self, env_name):
        return []

class VirtualenvEnvironmentManager(AbstractEnvironmentManager):
    """:class:`AbstractEnvironmentManager` that manages dependencies assuming
    that current versions of the scripting language executables are already
    available on ``$PATH``. For python-based PODs, it uses pip and virtualenvs
    to install needed libraries. For R-based PODs, it attempts to install needed
    libraries into the current user's ``$PATH``. For other scripting languages,
    no library management is performed.
    """
    def __init__(self, log=_log):
        super(VirtualenvEnvironmentManager, self).__init__(log=log)

        paths = core.PathManager()
        self.venv_root = paths.get('venv_root', '')
        self.r_lib_root = paths.get('r_lib_root', '')

    def create_environment(self, env_key):
        env_name = env_key[0]
        for tup in env_key[1:]:
            lang = tup[0].lower()
            if lang.startswith('py'):
                self._create_py_venv(env_name, tup[1])
            elif lang.startswith('r'):
                self._create_r_venv(env_name, tup[1])

    def _create_py_venv(self, env_name, py_pkgs):
        env_path = os.path.join(self.venv_root, env_name)
        if not os.path.isdir(env_path):
            os.makedirs(env_path) # recursive mkdir if needed
        for cmd in [
            f"python -m virtualenv {env_path}",
            f"source {env_path}/bin/activate",
            'pip install {}'.format(' '.join(py_pkgs)),
            'deactivate'
        ]:
            util.run_shell_command(cmd, log=self.log)

    def _create_r_venv(self, env_name, r_pkgs):
        r_pkg_str = ', '.join(['"'+x+'"' for x in r_pkgs])
        if self.r_lib_root != '':
            env_path = os.path.join(self.r_lib_root, env_name)
            if not os.path.isdir(env_path):
                os.makedirs(env_path) # recursive mkdir if needed
            cmds = [
                f'export R_LIBS_USER="{env_path}"',
                f'Rscript -e \'install.packages(c({r_pkg_str}), ' \
                    + 'lib=Sys.getenv("R_LIBS_USER"))\''
            ]
        else:
            cmds = [f'Rscript -e \'install.packages(c({r_pkg_str}))\'']
        for cmd in cmds:
            util.run_shell_command(cmd, log=self.log)

    def destroy_environment(self, env_key):
        pass

    def get_pod_env(self, pod):
        env_key = [pod.name]
        return tuple(env_key + [(k, frozenset(v)) for k,v \
            in pod.runtime_requirements.items()])

    def activate_env_commands(self, env_key):
        env_name = env_key[0]
        langs = [tup[0] for tup in env_key[1:]]
        cmd_list = []
        for lang in langs:
            if lang.startswith('py'):
                env_path = os.path.join(self.venv_root, env_name)
                cmd_list.append(f"source {env_path}/bin/activate")
            elif lang.startswith('r'):
                env_path = os.path.join(self.r_lib_root, env_name)
                cmd_list.append(f'export R_LIBS_USER="{env_path}"')
        return cmd_list

    def deactivate_env_commands(self, env_key):
        langs = [tup[0] for tup in env_key[1:]]
        cmd_list = []
        for lang in langs:
            if lang.startswith('py'):
                cmd_list.append('deactivate')
            elif lang.startswith('r'):
                cmd_list.append('unset R_LIBS_USER')
        return cmd_list

class CondaEnvironmentManager(AbstractEnvironmentManager):
    """:class:`AbstractEnvironmentManager` that uses the conda package manager
    to define and switch runtime environments.
    """
    env_name_prefix = '_MDTF_' # our envs start with this string to avoid conflicts

    def __init__(self, log=_log):
        super(CondaEnvironmentManager, self).__init__(log=log)

        paths = core.PathManager()
        self.code_root = paths.CODE_ROOT
        self.conda_dir = os.path.join(self.code_root, 'src','conda')
        self.env_list = []
        for file_ in os.listdir(self.conda_dir):
            if file_.endswith('.yml'):
                name, _ = os.path.splitext(file_)
                self.env_list.append(name.split('env_')[-1])

        # find conda executable
        # conda_init for bash defines conda as a shell function; will get error
        # if we try to call the conda executable directly
        try:
            conda_info = util.run_shell_command(
                f"{self.conda_dir}/conda_init.sh {paths.get('conda_root','')}",
                log=self.log
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
        if 'conda_env_root' in paths and paths.conda_env_root:
            self.conda_env_root = paths.conda_env_root
            if not os.path.isdir(self.conda_env_root):
                self.log.warning("Conda env directory '%s' not found; creating.",
                    self.conda_env_root)
                os.makedirs(self.conda_env_root) # recursive mkdir if needed
        else:
            # only true in default anaconda install, may need to fix
            self.conda_env_root = os.path.join(self.conda_root, 'envs')

    def create_environment(self, env_name):
        # check to see if conda env exists, and if not, try to create it
        conda_prefix = os.path.join(self.conda_env_root, env_name)
        if not os.path.exists(conda_prefix):
            self.log.warning(("Conda env '%s' not found (grepped for '%s'); "
                "continuing."), env_name, conda_prefix)
            #self._call_conda_create(env_name)

    def _call_conda_create(self, env_name):
        if env_name.startswith(self.env_name_prefix):
            short_name = env_name[(len(self.env_name_prefix)+1):]
        else:
            short_name = env_name
        path = f"{self.conda_dir}/env_{short_name}.yml"
        if not os.path.exists(path):
            self.log.error("Can't find %s", path)
        else:
            conda_prefix = os.path.join(self.conda_env_root, env_name)
            self.log.info("Creating conda env '%s' in '%s'.", env_name, conda_prefix)
        command = (
            f'source {self.conda_dir}/conda_init.sh {self.conda_root} && '
            f'{self.conda_exe} env create --force -q -p "{conda_prefix}" -f "{path}"'
        )
        try:
            _ = util.run_shell_command(command, log=self.log)
        except Exception:
            raise

    def create_all_environments(self):
        try:
            _ = util.run_shell_command((
                f'{self.conda_dir}/conda_env_setup.sh -c "{self.conda_exe}" '
                f'-d "{self.conda_env_root}" --all'
                ), log=self.log
            )
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
            elif 'python2' in langs:
                raise NotImplementedError('Python 2 not supported for new PODs.')
                # return self.env_name_prefix + 'python2_base'
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
        return [
            f'source {self.conda_dir}/conda_init.sh {self.conda_root}',
            f'conda activate {conda_prefix}'
        ]

    def deactivate_env_commands(self, env_name):
        return []

# ============================================================================

class AbstractRuntimeManager(abc.ABC):
    """Interface for RuntimeManagers.
    """
    @abc.abstractmethod
    def setup(self): pass

    @abc.abstractmethod
    def run(self): pass

    @abc.abstractmethod
    def tear_down(self): pass


@util.mdtf_dataclass
class SubprocessRuntimePODWrapper(object):
    """Wrapper for :class:`diagnostic.Diagnostic` that adds fields and methods
    used by :class:`SubprocessRuntimeManager`.
    """
    pod: typing.Any = util.MANDATORY
    env: typing.Any = None
    env_vars: dict = dataclasses.field(default_factory=dict)
    process: typing.Any = dataclasses.field(default=None, init=False)

    def pre_run_setup(self):
        self.pod.log_file = io.open(
            os.path.join(self.pod.POD_WK_DIR, self.pod.name+".log"),
            'w', encoding='utf-8'
        )
        self.pod.log_file.write(
            util.mdtf_log_header(f"MDTF {self.pod.name} DIAGNOSTIC LOG")
        )

        self.pod.log.info('### Starting %s', self.pod.full_name)
        self.pod.pre_run_setup()
        self.pod.log.info("%s will run using '%s' from conda env '%s'.",
            self.pod.full_name, self.pod.program, self.env)

        self.pod.log_file.write(self.pod.format_log(children=True))
        self.pod._log_handler.reset_buffer()
        self.setup_env_vars()

    def setup_env_vars(self):
        def _envvar_format(x):
            # environment variables must be strings
            if isinstance(x, str):
                return x
            elif isinstance(x, bool):
                return ('1' if x else '0')
            else:
                return str(x)

        self.env_vars = {k: _envvar_format(v) \
            for k,v in self.pod.pod_env_vars.items()}
        env_list = [f"  {k}: {v}" for k,v in self.env_vars.items()]
        self.pod.log_file.write("\n")
        self.pod.log_file.write("\n".join(["### Shell env vars: "] + sorted(env_list)))
        self.pod.log_file.write("\n\n")


    def setup_exception_handler(self, exc):
        chained_exc = util.chain_exc(exc, f"preparing to run {self.pod.full_name}.",
            util.PodRuntimeError)
        self.pod.deactivate(chained_exc)
        self.tear_down()
        raise exc # include in production, or just for debugging?

    def run_commands(self):
        """Produces the shell command(s) to run the POD.
        """
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
        paths = core.PathManager()
        command_path = os.path.join(paths.CODE_ROOT, \
            'src', 'validate_environment.sh')
        reqs = self.pod.runtime_requirements # abbreviate
        command = [
            command_path,
            ' -v',
            ' -p '.join([''] + list(reqs)),
            ' -z '.join([''] + list(self.pod.pod_env_vars)),
            ' -a '.join([''] + reqs.get('python', [])),
            ' -b '.join([''] + reqs.get('ncl', [])),
            ' -c '.join([''] + reqs.get('Rscript', []))
        ]
        return [''.join(command)]

    def runtime_exception_handler(self, exc):
        chained_exc = util.chain_exc(exc, f"running {self.pod.full_name}.",
            util.PodExecutionError)
        self.pod.deactivate(chained_exc)
        self.tear_down()
        raise exc # include in production, or just for debugging?

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

        if self.pod.status != core.ObjectStatus.INACTIVE:
            if retcode == 0:
                log_str = f"{self.pod.full_name} exited successfully (code={retcode})."
                self.pod.log.info(log_str)
            elif retcode is None or self.pod.failed:
                log_str = f"{self.pod.full_name} was terminated or exited abnormally."
                self.pod.log.info(log_str)
            else:
                log_str = f"{self.pod.full_name} exited abnormally (code={retcode})."
                exc = util.PodExecutionError(log_str)
                self.pod.deactivate(exc)

        if self.pod.log_file is not None:
            self.pod.log_file.write(80 * '-' + '\n')
            self.pod.log_file.write(log_str + '\n')
            self.pod.log_file.flush() # redundant?

        if not self.pod.failed:
            self.pod.status = core.ObjectStatus.INACTIVE
        # elapsed = timeit.default_timer() - start_time
        # print(pod+" Elapsed time ",elapsed)

class SubprocessRuntimeManager(AbstractRuntimeManager):
    """RuntimeManager that spawns a separate system subprocess for each POD.
    """
    _PodWrapperClass = SubprocessRuntimePODWrapper

    def __init__(self, case, EnvMgrClass):
        config = core.ConfigManager()
        self.test_mode = config.test_mode
        # transfer all pods, even failed ones, because we need to call their
        self.pods = [self._PodWrapperClass(pod=p) for p in case.pods.values()]
        self.env_mgr = EnvMgrClass(log=case.log)
        self.case = case

        # Need to run bash explicitly because 'conda activate' sources
        # env vars (can't do that in posix sh). tcsh could also work.
        self.bash_exec = find_executable('bash')

    def iter_active_pods(self):
        """Generator iterating over all wrapped pods which haven't been skipped
        due to requirement errors.
        """
        yield from filter((lambda p: p.pod.active), self.pods)

    def setup(self):
        self.env_mgr.setup()
        for p in self.iter_active_pods():
            p.env = self.env_mgr.get_pod_env(p.pod)
        envs = set([p.env for p in self.pods if p.env])
        for env in envs:
            self.env_mgr.create_environment(env)

    def spawn_subprocess(self, p, env_vars_base):
        run_cmds = p.validate_commands() + p.run_commands()
        if self.test_mode:
            run_cmds = ['echo "TEST MODE: call {}"'.format('; '.join(run_cmds))]
        commands = self.env_mgr.activate_env_commands(p.env) \
            + run_cmds \
            + self.env_mgr.deactivate_env_commands(p.env)
        if self.test_mode:
            for cmd in commands:
                print('\tTEST MODE: call {}'.format(cmd))
        else:
            p.pod.log.info('\t'+p.run_msg())
        # '&&' so we abort if any command in the sequence fails.
        commands = ' && '.join([s for s in commands if s])

        assert os.path.isdir(p.pod.POD_WK_DIR)
        env_vars = env_vars_base.copy()
        env_vars.update(p.env_vars)
        # Need to run bash explicitly because 'conda activate' sources
        # env vars (can't do that in posix sh). tcsh could also work.
        return subprocess.Popen(
            commands,
            shell=True, executable=self.bash_exec,
            env=env_vars, cwd=p.pod.POD_WK_DIR,
            stdout=p.pod.log_file, stderr=p.pod.log_file,
            universal_newlines=True, bufsize=1
        )

    def run(self):
        # Call cleanup method if we're killed
        signal.signal(signal.SIGTERM, self.runtime_terminate)
        signal.signal(signal.SIGINT, self.runtime_terminate)

        test_list = [p for p in self.iter_active_pods()]
        if not test_list:
            self.case.log.error('%s: no PODs met data requirements; returning',
                self.__class__.__name__)
            return

        env_vars_base = os.environ.copy()
        for p in self.iter_active_pods():
            p.pod.log.info('%s: run %s.', self.__class__.__name__, p.pod.full_name)
            try:
                p.pre_run_setup()
            except Exception as exc:
                p.setup_exception_handler(exc)
                continue
            try:
                p.pod.log_file.write(f"### Start execution of {p.pod.full_name}\n")
                p.pod.log_file.write(80 * '-' + '\n')
                p.pod.log_file.flush()
                p.process = self.spawn_subprocess(p, env_vars_base)
            except Exception as exc:
                p.runtime_exception_handler(exc)
                continue
        # should use asyncio, instead wait for each process
        # to terminate and close all log files
        # TODO: stderr gets eaten with current setup; possible to do a proper
        # tee if procs are run with asyncio? https://stackoverflow.com/a/59041913
        for p in self.pods:
            if p.process is not None:
                p.process.wait()
            p.tear_down()
        self.case.log.info('%s: completed all PODs.', self.__class__.__name__)
        self.tear_down()

    def tear_down(self):
        # cleanup all envs that were defined, just to be safe
        envs = set([p.env for p in self.pods if p.env])
        for env in envs:
            self.env_mgr.destroy_environment(env)
        self.env_mgr.tear_down()

    def runtime_terminate(self, signum=None, frame=None):
        # try to clean up everything
        util.signal_logger(self.__class__.__name__, signum, frame, log=self.case.log)
        for p in self.pods:
            util.signal_logger(self.__class__.__name__, signum, frame, log=p.pod.log)
            p.tear_down()
            p.pod.close_log_file(log=True)
        self.tear_down()
        self.case.close_log_file()
        util.exit_handler(code=1)
