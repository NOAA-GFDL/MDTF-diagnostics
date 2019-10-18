import os
import sys
import glob
import shutil
import atexit
import signal
from collections import defaultdict
from itertools import chain
from operator import attrgetter
from abc import ABCMeta, abstractmethod
import datetime
import util
import datelabel
import netcdf_helper
from shared_diagnostic import PodRequirementFailure

class DataQueryFailure(Exception):
    """Exception signaling a failure to find requested data in the remote location. 
    
    Raised by :meth:`~data_manager.DataManager.queryData` to signal failure of a
    data query. Should be caught properly in :meth:`~data_manager.DataManager.planData`
    or :meth:`~data_manager.DataManager.fetchData`.
    """
    def __init__(self, dataset, msg=''):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        return 'Query failure for {}: {}.'.format(self.dataset.name, self.msg)

class DataAccessError(Exception):
    """Exception signaling a failure to obtain data from the remote location.
    """
    def __init__(self, dataset, msg=''):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        return 'Data access error for {}: {}.'.format(
            self.dataset._remote_data, self.msg)

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
        elif 'pod_list' in config:
            self.pod_list = config['pod_list'] # use global list of PODs  
        else:
            self.pod_list = [] # should raise warning    
        if 'data_freq' in case_dict:
            self.data_freq = datelabel.DateFrequency(case_dict['data_freq'])
        else:
            self.data_freq = None
        self.pods = []

        paths = util.PathManager()
        self.__dict__.update(paths.modelPaths(self))

        # dynamic inheritance to add netcdf manipulation functions
        # source: https://stackoverflow.com/a/8545134
        if ('settings' not in config) or ('netcdf_helper' not in config['settings']):
            mixin = 'NetcdfHelper' # default
        else:
            mixin = config['settings']['netcdf_helper']
        mixin = getattr(netcdf_helper, mixin)
        self.__class__ = type(self.__class__.__name__, (self.__class__, mixin), {})
        try:
            self.nc_check_environ() # make sure we have dependencies
        except Exception:
            raise

        if ('settings' not in config) or ('file_transfer_timeout' not in config['settings']):
            self.file_transfer_timeout = 0 # syntax for no timeout
        else:
            self.file_transfer_timeout = config['settings']['file_transfer_timeout']

        # delete temp files if we're killed
        atexit.register(self.abortHandler)
        signal.signal(signal.SIGTERM, self.abortHandler)
        signal.signal(signal.SIGINT, self.abortHandler)

    def iter_pods(self):
        """Generator iterating over all pods which haven't been
        skipped due to requirement errors.
        """
        for p in self.pods:
            if p.skipped is None:
                yield p

    def iter_vars(self):
        """Generator iterating over all variables in all pods which haven't been
        skipped due to requirement errors.
        """
        for p in self.iter_pods():
            for var in p.varlist:
                yield var

    # -------------------------------------

    def setUp(self):
        self._setup_model_paths()
        self._set_model_env_vars()
        self._setup_html()
        for pod in self.iter_pods():
            self._setup_pod(pod)
        self._build_data_dicts()

    def _setup_model_paths(self, verbose=0):
        # pylint: disable=maybe-no-member
        util.check_required_dirs(
            already_exist =[], 
            create_if_nec = [self.MODEL_WK_DIR, self.MODEL_DATA_DIR], 
            verbose=verbose)

    def _set_model_env_vars(self, verbose=0):
        # pylint: disable=maybe-no-member
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
        temp = translate.field_dict[self.convention].to_dict()
        for key, val in temp.items():
            util.setenv(key, val, self.envvars, verbose=verbose)

    def _setup_html(self):
        # pylint: disable=maybe-no-member
        paths = util.PathManager()
        src_dir = os.path.join(paths.CODE_ROOT, 'src', 'html')
        src = os.path.join(src_dir, 'mdtf1.html')
        dest = os.path.join(self.MODEL_WK_DIR, 'index.html')
        if os.path.isfile(dest):
            print("WARNING: index.html exists, deleting.")
            os.remove(dest)
        util.append_html_template(src, dest, self.envvars, create=True)
        shutil.copy2(
            os.path.join(src_dir, 'mdtf_diag_banner.png'), self.MODEL_WK_DIR
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
            var._local_data = self.local_path(var)

        if self.data_freq is not None:
            for var in pod.iter_vars_and_alts():
                if var.date_freq != self.data_freq:
                    pod.skipped = PodRequirementFailure(pod,
                        """{} requests {} (= {}) at {} frequency, which isn't compatible
                        with case {} providing data at {} frequency only.""".format(
                        pod.name, var.name_in_model, var.name, var.date_freq,
                        self.case_name, self.data_freq
                    ))
                    break

    def local_path(self, dataset):
        """Returns the absolute path of the local copy of the file for dataset.

        This determines the local model data directory structure, which is
        `$MODEL_DATA_ROOT/<CASENAME>/<freq>/<CASENAME>.<var name>.<freq>.nc'`.
        Files not following this convention won't be found.
        """
        # pylint: disable=maybe-no-member
        freq = dataset.date_freq.format_local()
        return os.path.join(
            self.MODEL_DATA_DIR, freq,
            "{}.{}.{}.nc".format(
                self.case_name, dataset.name_in_model, freq)
        )

    @staticmethod
    def dataset_key(dataset):
        """Return immutable representation of DataSet. Two DataSets should have 
        the same key 
        """
        return dataset._freeze()

    def _build_data_dicts(self):
        self.data_keys = defaultdict(list)
        self.data_files = util.MultiMap()
        for pod in self.iter_pods():
            for var in pod.iter_vars_and_alts():
                key = self.dataset_key(var)
                self.data_keys[key].append(var)
                self.data_files[key].update(var._remote_data)
    
    # -------------------------------------

    def fetch_data(self, verbose=0):
        self._query_data()
        # populate vars with found files
        for data_key in self.data_keys:
            for var in self.data_keys[data_key]:
                var._remote_data.extend(list(self.data_files[data_key]))
        
        for pod in self.iter_pods():
            try:
                new_varlist = [var for var \
                    in self._iter_populated_varlist(pod.varlist, pod.name)]
            except DataQueryFailure as exc:
                print "Data query failed on pod {}; skipping.".format(pod.name)
                pod.skipped = exc
                new_varlist = []
            pod.varlist = new_varlist
        # revise DataManager's to-do list, now that we've marked some PODs as
        # being skipped due to data inavailability
        self._build_data_dicts()

        self.plan_data_fetch_hook()

        for file_ in self.remote_data_list():
            try:
                self.fetch_dataset(file_)
            except Exception as exc:
                # TODO: reraise as DataAccessError, retry fetch, disqualify PODs
                # that needed this data, log error.
                print exc
                continue

        # do translation/ transformations of data here
        self.process_fetched_data_hook()

    def _query_data(self):
        for data_key in self.data_keys:
            try:
                var = self.data_keys[data_key][0]
                print "Calling query_dataset on {} @ {}".format(
                    var.name_in_model, var.date_freq)
                files = self.query_dataset(var)
                self.data_files[data_key].update(files)
            except DataQueryFailure:
                continue

    def _iter_populated_varlist(self, var_iter, pod_name):
        """Generator function yielding either a variable, its alternates if the
        variable was not found in the data query, or DataQueryFailure if the
        variable request can't be satisfied with found data.
        """
        for var in var_iter:
            if var._remote_data:
                print "Found {} (= {}) @ {} for {}".format(
                    var.name_in_model, var.name, var.date_freq, pod_name)
                var.alternates = []
                yield var
            elif not var.alternates:
                raise DataQueryFailure(
                    var,
                    "Couldn't find {} (= {}) @ {} for {} & no other alternates".format(
                    var.name_in_model, var.name, var.date_freq, pod_name)
                )
            else:
                print "Couldn't find {} (= {}) @ {} for {}, trying alternates".format(
                    var.name_in_model, var.name, var.date_freq, pod_name)
                for alt_var in self._iter_populated_varlist(var.alternates, pod_name):
                    yield alt_var  # no 'yield from' in py2.7

    def remote_data_list(self):
        """Process list of requested data to make data fetching efficient.

        This is intended as a hook to be used by subclasses. Default behavior is
        to delete from the list duplicate datasets and datasets where a local
        copy of the data already exists and is current (as determined by 
        :meth:`~data_manager.DataManager.local_data_is_current`).
        
        Returns: collection of :class:`~util.DataSet`
            objects.
        """
        # flatten list of all _remote_datas and remove duplicates
        unique_files = set(f for f in chain.from_iterable(self.data_files.values()))
        # filter out any data we've previously fetched that's up to date
        unique_files = [f for f in unique_files if not self.local_data_is_current(f)]
        # fetch data in sorted order to make interpreting logs easier
        if hasattr(self, 'fetch_ordering_function'):
            sort_key = self.fetch_ordering_function
        if hasattr(unique_files[0], '_remote_data'):
            sort_key = attrgetter('_remote_data')
        else:
            sort_key = None
        unique_files.sort(key=sort_key)
        return unique_files
    
    def local_data_is_current(self, dataset):
        """Determine if local copy of data needs to be refreshed.

        This is intended as a hook to be used by subclasses. Default is to always
        return `False`, ie always fetch remote data.

        Returns: `True` if local copy of data exists and remote copy hasn't been
            updated.
        """
        return False

    def plan_data_fetch_hook(self):
        pass

    def process_fetched_data_hook(self):
        pass

    # -------------------------------------

    # following are specific details that must be implemented in child class 
    @abstractmethod
    def query_dataset(self, dataset):
        pass

    @abstractmethod
    def fetch_dataset(self, dataset):
        pass

    # -------------------------------------

    def tearDown(self, config):
        # TODO: handle OSErrors in all of these
        self._finalize_html()
        self._backup_config_file(config)
        self._make_tar_file()
        self._copy_to_output()
        paths = util.PathManager()
        paths.cleanup()

    def _finalize_html(self):
        # pylint: disable=maybe-no-member
        paths = util.PathManager()
        src = os.path.join(paths.CODE_ROOT, 'src', 'html', 'mdtf2.html')
        dest = os.path.join(self.MODEL_WK_DIR, 'index.html')
        dt = datetime.datetime.utcnow()
        template_dict = {
            'DATE_TIME': dt.strftime("%A, %d %B %Y %I:%M%p (UTC)")
        }
        util.append_html_template(src, dest, template_dict)

    def _backup_config_file(self, config, verbose=0):
        """Record settings in file variab_dir/config_save.yml for rerunning
        """
        # pylint: disable=maybe-no-member
        out_file = os.path.join(self.MODEL_WK_DIR, 'config_save.yml')
        if os.path.isfile(out_file):
            out_fileold = os.path.join(self.MODEL_WK_DIR, 'config_save.yml.old')
            if verbose > 1: 
                print "WARNING: moving existing namelist file to ", out_fileold
            shutil.move(out_file, out_fileold)
        util.write_yaml(config, out_file)

    def _make_tar_file(self):
        """Make tar file
        """
        # pylint: disable=maybe-no-member
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
        # pylint: disable=maybe-no-member
        paths = util.PathManager()
        if paths.OUTPUT_DIR != paths.WORKING_DIR:
            print "copy {} to {}".format(self.MODEL_WK_DIR, self.MODEL_OUT_DIR)
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

    @staticmethod
    def dataset_key(dataset):
        return (dataset.name_in_model, str(dataset.date_freq))

    def query_dataset(self, dataset):
        path = self.local_path(dataset)
        if os.path.isfile(path):
            return [path]
        else:
            raise DataQueryFailure(dataset, 'File not found at {}'.format(path))
    
    def local_data_is_current(self, dataset):
        return True 

    def fetch_dataset(self, dataset):
        pass

