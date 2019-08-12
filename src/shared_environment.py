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
from util import setenv # fix
from shared_diagnostic import Diagnostic

# TODO: combine pod_list and pod_configs

class EnvironmentManager:
    # analogue of TestSuite in xUnit
    def __init__(self, config):
        if 'pod_list' in config['case_list'][0]:
            # run a set of PODs specific to this model
            self.pod_list = config['case_list'][0]['pod_list']
        else:
            self.pod_list = config['pod_list'] # use global list of PODs
        self.pod_configs = []

    # -------------------------------------

    def setUp(self, verbose=0):
        for pod_name in self.pod_list: # list of pod names to do here
            try:
                pod = Diagnostic(pod_name)
                self._check_pod_driver(pod.config['settings'])
                var_files = self._check_for_varlist_files(pod.config['varlist'], verbose)
                pod.config.update(var_files)
            except AssertionError as error:  
                print str(error)
            if ('long_name' in pod.config['settings']) and verbose > 0: 
                print "POD long name: ", pod.config['settings']['long_name']

            if len(pod.config['missing_files']) > 0:
                print "WARNING: POD ",pod," Not executed because missing required input files:"
                print pod.config['missing_files']
                continue
            else:
                if (verbose > 0): print "No known missing required input files"
            self.pod_configs.append(pod)

    def _check_pod_driver(self, settings, verbose=0):
        from distutils.spawn import find_executable #determine if a program is on $PATH

        func_name = "check_pod_driver "
        if (verbose > 1):  print func_name," received POD settings: ", settings

        pod_name = settings['pod_name']
        pod_dir  = settings['pod_dir']
        programs = util.get_available_programs()

        if (not 'driver' in settings):  
            print "WARNING: no valid driver entry found for ", pod_name
            #try to find one anyway
            try_filenames = [pod_name+".","driver."]      
            file_combos = [ file_root + ext for file_root in try_filenames for ext in programs.keys()]
            if verbose > 1: print "Checking for possible driver names in ",pod_dir," ",file_combos
            for try_file in file_combos:
                try_path = os.path.join(pod_dir,try_file)
                if verbose > 1: print " looking for driver file "+try_path
                if os.path.exists(try_path):
                    settings['driver'] = try_path
                    if (verbose > 0): print "Found driver script for "+pod_name+" : "+settings['driver']
                    break    #go with the first one found
                else:
                    if (verbose > 1 ): print "\t "+try_path+" not found..."
        errstr_nodriver = "No driver script found for package "+pod_name +"\n\t"\
            +"Looked in "+pod_dir+" for pod_name.* or driver.* \n\t"\
            +"To specify otherwise, add a line to "+pod_name+"/settings file containing:  driver driver_script_name \n\t" \
            +"\n\t"+func_name
        assert ('driver' in settings), errstr_nodriver

        if not os.path.isabs(settings['driver']): # expand relative path
            settings['driver'] = os.path.join(settings['pod_dir'], settings['driver'])

        errstr = "ERROR: "+func_name+" can't find "+ settings['driver']+" to run "+pod_name
        assert(os.path.exists(settings['driver'])), errstr 

        if (not 'program' in settings):
            # Find ending of filename to determine the program that should be used
            driver_ext  = settings['driver'].split(".")[-1]
            # Possible error: Driver file type unrecognized
            errstr_badext = func_name+" does not know how to call a ."+driver_ext+" file \n\t"\
                +"Available programs: "+str(programs.keys())
            assert (driver_ext in programs), errstr_badext
            settings['program'] = programs[driver_ext]
            if ( verbose > 1): print func_name +": Found program "+programs[driver_ext]
        errstr = "ERROR: "+func_name+" can't find "+ settings['program']+" to run "+pod_name
        assert(find_executable(settings['program']) is not None), errstr     

    def _check_for_varlist_files(self, varlist, verbose=0):
        func_name = "\t \t check_for_varlist_files :"
        if ( verbose > 2 ): print func_name+" check_for_varlist_files called with ",varlist
        found_list = []
        missing_list = []
        for item in varlist:
            if (verbose > 2 ): print func_name +" "+item
            filepath = util.makefilepath(item['name_in_model'],item['freq'],os.environ['CASENAME'],os.environ['DATADIR'])

            if (os.path.isfile(filepath)):
                print "found ",filepath
                found_list.append(filepath)
                continue
            if (not item['required']):
                print "WARNING: optional file not found ",filepath
                continue
            if not (('alternates' in item) and (len(item['alternates'])>0)):
                print "ERROR: missing required file ",filepath,". No alternatives found"
                missing_list.append(filepath)
            else:
                alt_list = item['alternates']
                print "WARNING: required file not found ",filepath,"\n \t Looking for alternatives: ",alt_list
                for alt_item in alt_list: # maybe some way to do this w/o loop since check_ takes a list
                    if (verbose > 1): print "\t \t examining alternative ",alt_item
                    new_var = item.copy()  # modifyable dict with all settings from original
                    new_var['name_in_model'] = util.translate_varname(alt_item,verbose=verbose)  # alternative variable name 
                    del new_var['alternates']    # remove alternatives (could use this to implement multiple options)
                    if ( verbose > 2): print "created new_var for input to check_for_varlist_files",new_var
                    new_files = self._check_for_varlist_files([new_var],verbose=verbose)
                    found_list.extend(new_files['found_files'])
                    missing_list.extend(new_files['missing_files'])

        if (verbose > 2): print "check_for_varlist_files returning ",missing_list
        # remove empty list entries
        files = {}
        files['found_files'] = [x for x in found_list if x]
        files['missing_files'] = [x for x in missing_list if x]
        return files

    # -------------------------------------

    def run(self, config, verbose=0):
        os.chdir(os.environ["WORKING_DIR"])

        pod_procs = []
        log_files = []
        for pod in self.pod_configs:
            # Find and confirm POD driver script , program (Default = {pod_name,driver}.{program} options)
            # Each pod could have a settings files giving the name of its driver script and long name
            pod_name = pod.config['settings']['pod_name']
            if verbose > 0: print("--- MDTF.py Starting POD "+pod_name+"\n")
            pod.setUp()

            command_str = pod.config['settings']['program']+" "+pod.config['settings']['driver']  
            if config['envvars']['test_mode']:
                print("TEST mode: would call :  "+command_str)
            else:
                start_time = timeit.default_timer()
                log = open(os.environ["WK_DIR"]+"/"+pod_name+".log", 'w')
                log_files.append(log)   
                try:
                    print("Calling :  "+command_str) # This is where the POD is called #
                    print('Will run in conda env: '+pod.config['settings']['conda_env'])
                    # Details on this invocation: Need to run bash explicitly because 
                    # 'conda activate' sources env vars (can't do that in posix sh).
                    # tcsh would also work. Source conda_init.sh to set things that 
                    # aren't set b/c we aren't in an interactive shell. '&&' so we abort 
                    # and don't try to run the POD if 'conda activate' fails.
                    proc = subprocess.Popen([
                        'bash', '-c',
                        'source '+os.environ['DIAG_HOME']+'/src/conda_init.sh' \
                        + ' && conda activate '+pod.config['settings']['conda_env'] \
                        + ' && ' + command_str],
                        env=os.environ, stdout=log, stderr=subprocess.STDOUT)
                    pod_procs.append(proc)
                except OSError as e:
                    print('ERROR :',e.errno,e.strerror)
                    print(" occured with call: " +command_str)

        for proc in pod_procs:
            proc.wait()

        for log in log_files:
            log.close

    # -------------------------------------

    def tearDown(self):
        # call diag's tearDown to clean up
        for pod in self.pod_configs:
            pod.tearDown()