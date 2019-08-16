import os
import sys
import glob
import shutil
import timeit
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except (ImportError, ModuleNotFoundError):
        import subprocess
else:
    import subprocess
import util
from shared_diagnostic import Diagnostic

class EnvironmentManager:
    # analogue of TestSuite in xUnit
    def __init__(self, config, verbose=0):
        if 'pod_list' in config['case_list'][0]:
            # run a set of PODs specific to this model
            pod_list = config['case_list'][0]['pod_list']
        else:
            pod_list = config['pod_list'] # use global list of PODs
        self.pods = []
        for pod_name in pod_list: # list of pod names to do here
            try:
                pod = Diagnostic(pod_name)
            except AssertionError as error:  
                print str(error)
            if verbose > 0: print "POD long name: ", pod.long_name
            self.pods.append(pod)

    # -------------------------------------

    def setUp(self, verbose=0):
        pass 

    # -------------------------------------

    def run(self, config, verbose=0):
        os.chdir(os.environ["WORKING_DIR"])

        for pod in self.pods:
            # Find and confirm POD driver script , program (Default = {pod_name,driver}.{program} options)
            # Each pod could have a settings files giving the name of its driver script and long name
            if verbose > 0: print("--- MDTF.py Starting POD "+pod.name+"\n")

            pod.setUp()
            if pod.missing_files != []:
                print "WARNING: POD ",pod.name," Not executed because missing required input files:"
                print pod.missing_files
                continue
            else:
                if (verbose > 0): print "No known missing required input files"

            pod.logfile_obj = open(os.path.join(os.environ["WK_DIR"], pod.name+".log"), 'w')

            command_str = pod.run_command()            
            if config['envvars']['test_mode']:
                command_str = 'echo "TEST MODE: would call {}"'.format(command_str)
            
            start_time = timeit.default_timer()
            try:
                print("Calling :  "+command_str) # This is where the POD is called #
                print('Will run in conda env: '+pod.conda_env)
                # Details on this invocation: Need to run bash explicitly because 
                # 'conda activate' sources env vars (can't do that in posix sh).
                # tcsh would also work. Source conda_init.sh to set things that 
                # aren't set b/c we aren't in an interactive shell. '&&' so we abort 
                # and don't try to run the POD if 'conda activate' fails.
                pod.process_obj = subprocess.Popen([
                    'bash', '-c',
                    'source '+os.environ['DIAG_HOME']+'/src/conda_init.sh' \
                    + ' && conda activate ' + pod.conda_env \
                    + ' && ' + pod.validate_command() \
                    + ' && ' + command_str],
                    env=os.environ, stdout=pod.logfile_obj, stderr=subprocess.STDOUT)
            except OSError as e:
                print('ERROR :',e.errno,e.strerror)
                print(" occured with call: " +command_str)

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