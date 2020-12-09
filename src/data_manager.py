import os
import abc
import collections
import copy
import dataclasses
import datetime
import functools
from itertools import chain
from operator import attrgetter
import shutil
import signal
from subprocess import CalledProcessError
import typing
from src import util, configs, datelabel, preprocessor, data_model, diagnostic

import logging
_log = logging.getLogger(__name__)

@util.mdtf_dataclass(frozen=True)
class DefaultDataKey(object):
    """Minimal data_key that captures the relevant information for the data 
    PODs require so far.
    """
    case_name: str = ""
    date_range: datelabel.DateRange = None
    name_in_model: str = ""
    frequency: datelabel.DateFrequency = None
    level: int = None

    def __str__(self):
        s = f"<{self.name_in_model}"
        attrs_ = []
        if self.frequency and not self.frequency.is_static:
            attrs_.append(f'{self.frequency}')
        if self.level:
            attrs_.append(f'{self.level}mb')
        if attrs_:
            return s + ' @ ' + ', '.join(attrs_) + '>'
        else:
            return s + '>'

    @property
    def is_static(self):
        return (not self.frequency) or self.frequency.is_static

    @classmethod
    def from_dataset(cls, dataset, data_mgr):
        if isinstance(dataset, cls):
            return util.coerce_to_dataclass(dataset, cls)
        assert isinstance(dataset, diagnostic.VarlistEntry)
        if dataset.is_static:
            dt_range = datelabel.FXDateRange
            freq = datelabel.FXDateFrequency
        else:
            dt_range = dataset.T.range
            freq = dataset.T.frequency
        return cls(
            case_name = data_mgr.case_name,
            date_range = dt_range,
            name_in_model = dataset.name_in_model, 
            frequency = freq
        )

@util.mdtf_dataclass(frozen=True)
class _RemoteFileDatasetBase(object):
    """Base class for describing data contained in a single file.
    """
    remote_path: str = ""
    local_path: str = ""

def remote_file_dataset_factory(class_name, *key_classes):
    """Factory returning a dataclass class that wraps whatever fields are used
    in key_classes with the additional attributes in _RemoteFileDatasetBase.
    """
    key_classes = util.to_iter(key_classes, list)
    key_classes.append(_RemoteFileDatasetBase)
    return util.dataclass_factory(util.mdtf_dataclass, class_name, *key_classes, 
        frozen=True)

@util.mdtf_dataclass(frozen=True)
class DataManagerAttributesBase():
    """Attributes that any data source must specify.
    """
    FIRSTYR: dataclasses.InitVar = util.MANDATORY
    LASTYR: dataclasses.InitVar = util.MANDATORY
    date_range: datelabel.DateRange = dataclasses.field(init=False)

    def __post_init__(self, FIRSTYR, LASTYR):
        self.date_range = datelabel.DateRange(FIRSTYR, LASTYR)

class DataManager(abc.ABC):
    """Base class for handling the data needs of PODs. Executes query for 
    requested model data against the remote data source, fetches the required 
    data locally, preprocesses it, and performs cleanup/formatting of the POD's 
    output.
    """
    _AttributesClass = DataManagerAttributesBase

    def __init__(self, case_dict, pod_dict, PreprocessorClass):
        self.case_name = case_dict['CASENAME']
        self.convention = case_dict.get('convention', 'CF')
        self.attrs = util.coerce_to_dataclass(case_dict, self._AttributesClass)
        self.pods = pod_dict
        self._PreprocessorClass = PreprocessorClass

        config = configs.ConfigManager()
        self.env_vars = config.global_env_vars.copy()
        self.env_vars.update({
            k: case_dict[k] for k in ("CASENAME", "FIRSTYR", "LASTYR")
        })
        # assign explicitly else linter complains
        self.dry_run = config.dry_run
        self.file_transfer_timeout = config.file_transfer_timeout
        self.make_variab_tar = config.make_variab_tar
        self.keep_temp = config.keep_temp
        self.overwrite = config.overwrite
        self.file_overwrite = self.overwrite # overwrite config and .tar

        paths = configs.PathManager()
        d = paths.model_paths(case_dict, overwrite=self.overwrite)
        self.code_root = paths.CODE_ROOT
        self.MODEL_DATA_DIR = d.MODEL_DATA_DIR
        self.MODEL_WK_DIR = d.MODEL_WK_DIR
        self.MODEL_OUT_DIR = d.MODEL_OUT_DIR
        self.TEMP_HTML = os.path.join(self.MODEL_WK_DIR, 'pod_output_temp.html')

        self.data_keys = collections.defaultdict(list)
        self.data_pods = util.MultiMap()
        self.queried_keys = set([])
        self.fetched_keys = set([])
        self.data_files = util.MultiMap()

    def iter_pods(self, all_pods=False):
        """Generator iterating over all pods which haven't been
        skipped due to requirement errors.
        """
        for p in self.pods.values():
            if all_pods or p.active:
                yield p

    # -------------------------------------

    def setup(self):
        util.check_dirs(self.MODEL_WK_DIR, self.MODEL_DATA_DIR, create=True)

        translate = configs.VariableTranslator()
        # set env vars for unit conversion factors (TODO: honest unit conversion)
        if self.convention not in translate.units:
            raise AssertionError(("Variable name translation doesn't recognize "
                f"{self.convention}."))
        temp = translate.units[self.convention].to_dict()
        self.env_vars.update(temp)
        # shouldn't need to do this for *all* var names the mdoel defines, but 
        # think a POD was testing for env var for a variable it didn't request
        # TODO: fix this
        temp = translate.variables[self.convention].to_dict()
        self.env_vars.update(temp)

        for pod in self.iter_pods(all_pods=True):
            try:
                self.setup_pod(pod)
            except Exception as exc:
                raise
                try:
                    raise util.PodConfigError(pod, 
                        "Caught exception in DataManager setup.") from exc
                except Exception as chained_exc:
                    pod.exceptions.log(chained_exc)    
                continue

        print('####################')
        for pod in self.iter_pods(all_pods=True):
            for v in pod.iter_vars(all_vars=True):
                v.print_debug()
        print('####################')

    def setup_pod(self, pod):
        paths = configs.PathManager()
        paths = paths.pod_paths(pod, self)
        for k,v in paths.items():
            setattr(pod, k, v)
        pod.pod_env_vars.update(self.env_vars)

        for v in pod.iter_vars(all_vars=True):
            try:
                self.setup_var(pod, v)
            except Exception as exc:
                try:
                    raise util.PodConfigError(pod, 
                        f"Caught exception when configuring {v.name}") from exc
                except Exception as chained_exc:
                    pod.exceptions.log(chained_exc)  
                continue
        pod.preprocessor = self._PreprocessorClass(self, pod)
        pod.preprocessor.edit_request(self, pod)

    def setup_var(self, pod, v):
        """Update VarlistEntry fields with information that only becomes 
        available after DataManager and Diagnostic have been configured (ie, 
        only known at runtime, not from settings.jsonc.)
        """
        translate = configs.VariableTranslator()
        v.change_coord(
            'T',
            new_class = {
                'self': diagnostic.VarlistTimeCoordinate,
                'range': datelabel.DateRange,
                'frequency': datelabel.DateFrequency
            },
            range=self.attrs.date_range
        )
        v.dest_path = self.variable_dest_path(pod, v)
        try:
            v.name_in_model = translate.from_CF(self.convention, v.standard_name)
        except KeyError:
            err_str = (f"CF name '{v.standard_name}' for varlist entry "
                f"{v.name} in POD {pod.name} not recognized by naming "
                f"convention '{self.convention}'.")
            _log.exception(err_str)
            v.exception = util.PodConfigError(pod, err_str)
            v.active = False
            raise v.exception

    def variable_dest_path(self, pod, var):
        """Returns the absolute path of the POD's preprocessed, local copy of 
        the file containing the requested dataset. Files not following this 
        convention won't be found by the POD.
        """
        if var.is_static:
            f_name = f"{self.case_name}.{var.name}.nc"
            return os.path.join(pod.POD_WK_DIR, f_name)
        else:
            freq = var.T.frequency.format_local()
            f_name = f"{self.case_name}.{var.name}.{freq}.nc"
            return os.path.join(pod.POD_WK_DIR, freq, f_name)

    @staticmethod
    def dataset_key(dataset):
        """Return immutable representation of a :class:`DataSetBase` object. 
        Two DataSets should have the same key if they can be retrieved from the 
        remote data source with a single query/fetch operation.
        """
        return dataset._freeze()

    def build_data_dicts(self):
        """Initialize or update internal bookkeeping: which PODs use which 
        variables, and which variables are contained in which files. Current 
        implementation is needlessly opaque and should be replaced with sqlite
        queries.

        - A ``data_key`` is an object identifying a dataset for a single 
            variable, in the sense that it can be retrieved from the remote data
            source with a single query/fetch operation.
        - ``data_keys`` maps a data_key to a list of 
            :class:`~diagnostic.VarlistEntry` objects representing specific 
            versions of that variable.
        - ``data_pods`` is a reversible map (:class:`~util.MultiMap`) between a
            data_key and a set of names of PODs that use that variable. The PODs
            themselves can be accessed through the ``pods`` dict.
        - ``data_files`` is a reversible map (:class:`~util.MultiMap`) between a
            data_key and the set of files (represented as :class:`SingleFileDataSet` 
            objects) that contain that variable's data.
        """
        self.data_keys = collections.defaultdict(list)
        self.data_pods = util.MultiMap()
        for pod in self.iter_pods():
            pod.update_active_vars()
            for var in pod.iter_vars():
                key = self.dataset_key(var)
                self.data_keys[key].append(var)
                self.data_pods[key].update([pod.name])

    def deactivate_key(self, data_key, exc):
        """Deactivate all active variables corresponding to data_key.
        """
        for v in self.data_keys[data_key]:
            v.exception = exc
        
    # DATA QUERY -------------------------------------

    def pre_query_hook(self):
        """Called before querying the presence of a new batch of variables.
        """
        pass

    # specific details that must be implemented in child class 
    @abc.abstractmethod
    def query_dataset(self, data_key):
        pass

    def query_data(self):
        update = True
        # really a while-loop, but we limit # of iterations to be safe
        for _ in range(10): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time.
            if update:
                self.build_data_dicts()
                update = False
            keys_to_query = set(self.data_keys).difference(self.queried_keys)
            if not keys_to_query:
                break # normal exit: queried everything
            
            self.pre_query_hook()
            for d_key in keys_to_query:
                try:
                    _log.info("    Querying '%s'", d_key)
                    # add before query, in case query raises an exc
                    self.queried_keys.add(d_key) 
                    files = util.to_iter(self.query_dataset(d_key))
                    if not files:
                        raise util.DataQueryError(d_key, "No data found by query.")
                    self.data_files[d_key].update(files)
                except Exception as exc:
                    update = True
                    if not isinstance(exc, util.DataQueryError):
                        _log.exception("Caught exception querying %s: %s",
                            d_key, repr(exc))
                    try:
                        raise util.DataQueryError(d_key, 
                            "Caught exception while querying data.") from exc
                    except Exception as chained_exc:
                        self.deactivate_key(d_key, chained_exc)
                    continue
            self.post_query_hook()
        else:
            # only hit this if we don't break
            raise Exception(
                f'Too many iterations in {self.__class__.__name__}.query_data().'
            )

    def post_query_hook(self):
        """Called after querying the presence of a new batch of variables.
        """
        pass

    # FETCH REMOTE DATA -------------------------------------

    def pre_query_and_fetch_hook(self):
        """Called once, before the iterative query_and_fetch() process starts.
        Use to, eg, initialize database or remote filesystem connections.
        """
        pass

    def pre_fetch_hook(self):
        """Called before fetching each batch of query results.
        """
        pass

    def sort_dataset_files(self, d_key):
        """Process list of requested data to make data fetching efficient.

        This is intended as a hook to be used by subclasses. Default behavior is
        to delete from the list duplicate datasets and datasets where a local
        copy of the data already exists and is current (as determined by 
        :meth:`~data_manager.DataManager.local_data_is_current`).
        
        Returns: collection of :class:`SingleFileDataSet` objects.
        """
        # flatten list of all data_files and remove duplicates
        # filter out any data we've previously fetched that's up to date
        unique_files = set(f for f in self.data_files[d_key] \
            if not self.local_data_is_current(f))
        # fetch data in sorted order to make interpreting logs easier
        unique_files = list(unique_files)
        sort_key = None
        if unique_files:
            if self._fetch_order_function is not None:
                sort_key = self._fetch_order_function
            elif hasattr(unique_files[0], 'remote_path'):
                sort_key = attrgetter('remote_path')
            else:
                sort_key = None
        return sorted(unique_files, key=sort_key)
    
    _fetch_order_function = None

    def local_data_is_current(self, dataset_obj):
        """Determine if local copy of data needs to be refreshed. This is 
        intended as a hook to be used by subclasses. Default is to always
        return `False`, ie always fetch remote data.

        Returns: `True` if local copy of data exists and remote copy hasn't been
            updated.
        """
        return False
        # return os.path.getmtime(dataset.local_path) \
        #     >= os.path.getmtime(dataset.remote_path)

    # specific details that must be implemented in child class 
    @abc.abstractmethod
    def fetch_dataset(self, data_key):
        pass

    def query_and_fetch_data(self):
        # Call cleanup method if we're killed
        signal.signal(signal.SIGTERM, self.query_and_fetch_cleanup)
        signal.signal(signal.SIGINT, self.query_and_fetch_cleanup)
        self.pre_query_and_fetch_hook()

        update = True
        # really a while-loop, but we limit # of iterations to be safe
        for _ in range(10): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time and query them.
            if update:
                self.query_data()
                update = False
            keys_to_fetch = set(self.data_keys).difference(self.fetched_keys)
            if not keys_to_fetch:
                break # normal exit: fetched everything

            self.pre_fetch_hook()
            for d_key in keys_to_fetch:
                try:
                    _log.info(f"    Fetching '%s'", d_key)
                    # add before fetch, in case fetch raises an exc
                    self.fetched_keys.add(d_key) 
                    self.fetch_dataset(d_key)
                except Exception as exc:
                    update = True
                    _log.exception("Caught exception fetching %s: %s",
                        d_key, repr(exc))
                    try:
                        raise util.DataAccessError(d_key, 
                            "Caught exception while fetching data.") from exc
                    except Exception as chained_exc:
                        self.deactivate_key(d_key, chained_exc)
                    continue
            self.post_fetch_hook()
        else:
            # Do cleanup regardless of success/fail
            self.post_query_and_fetch_hook()
            # only hit this if we don't break
            raise Exception(
                f'Too many iterations in {self.__class__.__name__}.fetch_data().'
            )
        self.post_query_and_fetch_hook()       

    def post_fetch_hook(self):
        """Called after fetching each batch of query results.
        """
        pass

    def post_query_and_fetch_hook(self):
        """Called once, after the iterative query_and_fetch() process ends.
        Use to, eg, close database or remote filesystem connections.
        """
        pass

    def query_and_fetch_cleanup(self, signum=None, frame=None):
        """Called if framework is terminated abnormally. Not called during
        normal exit.
        """
        util.signal_logger(self.__class__.__name__, signum, frame)
        self.post_query_and_fetch_hook()

    # -------------------------------------

    def preprocess_data(self):
        """Hook to run the preprocessing function on all variables. The 
        preprocessor class to use is determined by :class:`~mdtf.MDTFFramework`.
        """
        for pod in self.iter_pods():
            pod.setup_pod_directories()
            pod.preprocessor.setup()
            for var in pod.iter_vars():
                d_key = self.dataset_key(var)
                pod.preprocessor.process(var, list(self.data_files[d_key]))
            pod.preprocessor.tear_down()

    # HTML & PLOT OUTPUT -------------------------------------

    def tear_down(self):
        # TODO: handle OSErrors in all of these
        config = configs.ConfigManager()
        paths = configs.PathManager()
        
        # create empty text file for PODs to append to
        open(self.TEMP_HTML, 'w').close()
        for p in self.iter_pods(all_pods=True):
            p.tear_down()
        self._make_html()
        _ = self._backup_config_file(config)
        if self.make_variab_tar:
            _ = self._make_tar_file(paths.OUTPUT_DIR)
        self._copy_to_output()

    def _make_html(self, cleanup=True):
        src_dir = os.path.join(self.code_root, 'src', 'html')
        dest = os.path.join(self.MODEL_WK_DIR, 'index.html')
        if os.path.isfile(dest):
            _log.warning("%s: index.html exists, deleting.", self.case_name)
            os.remove(dest)

        template_dict = self.env_vars.copy()
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

    def _backup_config_file(self, config):
        """Record settings in file variab_dir/config_save.json for rerunning
        """
        out_file = os.path.join(self.MODEL_WK_DIR, 'config_save.json')
        if not self.file_overwrite:
            out_file, _ = util.bump_version(out_file)
        elif os.path.exists(out_file):
            _log.info("%s: Overwriting %s.", self.case_name, out_file)
        util.write_json(config.toDict(), out_file)
        return out_file

    def _make_tar_file(self, tar_dest_dir):
        """Make tar file of web/bitmap output.
        """
        out_file = os.path.join(tar_dest_dir, self.MODEL_WK_DIR+'.tar')
        if not self.file_overwrite:
            out_file, _ = util.bump_version(out_file)
            _log.info("%s: Creating %s.", self.case_name, out_file)
        elif os.path.exists(out_file):
            _log.info("%s: Overwriting %s.", self.case_name, out_file)
        tar_flags = [f"--exclude=.{s}" for s in ('netCDF','nc','ps','PS','eps')]
        tar_flags = ' '.join(tar_flags)
        util.run_shell_command(
            f'tar {tar_flags} -czf {out_file} -C {self.MODEL_WK_DIR} .',
            dry_run = self.dry_run
        )
        return out_file

    def _copy_to_output(self):
        if self.MODEL_WK_DIR == self.MODEL_OUT_DIR:
            return # no copying needed
        _log.debug("%s: Copy %s to %s.", 
            self.case_name, self.MODEL_WK_DIR, self.MODEL_OUT_DIR)
        try:
            if os.path.exists(self.MODEL_OUT_DIR):
                if not self.overwrite:
                    _log.error("%s: %s exists, overwriting.", self.case_name,
                        self.MODEL_OUT_DIR)
                shutil.rmtree(self.MODEL_OUT_DIR)
        except Exception:
            raise
        shutil.move(self.MODEL_WK_DIR, self.MODEL_OUT_DIR)

# =================================================================

@util.mdtf_dataclass(frozen=True)
class LocalfileDataManagerAttributes(DataManagerAttributesBase):
    CASENAME: dataclasses.InitVar
    sample_data_source: str = None

    def __post_init__(self, FIRSTYR, LASTYR, CASENAME):
        super(LocalfileDataManagerAttributes, self).__post_init__(FIRSTYR, LASTYR)
        if not self.sample_data_source:
            assert (CASENAME) # is not empty
            self.sample_data_source = CASENAME

class LocalfileDataManager(DataManager):
    """:class:`DataManager` for working with input model data files that are 
    already present in ``MODEL_DATA_DIR`` (on a local filesystem), for example
    the PODs' sample model data.
    """
    _AttributesClass = LocalfileDataManagerAttributes
    _DataKeyClass = DefaultDataKey
    _PreprocessorClass = preprocessor.MDTFDataPreprocessor

    FileDataSet = remote_file_dataset_factory('FileDataSet', _DataKeyClass)

    def dataset_key(self, varlist_entry):
        return self._DataKeyClass.from_dataset(varlist_entry, self)

    def remote_path(self, data_key):
        """Returns the absolute path of the local copy of the file for dataset.

        This determines the local sample model data directory structure, which 
        is
        ``$MODEL_DATA_ROOT/<CASENAME>/<freq>/<CASENAME>.<var name>.<freq>.nc'``.
        Sample model data not following this convention won't be found.
        """
        freq = data_key.frequency.format_local()
        return os.path.join(
            self.MODEL_DATA_DIR, freq,
            f"{data_key.case_name}.{data_key.name_in_model}.{freq}.nc"
        )

    def query_dataset(self, data_key):
        tmpdirs = configs.TempDirManager()

        path = self.remote_path(data_key)
        tmpdir = tmpdirs.make_tempdir(hash_obj = data_key)
        if os.path.isfile(path):
            return self.FileDataSet.from_dataclasses(
                data_key,
                remote_path = path,
                local_path = os.path.join(tmpdir, os.path.basename(path))
            )
        else:
            raise util.DataQueryError(data_key, f"File not found at {path}.")
    
    def local_data_is_current(self, dataset):
        return False 

    def fetch_dataset(self, data_key):
        files = self.sort_dataset_files(data_key)
        for file_ds in files:
            shutil.copy2(file_ds.remote_path, file_ds.local_path)
