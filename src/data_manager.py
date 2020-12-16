"""Classes for querying, fetching and preprocessing model data requested by the
PODs.
"""
import os
import abc
import dataclasses
from src import util, diagnostic
import pandas as pd
import intake_esm

class AbstractQueryMixin(abc.ABC):
    @abc.abstractmethod
    def query_dataset(self, var): pass

    def setup_query(self):
        """Called once, before the iterative query_and_fetch() process starts.
        Use to, eg, initialize database or remote filesystem connections.
        """
        pass

    def pre_query_hook(self):
        """Called before querying the presence of a new batch of variables."""
        pass

    def post_query_hook(self):
        """Called after querying the presence of a new batch of variables."""
        pass

    def tear_down_query(self):
        """Called once, after the iterative query_and_fetch() process ends.
        Use to, eg, close database or remote filesystem connections.
        """
        pass

class AbstractFetchMixin(abc.ABC):
    @abc.abstractmethod
    def fetch_dataset(self, var): pass

    def setup_fetch(self):
        """Called once, before the iterative query_and_fetch() process starts.
        Use to, eg, initialize database or remote filesystem connections.
        """
        pass

    def pre_fetch_hook(self):
        """Called before fetching each batch of query results."""
        pass

    def post_fetch_hook(self):
        """Called after fetching each batch of query results."""
        pass

    def tear_down_fetch(self):
        """Called once, after the iterative query_and_fetch() process ends.
        Use to, eg, close database or remote filesystem connections.
        """
        pass

class AbstractDataSource(abc.ABC):
    @abc.abstractmethod
    def query_dataset(self, var): pass

    @abc.abstractmethod
    def fetch_dataset(self, var): pass

    def pre_query_and_fetch_hook(self):
        """Called once, before the iterative query_and_fetch() process starts.
        Use to, eg, initialize database or remote filesystem connections.
        """
        pass

    def pre_query_hook(self):
        """Called before querying the presence of a new batch of variables."""
        pass

    def pre_fetch_hook(self):
        """Called before fetching each batch of query results."""
        pass

    def post_query_hook(self):
        """Called after querying the presence of a new batch of variables."""
        pass

    def post_fetch_hook(self):
        """Called after fetching each batch of query results."""
        pass

    def post_query_and_fetch_hook(self):
        """Called once, after the iterative query_and_fetch() process ends.
        Use to, eg, close database or remote filesystem connections.
        """
        pass

# --------------------------------------------------------------------------

@util.mdtf_dataclass
class DataSourceAttributesBase():
    """Attributes that any data source must specify.
    """
    CASENAME: str = util.MANDATORY
    FIRSTYR: str = util.MANDATORY
    LASTYR: str = util.MANDATORY
    convention: str = util.MANDATORY
    date_range: datelabel.DateRange = dataclasses.field(init=False)

    def __post_init__(self):
        self.date_range = datelabel.DateRange(FIRSTYR, LASTYR)

class DataSourceBase(AbstractDataSource, metaclass=util.MDTFABCMeta):
    """Base class for handling the data needs of PODs. Executes query for 
    requested model data against the remote data source, fetches the required 
    data locally, preprocesses it, and performs cleanup/formatting of the POD's 
    output.
    """
    _AttributesClass = util.abstract_attribute()
    _DiagnosticClass = util.abstract_attribute()
    _PreprocessorClass = util.abstract_attribute()

    def __init__(self, case_dict):
        self.attrs = util.coerce_to_dataclass(case_dict, self._AttributesClass)
        self.pods = case_dict.get('pod_list', [])

        # configure case-specific env vars
        config = core.ConfigManager()
        self.env_vars = config.global_env_vars.copy()
        self.env_vars.update({
            k: case_dict[k] for k in ("CASENAME", "FIRSTYR", "LASTYR")
        })

        # configure paths
        self.overwrite = config.overwrite
        paths = core.PathManager()
        d = paths.model_paths(case_dict, overwrite=self.overwrite)
        self.code_root = paths.CODE_ROOT
        self.MODEL_DATA_DIR = d.MODEL_DATA_DIR
        self.MODEL_WK_DIR = d.MODEL_WK_DIR
        self.MODEL_OUT_DIR = d.MODEL_OUT_DIR
        util.check_dirs(self.MODEL_WK_DIR, self.MODEL_DATA_DIR, create=True)

        # configure logger
        util.case_log_config(
            config, mdtf_log_file= os.path.join(d.MODEL_WK_DIR, "mdtf.log")
        )

    @property
    def name(self):
        return self.attrs.CASENAME

    @property
    def convention(self):
        return self.attrs.convention

    def iter_pods(self):
        """Generator iterating over all pods which haven't been
        skipped due to requirement errors.
        """
        for p in self.pods.values():
            if p.active:
                yield p

    def iter_vars(self, all_vars=False):
        for p in self.iter_pods():
            yield from p.iter_vars(all_vars=all_vars)

    def iter_vars_with_pod(self):
        for p in self.iter_pods():
            for v in p.iter_vars():
                yield (v,p)

    # -------------------------------------

    def setup(self):
        self.pods = {
            pod_name: self._DiagnosticClass.from_config(pod_name) \
                for pod_name in self.pods
        }
        for pod in self.pods.values():
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
        for v in self.iter_vars(all_vars=True):
            v.print_debug()
        print('####################')

    def setup_pod(self, pod):
        """Update POD with information that only becomes available after 
        DataManager and Diagnostic have been configured (ie, only known at 
        runtime, not from settings.jsonc.)

        Could arguably be moved into Diagnostic's init, at the cost of 
        dependency inversion.
        """
        # set up paths/working directories
        paths = core.PathManager()
        paths = paths.pod_paths(pod, self)
        for k,v in paths.items():
            setattr(pod, k, v)
        pod.setup_pod_directories()
        # set up env vars
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

        Could arguably be moved into VarlistEntry's init, at the cost of 
        dependency inversion.
        """
        translate = core.VariableTranslator()
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
            v.translation = translate.translate(self.convention, v)
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
            f_name = f"{self.name}.{var.name}.nc"
            return os.path.join(pod.POD_WK_DIR, f_name)
        else:
            freq = var.T.frequency.format_local()
            f_name = f"{self.name}.{var.name}.{freq}.nc"
            return os.path.join(pod.POD_WK_DIR, freq, f_name)
        
    # DATA QUERY/FETCH/PREPROCESS -------------------------------------

    def query_data(self):
        update = True
        # really a while-loop, but we limit # of iterations to be safe
        for _ in range(5): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time.
            if update:
                for pod in self.iter_pods():
                    pod.update_active_vars()
                update = False
            vars_to_query = [v for v in self.iter_vars() \
                if v.status < diagnostic.VarlistEntryStatus.QUERIED]
            if not vars_to_query:
                break # normal exit: queried everything
            
            self.pre_query_hook()
            for var in vars_to_query:
                try:
                    _log.info("    Querying '%s'", var.short_format())
                    # add before query, in case query raises an exc
                    var.status = diagnostic.VarlistEntryStatus.QUERIED
                    files = util.to_iter(self.query_dataset(var))
                    if not files:
                        raise util.DataQueryError(d_key, "No data found by query.")
                    self.data_files[d_key].update(files)
                except Exception as exc:
                    update = True
                    if not isinstance(exc, util.DataQueryError):
                        _log.exception("Caught exception querying %s: %s",
                            var.short_format(), repr(exc))
                    try:
                        raise util.DataQueryError(var, 
                            "Caught exception while querying data.") from exc
                    except Exception as chained_exc:
                        var.deactivate(chained_exc)
                    continue
            self.post_query_hook()
        else:
            # only hit this if we don't break
            raise Exception(
                f"Too many iterations in {self.__class__.__name__}.query_data()."
            )

    def fetch_data(self):
        update = True
        # really a while-loop, but we limit # of iterations to be safe
        for _ in range(5): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time and query them.
            if update:
                self.query_data()
                update = False
            vars_to_fetch = [v for v in self.iter_vars() \
                if v.status < diagnostic.VarlistEntryStatus.FETCHED]
            if not vars_to_fetch:
                break # normal exit: fetched everything

            self.pre_fetch_hook()
            for var in vars_to_fetch:
                try:
                    _log.info("    Fetching '%s'", var.short_format())
                    # add before fetch, in case fetch raises an exc
                    var.status = diagnostic.VarlistEntryStatus.FETCHED
                    self.fetch_dataset(var)
                except Exception as exc:
                    update = True
                    _log.exception("Caught exception fetching %s: %s",
                        var.short_format(), repr(exc))
                    try:
                        raise util.DataAccessError(var, 
                            "Caught exception while fetching data.") from exc
                    except Exception as chained_exc:
                        var.deactivate(chained_exc)
                    continue
            self.post_fetch_hook()
        else:
            # only hit this if we don't break
            raise Exception(
                f"Too many iterations in {self.__class__.__name__}.fetch_data()."
            )

    def preprocess_data(self):
        """Hook to run the preprocessing function on all variables. The 
        preprocessor class to use is determined by :class:`~mdtf.MDTFFramework`.
        """
        update = True
        # really a while-loop, but we limit # of iterations to be safe
        for _ in range(5): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time and fetch them.
            if update:
                self.fetch_data()
                update = False
            vars_to_process = [vp for vp in self.iter_vars_with_pod() \
                if vp[0].status < diagnostic.VarlistEntryStatus.PREPROCESSED]
            if not vars_to_process:
                break # normal exit: processed everything

            for var, pod in vars_to_process:
                try:
                    _log.info("    Processing '%s'", var.short_format())
                    var.status = diagnostic.VarlistEntryStatus.PREPROCESSED
                    pod.preprocessor.process(var, list(self.data_files[d_key]))
                except Exception as exc:
                    update = True
                    _log.exception("Caught exception processing %s: %s",
                        var.short_format(), repr(exc))
                    try:
                        raise util.DataPreprocessError(var, 
                            "Caught exception while processing data.") from exc
                    except Exception as chained_exc:
                        var.deactivate(chained_exc)
                    continue
        else:
            # only hit this if we don't break
            raise Exception(
                f"Too many iterations in {self.__class__.__name__}.preprocess_data()."
            )

    def data_pipeline(self):
        # Call cleanup method if we're killed
        signal.signal(signal.SIGTERM, self.query_and_fetch_cleanup)
        signal.signal(signal.SIGINT, self.query_and_fetch_cleanup)
        self.pre_query_and_fetch_hook()
        try:
            self.preprocess_data()
        except Exception as exc:
            _log.exception(f"{repr(exc)}")
            pass
        # clean up regardless of success/fail
        self.post_query_and_fetch_hook()

    def query_and_fetch_cleanup(self, signum=None, frame=None):
        """Called if framework is terminated abnormally. Not called during
        normal exit.
        """
        util.signal_logger(self.__class__.__name__, signum, frame)
        self.post_query_and_fetch_hook()

# --------------------------------------------------------------------------

class OnTheFlyCatalogQueryMixin(AbstractQueryMixin):
    asset_file_format = "netcdf"
        
    @property
    def df(self):
        if self.catalog:
            return self.catalog.df
        else:
            return None
    
    def iter_files(self):
        root_dir = os.path.join(self.CATALOG_DIR, "") # adds separator if not present
        for root, _, files in os.walk(root_dir):
            for f in files:
                if f.startswith('.'):
                    continue
                try:
                    path = os.path.join(root, f)
                    yield self._dataclass.from_string(path, len(root_dir))
                except (ValueError):
                    print('XXX', f)
                    continue
                
    def _dummy_esmcol_spec(self):
        pattern = self._dataclass._pattern # abbreviate
        attr_fields = set(pattern.fields).remove(pattern.input_field)
        attrs = [{"column_name":f, "vocabulary": ""} for f in attr_fields]
        return {
            "esmcat_version": "0.1.0",
            "id": "MDTF_" + self.__class__.__name__,
            "description": "",
            "attributes": attrs,
            "assets": {
                "column_name": pattern.input_field,
                "format": self.asset_file_format
            },
            "last_updated": "2020-12-06"   
        }

    def setup_query(self):
        # verify parent class defined attributes correctly
        assert hasattr(self, "CATALOG_DIR")
        assert hasattr(self, "_dataclass")
        # generate catalog
        df = pd.DataFrame.from_records(
            [dataclasses.todict(dc) for dc in self.iter_files()]
        )
        self.catalog = intake_esm.core.esm_datastore.from_df(
            df, esmcol_data = self._dummy_esmcol_spec(), 
            progressbar=False, sep='|'
        )

    def query_dataset(self, var): 
        # TODO
        pass

class LocalFetchMixin(AbstractFetchMixin):
    def fetch_dataset(self, var):
        # TODO
        pass

class LocalFileDataSource(OnTheFlyCatalogQueryMixin, LocalFetchMixin):
    def __init__(self, data_root_dir, DataClass):
        self.CATALOG_DIR = data_root_dir
        self._dataclass = DataClass
        self.catalog = None

# --------------------------------------------------------------------------

sample_data_regex = util.RegexPattern(
    r"""
        (?P<sample_dataset>\S+)/       # first directory: model name
        (?P<frequency>\w+)/   # subdirectory: data frequency
        # file name = model name + variable name + frequency
        (?P=sample_dataset)\.(?P<variable>\w+)\.(?P=frequency)\.nc
    """,
    input_field="remote_path"
)
@util.regex_dataclass(sample_data_regex)
@util.mdtf_dataclass()
class SampleDataDataclass():
    sample_dataset: str = util.MANDATORY # <- mark this as CLI attribute? 
    frequency: datelabel.DateFrequency = util.MANDATORY
    variable: str = util.MANDATORY
    remote_path: str = util.MANDATORY
    local_path: # XXX

@util.mdtf_dataclass
class SampleDataAttributes():
    MODEL_DATA_ROOT: str = ""
    sample_dataset: str = ""

    def __post_init__(self):
        if not os.path.isdir(self.MODEL_DATA_ROOT):
            _log.critical("Data directory %s = '%s' not found.",
                'MODEL_DATA_ROOT', self.MODEL_DATA_ROOT)
            exit(1)
        if not os.path.isdir(
            os.path.join(self.MODEL_DATA_ROOT, self.sample_dataset)
        ):
            _log.critical("Sample dataset name '%s' not found in %s = '%s'.",
                self.sample_dataset, 'MODEL_DATA_ROOT', self.MODEL_DATA_ROOT)
            exit(1)


class SampleDataDataSource(LocalFileDataSource):
    pass


# ---------------------------

@util.mdtf_dataclass
class CMIP6DataSourceAttributes():
    activity_id: str = ""
    institution_id: str = ""
    source_id: str = ""
    experiment_id: str = ""
    member_id: str = ""
    grid_label: str = ""
    version_date: str = ""

    def __post_init__(self):
        cmip = cmip6.CMIP6_CVs()
        for field_name, val in dataclasses.asdict(self).items():
            if field_name in ('version_date', 'member_id'):
                continue
            if val and not cmip.is_in_cv(field_name, val):
                _log.error(("Supplied value '%s' for '%s' is not recognized by "
                    "the CMIP6 CV. Continuing, but queries will probably fail."),
                    val, field_name)
        # try to infer values:
        cmip.lookup_single(self, 'experiment_id', 'activity_id')
        cmip.lookup_single(self, 'source_id', 'institution_id')
        # bail out if we're in strict mode with undetermined fields

