import os
import sys
import glob
import shutil
import atexit
import signal
from abc import ABCMeta, abstractmethod
import util
import datelabel
from shared_diagnostic import PodRequirementFailure

class DataQueryFailure(Exception):
    """Exception signaling a failure to find requested data in the remote location. 
    
    Raised by :meth:`~data_manager.DataManager.queryData` to signal failure of a
    data query. Should be caught properly in :meth:`~data_manager.DataManager.planData`
    or :meth:`~data_manager.DataManager.fetchData`.
    """
    def __init__(self, dataset, msg=None):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        if self.msg is not None:
            return 'Query failure for {}: {}.'.format(self.dataset.name, self.msg)
        else:
            return 'Query failure for {}.'.format(self.dataset.name)

class DataManager(object):
    # analogue of TestFixture in xUnit
    __metaclass__ = ABCMeta

    def __init__(self, case_dict, config={}, verbose=0):
        self.case_name = case_dict['CASENAME']
        self.model_name = case_dict['model']
        self.firstyr = datelabel.Date(case_dict['FIRSTYR'])
        self.lastyr = datelabel.Date(case_dict['LASTYR'])
        self.date_range = datelabel.DateRange(self.firstyr, self.lastyr)
        if 'envvars' in config:
            self.envvars = config['envvars'].copy() # gets appended to
        else:
            self.envvars = {}

        if 'variable_convention' in case_dict:
            self.convention = case_dict['variable_convention']
        else:
            self.convention = 'CF' # default to assuming CF-compliance
        if 'pod_list' in case_dict:
            # run a set of PODs specific to this model
            self.pod_list = case_dict['pod_list'] 
        else:
            self.pod_list = config['pod_list'] # use global list of PODs      
        self.pods = []

        paths = util.PathManager()
        self.__dict__.update(paths.modelPaths(self))

        # delete temp files if we're killed
        atexit.register(self.abortHandler)
        signal.signal(signal.SIGTERM, self.abortHandler)
        signal.signal(signal.SIGINT, self.abortHandler)

    def iter_vars(self):
        """Generator iterating over all variables in all pods.
        """
        for p in self.pods:
            for var in p.varlist:
                yield var

    def iter_remotes(self):
        """Generator iterating over remote_resource attributes of pods' variables.
        """
        for var in self.iter_vars():
            for file_ in var.remote_resource:
                yield file_


    # -------------------------------------

    def setUp(self):
        self._setup_model_paths()
        self._set_model_env_vars()
        self._setup_html()
        for pod in self.pods:
            self._setup_pod(pod)

    def _setup_model_paths(self, verbose=0):
        util.check_required_dirs(
            already_exist =[], 
            create_if_nec = [self.MODEL_WK_DIR, self.MODEL_DATA_DIR], 
            verbose=verbose)

    def _set_model_env_vars(self, verbose=0):
        self.envvars.update({
            "DATADIR": self.MODEL_DATA_DIR,
            "variab_dir": self.MODEL_WK_DIR,
            "CASENAME": self.case_name,
            "model": self.model_name,
            "FIRSTYR": self.firstyr,
            "LASTYR": self.lastyr
        })

        translate = util.VariableTranslator()
        # Silently set env vars for *all* model variables, because it contains
        # things like axis mappings etc. Relevant variable names will get 
        # overridden when POD sets its variables.
        assert self.convention in translate.field_dict, \
            "Variable name translation doesn't recognize {}.".format(self.convention)
        for key, val in translate.field_dict[self.convention].items():
            util.setenv(key, val, self.envvars, verbose=verbose)

    def _setup_html(self):
        paths = util.PathManager()
        html_dir = os.path.join(paths.CODE_ROOT, 'src', 'html')
        html_file = os.path.join(self.MODEL_WK_DIR, 'index.html')
        if os.path.isfile(html_file):
            print("WARNING: index.html exists, deleting.")
            os.remove(html_file)
        shutil.copy2(
            os.path.join(html_dir, 'mdtf_diag_banner.png'), self.MODEL_WK_DIR
        )
        shutil.copy2(
            os.path.join(html_dir, 'mdtf1.html'), html_file
        )

    def _setup_pod(self, pod):
        paths = util.PathManager()
        translate = util.VariableTranslator()
        pod.__dict__.update(paths.modelPaths(self))
        pod.__dict__.update(paths.podPaths(pod))
        pod.pod_env_vars.update(self.envvars)

        for var in pod.iter_vars_and_alts():
            var.name_in_model = translate.fromCF(self.convention, var.CF_name)
            var.date_range = self.date_range
            var.local_resource = self.local_path(var)

    # -------------------------------------

    def local_path(self, dataset):
        """Returns the absolute path of the local copy of the file for dataset.

        This determines the local model data directory structure, which is
        `$MODEL_DATA_ROOT/<CASENAME>/<freq>/<CASENAME>.<var name>.<freq>.nc'`.
        Files not following this convention won't be found.
        """
        freq = dataset.date_freq.format_local()
        return os.path.join(
            self.MODEL_DATA_DIR, freq,
            "{}.{}.{}.nc".format(
                self.case_name, dataset.name_in_model, freq)
        )

    def fetch_data(self, verbose=0):
        for pod in self.pods:
            new_varlist = []
            for var in pod.varlist:
                try:
                    new_varlist.extend(self._query_dataset_and_alts(var))
                except DataQueryFailure:
                    print "Data query failed on pod {}".format(pod.name)
                    continue
            pod.varlist = new_varlist

        # TODO: better way to handle these two options
        data_to_fetch = self.plan_data_fetching()
        if data_to_fetch is not None:
            # explicit list of files/resources
            for file_ in data_to_fetch:
                self.fetch_dataset(file_)
        else:
            # fetch_dataset will figure out files from info in vars
            for var in self.iter_vars():
                self.fetch_dataset(var)

        # do translation/ transformations of data here
        self.process_fetched_data()

    def _query_dataset_and_alts(self, dataset):
        """Wrapper for query_dataset that looks for alternate variables.

        Note: 
            This has a different interface than 
            :meth:`~data_manager.DataManager.query_dataset`. That method returns
            nothing but populates the remote_resource attribute of its argument.
            This method returns a list of :obj:`~util.DataSet`s.

        Args:
            dataset (:obj:`~util.DataSet`): Requested variable
                to search for.
        
        Returns: :obj:`list` of :obj:`~util.DataSet`.
        """
        try:
            self.query_dataset(dataset)
            dataset.alternates = []
            return [dataset]
        except DataQueryFailure:
            print "Couldn't find {}, trying alternates".format(dataset.name)
            if len(dataset.alternates) == 0:
                print "Couldn't find {} & no alternates".format(dataset.name)
                raise
            # check for all alternates
            for alt_var in dataset.alternates:
                try: 
                    self.query_dataset(alt_var)
                except DataQueryFailure:
                    print "Couldn't find alternate data {}".format(alt_var.name)
                    raise
            return dataset.alternates

    def plan_data_fetching(self):
        """Process list of requested data to make data fetching efficient.

        This is intended as a hook to be used by subclasses. Default behavior is
        to delete from the list duplicate datasets and datasets where a local
        copy of the data already exists and is current (as determined by 
        :meth:`~data_manager.DataManager.local_data_is_current`).
        
        Returns: collection of :class:`~util.DataSet`
            objects.
        """
        # remove duplicates from list of all remote_resources
        unique_data = set(self.iter_remotes())
        # filter out any data we've previously fetched that's up to date
        return [d for d in unique_data if not self.local_data_is_current(d)]
    
    def local_data_is_current(self, dataset):
        """Determine if local copy of data needs to be refreshed.

        This is intended as a hook to be used by subclasses. Default is to always
        return `False`, ie always fetch remote data.

        Returns: `True` if local copy of data exists and remote copy hasn't been
            updated.
        """
        return False

    # following are specific details that must be implemented in child class 
    @abstractmethod
    def query_dataset(self, dataset):
        pass

    @abstractmethod
    def fetch_dataset(self, dataset):
        pass

    @abstractmethod
    def process_fetched_data(self):
        pass

    # -------------------------------------

    def tearDown(self, config):
        # TODO: handle OSErrors in all of these
        self._backup_config_file(config)
        self._make_tar_file()
        self._copy_to_output()
        paths = util.PathManager()
        paths.cleanup()

    def _backup_config_file(self, config, verbose=0):
        # Record settings in file variab_dir/config_save.yml for rerunning
        out_file = os.path.join(self.MODEL_WK_DIR, 'config_save.yml')
        if os.path.isfile(out_file):
            out_fileold = os.path.join(self.MODEL_WK_DIR, 'config_save.yml.old')
            if verbose > 1: 
                print "WARNING: moving existing namelist file to ", out_fileold
            shutil.move(out_file, out_fileold)
        util.write_yaml(config, out_file)

    def _make_tar_file(self):
        # Make tar file
        if os.environ["make_variab_tar"] == "0":
            print "Not making tar file because make_variab_tar = 0"
            return

        print "Making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
        if os.path.isfile(self.MODEL_WK_DIR+'.tar'):
            print "Moving existing {0}.tar to {0}.tar.old".format(self.MODEL_WK_DIR)
            shutil.move(self.MODEL_WK_DIR+'.tar', self.MODEL_WK_DIR+'.tar.old')

        print "Creating {}.tar".format(self.MODEL_WK_DIR)
        # not running in shell, so don't need to quote globs
        tar_flags = ["--exclude=*.{}".format(s) for s in ['netCDF','nc','ps','PS']]
        util.run_command(['tar', '-cf', '{}.tar'.format(self.MODEL_WK_DIR),
            self.MODEL_WK_DIR ] + tar_flags
        )

    def _copy_to_output(self):
        paths = util.PathManager()
        if paths.OUTPUT_DIR != paths.WORKING_DIR:
            if os.path.exists(self.MODEL_OUT_DIR):
                shutil.rmtree(self.MODEL_OUT_DIR)
            shutil.copytree(self.MODEL_WK_DIR, self.MODEL_OUT_DIR)

    def abortHandler(self, *args):
        # delete any temp files if we're killed
        # normal operation should call tearDown for organized cleanup
        paths = util.PathManager()
        paths.cleanup()


class LocalfileDataManager(DataManager):
    # Assumes data files are already present in required directory structure 
    def query_dataset(self, dataset):
        path = self.local_path(dataset)
        if os.path.isfile(path):
            dataset.remote_resource = path
        else:
            raise DataQueryFailure(dataset, 'File not found at {}'.format(path))
    
    def local_data_is_current(self, dataset):
        return True 

    def fetch_dataset(self, dataset):
        dataset.local_resource = dataset.remote_resource

    def process_fetched_data(self):
        pass
