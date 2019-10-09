import os
import sys
import glob
import shutil
import timeit
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
from shared_diagnostic import PodRequirementFailure

class EnvironmentManager(object):
    # analogue of TestSuite in xUnit - abstract base class
    __metaclass__ = ABCMeta

    def __init__(self, config, verbose=0):
        self.test_mode = config['envvars']['test_mode']
        self.pods = []
        self.envs = set()

        # kill child processes if we're killed
        atexit.register(self.abortHandler)
        signal.signal(signal.SIGTERM, self.abortHandler)
        signal.signal(signal.SIGINT, self.abortHandler)

    # -------------------------------------
    # following are specific details that must be implemented in child class 

    @abstractmethod
    def create_environment(self, env_name):
        pass 

    @abstractmethod
    def set_pod_env(self, pod):
        pass 

    @abstractmethod
    def activate_env_commands(self, pod):
        pass 

    @abstractmethod
    def deactivate_env_commands(self, pod):
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
            pod.logfile_obj = open(os.path.join(pod.POD_WK_DIR, pod.name+".log"), 'w')
            log_str = "--- MDTF.py Starting POD {}\n".format(pod.name)
            pod.logfile_obj.write(log_str)
            if verbose > 0: print log_str

            try:
                pod.setUp()
            except PodRequirementFailure as exc:
                log_str = "Skipping execution of {}.\n\tReason: {}\n".format(
                    exc.pod.name, str(exc))
                pod.logfile_obj.write(log_str)
                pod.logfile_obj.close()
                pod.logfile_obj = None
                print log_str
                pod.skipped = exc
                continue
            pod.logfile_obj.write("Found files:\n")
            pod.logfile_obj.write("\n".join(pod.found_files))

            run_command = pod.run_commands()          
            if self.test_mode:
                run_command = ['echo "TEST MODE: would call {}"'.format(run_command)]
            commands = self.activate_env_commands(pod) \
                + pod.validate_commands() \
                + run_command \
                + self.deactivate_env_commands(pod)
            # '&&' so we abort if any command in the sequence fails.
            commands = ' && '.join([s for s in commands if s])
 
            print "Calling : {}".format(run_command)
            print "Will run in env: {}".format(pod.env)
            start_time = timeit.default_timer()
            try:
                # Need to run bash explicitly because 'conda activate' sources 
                # env vars (can't do that in posix sh). tcsh could also work.
                pod.process_obj = subprocess.Popen(
                    ['bash', '-c', commands],
                    env = os.environ, 
                    cwd = pod.POD_WK_DIR,
                    stdout = pod.logfile_obj, stderr = subprocess.STDOUT)
            except OSError as exc:
                print('ERROR :', exc.errno, exc.strerror)
                print " occured with call: {}".format(run_command)
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

    # -------------------------------------

    def tearDown(self):
        # call diag's tearDown to clean up
        for pod in self.pods:
            if isinstance(pod.skipped, Exception):
                pod.append_error_link(pod.skipped)
            else:
                pod.tearDown()
        for env in self.envs:
            self.destroy_environment(env)

    def abortHandler(self, *args):
        # kill child processes if we're killed
        # normal operation should call tearDown for organized cleanup
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

    def activate_env_commands(self, pod):
        return []

    def deactivate_env_commands(self, pod):
        return []

class VirtualenvEnvironmentManager(EnvironmentManager):
    # create Python virtualenv to manage environments.
    # for R, use xxx.
    # Do not attempt management for NCL.

    def __init__(self, config, verbose=0):
        super(VirtualenvEnvironmentManager, self).__init__(config, verbose)

        paths = util.PathManager()
        src_path = os.path.join(paths.CODE_ROOT, 'src')
        assert ('venv_root' in config['settings'])
        # need to resolve relative path
        self.venv_root = util.resolve_path(
            config['settings']['venv_root'], src_path
        )
        if ('r_lib_root' in config['settings']) and \
            config['settings']['r_lib_root'] != '':
            self.r_lib_root = util.resolve_path(
                config['settings']['r_lib_root'], src_path
            )
        else:
            self.r_lib_root = ''

    def create_environment(self, env_name):
        if env_name == 'python':
            self._create_py_venv(env_name)
        elif env_name == 'r':
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
            'pip install --user virtualenv',
            'virtualenv {}'.format(env_path),
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
            pod.env = 'r'
        elif 'ncl' in keys:
            pod.env = 'ncl'
        else:
            pod.env = 'python'

    def activate_env_commands(self, pod):
        env_name = pod.env
        if env_name == 'python':
            env_path = os.path.join(self.venv_root, pod.env)
            return ['source {}/bin/activate'.format(env_path)]
        elif env_name == 'r':
            env_path = os.path.join(self.r_lib_root, pod.env)
            return ['export R_LIBS_USER="{}"'.format(env_path)]
        else:
            return []

    def deactivate_env_commands(self, pod):
        env_name = pod.env
        if env_name == 'python':
            return ['deactivate']
        elif env_name == 'r':
            return ['unset R_LIBS_USER']
        else:
            return []


class CondaEnvironmentManager(EnvironmentManager):
    # Use Anaconda to switch execution environments.

    def __init__(self, config, verbose=0):
        super(CondaEnvironmentManager, self).__init__(config, verbose)

        if ('conda_env_root' in config['settings']) and \
            config['settings']['conda_env_root'] != '':
            # need to resolve relative path
            paths = util.PathManager()
            self.conda_env_root = util.resolve_path(
                config['settings']['conda_env_root'],
                os.path.join(paths.CODE_ROOT, 'src')
            )
            if not os.path.isdir(self.conda_env_root):
                os.makedirs(self.conda_env_root) # recursive mkdir if needed
        else:
            self.conda_env_root = os.path.join(
                subprocess.check_output('conda info --root', shell=True),
                'envs' # only true in default anaconda install, need to fix
            ) 

    def create_environment(self, env_name):
        # check to see if conda env exists, and if not, try to create it
        conda_prefix = os.path.join(self.conda_env_root, env_name)
        test = subprocess.call(
            'conda env list | grep -qF "{}"'.format(conda_prefix), 
            shell=True
        )
        if test != 0:
            print 'Conda env {} not found; creating it'
            self._call_conda_create(env_name)

    def _call_conda_create(self, env_name):
        paths = util.PathManager()
        prefix = '_MDTF-diagnostics'
        if env_name == prefix:
            short_name = 'base'
        else:
            short_name = env_name[(len(prefix)+1):]
        path = '{}/src/conda_env_{}.yml'.format(paths.CODE_ROOT, short_name)
        if not os.path.exists(path):
            print "Can't find {}".format(path)
        else:
            conda_prefix = os.path.join(self.conda_env_root, env_name)
            print 'Creating conda env {} in {}'.format(env_name, conda_prefix)
        
        commands = \
            'source {}/src/conda_init.sh && '.format(paths.CODE_ROOT) \
                + 'conda env create --force -q -p="{}" -f="{}"'.format(
                conda_prefix, path
            )
        try: 
            subprocess.Popen(['bash', '-c', commands])
        except OSError as e:
            print('ERROR :',e.errno,e.strerror)

    def create_all_environments(self):
        paths = util.PathManager()
        command = '{}/src/conda_env_setup.sh'.format(paths.CODE_ROOT)
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

    def activate_env_commands(self, pod):
        # Source conda_init.sh to set things that aren't set b/c we aren't 
        # in an interactive shell.
        paths = util.PathManager()
        conda_prefix = os.path.join(self.conda_env_root, pod.env)
        return ['source {}/src/conda_init.sh && conda activate {}'.format(
            paths.CODE_ROOT, conda_prefix
            )]

    def deactivate_env_commands(self, pod):
        return [] 

