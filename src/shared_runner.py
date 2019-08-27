import os
import sys
import glob
import shutil
import yaml
import util
from util import setenv # fix

class DiagnosticRunner(object):
    # analogue of TestRunner in xUnit
    def __init__(self, args, config,
        data_mgr=None, environment_mgr=None, diagnostic=None):
        # set up env vars, paths
        self._set_mdtf_env_vars(args, config, verbose=0)
        verbose = config['envvars']['verbose']
        util.check_required_dirs(
            already_exist =["DIAG_HOME","MODEL_ROOT_DIR","OBS_ROOT_DIR","RGB"], 
            create_if_nec = ["WORKING_DIR","OUTPUT_DIR"], 
            verbose=verbose)
        self.caselist = []
        self.DataMgr = data_mgr
        self.EnvironmentMgr = environment_mgr
        self.Diagnostic = diagnostic

    def _set_mdtf_env_vars(self, args, config, verbose=0):
        config['envvars'] = {}
        # need to expand ./ and ../ in paths
        for key, val in config['paths'].items():
            if (key in args.__dict__) and (args.__getattribute__(key) != None):
                val = args.__getattribute__(key)
            val = os.path.realpath(val)
            setenv(key, val, config['envvars'], verbose=verbose)

        # following are redundant but used by PODs
        setenv("RGB",os.environ["DIAG_HOME"]+"/src/rgb",config['envvars'],overwrite=False,verbose=verbose)

        vars_to_set = config['settings'].copy()
        vars_to_set.update(config['case_list'][0])
        for key, val in vars_to_set.items():
            if (key in args.__dict__) and (args.__getattribute__(key) != None):
                val = args.__getattribute__(key)
            setenv(key, val, config['envvars'], verbose=verbose)

    # -------------------------------------

    def setUp(self, config, caselist, verbose=0):
        # parse caselist - foreach model init data, and call prefetch to (possibly) download data
        for case_dict in caselist:
            case = self.DataMgr(case_dict)

            if 'pod_list' in case_dict:
                pod_list = case_dict['pod_list'] # run a set of PODs specific to this model
            else:
                pod_list = config['pod_list'] # use global list of PODs      
            for pod_name in pod_list:
                try:
                    pod = self.Diagnostic(pod_name)
                except AssertionError as error:  
                    print str(error)
                if verbose > 0: print "POD long name: ", pod.long_name
                case.pods.append(pod)

            case.setUp(config)
            case.fetchData()
            self.caselist.append(case)

    # -------------------------------------

    def run(self, config):
        # foreach model call in-loop setup
        # for case in caselist:
        for case in self.caselist:
            env = self.EnvironmentMgr(config)
            env.pods = case.pods # best way to do this?
            env.setUp()
            env.run()
            env.tearDown()

    # -------------------------------------

    def tearDown(self, config):
        for case in self.caselist:
            case.tearDown(config)