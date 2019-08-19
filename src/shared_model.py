import os
import sys
import glob
import shutil
import util
from util import setenv # fix
from shared_diagnostic import Diagnostic

class Model:
    # analogue of TestFixture in xUnit
    def __init__(self, case, config, verbose=0):
        self.case_name = case['CASENAME']
        self.model_name = case['model']
        self.pods = []
        if 'pod_list' in case:
            pod_list = case['pod_list'] # run a set of PODs specific to this model
        else:
            pod_list = config['pod_list'] # use global list of PODs      
        for pod_name in pod_list:
            try:
                pod = Diagnostic(pod_name, self.model_name)
            except AssertionError as error:  
                print str(error)
            if verbose > 0: print "POD long name: ", pod.long_name
            self.pods.append(pod)

    # -------------------------------------

    def prefetchData(self):
        pass

    def fetchData(self):
        pass

    # -------------------------------------

    def setUp(self, config):
        self._setup_model_paths(config)
        self._set_model_env_vars(self.model_name)
        self._setup_html()

    def _setup_model_paths(self, config, verbose=0):
        setenv("DATADIR",os.path.join(os.environ['MODEL_ROOT_DIR'], os.environ["CASENAME"]),config['envvars'],overwrite=False,verbose=verbose)
        variab_dir = "MDTF_"+os.environ["CASENAME"]+"_"+os.environ["FIRSTYR"]+"_"+os.environ["LASTYR"]
        setenv("variab_dir",os.path.join(os.environ['WORKING_DIR'], variab_dir),config['envvars'],overwrite=False,verbose=verbose)
        util.check_required_dirs(
            already_exist =["DATADIR"], create_if_nec = ["variab_dir"], 
            verbose=verbose)

    def _set_model_env_vars(self, model_name):
        translate = util.VariableTranslator()
        # todo: set/unset for multiple models
        # verify all vars requested by PODs have been set
        for key, val in translate.model_dict[model_name].items():
            os.environ[key] = str(val)

    def _setup_html(self):
        if os.path.isfile(os.environ["variab_dir"]+"/index.html"):
            print("WARNING: index.html exists, not re-creating.")
        else: 
            html_dir = os.environ["DIAG_HOME"]+"/src/html/"
            os.system("cp "+html_dir+"mdtf_diag_banner.png "+os.environ["variab_dir"])
            os.system("cp "+html_dir+"mdtf1.html "+os.environ["variab_dir"]+"/index.html")

    # -------------------------------------

    def tearDown(self):
        # delete data if we need to
        pass