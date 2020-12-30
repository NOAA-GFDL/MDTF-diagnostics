"""Classes for querying, fetching and preprocessing model data requested by the
PODs.
"""
import os
import abc
import collections
import dataclasses
import itertools
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
    def iter_data_keys(self, var):
        """Generator iterating over the data_keys (query results) for var 
        corresponding to the selected experiment (assumed set in DataSource 
        instance's state)."""
        pass

    @abc.abstractmethod
    def remote_data(self, data_key):
        """Translates between data_keys (output of query_data) and paths, urls, 
        etc. (input to fetch_data.)"""
        pass

    def setup_query(self):
        """Called once, before the iterative query_and_fetch() process starts.
        Use to, eg, initialize database or remote filesystem connections.
        """
        pass

    def pre_query_hook(self, vars):
        """Called before querying the presence of a new batch of variables."""
        pass

    def set_experiment(self):
        """Called after querying the presence of a new batch of variables, to 
        filter or otherwise ensure that the returned remote_data for *all* 
        variables comes from the same experimental run of the model."""
        pass

    def post_query_hook(self, vars):
        """Called after select_experiment(), after each query of a new batch of 
        variables."""
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

    def pre_fetch_hook(self, vars):
        """Called before fetching each batch of query results."""
        pass

    def post_fetch_hook(self, vars):
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
    def iter_data_keys(self, var):
        """Generator iterating over the data_keys (query results) for var 
        corresponding to the selected experiment (assumed set in DataSource 
        instance's state)."""
        pass

    @abc.abstractmethod
    def remote_data(self, data_key):
        """Translates between data_keys (output of query_data) and paths, urls, 
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

    def pre_query_hook(self, vars):
        """Called before querying the presence of a new batch of variables."""
        pass

    def pre_fetch_hook(self, vars):
        """Called before fetching each batch of query results."""
        pass

    def set_experiment(self):
        """Called after querying the presence of a new batch of variables, to 
        filter or otherwise ensure that the returned remote_data for *all* 
        variables comes from the same experimental run of the model."""
        pass

    def post_query_hook(self, vars):
        """Called after select_experiment(), after each query of a new batch of 
        variables."""
        pass

    def post_fetch_hook(self, vars):
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

FetchStatus = util.MDTFEnum(
    'FetchStatus', 'NOT_FETCHED SUCCEEDED FAILED', module=__name__
)

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
        self._id = 0
        self.id_number = itertools.count(start=1) # IDs for PODs, vars
        self.strict = config.get('strict', False)
        self.attrs = util.coerce_to_dataclass(case_dict, self._AttributesClass)
        self.pods = case_dict.get('pod_list', [])
        # data_key -> FetchStatus
        self.fetch_status = collections.defaultdict((lambda: FetchStatus.NOT_FETCHED))
        self.exceptions = util.ExceptionQueue()

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

        print('####################\nDEBUG varlist: ')
        for v in self.iter_vars(active=None, active_pods=None):
            v.print_debug()
        print('####################')

    def setup_pod(self, pod):
        """Update POD with information that only becomes available after 
        DataManager and Diagnostic have been configured (ie, only known at 
        runtime, not from settings.jsonc.)

        Could arguably be moved into Diagnostic's init, at the cost of 
        dependency inversion.
        """
        pod._id = next(self.id_number)
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
                        f"Caught exception when configuring <{v.full_name}>.") from exc
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
        v._id = next(self.id_number)
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
            
            self.pre_query_hook(vars_to_query)
            for var in vars_to_query:
                try:
                    _log.info("    Querying <%s>", var.short_format())
                    # add before query, in case query raises an exc
                    var.status = diagnostic.VarlistEntryStatus.QUERIED
                    self.query_dataset(var) # sets var.remote_data
                    if not var.remote_data:
                        raise AssertionError("No data found by query.")
                except Exception as exc:
                    update = True
                    if not isinstance(exc, util.DataQueryError):
                        _log.exception("Caught exception querying <%s>: %s",
                            var.short_format(), repr(exc))
                    try:
                        raise util.DataQueryError(var, (f"Caught exception while "
                            f"querying data for <{var.full_name}>.")) from exc
                    except Exception as chained_exc:
                        var.deactivate(chained_exc)
                    continue
            try:
                self.set_experiment()
                self.post_query_hook(vars_to_query)
            except Exception as exc:
                _log.exception("Caught exception setting experiment: %s", repr(exc))
                raise exc
        else:
            # only hit this if we don't break
            raise util.DataQueryError(None,
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

            self.pre_fetch_hook(vars_to_fetch)
            for var in vars_to_fetch:
                try:
                    _log.info("    Fetching <%s>", var.short_format())
                    # add before fetch, in case fetch raises an exc
                    var.status = diagnostic.VarlistEntryStatus.FETCHED
                    for data_key in self.iter_data_keys(var):
                        if self.fetch_status[data_key] != FetchStatus.NOT_FETCHED:
                            continue
                        self.fetch_status[data_key] = FetchStatus.FAILED
                        self.fetch_dataset(var, self.remote_data(data_key))
                        self.fetch_status[data_key] = FetchStatus.SUCCEEDED
                    if not all(self.fetch_status[dk] == FetchStatus.SUCCEEDED \
                        for dk in self.iter_data_keys(var)):
                        raise AssertionError('Unreported fetch failure.')
                except Exception as exc:
                    update = True
                    if not isinstance(exc, util.DataFetchError):
                        _log.exception("Caught exception fetching <%s>: %s",
                            var.short_format(), repr(exc))
                    try:
                        raise util.DataFetchError(var, ("Caught exception while "
                            f"fetching data for <{var.full_name}>.")) from exc
                    except Exception as chained_exc:
                        var.deactivate(chained_exc)
                    continue
            self.post_fetch_hook(vars_to_fetch)
        else:
            # only hit this if we don't break
            raise util.DataFetchError(None, 
                f"Too many iterations in {self.__class__.__name__}.fetch_data()."
            )

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
                    if not isinstance(exc, util.DataPreprocessError):
                        _log.exception("Caught exception processing %s: %s",
                            var.short_format(), repr(exc))
                    try:
                        raise util.DataPreprocessError(var, ("Caught exception "
                            f"while processing data for <{var.full_name}>.")) from exc
                    except Exception as chained_exc:
                        var.deactivate(chained_exc)
                    continue
        else:
            # only hit this if we don't break
            raise util.DataPreprocessError(None, 
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
            _log.exception(f"Caught DataSource-level exception: {repr(exc)}.")
            self.exceptions.log(exc)
            self.deactivate_if_failed()
        # clean up regardless of success/fail
        self.post_query_and_fetch_hook()

    def query_and_fetch_cleanup(self, signum=None, frame=None):
        """Called if framework is terminated abnormally. Not called during
        normal exit.
        """
        util.signal_logger(self.__class__.__name__, signum, frame)
        self.post_query_and_fetch_hook()

# --------------------------------------------------------------------------

class DataframeQueryDataSource(DataSourceBase, metaclass=util.MDTFABCMeta):
    """DataSource which queries a data catalog made available as a pandas 
    DataFrame, and includes logic for selecting experiment based on column values.

    .. note::
       This implementation assumes the catalog is static and locally loaded into
       memory. (I think) the only source of this limitation is the fact that it 
       uses values of the DataFrame's Index as its data_keys, instead of storing
       the complete row contents, so this limitation could be lifted if needed.

       TODO: integrate better with general Intake API.
    """
    def __init__(self, case_dict):
        super(DataframeQueryDataSource, self).__init__(case_dict)
        self.expt_keys = dict() # _id -> expt_key tuple

    @property
    @abc.abstractmethod
    def df(self):
        """Synonym for the DataFrame containing the catalog."""
        pass

    # Name of the column in the catalog containing the location (eg, the path)
    # of the data for that row.
    remote_data_col = util.abstract_attribute()

    # column of the DataFrame containing datelabel.DateRange objects 
    # If 'None', date range selection logic is skipped.
    # TODO: generate DateRange from start/end date columns
    daterange_col = None

    @property
    def has_date_info(self):
        return (self.daterange_col is not None)

    # Catalog columns whose values must be the same for all varaibles being
    # fetched. This is the most common sense in which we "specify an experiment."
    expt_cols = util.abstract_attribute()

    # Catalog columns whose values must be the same for each POD, but may differ
    # between PODs. An example could be spatial grid resolution.
    pod_expt_cols = tuple()

    # Catalog columns whose values must "be the same for each variable", ie are 
    # irrelevant differences for our purposes but must be constrained to a 
    # unique value. An example is the CMIP6 MIP table: the same variable can 
    # appear in multiple MIP tables, but the choice of table isn't relvant for PODs.
    var_expt_cols = tuple()

    @property
    def all_expt_cols(self):
        """Columns of the DataFrame specifying the experiment. We assume that 
        specifying a valid value for each of the columns in this set uniquely 
        identifies an experiment. 
        """
        return tuple(set(self.expt_cols + self.pod_expt_cols + self.var_expt_cols))

    @property
    def all_columns(self):
        return tuple(self.df.columns)

    def _query_clause(self, col_name, k, v):
        """Translate a single field value into a logical clause in the dataframe
        catalog query. All queryable field values are assumed to be attribute
        values on a local variable named _dict_var_name.
        """
        _dict_var_name = 'd'
        if v == util.NOTSET:
            return ""
        elif v is None:
            # In pandas filtering, ==, != fail on None; should convert Nones to np.nans
            return f"({col_name}.isnull())"
        if isinstance(v, datelabel.DateRange):
            # return files having any date range overlap at all
            return f"({col_name} in @{_dict_var_name}.{k})"
        elif k == 'max_frequency':
            return f"({col_name} <= @{_dict_var_name}.frequency)"
        elif k == 'max_frequency':
            return f"({col_name} <= @{_dict_var_name}.frequency)"
        else:
            return f"({col_name} == @{_dict_var_name}.{k})"

    def _query_catalog(self, var):
        """Construct and execute the query to determine whether data matching 
        var is present in the catalog.
        
        Split off logic done here to perform the query against the catalog 
        (returning a dataframe with results) from the processing of those 
        results, in order to simplify overriding by child classes.
        """
        def _filter_columns(obj):
            return {col: getattr(obj, col) for col in self.all_columns \
                if hasattr(obj, col)}

        query_d = util.WormDict()
        query_d.update(_filter_columns(self.attrs))
        query_d.update(_filter_columns(var.query_attrs))
        clauses = [self._query_clause(k, k, v) for k,v in query_d.items()]
        d = util.NameSpace.fromDict(query_d) # set local var for df.query()
        return self.df.query(' and '.join(clauses))

    def _experiment_key(self, df=None, idx=None, cols=None):
        """Returns tuple of string-valued keys for grouping files by experiment:
        (<values of case_expt_cols>, <values of pod_expt_cols>, 
        <values of var_expt_cols>).

        .. note::
           We can't just do a .groupby on column names, because pandas attempts 
           to coerce DateFrequency to a timedelta64, which overflows for static 
           DateFrequency. There doesn't seem to be a way to disable this type 
           coercion.
        """
        if df is None:        # df used when .apply()'ed across rows
            df = self.df
        if idx is not None:   # index used in groupby
            df = df.loc[idx]

        def _key_str(cols_):
            return '|'.join(str(df[c]) for c in cols_)

        if cols is None:
            # full key
            return tuple(_key_str(x) for x in \
                (self.expt_cols, self.pod_expt_cols, self.var_expt_cols))
        else:
            # computing one of the entries in the tuple
            return _key_str(cols)

    @staticmethod
    def _data_key(group_df):
        """Return tuple of row indices: this implementation's data_key."""
        return tuple(group_df.index.tolist())

    def _check_group_daterange(self, group_df):
        """Sort the files found for each experiment by date, verify that
        the date ranges contained in the files are contiguous in time and that
        the date range of the files spans the query date range.
        """
        if not self.has_date_info:
            return group_df

        data_key = self._data_key(group_df)
        try:
            sorted_df = group_df.sort_values(by=[self.daterange_col])
            # method throws ValueError if ranges aren't contiguous
            files_date_range = datelabel.DateRange.from_contiguous_span(
                *(sorted_df[self.daterange_col].to_list())
            )
            # throws AssertionError if we don't span the query range
            assert files_date_range.contains(self.attrs.date_range)
            return sorted_df
        except ValueError:
            self._query_error_logger(
                "Noncontiguous or malformed date range in files:", data_key
            )
        except AssertionError:
            self._query_error_logger(
                f"Returned files don't span query date range ({self.attrs.date_range}):",
                data_key
            )
        except Exception as exc:
            self._query_error_logger(f"Caught exception {repr(exc)}:", data_key)
        # hit an exception; return empty DataFrame to signify failure
        return pd.DataFrame(columns=group_df.columns)

    def _query_group_hook(self, group_df):
        """Additional filtering to do on query results for a single experiment,
        for use by child classes.
        """
        return group_df

    def query_dataset(self, var):
        """Find all rows of the catalog matching relevant attributes of the 
        DataSource and of the variable. Group these by experiments, and for each
        experiment obtain the row indices in the the catalog DataFrame (the 
        data_key for this query implementation) and store it in var's remote_data 
        attribute. Specifically, the remote_data attribute is a dict mapping
        experiments (labeled by experiment_keys) to data found for that variable
        by this query (labeled by the data_keys).
        """
        query_df = self._query_catalog(var)
        # assign set of sets of catalog row indices to var's remote_data attr
        # filter out empty entries = queries that failed.
        expt_groups = query_df.groupby(
            by=(lambda idx: self._experiment_key(query_df, idx))
        )
        var.remote_data = util.WormDict()
        for expt_key, group in expt_groups:
            group = group.apply(self._check_group_daterange)
            if group.empty:
                continue
            group = group.apply(self._query_group_hook)
            if group.empty:
                continue
            data_key = self._data_key(group)
            _log.debug('Query found <expt_key=%s, data_key=%s> for <%s>',
                expt_key, data_key, var.full_name)
            var.remote_data[expt_key] = data_key

    def _query_error_logger(self, msg, data_key):
        """Log debugging message or raise an exception, depending on if we're
        in strict mode.
        """
        data_key = util.to_iter(data_key, list)
        err_str = '\n'.join(
            str(self.df.loc[idx].to_dict()) for idx in data_key
        )
        err_str = msg + '\n' + err_str
        if self.strict:
            raise util.DataQueryError(data_key, err_str)
        else:
            _log.warning(err_str)

    # --------------------------------------------------------------

    _expt_key_col = 'expt_key'

    def _expt_df(self, obj, cols, parent_id=None):
        """Return a DataFrame of partial experiment attributes (as determined by
        cols) that are shared by the query results of all variables covered by
        var_iterator.
        """
        cols = list(cols) # DataFrame requires list
        if not cols:
            # short-circuit construction for trivial case (empty key)
            return pd.DataFrame({self._expt_key_col: [""]}, dtype='object')

        expt_df = None
        if parent_id is None:
            parent_key = tuple()
        else:
            parent_key = self.expt_keys[parent_id]
        if hasattr(obj, 'iter_vars'):
            var_iterator = obj.iter_vars(active=True)
        else:
            assert isinstance(obj, diagnostic.VarlistEntry)
            var_iterator = tuple(obj)

        for v in var_iterator:
            if v.status < diagnostic.VarlistEntryStatus.QUERIED:
                continue
            rows = set([])
            for expt_key, data_key in v.remote_data.items():
                # filter variables on the basis of previously selected expt 
                # attributes
                if expt_key[:len(parent_key)] == parent_key:
                    rows.update(data_key)
            v_expt_df = self.df[cols].loc[list(rows)].drop_duplicates()
            v_expt_df[self._expt_key_col] = v_expt_df.apply(
                (lambda df: self._experiment_key(df, idx=None, cols=cols)), axis=1)
            if v_expt_df.empty:
                # should never get here
                raise util.DataExperimentError(v, ("No choices of experiment "
                    f"attributes for <{v.full_name}> in {obj.name}."))

            # take intersection with possible values for other vars
            if expt_df is None:
                expt_df = v_expt_df.copy()
            else:
                expt_df = pd.merge(
                    expt_df, v_expt_df, 
                    how='inner', on=self._expt_key_col, sort=False, validate='1:1'
                )
            if expt_df.empty:
                raise util.DataExperimentError(v, ("Eliminated all choices of "
                    f"experiment attributes for {obj.name} when adding <{v.full_name}>."))
        return expt_df

    def _set_expt_key(self, obj, expt_df_cols, resolve_func, parent_id=None):
        """Set experiment attributes at the case, pod or variable level. Given obj,
        construct a DataFrame of epxeriment attributes that are found in the 
        queried data for all variables in obj. If more than one choice of 
        experiment is possible, call DataSource-specific heuristics in resolve_func
        to choose between them. 
        """
        expt_df = self._expt_df(obj, expt_df_cols, parent_id)
        
        if len(expt_df) > 1:
            if self.strict:
                raise util.DataExperimentError(None, (f"Experiment for {obj.name} "
                    "not uniquely specified by user input in strict mode."))
            else:
                expt_df = resolve_func(expt_df, obj)
        if expt_df.empty:
            raise util.DataExperimentError(None, ("Eliminated all consistent "
                f"choices of experiment for {obj.name}."))
        elif len(expt_df) > 1:  
            raise util.DataExperimentError(None, (f"Experiment for {obj.name} "
                "not uniquely specified by user input."))
        # successful exit: we've narrowed down the experiment to a single value
        
        expt_key = (expt_df[self._expt_key_col].iloc[0], )
        if parent_id is not None:
            expt_key = self.expt_keys[parent_id] + expt_key
        _log.debug("Setting experiment_key for %s to %s", obj.name, expt_key)
        self.expt_keys[obj._id] = expt_key

    def set_experiment(self):
        """Ensure that all data we're about to fetch comes from the same experiment.
        If data from multiple experiments was returned by the query that just
        finished, either employ data source-specific heuristics to select one
        or return an error. 
        """
        # set attributes that must be the same for all variables
        self._set_expt_key(self, self.expt_cols, self.resolve_expt)
        for p in self.iter_pods(active=True):
            # set attributes that must be the same for all variables in each POD
            self._set_expt_key(p, self.pod_expt_cols, self.resolve_pod_expt, self._id)
        for p, v in self.iter_pod_vars(active=True):
            # resolve irrelevant attributes
            self._set_expt_key(v, self.var_expt_cols, self.resolve_var_expt, p._id)
        
    def resolve_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be 
        specified by child classes.
        """
        return expt_df

    def resolve_pod_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be 
        specified by child classes.
        """
        return expt_df

    def resolve_var_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be 
        specified by child classes.
        """
        return expt_df

    def iter_data_keys(self, var):
        expt_key = self.expt_keys[var._id]
        yield from var.remote_data[expt_key]
  
    def remote_data(self, data_key):
        """Given one or more row indices in the catalog's dataframe (data_keys, 
        as found by query_dataset()), return the corresponding remote_paths.
        """
        if util.is_iterable(data_key):
            # iloc requires list, not just iterable
            data_key = util.to_iter(data_key, list) 
        return self.df[self.remote_data_col].loc[data_key]


class OnTheFlyDirectoryHierarchyQueryMixin(metaclass=util.MDTFABCMeta):
    """Mixin that creates an intake_esm.esm_datastore catalog by crawling a 
    directory hierarchy and populating catalog entry attributes
    by running a regex against the paths of files in the directory hierarchy.

    .. note::
       At time of writing, the `filename parsing 
       <https://www.anaconda.com/blog/intake-parsing-data-from-filenames-and-paths>`__
       functionality included in `intake <https://intake.readthedocs.io/en/latest/index.html>`__
       is too limited to correctly parse our use cases, which is why we use the 
       :class:`~src.util.RegexPattern` class instead.
    """
    # root directory to begin crawling at:
    CATALOG_DIR = util.abstract_attribute()
    # regex to use to generate catalog entries from relative paths:
    _FileRegexClass = util.abstract_attribute()
    _asset_file_format = "netcdf"

    @property
    def df(self):
        assert (hasattr(self, 'catalog') and hasattr(self.catalog, 'df'))
        return self.catalog.df

    @property
    def remote_data_col(self):
        """Name of the column in the catalog containing the path to the remote 
        data file.
        """
        return self._FileRegexClass._pattern.input_field

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
                    _log.info("Couldn't parse path %s", path[len(root_dir):])
                    continue
                
    def _dummy_esmcol_spec(self):
        """Dummy specification dict that enables us to use intake_esm's 
        machinery. The catalog is temporary and not retained after the code
        finishes running.
        """
        data_cols = list(self._FileRegexClass._pattern.fields)
        data_cols.remove(self.remote_data_col)
        # no aggregations, since for now we want to manually insert logic for
        # file fetching (& error handling etc.) before we load an xarray Dataset.
        return {
            "esmcat_version": "0.1.0",
            "id": "MDTF_" + self.__class__.__name__,
            "description": "",
            "attributes": [
                {"column_name":c, "vocabulary": ""} for c in data_cols
            ],
            "assets": {
                "column_name": self.remote_data_col,
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

    def _query_catalog(self, var):
        """Construct and execute the query to determine whether data matching 
        var is present in the catalog.
        
        Split off logic done here to perform the query against the catalog 
        (returning a dataframe with results) from the processing of those 
        results, in order to simplify overriding by child classes.
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
                    f"Fetch <{var.full_name}>: File not found at {path}.")
            else:
                _log.debug(f'Fetch <{var.full_name}>: found {path}.')
        var.local_data.extend(paths)


class LocalFileDataSource(
    OnTheFlyDirectoryHierarchyQueryMixin, LocalFetchMixin, DataframeQueryDataSource
):
    """DataSource for dealing data in a regular directory hierarchy on a 
    locally mounted filesystem. Assumes data for each variable may be split into
    several files according to date, with the dates present in their filenames.
    """
    def __init__(self, case_dict):
        self.catalog = None
        super(LocalFileDataSource, self).__init__(case_dict)


class SingleLocalFileDataSource(LocalFileDataSource):
    """DataSource for dealing data in a regular directory hierarchy on a 
    locally mounted filesystem. Assumes all data for each variable (in each 
    experiment) is contained in a single file.
    """
    def query_dataset(self, var):
        """Verify that only a single file was found from each experiment.
        """
        super(SingleLocalFileDataSource, self).query_dataset(var)
        for data_key in var.remote_data.values():
            if len(data_key) != 1:
                self._query_error_logger(
                    "Query found multiple files when one was expected:", data_key
                )

    def remote_data(self, data_key):
        """Verify that only a single file is being requested.
        (Should be unnecessary given constraint enforced in _group_query_results, 
        but check here just to be safe.)
        """
        if util.is_iterable(data_key) and len(data_key) != 1:
            self._query_error_logger(
                "Requested multiple files when one was expected:", data_key
            )
        return super(SingleLocalFileDataSource, self).remote_data(data_key)


# IMPLEMENTATION CLASSES ======================================================

# RegexPattern that matches any string (path) that doesn't end with ".nc".
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

        # verify model data root dir exists
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


class SampleLocalFileDataSource(SingleLocalFileDataSource):
    """DataSource for handling POD sample model data stored on a local filesystem.
    """
    _FileRegexClass = SampleDataFile
    _AttributesClass = SampleDataAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = preprocessor.SampleDataPreprocessor

    expt_cols = ("sample_dataset", )

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'MODEL_DATA_ROOT'))
        return self.attrs.MODEL_DATA_ROOT

# ----------------------------------------------------------------------------

@util.regex_dataclass(cmip6.drs_path_regex)
@util.mdtf_dataclass
class CMIP6DataSourceFile(cmip6.CMIP6_DRSPath):
    """Dataclass which represents and parses a full CMIP6 DRS path.
    """
    # map "name" field in VarlistEntry's query_attrs() to "variable_id" field here
    _query_attrs_synonyms = {'name': 'variable_id'}

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
        cv = cmip6.CMIP6_CVs()

        def _init_x_from_y(source, dest):
            if not getattr(self, dest, ""):
                try:
                    source_val = getattr(self, source, "")
                    if not source_val:
                        raise KeyError()
                    dest_val = cv.lookup_single(source_val, source, dest)
                    _log.debug("Set %s='%s' based on %s='%s'.", 
                        dest, dest_val, source, source_val)
                    setattr(self, dest, dest_val)
                except KeyError:
                    _log.debug("Couldn't set %s from %s='%s'.", 
                        dest, source, source_val)
                    setattr(self, dest, "")
                    
        if not self.MODEL_DATA_ROOT:
            self.MODEL_DATA_ROOT = getattr(paths, 'MODEL_DATA_ROOT', None)
        if not self.MODEL_DATA_ROOT and config.CASE_ROOT_DIR:
            _log.debug(
                "MODEL_DATA_ROOT not supplied, using CASE_ROOT_DIR = '%s'.",
                config.CASE_ROOT_DIR
            )
            self.MODEL_DATA_ROOT = config.CASE_ROOT_DIR
        # verify model data root dir exists
        if not os.path.isdir(self.MODEL_DATA_ROOT):
            _log.critical("Data directory MODEL_DATA_ROOT = '%s' not found.",
                self.MODEL_DATA_ROOT)
            exit(1)

        # validate non-empty field values
        for field_name, val in dataclasses.asdict(self).items():
            if field_name in ('version_date', 'member_id'):
                continue
            if val and not cv.is_in_cv(field_name, val):
                _log.error(("Supplied value '%s' for '%s' is not recognized by "
                    "the CMIP6 CV. Continuing, but queries will probably fail."),
                    val, field_name)
        # currently no inter-field consistency checks: happens implicitly, since
        # set_experiment will find zero experiments.

        # Attempt to determine first few fields of DRS, to avoid having to crawl
        # entire DRS structure
        _init_x_from_y('experiment_id', 'activity_id')
        _init_x_from_y('source_id', 'institution_id')
        _init_x_from_y('institution_id', 'source_id')
        # TODO: multi-column lookups
        # set MODEL_DATA_ROOT to be further down the hierarchy if possible, to
        # avoid having to crawl entire DRS strcture
        new_root = self.MODEL_DATA_ROOT
        for drs_dir in ("activity_id", "institution_id", "source_id", "experiment_id"):
            if not getattr(self, drs_dir, ""):
                break
            new_root = os.path.join(new_root, drs_dir)
        if not os.path.isdir(new_root):
            _log.error("Data directory '%s' not found; reverting to '%s'.",
                new_root, self.MODEL_DATA_ROOT)
        else:
            self.MODEL_DATA_ROOT = new_root


class CMIP6LocalFileDataSource(LocalFileDataSource):
    """DataSource for handling model data named following the CMIP6 DRS and 
    stored on a local filesystem.
    """
    _FileRegexClass = CMIP6DataSourceFile
    _AttributesClass = CMIP6DataSourceAttributes
    _DiagnosticClass = diagnostic.Diagnostic
    _PreprocessorClass = preprocessor.MDTFDataPreprocessor

    daterange_col = "date_range"
    # Catalog columns whose values must be the same for all variables.
    expt_cols = (
        "activity_id", "institution_id", "source_id", "experiment_id",
        "member_id", "version_date",
        # derived columns
        "region", "spatial_avg", 'realization_index', 'initialization_index', 
        'physics_index', 'forcing_index'
    )
    # Catalog columns whose values must be the same for each POD.
    pod_expt_cols = ('grid_label',
        # derived columns
        'regrid', 'grid_number'
    )
    # Catalog columns whose values must "be the same for each variable", ie are 
    # irrelevant but must be constrained to a unique value.
    var_expt_cols = ("table_id", )

    @property
    def CATALOG_DIR(self):
        assert (hasattr(self, 'attrs') and hasattr(self.attrs, 'MODEL_DATA_ROOT'))
        return self.attrs.MODEL_DATA_ROOT

    @staticmethod
    def _filter_column(df, col_name, func, obj_name):
        values = list(df[col_name].drop_duplicates())
        if len(values) <= 1:
            # unique value, no need to filter
            return df
        if msg is None:
            msg = ""
        filter_val = func(values)
        _log.debug("Selected experiment attribute %s='%s' for %s (out of %s).", 
            col_name, filter_val, obj_name, values)
        return df[df[col_name] == filter_val]

    def _filter_column_min(self, df, obj_name, *col_names):
        for c in col_names:
            df = self._filter_column(df, c, min, obj_name=obj_name)
        return df

    def _filter_column_max(self, df, obj_name, *col_names):
        for c in col_names:
            df = self._filter_column(df, c, max, obj_name=obj_name)
        return df

    def resolve_expt(self, df, obj):
        # No POD currently makes use of spatially averaged or subsetted data
        df = df[(df['region'].isnull()) & (df['spatial_avg'].isnull())]

        # If multiple ensemble/forcing members, choose lowest-numbered one
        df = self._filter_column_min(df, obj.name,
            'realization_index', 'initialization_index', 'physics_index', 'forcing_index'
        )
        # use most recent version_date
        df = self._filter_column_max(df, obj.name, 'version_date')
        return df

    def resolve_pod_expt(self, df, obj):
        # prefer regridded data
        if any(df['regrid'] == 'r'):
            df = df[df['regrid'] == 'r']
        # if multiple regriddings, choose the lowest-numbered one
        df = self._filter_column_min(df, obj.name, 'grid_number')
        return df

    def resolve_var_expt(self, df, obj):
        # TODO: minimize number of MIP tables
        col_name = 'table_id'
        filter_val = df[col_name].iloc[0]
        _log.debug("Selected experiment attribute %s='%s' for %s.", 
            col_name, filter_val, obj.name)
        return df.iloc[0]

