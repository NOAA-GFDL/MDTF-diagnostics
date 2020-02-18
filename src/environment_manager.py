from __future__ import print_function
import os
import sys
import glob
import shutil
import atexit
import signal
from abc import ABCMeta, abstractmethod
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
else:
    import subprocess
import util
import util_mdtf
from shared_diagnostic import PodRequirementFailure

class EnvironmentManager(object):
    # analogue of TestSuite in xUnit - abstract base class
    __metaclass__ = ABCMeta

    def __init__(self, verbose=0):
        config = util_mdtf.ConfigManager()
        self.test_mode = config.config.test_mode
        self.pods = []
        self.envs = set()

        # kill any subprocesses that are still active if we exit normally 
        # (shouldn't be necessary) or are killed
        atexit.register(self.subprocess_cleanup)
        signal.signal(signal.SIGTERM, self.subprocess_cleanup)
        signal.signal(signal.SIGINT, self.subprocess_cleanup)

    # -------------------------------------
    # following are specific details that must be implemented in child class 

    @abstractmethod
    def create_environment(self, env_name):
        pass 

    @abstractmethod
    def set_pod_env(self, pod):
        pass 

    @abstractmethod
    def activate_env_commands(self, env_name):
        pass 

    @abstractmethod
    def deactivate_env_commands(self, env_name):
        pass 

    @abstractmethod
    def destroy_environment(self, env_name):
        pass 

    # -------------------------------------

    def setUp(self):
        for pod in self.pods:
            self.set_pod_env(pod)
            self.envs.add(pod.env)
        for env in self.envs:
            self.create_environment(env)

    # -------------------------------------

    def run(self, verbose=0):
        for pod in self.pods:
            pod._setup_pod_directories() # should refactor setUp

            pod.logfile_obj = open(os.path.join(pod.POD_WK_DIR, pod.name+".log"), 'w')
            log_str = "--- MDTF.py Starting POD {}\n".format(pod.name)
            pod.logfile_obj.write(log_str)
            if verbose > 0: print(log_str)

            try:
                pod.setUp()
            except PodRequirementFailure as exc:
                log_str = "\nSkipping execution of {}.\nReason: {}\n".format(
                    exc.pod.name, str(exc))
                pod.logfile_obj.write(log_str)
                pod.logfile_obj.close()
                pod.logfile_obj = None
                print(log_str)
                pod.skipped = exc
                continue
            print("{} will run in env: {}".format(pod.name, pod.env))
            pod.logfile_obj.write("\n".join(
                ["Found files: "] + pod.found_files + [" "]))
            env_list = ["{}: {}". format(k,v) for k,v in pod.pod_env_vars.iteritems()]
            pod.logfile_obj.write("\n".join(
                ["Env vars: "] + sorted(env_list) + [" "]))

            try:
                pod.logfile_obj.write("--- MDTF.py calling POD {}\n\n".format(pod.name))
                pod.logfile_obj.flush()
                pod.process_obj = self.spawn_subprocess(
                    pod.validate_commands() + pod.run_commands(),
                    pod.env,
                    env = os.environ, cwd = pod.POD_WK_DIR,
                    stdout = pod.logfile_obj, stderr = subprocess.STDOUT
                )
            except OSError as exc:
                print('ERROR :', exc.errno, exc.strerror)
                print(" occured with call: {}".format(pod.run_commands()))
                pod.skipped = exc
                pod.logfile_obj.close()
                pod.logfile_obj = None
                continue

        # if this were python3 we'd have asyncio, instead wait for each process
        # to terminate and close all log files
        for pod in self.pods:
            if pod.process_obj is not None:
                pod.process_obj.wait()
                pod.process_obj = None
            if pod.logfile_obj is not None:
                pod.logfile_obj.close()
                pod.logfile_obj = None

    def spawn_subprocess(self, cmd_list, env_name,
        env=None, cwd=None, stdout=None, stderr=None):
        if stdout is None:
            stdout = subprocess.STDOUT
        if stderr is None:
            stderr = subprocess.STDOUT
        run_cmds = util.coerce_to_iter(cmd_list, list)
        if self.test_mode:
            run_cmds = ['echo "TEST MODE: call {}"'.format('; '.join(run_cmds))]
        commands = self.activate_env_commands(env_name) \
            + run_cmds \
            + self.deactivate_env_commands(env_name)
        # '&&' so we abort if any command in the sequence fails.
        if self.test_mode:
            for cmd in commands:
                print('TEST MODE: call {}'.format(cmd))
        else:
            print("Calling : {}".format(run_cmds[-1]))
        commands = ' && '.join([s for s in commands if s])

        # Need to run bash explicitly because 'conda activate' sources 
        # env vars (can't do that in posix sh). tcsh could also work.
        return subprocess.Popen(
            ['bash', '-c', commands],
            env=env, cwd=cwd, stdout=stdout, stderr=stderr 
        )

    # -------------------------------------

    def tearDown(self):
        # call diag's tearDown to clean up
        for pod in self.pods:
            pod.tearDown()
        for env in self.envs:
            self.destroy_environment(env)

    def subprocess_cleanup(self, signum=None, frame=None):
        util.signal_logger(self.__class__.__name__, signum, frame)
        # kill any active subprocesses
        for pod in self.pods:
            if pod.process_obj is not None:
                pod.process_obj.kill()


class NoneEnvironmentManager(EnvironmentManager):
    # Do not attempt to switch execution environments for each POD.
    def create_environment(self, env_name):
        pass 
    
    def destroy_environment(self, env_name):
        pass 

    def set_pod_env(self, pod):
        pass

    def activate_env_commands(self, env_name):
        return []

    def deactivate_env_commands(self, env_name):
        return []

class VirtualenvEnvironmentManager(EnvironmentManager):
    # create Python virtualenv to manage environments.
    # for R, use xxx.
    # Do not attempt management for NCL.

    def __init__(self, verbose=0):
        super(VirtualenvEnvironmentManager, self).__init__(verbose)

        config = util_mdtf.ConfigManager()
        self.venv_root = config.paths.get('venv_root', '')
        self.r_lib_root = config.paths.get('r_lib_root', '')

    def create_environment(self, env_name):
        if env_name.startswith('py_'):
            self._create_py_venv(env_name)
        elif env_name.startswith('r_'):
            self._create_r_venv(env_name)
        else:
            pass

    def _create_py_venv(self, env_name):
        py_pkgs = set()
        for pod in self.pods: 
            if pod.env == env_name:
                py_pkgs.update(set(pod.required_python_modules))
        
        env_path = os.path.join(self.venv_root, env_name)
        if not os.path.isdir(env_path):
            os.makedirs(env_path) # recursive mkdir if needed
        cmds = [
            'python -m virtualenv {}'.format(env_path),
            'source {}/bin/activate'.format(env_path),
            'pip install {}'.format(' '.join(py_pkgs)),
            'deactivate'
        ]
        util.run_shell_commands(cmds)
    
    def _create_r_venv(self, env_name):
        r_pkgs = set()
        for pod in self.pods: 
            if pod.env == env_name:
                r_pkgs.update(set(pod.required_r_packages))
        r_pkg_str = ', '.join(['"'+x+'"' for x in r_pkgs])

        if self.r_lib_root != '':
            env_path = os.path.join(self.r_lib_root, env_name)
            if not os.path.isdir(env_path):
                os.makedirs(env_path) # recursive mkdir if needed
            cmds = [
                'export R_LIBS_USER="{}"'.format(env_path),
                'Rscript -e \'install.packages(c({}), '.format(r_pkg_str) \
                    + 'lib=Sys.getenv("R_LIBS_USER"))\''
            ]
        else:
            cmds = [
                'Rscript -e \'install.packages(c({}))\''.format(r_pkg_str)
            ]
        util.run_shell_commands(cmds)

    def destroy_environment(self, env_name):
        pass 

    def set_pod_env(self, pod):
        keys = [s.lower() for s in pod.required_programs]
        if ('r' in keys) or ('rscript' in keys):
            pod.env = 'r_' + pod.name
        elif 'ncl' in keys:
            pod.env = 'ncl'
        else:
            pod.env = 'py_' + pod.name

    def activate_env_commands(self, env_name):
        if env_name.startswith('py_'):
            env_path = os.path.join(self.venv_root, env_name)
            return ['source {}/bin/activate'.format(env_path)]
        elif env_name.startswith('r_'):
            env_path = os.path.join(self.r_lib_root, env_name)
            return ['export R_LIBS_USER="{}"'.format(env_path)]
        else:
            return []

    def deactivate_env_commands(self, env_name):
        if env_name.startswith('py_'):
            return ['deactivate']
        elif env_name.startswith('r_'):
            return ['unset R_LIBS_USER']
        else:
            return []


class CondaEnvironmentManager(EnvironmentManager):
    # Use Anaconda to switch execution environments.

    def __init__(self, verbose=0):
        super(CondaEnvironmentManager, self).__init__(verbose)

        config = util_mdtf.ConfigManager()
        self.code_root = config.paths.CODE_ROOT
        if 'conda_root' in config.paths:
            self.conda_root = config.paths.conda_root
            self.conda_exe = os.path.join(self.conda_root, 'bin', 'conda')
            assert os.path.exists(self.conda_exe)          
        else:
            self.conda_root = ''
            self.conda_exe = 'conda'

        if 'conda_env_root' in config.paths:
            self.conda_env_root = config.paths.conda_env_root
            if not os.path.isdir(self.conda_env_root):
                os.makedirs(self.conda_env_root) # recursive mkdir if needed
        else:
            # only true in default anaconda install, need to fix
            self.conda_env_root = os.path.join(
                subprocess.check_output(
                    '{} info --root'.format(self.conda_exe), shell=True),
                'envs'
            )

    def create_environment(self, env_name):
        # check to see if conda env exists, and if not, try to create it
        conda_prefix = os.path.join(self.conda_env_root, env_name)
        test = subprocess.call(
            '{} env list | grep -qF "{}"'.format(self.conda_exe, conda_prefix), 
            shell=True
        )
        if test != 0:
            print('Conda env {} not found; creating it'.format(env_name))
            print('grepped for {}'.format(conda_prefix))
            print(subprocess.check_output('echo $CONDA_EXE',shell=True))
            #self._call_conda_create(env_name)

    def _call_conda_create(self, env_name):
        prefix = '_MDTF-diagnostics'
        if env_name == prefix:
            short_name = 'base'
        else:
            short_name = env_name[(len(prefix)+1):]
        path = '{}/src/conda_env_{}.yml'.format(self.code_root, short_name)
        if not os.path.exists(path):
            print("Can't find {}".format(path))
        else:
            conda_prefix = os.path.join(self.conda_env_root, env_name)
            print('Creating conda env {} in {}'.format(env_name, conda_prefix))
        # conda_init for bash defines conda as a shell function; will get error
        # if we try to call the conda executable directly
        commands = \
            'source {}/src/conda_init.sh {} && '.format(
                self.code_root, self.conda_root
            ) \
            + 'conda env create --force -q -p="{}" -f="{}"'.format(
                conda_prefix, path
            )
        try: 
            subprocess.Popen(['bash', '-c', commands])
        except OSError as e:
            print('ERROR :',e.errno,e.strerror)

    def create_all_environments(self):
        command = '{}/src/conda_env_setup.sh'.format(self.code_root)
        try: 
            subprocess.Popen(['bash', '-c', command])
        except OSError as e:
            print('ERROR :',e.errno,e.strerror)

    def destroy_environment(self, env_name):
        pass 

    def set_pod_env(self, pod):
        keys = [s.lower() for s in pod.required_programs]
        if ('r' in keys) or ('rscript' in keys):
            pod.env = '_MDTF-diagnostics-R'
        elif 'ncl' in keys:
            pod.env = '_MDTF-diagnostics-NCL'
        else:
            pod.env = '_MDTF-diagnostics-python'

    def activate_env_commands(self, env_name):
        """Source conda_init.sh to set things that aren't set b/c we aren't 
        in an interactive shell.
        """
        # conda_init for bash defines conda as a shell function; will get error
        # if we try to call the conda executable directly
        conda_prefix = os.path.join(self.conda_env_root, env_name)
        return [
            'source {}/src/conda_init.sh {}'.format(
                self.code_root, self.conda_root
            ),
            'conda activate {}'.format(conda_prefix)
        ]

    def deactivate_env_commands(self, env_name):
        return [] 

