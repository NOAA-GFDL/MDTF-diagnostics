from __future__ import print_function
import os
import sys
import glob
import copy
import shutil
import atexit
import signal
from collections import defaultdict, namedtuple
from itertools import chain
from operator import attrgetter
from abc import ABCMeta, abstractmethod
import datetime
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        from subprocess32 import CalledProcessError
    except ImportError:
        from subprocess import CalledProcessError
else:
    from subprocess import CalledProcessError
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
        if hasattr(self.dataset, 'name'):
            return 'Query failure for {}: {}.'.format(self.dataset.name, self.msg)
        else:
            return 'Query failure: {}.'.format(self.msg)

class DataAccessError(Exception):
    """Exception signaling a failure to obtain data from the remote location.
    """
    def __init__(self, dataset, msg=''):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        if hasattr(self.dataset, '_remote_data'):
            return 'Data access error for {}: {}.'.format(
                self.dataset._remote_data, self.msg)
        else:
            return 'Data access error: {}.'.format(self.msg)

class DataSet(util.Namespace):
    """Class to describe datasets.

    `https://stackoverflow.com/a/48806603`_ for implementation.
    """
    def __init__(self, *args, **kwargs):
        # pylint: disable=maybe-no-member
        if 'DateFreqMixin' not in kwargs:
            self.DateFreq = datelabel.DateFrequency
        else:
            self.DateFreq = kwargs['DateFreqMixin']
            del kwargs['DateFreqMixin']

        super(DataSet, self).__init__(*args, **kwargs)
        for key in ['name', 'units', 'date_range', 'date_freq', '_local_data']:
            if key not in self:
                self[key] = None
        
        for key in ['_remote_data', 'alternates']:
            if key not in self:
                self[key] = []

        for key in ['axes']:
            if key not in self:
                self[key] = dict()
                
        if ('var_name' in self) and (self.name is None):
            self.name = self.var_name
            del self.var_name
        if ('freq' in self) and (self.date_freq is None):
            self.date_freq = self.DateFreq(self.freq)
            del self.freq

    def copy(self, new_name=None):
        temp = super(DataSet, self).copy()
        if new_name is not None:
            temp.name = new_name
        return temp  

    @classmethod
    def from_pod_varlist(cls, pod_convention, var, dm_args):
        translate = util.VariableTranslator()
        var_copy = var.copy()
        var_copy.update(dm_args)
        ds = cls(**var_copy)
        ds.original_name = ds.name
        ds.CF_name = translate.toCF(pod_convention, ds.name)
        alt_ds_list = []
        for alt_var in ds.alternates:
            alt_ds = ds.copy(new_name=alt_var)
            alt_ds.original_name = ds.original_name
            alt_ds.CF_name = translate.toCF(pod_convention, alt_ds.name)
            alt_ds.alternates = []
            alt_ds_list.append(alt_ds)
        ds.alternates = alt_ds_list
        return ds

    def _freeze(self):
        """Return immutable representation of (current) attributes.

        Exclude attributes starting with '_' from the comparison, in case 
        we want DataSets with different timestamps, temporary directories, etc.
        to compare as equal.
        """
        d = self.toDict()
        keys_to_hash = sorted(k for k in d if not k.startswith('_'))
        d2 = {k: repr(d[k]) for k in keys_to_hash}
        FrozenDataSet = namedtuple('FrozenDataSet', keys_to_hash)
        return FrozenDataSet(**d2)

class DataManager(object):
    # analogue of TestFixture in xUnit
    __metaclass__ = ABCMeta

    def __init__(self, case_dict, config={}, DateFreqMixin=None):
        # pylint: disable=maybe-no-member
        self.case_name = case_dict['CASENAME']
        self.model_name = case_dict['model']
        self.firstyr = datelabel.Date(case_dict['FIRSTYR'])
        self.lastyr = datelabel.Date(case_dict['LASTYR'])
        self.date_range = datelabel.DateRange(self.firstyr, self.lastyr)
        if not DateFreqMixin:
            self.DateFreq = datelabel.DateFrequency
        else:
            self.DateFreq = DateFreqMixin

        if 'envvars' in config:
            self.envvars = config['envvars'].copy() # gets appended to
        else:
            self.envvars = {}

        if 'variable_convention' in case_dict:
            self.convention = case_dict['variable_convention']
        else:
            self.convention = 'CF' # default to assuming CF-compliance
        if 'data_freq' in case_dict:
            self.data_freq = self.DateFreq(case_dict['data_freq'])
        else:
            self.data_freq = None
        self.pod_list = case_dict['pod_list'] 
        self.pods = []

        paths = util.PathManager()
        self.__dict__.update(paths.modelPaths(self))
        self.TEMP_HTML = os.path.join(self.MODEL_WK_DIR, 'pod_output_temp.html')

        # dynamic inheritance to add netcdf manipulation functions
        # source: https://stackoverflow.com/a/8545134
        mixin = util.get_from_config('netcdf_helper', config, default='NcoNetcdfHelper')
        mixin = getattr(netcdf_helper, 'NcoNetcdfHelper')
        self.__class__ = type(self.__class__.__name__, (self.__class__, mixin), {})
        try:
            self.nc_check_environ() # make sure we have dependencies
        except Exception:
            raise

        self.dry_run = util.get_from_config('dry_run', config, default=False)
        self.file_transfer_timeout = util.get_from_config(
            'file_transfer_timeout', config, default=0) # 0 = syntax for no timeout

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

    def setUp(self, verbose=0):
        # pylint: disable=maybe-no-member
        util.check_required_dirs(
            already_exist =[], 
            create_if_nec = [self.MODEL_WK_DIR, self.MODEL_DATA_DIR], 
            verbose=verbose)
        self.envvars.update({
            "DATADIR": self.MODEL_DATA_DIR,
            "variab_dir": self.MODEL_WK_DIR,
            "CASENAME": self.case_name,
            "model": self.model_name,
            "FIRSTYR": self.firstyr.format(precision=1), 
            "LASTYR": self.lastyr.format(precision=1)
        })
        # set env vars for unit conversion factors (TODO: honest unit conversion)
        translate = util.VariableTranslator()
        if self.convention not in translate.units:
            raise AssertionError(("Variable name translation doesn't recognize "
                "{}.").format(self.convention))
        temp = translate.variables[self.convention].to_dict()
        for key, val in temp.iteritems():
            util.setenv(key, val, self.envvars, verbose=verbose)
        temp = translate.units[self.convention].to_dict()
        for key, val in temp.iteritems():
            util.setenv(key, val, self.envvars, verbose=verbose)

        for pod in self.iter_pods():
            self._setup_pod(pod)
        self._build_data_dicts()

    def _setup_pod(self, pod):
        paths = util.PathManager()
        translate = util.VariableTranslator()

        # transfer DataManager-specific settings
        pod.__dict__.update(paths.modelPaths(self))
        pod.__dict__.update(paths.podPaths(pod))
        pod.TEMP_HTML = self.TEMP_HTML
        pod.pod_env_vars.update(self.envvars)
        pod.dry_run = self.dry_run

        # express varlist as DataSet objects
        ds_list = []
        for var in pod.varlist:
            ds_list.append(DataSet.from_pod_varlist(
                pod.convention, var, {'DateFreqMixin': self.DateFreq}))
        pod.varlist = ds_list

        for var in pod.iter_vars_and_alts():
            var.name_in_model = translate.fromCF(self.convention, var.CF_name)
            var.date_range = self.date_range
            var._local_data = self.local_path(self.dataset_key(var))
            var.axes = copy.deepcopy(translate.axes[self.convention])

        if self.data_freq is not None:
            for var in pod.iter_vars_and_alts():
                if var.date_freq != self.data_freq:
                    pod.skipped = PodRequirementFailure(
                        pod,
                        ("{0} requests {1} (= {2}) at {3} frequency, which isn't "
                        "compatible with case {4} providing data at {5} frequency "
                        "only.").format(
                            pod.name, var.name_in_model, var.name, 
                            var.date_freq, self.case_name, self.data_freq
                    ))
                    break

    @staticmethod
    def dataset_key(dataset):
        """Return immutable representation of DataSet. Two DataSets should have 
        the same key 
        """
        return dataset._freeze()

    def local_path(self, data_key):
        """Returns the absolute path of the local copy of the file for dataset.

        This determines the local model data directory structure, which is
        `$MODEL_DATA_ROOT/<CASENAME>/<freq>/<CASENAME>.<var name>.<freq>.nc'`.
        Files not following this convention won't be found.
        """
        # pylint: disable=maybe-no-member
        assert 'name_in_model' in data_key._fields
        assert 'date_freq' in data_key._fields
        # values in key are repr strings by default, so need to instantiate the
        # datelabel object to use its formatting method
        try:
            # value in key is from __str__
            freq = self.DateFreq(data_key.date_freq)
        except ValueError:
            # value in key is from __repr__
            freq = eval('datelabel.'+data_key.date_freq)
        freq = freq.format_local()
        return os.path.join(
            self.MODEL_DATA_DIR, freq,
            "{}.{}.{}.nc".format(
                self.case_name, data_key.name_in_model, freq)
        )

    def _build_data_dicts(self):
        self.data_keys = defaultdict(list)
        self.data_pods = util.MultiMap()
        self.data_files = util.MultiMap()
        for pod in self.iter_pods():
            for var in pod.iter_vars_and_alts():
                key = self.dataset_key(var)
                self.data_pods[key].update(set([pod]))
                self.data_keys[key].append(var)
                self.data_files[key].update(var._remote_data)

    # -------------------------------------

    def fetch_data(self):
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
                print("Data query failed on pod {}; skipping.".format(pod.name))
                pod.skipped = exc
                new_varlist = []
            pod.varlist = new_varlist
            pod.alternates = []
        # revise DataManager's to-do list, now that we've marked some PODs as
        # being skipped due to data inavailability
        self._build_data_dicts()

        self.plan_data_fetch_hook()

        for file_ in self.remote_data_list():
            try:
                self.fetch_dataset(file_)
            except CalledProcessError as caught_exc:
                exc = DataAccessError(
                    file_,
                    """Running external command {} when fetching {} @ {} 
                    returned error: {} (status {}). Did not retry.
                    """.format(
                        caught_exc.cmd, file_.name_in_model, file_.date_freq,
                        caught_exc.output, caught_exc.returncode
                    )
                )
                self._fetch_exception_handler(exc)
                continue
            except Exception as caught_exc:
                exc = DataAccessError(
                    file_,
                    """Caught {} exception ({}) when fetching {} @ {}.
                    Did not retry.
                    """.format(
                        type(caught_exc).__name__, caught_exc, 
                        file_.name_in_model, file_.date_freq
                    )
                )
                self._fetch_exception_handler(exc)
                continue

        # do translation/ transformations of data here
        self.process_fetched_data_hook()

    def _fetch_exception_handler(self, exc):
        print(exc)
        keys_from_file = self.data_files.inverse()
        for key in keys_from_file[exc.dataset]:
            for pod in self.data_pods[key]:
                print(("\tSkipping pod {} due to data fetch error."
                    "").format(pod.name))
                pod.skipped = exc

    def _query_data(self):
        for data_key in self.data_keys:
            try:
                var = self.data_keys[data_key][0]
                print("Calling query_dataset on {} @ {}".format(
                    var.name_in_model, var.date_freq))
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
                print("Found {} (= {}) @ {} for {}".format(
                    var.name_in_model, var.name, var.date_freq, pod_name
                ))
                yield var
            elif not var.alternates:
                raise DataQueryFailure(
                    var,
                    ("Couldn't find {} (= {}) @ {} for {} & no other "
                        "alternates").format(
                        var.name_in_model, var.name, var.date_freq, pod_name
                ))
            else:
                print(("Couldn't find {} (= {}) @ {} for {}, trying "
                    "alternates").format(
                        var.name_in_model, var.name, var.date_freq, pod_name
                ))
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
        if unique_files:
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
        self._make_html()
        self._backup_config_file(config)
        self._make_tar_file()
        self._copy_to_output()
        paths = util.PathManager()
        paths.cleanup()

    def _make_html(self, cleanup=True):
        # pylint: disable=maybe-no-member
        paths = util.PathManager()
        src_dir = os.path.join(paths.CODE_ROOT, 'src', 'html')
        dest = os.path.join(self.MODEL_WK_DIR, 'index.html')
        if os.path.isfile(dest):
            print("WARNING: index.html exists, deleting.")
            os.remove(dest)

        template_dict = self.envvars.copy()
        template_dict['DATE_TIME'] = \
            datetime.datetime.utcnow().strftime("%A, %d %B %Y %I:%M%p (UTC)")
        util.append_html_template(
            os.path.join(src_dir, 'mdtf_header.html'), dest, template_dict
        )
        util.append_html_template(self.TEMP_HTML, dest, {})
        util.append_html_template(
            os.path.join(src_dir, 'mdtf_footer.html'), dest, template_dict
        )
        if cleanup:
            os.remove(self.TEMP_HTML)

        shutil.copy2(
            os.path.join(src_dir, 'mdtf_diag_banner.png'), self.MODEL_WK_DIR
        )

    def _backup_config_file(self, config, verbose=0):
        """Record settings in file variab_dir/config_save.json for rerunning
        """
        # pylint: disable=maybe-no-member
        out_file = os.path.join(self.MODEL_WK_DIR, 'config_save.json')
        if os.path.isfile(out_file):
            out_fileold = os.path.join(self.MODEL_WK_DIR, 'config_save.json.old')
            if verbose > 1: 
                print("WARNING: moving existing namelist file to ", out_fileold)
            shutil.move(out_file, out_fileold)
        util.write_json(config, out_file)

    def _make_tar_file(self):
        """Make tar file
        """
        # pylint: disable=maybe-no-member
        if os.environ["make_variab_tar"] == "0":
            print("Not making tar file because make_variab_tar = 0")
            return
        print("Making tar file because make_variab_tar = {}".format(
            os.environ["make_variab_tar"]
        ))
        if os.path.isfile(self.MODEL_WK_DIR+'.tar'):
            print("Moving existing {0}.tar to {0}.tar.old".format(self.MODEL_WK_DIR))
            shutil.move(self.MODEL_WK_DIR+'.tar', self.MODEL_WK_DIR+'.tar.old')

        print("Creating {}.tar".format(self.MODEL_WK_DIR))
        # not running in shell, so don't need to quote globs
        tar_flags = ["--exclude=*.{}".format(s) for s in ['netCDF','nc','ps','PS']]
        util.run_command(['tar', '-cf', '{}.tar'.format(self.MODEL_WK_DIR),
            self.MODEL_WK_DIR ] + tar_flags,
            dry_run = self.dry_run
        )

    def _copy_to_output(self):
        # pylint: disable=maybe-no-member
        paths = util.PathManager()
        if paths.OUTPUT_DIR != paths.WORKING_DIR:
            print("copy {} to {}".format(self.MODEL_WK_DIR, self.MODEL_OUT_DIR))
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

    DataKey = namedtuple('DataKey', ['name_in_model', 'date_freq'])  
    def dataset_key(self, dataset):
        return self.DataKey(
            name_in_model=dataset.name_in_model, 
            date_freq=str(dataset.date_freq)
        )

    def query_dataset(self, dataset):
        path = self.local_path(self.dataset_key(dataset))
        if os.path.isfile(path):
            return [path]
        else:
            raise DataQueryFailure(dataset, 'File not found at {}'.format(path))
    
    def local_data_is_current(self, dataset):
        return True 

    def fetch_dataset(self, dataset):
        pass

