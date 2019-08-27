import os
import sys
import glob
import shutil
from abc import ABCMeta, abstractmethod
import util
from util import setenv # fix

class DataManager(object):
    # analogue of TestFixture in xUnit
    __metaclass__ = ABCMeta

    def __init__(self, case, verbose=0):
        self.case_name = case['CASENAME']
        self.model_name = case['model']
        self.firstyr = case['FIRSTYR']
        self.lastyr = case['LASTYR']
        self.pods = []
        if 'variable_convention' in case:
            self.convention = case['variable_convention']
        else:
            self.convention = 'CF' # default to assuming CF-compliance

        paths = util.PathManager()
        self.__dict__.update(paths.modelPaths(self))

    # -------------------------------------

    def setUp(self, config):
        self._setup_model_paths()
        self._set_model_env_vars(config)
        self._setup_html()
        self._setup_pods()

    def _setup_model_paths(self, verbose=0):
        util.check_required_dirs(
            already_exist =[self.MODEL_DATA_DIR], 
            create_if_nec = [self.MODEL_WK_DIR], 
            verbose=verbose)

    def _set_model_env_vars(self, config, verbose=0):
        setenv("DATADIR", self.MODEL_DATA_DIR, config['envvars'],
            overwrite=False,verbose=verbose)
        setenv("variab_dir", self.MODEL_WK_DIR, config['envvars'],
            overwrite=False,verbose=verbose)

        translate = util.VariableTranslator()
        # todo: set/unset for multiple models
        # verify all vars requested by PODs have been set
        assert self.convention in translate.field_dict, \
            "Variable name translation doesn't recognize {}.".format(self.convention)
        for key, val in translate.field_dict[self.convention].items():
            os.environ[key] = str(val)

    def _setup_html(self):
        if os.path.isfile(os.path.join(self.MODEL_WK_DIR, 'index.html')):
            print("WARNING: index.html exists, not re-creating.")
        else: 
            paths = util.PathManager()
            html_dir = os.path.join(paths.CODE_ROOT, 'src', 'html')
            shutil.copy2(
                os.path.join(html_dir, 'mdtf_diag_banner.png'), self.MODEL_WK_DIR
            )
            shutil.copy2(
                os.path.join(html_dir, 'mdtf1.html'), 
                os.path.join(self.MODEL_WK_DIR, 'index.html')
            )

    def _setup_pods(self):
        paths = util.PathManager()
        translate = util.VariableTranslator()
        for pod in self.pods:
            pod.__dict__.update(paths.modelPaths(self))
            for idx, var in enumerate(pod.varlist):
                cf_name = translate.toCF(pod.convention, var['var_name'])
                pod.varlist[idx]['CF_name'] = cf_name
                pod.varlist[idx]['name_in_model'] = translate.fromCF(self.convention, cf_name)

    # -------------------------------------

    def fetchData(self):
        self.planData()
        for var in self.data_to_fetch:
            self.fetchDataset(var)
        # do translation/ transformation of data too

    def planData(self):
        # definitely a cleaner way to write this
        self.data_to_fetch = []
        for pod in self.pods:
            for var in pod.varlist:
                if self.queryDataset(var):
                    self.data_to_fetch.append(var)
                else:
                    alt_vars = []
                    for v in var['alternates']:
                        temp = var.copy()
                        temp['var_name'] = v
                        alt_vars.append(temp)
                    if all([self.queryDataset(v) for v in alt_vars]):
                        for v in alt_vars:
                            self.data_to_fetch.append(v)             

    # following are specific details that must be implemented in child class 
    @abstractmethod
    def queryDataset(self, dataspec_dict):
        return True
    
    @abstractmethod
    def fetchDataset(self, dataspec_dict):
        pass

    # -------------------------------------

    def tearDown(self, config):
        self._backupConfigFile(config)
        self._makeTarFile()

    def _backupConfigFile(self, config, verbose=0):
        # Record settings in file variab_dir/config_save.yml for rerunning
        out_file = os.path.join(self.MODEL_WK_DIR, 'config_save.yml')
        if os.path.isfile(out_file):
            out_fileold = os.path.join(self.MODEL_WK_DIR, 'config_save.yml.old')
            if verbose > 1: 
                print "WARNING: moving existing namelist file to ", out_fileold
            shutil.move(out_file, out_fileold)
        util.write_yaml(config, out_file)

    def _makeTarFile(self):
        # Make tar file
        if os.environ["make_variab_tar"] == "0":
            print "Not making tar file because make_variab_tar = 0"
            return

        print "Making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
        if os.path.isfile(self.MODEL_WK_DIR+'.tar'):
            print "Moving existing {0}.tar to {0}.tar.old".format(self.MODEL_WK_DIR)
            shutil.move(self.MODEL_WK_DIR+'.tar', self.MODEL_WK_DIR+'.tar.old')

        print "Creating {}.tar".format(self.MODEL_WK_DIR)
        tar_flags = "--exclude='*netCDF' --exclude='*nc' --exclude='*ps' --exclude='*PS'"
        status = os.system("tar {0} -cf {1}.tar {1}".format(tar_flags, self.MODEL_WK_DIR))
        if not status == 0:
            print("ERROR in assembling tar file for {}".format(self.case_name))


class LocalFileData(DataManager):
    # Assumes data files are already present in required directory structure 
    def queryDataset(self, dataspec_dict):
        filepath = util.makefilepath(
            dataspec_dict['name_in_model'], dataspec_dict['freq'],
            os.environ['CASENAME'], os.environ['DATADIR'])
        return os.path.isfile(filepath)
            
    def fetchDataset(self, dataspec_dict):
        pass