import os
import sys
import glob
import shutil
import yaml
import util
from util import setenv # fix
from shared_model import Model
from shared_environment import CondaEnvironmentManager

class DiagnosticRunner:
    # analogue of TestRunner in xUnit
    def __init__(self, args, config):
        # set up env vars, paths
        self._set_mdtf_env_vars(args, config, verbose=0)
        verbose = config['envvars']['verbose']
        util.check_required_dirs(
            already_exist =["DIAG_HOME","MODEL_ROOT_DIR","OBS_ROOT_DIR","RGB"], 
            create_if_nec = ["WORKING_DIR","OUTPUT_DIR"], 
            verbose=verbose)
        self.models = []

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

    def setUp(self, config, caselist):
        # parse caselist - foreach model init data, and call prefetch to (possibly) download data
        # for case in caselist:
        case = caselist[0]
        model = Model(case['model'])
        model.prefetchData()
        model.setUp(config)
        self.models.append(model)
        

    # -------------------------------------

    def run(self, config):
        # foreach model call in-loop setup
        # for case in caselist:
        env = CondaEnvironmentManager(config)
        env.setUp()
        env.run(config)
        env.tearDown()

    # -------------------------------------

    def tearDown(self, config):
        for model in self.models:
            model.tearDown()
        self._backupConfigFile(config)
        self._makeTarFile()

    def _backupConfigFile(self, config, verbose = 0):
        # Record settings in file variab_dir/config_save.yml for rerunning
        out_file = os.environ["variab_dir"]+'/config_save.yml'
        if os.path.isfile(out_file):
            out_fileold = os.environ["variab_dir"]+'/config_save_OLD.yml'
            if ( verbose > 1 ): print "WARNING: moving existing namelist file to ",out_fileold
            shutil.move(out_file,out_fileold)
        util.write_yaml(config, out_file)

    def _makeTarFile(self):
        # Make tar file
        variab_dir = os.environ["variab_dir"]
        if ( ( os.environ["make_variab_tar"] == "0" ) ):
            print "Not making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
        else:
            print "Making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
            if os.path.isfile( os.environ["variab_dir"]+".tar" ):
                print "Moving existing "+os.environ["variab_dir"]+".tar to "+os.environ["variab_dir"]+".tar_old"
                os.system("mv -f "+os.environ["variab_dir"]+".tar "+os.environ["variab_dir"]+".tar_old")
                os.chdir(os.environ["WORKING_DIR"])

        print "Creating "+os.environ["variab_dir"]+".tar "
        status = os.system(
            "tar --exclude='*netCDF' --exclude='*nc' --exclude='*ps' --exclude='*PS' -cf " + variab_dir + ".tar " + variab_dir)
        if not status == 0:
            print("ERROR $0")
            print("trying to do:     tar -cf "+os.environ["variab_dir"]+".tar "+os.environ["variab_dir"])
            exit()