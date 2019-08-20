import os
import sys
import glob
import shutil
import timeit
from abc import ABCMeta, abstractmethod
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except (ImportError, ModuleNotFoundError):
        import subprocess
else:
    import subprocess
import util

class EnvironmentManager(object):
    # analogue of TestSuite in xUnit - abstract base class
    __metaclass__ = ABCMeta

    def __init__(self, config, verbose=0):
        self.test_mode = config['envvars']['test_mode']
        self.pods = []
        self.envs = set()

    # -------------------------------------
    # following are specific details that must be implemented in child class 

    @abstractmethod
    def create_environment(self, env_name):
        pass 

    @abstractmethod
    def set_pod_env(self, pod):
        pass 

    @abstractmethod
    def activate_env_command(self, pod):
        pass 

    @abstractmethod
    def deactivate_env_command(self, pod):
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
        os.chdir(os.environ["WORKING_DIR"])

        for pod in self.pods:
            # Find and confirm POD driver script , program (Default = {pod_name,driver}.{program} options)
            # Each pod could have a settings files giving the name of its driver script and long name
            if verbose > 0: print("--- MDTF.py Starting POD "+pod.name+"\n")

            pod.setUp()
            # skip this pod if missing data
            if pod.missing_files != []:
                continue

            pod.logfile_obj = open(os.path.join(os.environ["WK_DIR"], pod.name+".log"), 'w')

            run_command = pod.run_command()          
            if self.test_mode:
                run_command = 'echo "TEST MODE: would call {}"'.format(run_command)
            commands = [
                self.activate_env_command(pod), pod.validate_command(), 
                run_command, self.deactivate_env_command(pod)
                ]
            # '&&' so we abort if any command in the sequence fails.
            commands = ' && '.join([s for s in commands if s])
 
            print("Calling :  "+run_command) # This is where the POD is called #
            print('Will run in env: '+pod.env)
            start_time = timeit.default_timer()
            try:
                # Need to run bash explicitly because 'conda activate' sources 
                # env vars (can't do that in posix sh). tcsh could also work.
                pod.process_obj = subprocess.Popen(
                    ['bash', '-c', commands],
                    env=os.environ, stdout=pod.logfile_obj, stderr=subprocess.STDOUT)
            except OSError as e:
                print('ERROR :',e.errno,e.strerror)
                print(" occured with call: " +run_command)

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
            pod.tearDown()
        for env in self.envs:
            self.destroy_environment(env)


class UnmanagedEnvironment(EnvironmentManager):
    # Do not attempt to switch execution environments for each POD.
    def create_environment(self, env_name):
        pass 
    
    def destroy_environment(self, env_name):
        pass 

    def set_pod_env(self, pod):
        pass

    def activate_env_command(self, pod):
        return ''

    def deactivate_env_command(self, pod):
        return '' 


class CondaEnvironmentManager(EnvironmentManager):
    # Use Anaconda to switch execution environments.

    def create_environment(self, env_name):
        # check to see if conda env exists, and if not, try to create it
        test = subprocess.call(
            'conda env list | grep -qF "{} "'.format(env_name), shell=True
        )
        if test != 0:
            print 'Conda env {} not found; creating it'
            self._call_conda_create(env_name)

    def _call_conda_create(self, env_name):
        prefix = '_MDTF-diagnostics'
        if env_name == prefix:
            env_name = 'base'
        else:
            env_name = env_name[(len(prefix)+1):]
        path = '{}/src/conda_env_{}.yml'.format(os.environ['DIAG_HOME'], env_name)
        if not os.path.exists(path):
            print "Can't find {}".format(path)
        else:
            print 'Creating conda env from {}'.format(path)
        
        commands = 'source {}/src/conda_init.sh && conda env create --force -q -f {}'.format(
            os.environ['DIAG_HOME'], path
        )
        try: 
            subprocess.Popen(['bash', '-c', commands])
        except OSError as e:
            print('ERROR :',e.errno,e.strerror)

    def create_all_environments(self):
        envs_to_create = glob.glob('{}/src/conda_env_*.yml'.format(os.environ['DIAG_HOME']))
        envs_to_create = ['echo Creating conda env from '+env+'\n' \
                +'conda env create --force -q -f '+ env for env in envs_to_create]
        command_str = '\n'.join(envs_to_create)
        command_str = 'source {}/src/conda_init.sh\n'.format(os.environ['DIAG_HOME']) \
            + command_str
        process = subprocess.Popen('/usr/bin/env bash', 
            stdin=subprocess.PIPE, shell=True)
        process.communicate(command_str)

    def destroy_environment(self, env_name):
        pass 

    def set_pod_env(self, pod):
        keys = [s.lower() for s in pod.required_programs]
        if ('r' in keys) or ('rscript' in keys):
            pod.env = '_MDTF-diagnostics-R'
        elif 'ncl' in keys:
            pod.env = '_MDTF-diagnostics-NCL'
        else:
            pod.env = '_MDTF-diagnostics'

    def activate_env_command(self, pod):
        # Source conda_init.sh to set things that aren't set b/c we aren't 
        # in an interactive shell. 
        return 'source {}/src/conda_init.sh && conda activate {}'.format(
            os.environ['DIAG_HOME'], pod.env
            )

    def deactivate_env_command(self, pod):
        return '' 
