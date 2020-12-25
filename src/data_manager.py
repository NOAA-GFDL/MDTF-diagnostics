"""Classes for querying, fetching and preprocessing model data requested by the
PODs.
"""
import os
import abc
import collections
import dataclasses
import signal
from src import util, core, datelabel, diagnostic, preprocessor, cmip6
import pandas as pd
import intake_esm

import logging
_log = logging.getLogger(__name__)

class AbstractQueryMixin(abc.ABC):
    @abc.abstractmethod
    def query_dataset(self, var): 
        """Sets remote_data attribute on var or raises an exception."""
        pass

    @abc.abstractmethod
    def remote_data(self, rd_key):
        """Translates between rd_keys (output of query_data) and paths, urls, 
        etc. (input to fetch_data.)"""
        pass

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
    def fetch_dataset(self, var, remote_data): 
        """Sets local_data attribute on var or raises an exception."""
        pass

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
    def __init__(self, case_dict): pass

    @abc.abstractmethod
    def query_dataset(self, var): 
        """Sets remote_data attribute on var or raises an exception."""
        pass

    @abc.abstractmethod
    def fetch_dataset(self, var, remote_data): 
        """Sets local_data attribute on var or raises an exception."""
        pass

    @abc.abstractmethod
    def remote_data(self, rd_key):
        """Translates between rd_keys (output of query_data) and paths, urls, 
        etc. (input to fetch_data.)"""
        pass

    def pre_query_and_fetch_hook(self):
        """Called once, before the iterative query_and_fetch() process starts.
        Use to, eg, initialize database or remote filesystem connections.
        """
        # call methods if we're using mixins; if not, child classes will override
        if hasattr(self, 'setup_query'):
            self.setup_query()
        if hasattr(self, 'setup_fetch'):
            self.setup_fetch()

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
        # call methods if we're using mixins; if not, child classes will override
        if hasattr(self, 'tear_down_query'):
            self.tear_down_query()
        if hasattr(self, 'tear_down_fetch'):
            self.tear_down_fetch()

# --------------------------------------------------------------------------

PodVarTuple = collections.namedtuple('PodVarTuple', ['pod', 'var'])

@util.mdtf_dataclass
class DataSourceAttributesBase():
    """Attributes that any DataSource must specify.
    """
    CASENAME: str = util.MANDATORY
    FIRSTYR: str = util.MANDATORY
    LASTYR: str = util.MANDATORY
    convention: str = util.MANDATORY
    date_range: datelabel.DateRange = dataclasses.field(init=False)

    def __post_init__(self):
        translate = core.VariableTranslator()
        self.convention = translate.get_convention_name(self.convention)
        self.date_range = datelabel.DateRange(self.FIRSTYR, self.LASTYR)

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
        config = core.ConfigManager()
        self.attrs = util.coerce_to_dataclass(case_dict, self._AttributesClass)
        self.pods = case_dict.get('pod_list', [])
        self.data = dict() # VarlistEntry -> set of rd_keys
        self.strict = config.get('strict', False)
        # rd_key -> bool or None; None = fetch hasn't been tried yet
        self.fetch_failed = util.WormDefaultDict((lambda: None))
        self.exceptions: util.ExceptionQueue()

        # configure case-specific env vars
        self.env_vars = util.WormDict.from_struct(
            config.global_env_vars.copy()
        )
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
        assert (hasattr(self,'attrs') and hasattr(self.attrs, 'CASENAME'))
        return self.attrs.CASENAME

    @property
    def convention(self):
        assert (hasattr(self,'attrs') and hasattr(self.attrs, 'convention'))
        return self.attrs.convention

    @property
    def failed(self):
        assert hasattr(self,'exceptions')
        return not self.exceptions.is_empty

    def iter_pods(self, active=None):
        """Generator iterating over all PODs associated with this case.

        Args:
            active: bool or None, default None. Selects subset of PODs which are
                returned.
                - active = True: only iterate over currently active PODs.
                - active = False: only iterate over inactive PODs (PODs which
                    have experienced an error during query-fetch.)
                - active = None: iterate over both active and inactive PODs.
        """
        if active is None:
            # default: all pods
            yield from self.pods.values()
        else:
            # either all active or inactive pods
            yield from filter(
                (lambda p: p.active == active), self.pods.values()
            )

    def iter_vars(self, active=None, active_pods=True):
        """Generator iterating over all VarlistEntries in all PODs associated 
        with this case.

        Args:
            active: bool or None, default None. Selects subset of VarlistEntries
                which are returned, *after* selecting a subset of PODs based on
                active_pods.
                - active = True: only iterate over currently active VarlistEntries.
                - active = False: only iterate over inactive VarlistEntries 
                    (Either alternates which have not yet been considered, or
                    variables which have experienced an error during query-fetch.)
                - active = None: iterate over all VarlistEntries.
            active_pods: bool or None, default True. Selects subset of PODs which 
                are returned.
                - active = True: only iterate over currently active PODs.
                - active = False: only iterate over inactive PODs (PODs which
                    have experienced an error during query-fetch.)
                - active = None: iterate over both active and inactive PODs.
        """
        for p in self.iter_pods(active=active_pods):
            yield from p.iter_vars(active=active)

    def iter_pod_vars(self, active=None, active_pods=True):
        """Generator similar to :meth:`DataSourceBase.iter_vars`, but returns a
        namedtuple of the :class:`~diagnostic.Diagnostic` and 
        :class:~diagnostic.VarlistEntry` objects corresponding to the POD and 
        its variable, respectively.

        Arguments are identical to :meth:`DataSourceBase.iter_vars`.
        """
        for p in self.iter_pods(active=active_pods):
            for v in p.iter_vars(active=active):
                yield PodVarTuple(pod=p, var=v)

    def deactivate_if_failed(self):
        """Deactivate all PODs for this case if the case itself has failed.
        """
        # should be called from a hook whenever we log an exception
        # only need to keep track of this up to pod execution
        if self.failed:
            for v in self.iter_pods():
                v.active = False

    # -------------------------------------

    def setup(self):
        self.pods = {
            pod_name: self._DiagnosticClass.from_config(pod_name) \
                for pod_name in self.pods
        }
        for pod in self.iter_pods():
            try:
                self.setup_pod(pod)
            except Exception as exc:
                # raise
                try:
                    raise util.PodConfigError(pod, 
                        "Caught exception in DataManager setup.") from exc
                except Exception as chained_exc:
                    pod.exceptions.log(chained_exc)    
                continue

        print('####################\n')
        for v in self.iter_vars(active=None, active_pods=None):
            v.print_debug()
        print('\n####################')

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

        for v in pod.iter_vars():
            try:
                self.setup_var(pod, v)
            except Exception as exc:
                try:
                    raise util.PodConfigError(pod, 
                        f"Caught exception when configuring {v.name}.") from exc
                except Exception as chained_exc:
                    pod.exceptions.log(chained_exc)  
                continue
        # preprocessor will edit varlist alternates, depending on enabled functions
        pod.preprocessor = self._PreprocessorClass(self, pod)
        pod.preprocessor.edit_request(self, pod)

    def setup_var(self, pod, v):
        """Update VarlistEntry fields with information that only becomes 
        available after DataManager and Diagnostic have been configured (ie, 
        only known at runtime, not from settings.jsonc.)

        Could arguably be moved into VarlistEntry's init, at the cost of 
        dependency inversion.
        """
        translate = core.VariableTranslator().get_convention(self.convention)
        try:
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
            v.translation = translate.translate(v)
        except Exception as exc:
            v.exception = exc    # "caught" by pod.update_active_vars()
            raise exc

    def variable_dest_path(self, pod, var):
        """Returns the absolute path of the POD's preprocessed, local copy of 
        the file containing the requested dataset. Files not following this 
        convention won't be found by the POD.
        """
        if var.is_static:
            f_name = f"{self.name}.{var.name}.static.nc"
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
                for pod in self.iter_pods(active=True):
                    pod.update_active_vars()
                update = False
            vars_to_query = [
                v for v in self.iter_vars(active=True) \
                    if v.status < diagnostic.VarlistEntryStatus.QUERIED
            ]
            if not vars_to_query:
                break # normal exit: queried everything
            
            self.pre_query_hook()
            for var in vars_to_query:
                try:
                    _log.info("    Querying <%s>", var.short_format())
                    # add before query, in case query raises an exc
                    var.status = diagnostic.VarlistEntryStatus.QUERIED
                    self.query_dataset(var) # sets var.remote_data
                    if not var.remote_data:
                        raise util.DataQueryError(var, "No data found by query.")
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
            raise util.DataQueryError(
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
            vars_to_fetch = [
                v for v in self.iter_vars(active=True) \
                    if v.status < diagnostic.VarlistEntryStatus.FETCHED
            ]
            if not vars_to_fetch:
                break # normal exit: fetched everything

            self.pre_fetch_hook()
            for var in vars_to_fetch:
                try:
                    _log.info("    Fetching <%s>", var.short_format())
                    # add before fetch, in case fetch raises an exc
                    var.status = diagnostic.VarlistEntryStatus.FETCHED
                    for rd_key in var.remote_data:
                        remote_data = self.remote_data(rd_key)
                        self.fetch_dataset(var, remote_data)
                        self.fetch_success(rd_key)
                    if not var.local_data:
                        raise util.DataFetchError(var, "No data fetched.")
                except Exception as exc:
                    update = True
                    self.fetch_fail(var, exc)
                    continue
            self.post_fetch_hook()
        else:
            # only hit this if we don't break
            raise util.DataFetchError(
                f"Too many iterations in {self.__class__.__name__}.fetch_data()."
            )

    def fetch_success(self, rd_key):
        self.fetch_failed[rd_key] = False

    def fetch_fail(self, var, exc):
        for rd_key in var.remote_data:
            self.fetch_failed[rd_key] = True
        _log.exception("Caught exception fetching %s: %s",
            var.short_format(), repr(exc))
        try:
            raise util.DataFetchError(var, 
                "Caught exception while fetching data.") from exc
        except Exception as chained_exc:
            var.deactivate(chained_exc)


    def preprocess_data(self):
        """Hook to run the preprocessing function on all variables.
        """
        update = True
        # really a while-loop, but we limit # of iterations to be safe
        for _ in range(5): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time and fetch them.
            if update:
                self.fetch_data()
                update = False
            vars_to_process = [
                pv for pv in self.iter_pod_vars(active=True) \
                    if pv.var.status < diagnostic.VarlistEntryStatus.PREPROCESSED
            ]
            if not vars_to_process:
                break # normal exit: processed everything

            for pod, var in vars_to_process:
                try:
                    _log.info("    Processing <%s> for %s", 
                        var.short_format(), pod.name)
                    var.status = diagnostic.VarlistEntryStatus.PREPROCESSED
                    pod.preprocessor.process(var)
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
            raise util.DataPreprocessError(
                f"Too many iterations in {self.__class__.__name__}.preprocess_data()."
            )

    def request_data(self):
        """Top-level method to iteratively query, fetch and preprocess all data
        requested by PODs, switching to alternate requested data as needed.
        """
        # Call cleanup method if we're killed
        signal.signal(signal.SIGTERM, self.query_and_fetch_cleanup)
        signal.signal(signal.SIGINT, self.query_and_fetch_cleanup)
        self.pre_query_and_fetch_hook()
        try:
            self.preprocess_data()
        except Exception as exc:
            _log.exception(f"{repr(exc)}")
            self.exceptions.log(exc)    
        # clean up regardless of success/fail
        self.post_query_and_fetch_hook()

    def query_and_fetch_cleanup(self, signum=None, frame=None):
        """Called if framework is terminated abnormally. Not called during
        normal exit.
        """
        util.signal_logger(self.__class__.__name__, signum, frame)
        self.post_query_and_fetch_hook()

# --------------------------------------------------------------------------

class DirectoryHierarchyQueryMixin(AbstractQueryMixin, metaclass=util.MDTFABCMeta):
    """Wrapper that creates and queries an intake_esm.esm_datastore catalog 
    made by crawling a directory hierarchy and populating catalog entry attributes
    by running a regex against the paths of files in the directory hierarchy.
    """
    CATALOG_DIR = util.abstract_attribute()
    _FileRegexClass = util.abstract_attribute()
    _asset_file_format = "netcdf"
        
    @property
    def df(self):
        assert (hasattr(self, 'catalog') and hasattr(self.catalog, 'df'))
        return self.catalog.df

    @property
    def path_column_name(self):
        """Name of the column in the catalog containing the path to the remote 
        data file.
        """
        return self._FileRegexClass._pattern.input_field

    @property
    def data_column_names(self):
        """Column names of the catalog (except for the path to the remote data.)
        """
        pat_fields = list(self._FileRegexClass._pattern.fields)
        pat_fields.remove(self.path_column_name)
        return pat_fields

    def iter_files(self):
        """Generator that yields instances of FileRegexClass generated from 
        relative paths of files in CATALOG_DIR. Only paths that match the regex
        in FileRegexClass are returned.
        """
        root_dir = os.path.join(self.CATALOG_DIR, "") # adds separator if not present
        for root, _, files in os.walk(root_dir):
            for f in files:
                if f.startswith('.'):
                    continue
                try:
                    path = os.path.join(root, f)
                    yield self._FileRegexClass.from_string(path, len(root_dir))
                except util.RegexSuppressedError:
                    # decided to silently ignore this file
                    continue
                except Exception:
                    _log.info("Couldn't parse %s", path[len(root_dir):])
                    continue
                
    def _dummy_esmcol_spec(self):
        """Dummy specification dict that enables us to use intake_esm's 
        machinery. The catalog is temporary and not retained after the code
        finishes running.
        """
        # no aggregations, since for now we want to manually insert logic for
        # file fetching (& error handling etc.) before we load an xarray Dataset.
        return {
            "esmcat_version": "0.1.0",
            "id": "MDTF_" + self.__class__.__name__,
            "description": "",
            "attributes": [
                {"column_name":c, "vocabulary": ""} for c in self.data_column_names
            ],
            "assets": {
                "column_name": self.path_column_name,
                "format": self._asset_file_format
            },
            "last_updated": "2020-12-06"   
        }

    def setup_query(self):
        """Generate an intake_esm catalog of files found in CATALOG_DIR. 
        Attributes of files listed in the catalog are inferred from the
        directory heirarchy structure of thier paths, which is encoded by
        FileRegexClass.
        """
        df = pd.DataFrame(tuple(self.iter_files()), dtype='object')
        self.catalog = intake_esm.core.esm_datastore.from_df(
            df, 
            esmcol_data = self._dummy_esmcol_spec(), 
            progressbar=False, sep='|'
        )

    def _query_clause(self, col_name, k, v):
        _dict_var_name = 'd'
        if v == util.NOTSET:
            return ""
        if isinstance(v, datelabel.DateRange):
            # return files having any date range overlap at all
            return f"({col_name} in @{_dict_var_name}.{k})"
        elif k == 'max_frequency':
            return f"({col_name} <= @{_dict_var_name}.frequency)"
        elif k == 'max_frequency':
            return f"({col_name} <= @{_dict_var_name}.frequency)"
        else:
            return f"({col_name} == @{_dict_var_name}.{k})"

    def _query_result_dataframe(self, var):
        """Construct and execute the query to determine whether data matching 
        var is present in the catalog.
        
        Split off logic performing the query against the catalog (returning a
        dataframe with results) from the processing of those results, in order
        to simplify overriding by child classes.
        """
        query_d = util.WormDict.from_struct(
            util.filter_dataclass(self.attrs, self._FileRegexClass)
        )
        var_attrs = var.query_attrs(
            getattr(self._FileRegexClass, '_query_attrs_synonyms', None)
        )
        query_d.update(util.filter_dataclass(var_attrs, self._FileRegexClass))
        clauses = [self._query_clause(k, k, v) for k,v in query_d.items()]
        d = util.NameSpace.fromDict(query_d) # set local var for df.query()
        return self.df.query(' and '.join(clauses))

    def _group_query_results(self, query_df):
        """Split off logic constructing the rd_keys from the dataframe containing
        query results in order to simplify overriding by child classes.
        """
        def experiment_key_func(idx):
            """Returns string-valued key for grouping files by experiment: all
            values of all data columns must match.
            (We can't just do a .groupby on column names, because pandas attempts 
            to coerce DateFrequency to a timedelta64, which overflows for static 
            DateFrequency. There doesn't seem to be a way to disable this type 
            coercion.)
            """
            return '|'.join(
                str(query_df[c].loc[idx]) for c in self.data_column_names
            )

        # group result by column values
        q_groups = query_df.groupby(by=experiment_key_func)
        # return set of sets of catalog row indices
        return {self._rd_key_func(group.apply(self._query_group_hook)) \
            for _, group in q_groups}

    def _query_group_hook(self, group_df):
        """Processing to do on query results for a single experiment.
        """
        return group_df

    @staticmethod
    def _rd_key_func(group_df):
        """Return tuple of row indices: this implementation's rd_key."""
        return tuple(group_df.index.tolist())

    def query_dataset(self, var):
        """Find all rows of the catalog matching relevant attributes of the 
        DataSource and of the variable. Obtain the set of matching row numbers
        (the rd_keys for this query implementation) and store it in var's 
        remote_data attribute. Store one set of row numbers for each distinct
        experiment (ie set of column values in the catalog) matching the query.
        """
        query_df = self._query_result_dataframe(var)
        # assign set of sets of catalog row indices to var's remote_data attr
        # filter out empty entries = queries that failed.
        var.remote_data = {x for x in self._group_query_results(query_df) if x}

    def remote_data(self, rd_keys):
        """Given one or more row indices in the catalog's dataframe (rd_keys, 
        as found by query_dataset()), return the corresponding remote_paths.
        """
        if util.is_iterable(rd_keys):
            rd_keys = util.to_iter(rd_keys, list) # iloc requires list, not just iterable
        return self.df[self.path_column_name].iloc[rd_keys]

    def _query_error_logger(self, msg, rd_keys):
        """Log debugging message or raise an exception, depending on if we're
        in strict mode.
        """
        rd_keys = util.to_iter(rd_keys, list)
        err_str = '\n'.join(
            [str(self.df.iloc[idx].to_dict()) for idx in rd_keys]
        )
        err_str = msg + '\n' + err_str
        if self.strict:
            raise util.DataQueryError(rd_keys, err_str)
        else:
            _log.warning(err_str)

class ChunkedDirectoryHierarchyQueryMixin(DirectoryHierarchyQueryMixin):
    _date_range_col = util.abstract_attribute()

    @property
    def data_column_names(self):
        """Column names of the catalog (except for the path to the remote data,
        and the file's date range, which get handled separately.)
        """
        col_names = super(ChunkedDirectoryHierarchyQueryMixin, self).data_column_names
        col_names.remove(self._date_range_col)
        return col_names

    def _query_group_hook(self, group_df):
        """Sort the files found for each experiment by date, verify that
        the date ranges contained in the files are contiguous in time and that
        the date range of the files spans the query date range.
        """
        rd_keys = self._rd_key_func(group_df)
        try:
            sorted_df = group_df.sort_values(by=[self._date_range_col])
            # method throws ValueError if ranges aren't contiguous
            files_date_range = datelabel.DateRange.from_contiguous_span(
                *(sorted_df[self._date_range_col].to_list())
            )
            # throws AssertionError if we don't span the query range
            assert files_date_range.contains(self.attrs.date_range)
            return sorted_df
        except ValueError:
            self._query_error_logger(
                "Noncontiguous or malformed date range in files:", rd_keys
            )
        except AssertionError:
            self._query_error_logger(
                f"Returned files don't span query date range ({self.attrs.date_range}):",
                rd_keys
            )
        except Exception as exc:
            self._query_error_logger(f"Caught exception {repr(exc)}:", rd_keys)
        # hit an exception; return empty DataFrame to signify failure
        return pd.DataFrame(columns=group_df.columns)


class LocalFetchMixin(AbstractFetchMixin):
    """Mixin implementing data fetch for files on a locally mounted filesystem. 
    No data is transferred; we assume that xarray can open the paths directly.
    """
    def fetch_dataset(self, var, paths):
        if not util.is_iterable(paths):
            paths = (paths, )
        for path in paths:
            if not os.path.exists(path):
                raise util.DataFetchError(var, 
                    f"Fetch {var.name}: File not found at {path}.")
            else:
                _log.debug(f'Fetch {var.name}: found {path}.')
        var.local_data.extend(paths)


class SingleLocalFileDataSource(
    DirectoryHierarchyQueryMixin, LocalFetchMixin, DataSourceBase
    ):
    """DataSource for dealing data in a regular directory hierarchy on a 
    locally mounted filesystem. Assumes all data for each variable (in each 
    experiment) is contained in a single file.
    """
    def __init__(self, case_dict):
        self.catalog = None
        super(SingleLocalFileDataSource, self).__init__(case_dict)

    def _group_query_results(self, query_df):
        """Verify that only a single file was found from each experiment.
        Convert set of (one-element) sets of row indices to set of row indices.
        """
        rd_keys = super(SingleLocalFileDataSource, self)._group_query_results(query_df)
        new_keys = set([])
        for rd_key in rd_keys:
            if len(rd_key) != 1:
                self._query_error_logger(
                    "Query found multiple files when one was expected:", rd_key
                )
            else:
                new_keys.add(rd_key[0])
        return new_keys

    def remote_data(self, rd_key):
        """Verify that only a single file is being requested.
        (Should be unnecessary given constraint enforced in _group_query_results, 
        but check here just to be safe.)
        """
        if util.is_iterable(rd_key) and len(rd_key) != 1:
            self._query_error_logger(
                "Requested multiple files when one was expected:", rd_key
            )
        return super(SingleLocalFileDataSource, self).remote_data(rd_key)

class ChunkedLocalFileDataSource(
    ChunkedDirectoryHierarchyQueryMixin, LocalFetchMixin, DataSourceBase
    ):
    """DataSource for dealing data in a regular directory hierarchy on a 
    locally mounted filesystem. Assumes data for each variable may be split into
    several files according to date, with the dates present in their filenames.
    """
    def __init__(self, case_dict):
        self.catalog = None
        super(ChunkedLocalFileDataSource, self).__init__(case_dict)


# IMPLEMENTATION CLASSES ======================================================

ignore_non_nc_regex = util.RegexPattern(r".*(?<!\.nc)")
sample_data_regex = util.RegexPattern(
    r"""
        (?P<sample_dataset>\S+)/    # first directory: model name
        (?P<frequency>\w+)/         # subdirectory: data frequency
        # file name = model name + variable name + frequency
        (?P=sample_dataset)\.(?P<variable>\w+)\.(?P=frequency)\.nc
    """,
    input_field="remote_path",
    match_error_filter=ignore_non_nc_regex
)
@util.regex_dataclass(sample_data_regex)
@util.mdtf_dataclass
class SampleDataFile():
    """Dataclass describing catalog entries for sample model data files.
    """
    sample_dataset: str = util.MANDATORY
    frequency: datelabel.DateFrequency = util.MANDATORY
    variable: str = util.MANDATORY
    remote_path: str = util.MANDATORY

    # map "name" field in VarlistEntry's query_attrs() to "variable" field here
    _query_attrs_synonyms = {'name': 'variable'}

@util.mdtf_dataclass
class SampleDataAttributes(DataSourceAttributesBase):
    """Data-source-specific attributes for the DataSource providing sample model
    data.
    """
    MODEL_DATA_ROOT: str = ""
    sample_dataset: str = ""

    def __post_init__(self):
        """Validate user input.
        """
        super(SampleDataAttributes, self).__post_init__()
        config = core.ConfigManager()
        paths = core.PathManager()
        # set MODEL_DATA_ROOT
        if not self.MODEL_DATA_ROOT:
            self.MODEL_DATA_ROOT = getattr(paths, 'MODEL_DATA_ROOT', None)
        if not self.MODEL_DATA_ROOT and config.CASE_ROOT_DIR:
            _log.debug(
                "MODEL_DATA_ROOT not supplied, using CASE_ROOT_DIR = '%s'.",
                config.CASE_ROOT_DIR
            )
            self.MODEL_DATA_ROOT = config.CASE_ROOT_DIR
        # set sample_dataset
        if not self.sample_dataset and self.CASENAME:
            _log.debug(
                "sample_dataset not supplied, using CASENAME = '%s'.",
                self.CASENAME
            )
            self.sample_dataset = self.CASENAME

        # verify data exists
        if not os.path.isdir(self.MODEL_DATA_ROOT):
            _log.critical("Data directory MODEL_DATA_ROOT = '%s' not found.",
                self.MODEL_DATA_ROOT)
            exit(1)
        if not os.path.isdir(
            os.path.join(self.MODEL_DATA_ROOT, self.sample_dataset)
        ):
            _log.critical(
                "Sample dataset '%s' not found in MODEL_DATA_ROOT = '%s'.",
                self.sample_dataset, self.MODEL_DATA_ROOT)
            exit(1)


class SampleDataDataSource(SingleLocalFileDataSource):
    """DataSource for handling POD sample model data stored on a local filesystem.
    """
    _FileRegexClass = SampleDataFile
    _AttributesClass = SampleDataAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = preprocessor.SampleDataPreprocessor

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'MODEL_DATA_ROOT'))
        return self.attrs.MODEL_DATA_ROOT

# ----------------------------------------------------------------------------

@util.mdtf_dataclass
class CMIP6DataSourceAttributes():
    MODEL_DATA_ROOT: str = ""
    activity_id: str = ""
    institution_id: str = ""
    source_id: str = ""
    experiment_id: str = ""
    member_id: str = ""
    grid_label: str = ""
    version_date: str = ""

    def __post_init__(self):
        config = core.ConfigManager()
        paths = core.PathManager()
        if not self.MODEL_DATA_ROOT:
            self.MODEL_DATA_ROOT = getattr(paths, 'MODEL_DATA_ROOT', None)
        if not self.MODEL_DATA_ROOT and config.CASE_ROOT_DIR:
            _log.debug(
                "MODEL_DATA_ROOT not supplied, using CASE_ROOT_DIR = '%s'.",
                config.CASE_ROOT_DIR
            )
            self.MODEL_DATA_ROOT = config.CASE_ROOT_DIR

        cmip = cmip6.CMIP6_CVs()
        for field_name, val in dataclasses.asdict(self).items():
            if field_name in ('version_date', 'member_id'):
                continue
            if val and not cmip.is_in_cv(field_name, val):
                _log.error(("Supplied value '%s' for '%s' is not recognized by "
                    "the CMIP6 CV. Continuing, but queries will probably fail."),
                    val, field_name)
        # try to infer values:
        # cmip.lookup_single(self, 'experiment_id', 'activity_id')
        # cmip.lookup_single(self, 'source_id', 'institution_id')
        # bail out if we're in strict mode with undetermined fields


class CMIP6LocalDataSource(ChunkedLocalFileDataSource):
    """DataSource for handling model data named following the CMIP6 DRS and 
    stored on a local filesystem.
    """
    _FileRegexClass = cmip6.CMIP6_DRSPath
    _AttributesClass = CMIP6DataSourceAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = preprocessor.MDTFDataPreprocessor

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'MODEL_DATA_ROOT'))
        return self.attrs.MODEL_DATA_ROOT
