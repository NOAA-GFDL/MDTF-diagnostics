import os
import sys
import glob
import shutil
import util
from util import setenv # fix

class Model:
    # analogue of TestFixture in xUnit
    def __init__(self, model_name):
        self.model_name = model_name
        # this is wrong place for this method - don't want multiple copies of this data
        self.model_dict = self._read_model_varnames()

    def _read_model_varnames(self, verbose=0):
        model_dict = {}
        config_files = glob.glob(os.environ["DIAG_HOME"]+"/src/config_*.yml")
        for filename in config_files:
            file_contents = util.read_yaml(filename)

            if type(file_contents['model_name']) is str:
                file_contents['model_name'] = [file_contents['model_name']]
            for model in file_contents['model_name']:
                if verbose > 0: print "found model "+ model
                model_dict[model] = file_contents['var_names']
        return model_dict

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
        # todo: set/unset for multiple models
        # verify all vars requested by PODs have been set
        if model_name in self.model_dict:
            for key, val in self.model_dict[model_name].items():
                os.environ[key] = str(val)
        else:
            print "ERROR: model ", model_name," Not Found"
            print "      This is set in namelist "
            print "      CASE case-name *model* start-year end-year"
            quit()

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