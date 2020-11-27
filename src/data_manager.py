from __future__ import absolute_import, division, print_function, unicode_literals
import os
from src import six
import copy
import shutil
import collections
from itertools import chain
from operator import attrgetter
from abc import ABCMeta, abstractmethod
import datetime
if os.name == 'posix' and six.PY2:
    try:
        from subprocess32 import CalledProcessError
    except ImportError:
        from subprocess import CalledProcessError
else:
    from subprocess import CalledProcessError
from src import util, util_mdtf, datelabel, preprocessor, data_modeln
from src.diagnostic import PodRequirementFailure


@six.python_2_unicode_compatible
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

@six.python_2_unicode_compatible
class DataAccessError(Exception):
    """Exception signaling a failure to obtain data from the remote location.
    """
    def __init__(self, dataset, msg=''):
        self.dataset = dataset
        self.msg = msg

    def __str__(self):
        if hasattr(self.dataset, 'remote_path'):
            return 'Data access error for {}: {}.'.format(
                self.dataset.remote_path, self.msg)
        else:
            return 'Data access error: {}.'.format(self.msg)

class DataManager(six.with_metaclass(ABCMeta)):
    # analogue of TestFixture in xUnit

    def __init__(self, case_dict, DateFreqMixin=None):
        self.case_name = case_dict['CASENAME']
        self.model_name = case_dict['model']
        self.firstyr = datelabel.Date(case_dict['FIRSTYR'])
        self.lastyr = datelabel.Date(case_dict['LASTYR'])
        self.date_range = datelabel.DateRange(self.firstyr, self.lastyr)
        self.convention = case_dict.get('convention', 'CF')
        if 'data_freq' in case_dict:
            self.data_freq = self.DateFreq(case_dict['data_freq'])
        else:
            self.data_freq = None
        self.pod_list = case_dict['pod_list'] 
        self.pods = []

        config = util_mdtf.ConfigManager()
        self.envvars = config.global_envvars.copy() # gets appended to
        # assign explicitly else linter complains
        self.dry_run = config.config.dry_run
        self.file_transfer_timeout = config.config.file_transfer_timeout
        self.make_variab_tar = config.config.make_variab_tar
        self.keep_temp = config.config.keep_temp
        self.overwrite = config.config.overwrite
        self.file_overwrite = self.overwrite # overwrite config and .tar

        d = config.paths.model_paths(case_dict, overwrite=self.overwrite)
        self.code_root = config.paths.CODE_ROOT
        self.MODEL_DATA_DIR = d.MODEL_DATA_DIR
        self.MODEL_WK_DIR = d.MODEL_WK_DIR
        self.MODEL_OUT_DIR = d.MODEL_OUT_DIR
        self.TEMP_HTML = os.path.join(self.MODEL_WK_DIR, 'pod_output_temp.html')

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
        util_mdtf.check_required_dirs(
            already_exist =[], 
            create_if_nec = [self.MODEL_WK_DIR, self.MODEL_DATA_DIR], 
            verbose=verbose)
        self.envvars.update({
            "CASENAME": self.case_name,
            "model": self.model_name,
            "FIRSTYR": self.firstyr.format(precision=1), 
            "LASTYR": self.lastyr.format(precision=1)
        })
        # set env vars for unit conversion factors (TODO: honest unit conversion)
        translate = util_mdtf.VariableTranslator()
        if self.convention not in translate.units:
            raise AssertionError(("Variable name translation doesn't recognize "
                "{}.").format(self.convention))
        temp = translate.variables[self.convention].to_dict()
        for key, val in iter(temp.items()):
            util_mdtf.setenv(key, val, self.envvars, verbose=verbose)
        temp = translate.units[self.convention].to_dict()
        for key, val in iter(temp.items()):
            util_mdtf.setenv(key, val, self.envvars, verbose=verbose)

        for pod in self.iter_pods():
            self._setup_pod(pod)
        self.build_data_dicts()

    def _setup_pod(self, pod):
        config = util_mdtf.ConfigManager()
        translate = util_mdtf.VariableTranslator()

        # transfer DataManager-specific settings
        pod.__dict__.update(config.paths.pod_paths(pod, self))
        pod.TEMP_HTML = self.TEMP_HTML
        pod.pod_env_vars.update(self.envvars)
        pod.dry_run = self.dry_run

        # express varlist as VarlistEntry objects
        ds_list = []
        for var in pod.varlist:
            ds_list.append(VarlistEntry.from_pod_varlist(
                pod.convention, var, {'DateFreqMixin': self.DateFreq}))
        pod.varlist = ds_list

        for var in pod.iter_vars_and_alts():
            var.name_in_model = translate.fromCF(self.convention, var.CF_name)
            if var.date_freq.is_static:
                # placeholder value for time-independent data
                var.date_range = datelabel.FXDateRange
            else:
                var.date_range = self.date_range
            var.dest_path = self.dest_path(pod.POD_WK_DIR, self.dataset_key(var))
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
        """Return immutable representation of a :class:`DataSetBase` object. 
        Two DataSets should have the same key 
        """
        return dataset._freeze()

    def dest_path(self, pod_wk_dir, data_key):
        """Returns the absolute path of the POD's preprocessed, local copy of 
        the file containing the requested dataset. Files not following this 
        convention won't be found by the POD.
        """
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
            pod_wk_dir, freq,
            "{}.{}.{}.nc".format(self.case_name, data_key.name_in_model, freq)
        )

    def build_data_dicts(self):
        """Initialize or update internal bookkeeping: which PODs use which 
        variables, and which variables are contained in which files. Current 
        implementation is needlessly opaque and should be replaced with sqlite
        queries.

        - A ``data_key`` is an object identifying a dataset for a single variable.
        - ``data_keys`` maps a data_key to a list of :class:`VarlistEntry` objects 
            representing specific versions of that variable.
        - ``data_pods`` is a reversible map (:class:`~util.MultiMap`) between a
            data_key and the set of PODs (represented as 
            :class:`~diagnostic.Diagnostic` objects) that use that variable.
        - ``data_files`` is a reversible map (:class:`~util.MultiMap`) between a
            data_key and the set of files (represented as :class:`SingleFileDataSet` 
            objects) that contain that variable's data.
        """
        self.data_keys = collections.defaultdict(list)
        self.data_pods = util.MultiMap()
        self.data_files = util.MultiMap()
        for pod in self.iter_pods():
            for var in pod.iter_vars_and_alts():
                key = self.dataset_key(var)
                self.data_pods[key].update(set([pod]))
                self.data_keys[key].append(var)
                self.data_files[key].update(var.remote_data)

    # DATA QUERY -------------------------------------

    def iter_populated_varlist(self, var_iter, pod_name):
        """Generator function yielding either a variable, its alternates if the
        variable was not found in the data query, or DataQueryFailure if the
        variable request can't be satisfied with found data.
        """
        for var in var_iter:
            if var.remote_data:
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
                for alt_var in self.iter_populated_varlist(var.alternates, pod_name):
                    yield alt_var  # no 'yield from' in py2.7

    # specific details that must be implemented in child class 
    @abstractmethod
    def query_dataset(self, dataset):
        pass

    def query_data(self):
        for data_key in self.data_keys:
            try:
                var = self.data_keys[data_key][0]
                print("Calling query_dataset on {} @ {}".format(
                    var.name_in_model, var.date_freq))
                self.data_files[data_key].update([self.query_dataset(var)])
            except DataQueryFailure:
                continue

        # populate vars with found files
        for data_key in self.data_keys:
            for var in self.data_keys[data_key]:
                for f in self.data_files[data_key]:
                    var.remote_data.append(f)
        
        for pod in self.iter_pods():
            try:
                new_varlist = [var for var \
                    in self.iter_populated_varlist(pod.varlist, pod.name)]
            except DataQueryFailure as exc:
                print("Data query failed on pod {}; skipping.".format(pod.name))
                pod.skipped = exc
                new_varlist = []
            for var in new_varlist:
                var.alternates = []
            pod.varlist = new_varlist
        # revise DataManager's to-do list, now that we've marked some PODs as
        # being skipped due to data inavailability
        self.build_data_dicts()

    # FETCH REMOTE DATA -------------------------------------

    def plan_data_fetch_hook(self):
        pass

    def remote_data_list(self):
        """Process list of requested data to make data fetching efficient.

        This is intended as a hook to be used by subclasses. Default behavior is
        to delete from the list duplicate datasets and datasets where a local
        copy of the data already exists and is current (as determined by 
        :meth:`~data_manager.DataManager.local_data_is_current`).
        
        Returns: collection of :class:`SingleFileDataSet` objects.
        """
        # flatten list of all remote_data and remove duplicates
        unique_files = set(f \
            for f in chain.from_iterable(iter(self.data_files.values())))
        # filter out any data we've previously fetched that's up to date
        unique_files = [f \
            for f in unique_files if not self.local_data_is_current(f)]
        # fetch data in sorted order to make interpreting logs easier
        if unique_files:
            if self._fetch_order_function is not None:
                sort_key = self._fetch_order_function
            elif hasattr(unique_files[0], 'remote_path'):
                sort_key = attrgetter('remote_path')
            else:
                sort_key = None
            unique_files.sort(key=sort_key)
        return unique_files
    
    _fetch_order_function=None

    def local_data_is_current(self, dataset):
        """Determine if local copy of data needs to be refreshed.

        This is intended as a hook to be used by subclasses. Default is to always
        return `False`, ie always fetch remote data.

        Returns: `True` if local copy of data exists and remote copy hasn't been
            updated.
        """
        return False

    # specific details that must be implemented in child class 
    @abstractmethod
    def fetch_dataset(self, dataset):
        pass

    def fetch_data(self):
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

    def _fetch_exception_handler(self, exc):
        print(exc)
        keys_from_file = self.data_files.inverse()
        for key in keys_from_file[exc.dataset]:
            for pod in self.data_pods[key]:
                print(("\tSkipping pod {} due to data fetch error."
                    "").format(pod.name))
                pod.skipped = exc

    # -------------------------------------

    def preprocess_data(self):
        for var in self.iter_vars():
            pp = preprocessor.MDTFPreprocessor(self, var)
            pp.preprocess()

    # HTML & PLOT OUTPUT -------------------------------------

    def tearDown(self):
        # TODO: handle OSErrors in all of these
        config = util_mdtf.ConfigManager()
        self._make_html()
        _ = self._backup_config_file(config)
        if self.make_variab_tar:
            _ = self._make_tar_file(config.paths.OUTPUT_DIR)
        self._copy_to_output()

    def _make_html(self, cleanup=True):
        src_dir = os.path.join(self.code_root, 'src', 'html')
        dest = os.path.join(self.MODEL_WK_DIR, 'index.html')
        if os.path.isfile(dest):
            print("WARNING: index.html exists, deleting.")
            os.remove(dest)

        template_dict = self.envvars.copy()
        template_dict['DATE_TIME'] = \
            datetime.datetime.utcnow().strftime("%A, %d %B %Y %I:%M%p (UTC)")
        util_mdtf.append_html_template(
            os.path.join(src_dir, 'mdtf_header.html'), dest, template_dict
        )
        util_mdtf.append_html_template(self.TEMP_HTML, dest, {})
        util_mdtf.append_html_template(
            os.path.join(src_dir, 'mdtf_footer.html'), dest, template_dict
        )
        if cleanup:
            os.remove(self.TEMP_HTML)

        shutil.copy2(
            os.path.join(src_dir, 'mdtf_diag_banner.png'), self.MODEL_WK_DIR
        )

    def _backup_config_file(self, config):
        """Record settings in file variab_dir/config_save.json for rerunning
        """
        out_file = os.path.join(self.MODEL_WK_DIR, 'config_save.json')
        if not self.file_overwrite:
            out_file, _ = util_mdtf.bump_version(out_file)
        elif os.path.exists(out_file):
            print('Overwriting {}.'.format(out_file))
        util.write_json(config.config.toDict(), out_file)
        return out_file

    def _make_tar_file(self, tar_dest_dir):
        """Make tar file of web/bitmap output.
        """
        out_file = os.path.join(tar_dest_dir, self.MODEL_WK_DIR+'.tar')
        if not self.file_overwrite:
            out_file, _ = util_mdtf.bump_version(out_file)
            print("Creating {}.".format(out_file))
        elif os.path.exists(out_file):
            print('Overwriting {}.'.format(out_file))
        tar_flags = ["--exclude=.{}".format(s) for s in ['netCDF','nc','ps','PS','eps']]
        tar_flags = ' '.join(tar_flags)
        util.run_shell_command(
            'tar {} -czf {} -C {} .'.format(tar_flags, out_file, self.MODEL_WK_DIR),
            dry_run = self.dry_run
        )
        return out_file

    def _copy_to_output(self):
        if self.MODEL_WK_DIR == self.MODEL_OUT_DIR:
            return # no copying needed
        print("copy {} to {}".format(self.MODEL_WK_DIR, self.MODEL_OUT_DIR))
        try:
            if os.path.exists(self.MODEL_OUT_DIR):
                if not self.overwrite:
                    print('Error: {} exists, overwriting anyway.'.format(
                        self.MODEL_OUT_DIR))
                shutil.rmtree(self.MODEL_OUT_DIR)
        except Exception:
            raise
        shutil.move(self.MODEL_WK_DIR, self.MODEL_OUT_DIR)


class LocalfileDataManager(DataManager):
    """:class:`DataManager` for working with input model data files that are 
    already present in ``MODEL_DATA_DIR`` (on a local filesystem), for example
    the PODs' sample model data.
    """
    DataKey = collections.namedtuple('DataKey', ['name_in_model', 'date_freq'])  
    def dataset_key(self, dataset):
        return self.DataKey(
            name_in_model=dataset.name_in_model, 
            date_freq=str(dataset.date_freq)
        )

    def remote_path(self, data_key):
        """Returns the absolute path of the local copy of the file for dataset.

        This determines the local sample model data directory structure, which 
        is
        ``$MODEL_DATA_ROOT/<CASENAME>/<freq>/<CASENAME>.<var name>.<freq>.nc'``.
        Sample model data not following this convention won't be found.
        """
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
            "{}.{}.{}.nc".format(self.case_name, data_key.name_in_model, freq)
        )

    def query_dataset(self, dataset):
        d_key = self.dataset_key(dataset)
        path = self.remote_path(d_key)
        tmpdirs = util_mdtf.TempDirManager()
        tmpdir = tmpdirs.make_tempdir(hash_obj = d_key)
        if os.path.isfile(path):
            out = SingleFileDataSet()
            out.name = dataset.name
            out.name_in_model = dataset.name_in_model
            out.date_range = dataset.date_freq
            out.axes = dataset.axes
            out.remote_path = path
            out.local_path = os.path.join(tmpdir, os.path.basename(path))
            return out
        else:
            raise DataQueryFailure(dataset, 'File not found at {}'.format(path))
    
    def local_data_is_current(self, dataset):
        return True 

    def fetch_dataset(self, file_ds):
        shutil.copy2(file_ds.remote_path, file_ds.local_path)
