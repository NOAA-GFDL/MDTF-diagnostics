"""Base classes implementing logic for querying, fetching and preprocessing
model data requested by the PODs; see :doc:`fmwk_datasources`.
"""
import os
import abc
import collections
import dataclasses as dc
import glob
import signal
import textwrap
import typing
from src import util, core, diagnostic, xr_parser, preprocessor
import pandas as pd
import intake_esm

import logging
_log = logging.getLogger(__name__)

class AbstractQueryMixin(abc.ABC):
    @abc.abstractmethod
    def query_dataset(self, var):
        """Sets *data* attribute on var or raises an exception."""
        pass

    def setup_query(self):
        """Called once, before the iterative :meth:`~DataSourceBase.request_data` process starts.
        Use to, eg, initialize database or remote filesystem connections.
        """
        pass

    def pre_query_hook(self, vars):
        """Called before querying the presence of a new batch of variables."""
        pass

    def set_experiment(self):
        """Called after querying the presence of a new batch of variables, to
        filter or otherwise ensure that the returned DataKeys for *all*
        variables comes from the same experimental run of the model, by setting
        the *status* attribute of those DataKeys to ACTIVE."""
        pass

    def post_query_hook(self, vars):
        """Called after select_experiment(), after each query of a new batch of
        variables."""
        pass

    def tear_down_query(self):
        """Called once, after the iterative :meth:`~DataSourceBase.request_data` process ends.
        Use to, eg, close database or remote filesystem connections.
        """
        pass

class AbstractFetchMixin(abc.ABC):
    @abc.abstractmethod
    def fetch_dataset(self, var, data_key):
        """Fetches data corresponding to *data_key*. Populates its *local_data*
        attribute with a list of identifiers for successfully fetched data
        (paths to locally downloaded copies of data).
        """
        pass

    def setup_fetch(self):
        """Called once, before the iterative :meth:`~DataSourceBase.request_data` process starts.
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
        """Called once, after the iterative :meth:`~DataSourceBase.request_data` process ends.
        Use to, eg, close database or remote filesystem connections.
        """
        pass

class AbstractDataSource(AbstractQueryMixin, AbstractFetchMixin,
    metaclass=util.MDTFABCMeta):
    @abc.abstractmethod
    def __init__(self, case_dict, parent):
        # sets signature of __init__ method
        pass

    def pre_query_and_fetch_hook(self):
        """Called once, before the iterative :meth:`~DataSourceBase.request_data` process starts.
        Use to, eg, initialize database or remote filesystem connections.
        """
        # call methods if we're using mixins; if not, child classes will override
        if hasattr(self, 'setup_query'):
            self.setup_query()
        if hasattr(self, 'setup_fetch'):
            self.setup_fetch()

    def post_query_and_fetch_hook(self):
        """Called once, after the iterative :meth:`~DataSourceBase.request_data` process ends.
        Use to, eg, close database or remote filesystem connections.
        """
        # call methods if we're using mixins; if not, child classes will override
        if hasattr(self, 'tear_down_query'):
            self.tear_down_query()
        if hasattr(self, 'tear_down_fetch'):
            self.tear_down_fetch()

# --------------------------------------------------------------------------

@util.mdtf_dataclass
class DataKeyBase(core.MDTFObjectBase, metaclass=util.MDTFABCMeta):
    # _id = util.MDTF_ID()           # fields inherited from core.MDTFObjectBase
    # name: str
    # _parent: object
    # log = util.MDTFObjectLogger
    # status: ObjectStatus
    name: str = dc.field(init=False)
    value: typing.Any = util.MANDATORY
    expt_key: typing.Any = None
    local_data: list = dc.field(default_factory=list, compare=False)

    def __post_init__(self):
        self.name = f"{self.__class__.__name__}_{self.value}"
        super(DataKeyBase, self).__post_init__()
        if self.status == core.ObjectStatus.NOTSET:
            self.status == core.ObjectStatus.INACTIVE

    @property
    def _log_name(self):
        # assign a unique log name through UUID; DataKey loggers sit in a
        # subtree of the DataSource logger distinct from the POD loggers
        return f"{self._parent._log_name}.{self.__class__.__name__}.{self._id._uuid}"

    @property
    def _children(self):
        """Iterable of child objects associated with this object."""
        return []

    # level at which to log deactivation events
    _deactivation_log_level = logging.INFO

    def __str__(self):
        if util.is_iterable(self.value):
            val_str = ', '.join(str(x) for x in self.value)
        else:
            val_str = str(self.value)
        return f"DataKey({val_str})"

    @abc.abstractmethod
    def remote_data(self):
        """Returns paths, urls, etc. to be used as input to a
        :meth:`~DataSourceBase.fetch_data` method to specify how this dataset is
        fetched.
        """
        pass

@util.mdtf_dataclass
class DataSourceAttributesBase():
    """Class defining attributes that any DataSource needs to specify:

    - *CASENAME*: User-supplied label to identify output of this run of the
      package.
    - *FIRSTYR*, *LASTYR*, *date_range*: Analysis period, specified as a closed
      interval (i.e. running from 1 Jan of FIRSTYR through 31 Dec of LASTYR).
    - *CASE_ROOT_DIR*: Root directory containing input model data. Different
      DataSources may interpret this differently.
    - *convention*: name of the variable naming convention used by the source of
      model data.
    """
    CASENAME: str = util.MANDATORY
    FIRSTYR: str = util.MANDATORY
    LASTYR: str = util.MANDATORY
    date_range: util.DateRange = dc.field(init=False)
    CASE_ROOT_DIR: str = ""
    convention: str = ""
    log: dc.InitVar = _log

    def _set_case_root_dir(self, log=_log):
        config = core.ConfigManager()
        if not self.CASE_ROOT_DIR and config.CASE_ROOT_DIR:
            log.debug("Using global CASE_ROOT_DIR = '%s'.", config.CASE_ROOT_DIR)
            self.CASE_ROOT_DIR = config.CASE_ROOT_DIR
        # verify case root dir exists
        if not os.path.isdir(self.CASE_ROOT_DIR):
            log.critical("Data directory CASE_ROOT_DIR = '%s' not found.",
                self.CASE_ROOT_DIR)
            util.exit_handler(code=1)

    def __post_init__(self, log=_log):
        self._set_case_root_dir(log=log)
        self.date_range = util.DateRange(self.FIRSTYR, self.LASTYR)


PodVarTuple = collections.namedtuple('PodVarTuple', ['pod', 'var'])
MAX_DATASOURCE_ITERS = 5

class DataSourceBase(core.MDTFObjectBase, util.CaseLoggerMixin,
    AbstractDataSource, metaclass=util.MDTFABCMeta):
    """Base class for handling the data needs of PODs. Executes query for
    requested model data against the remote data source, fetches the required
    data locally, preprocesses it, and performs cleanup/formatting of the POD's
    output.
    """
    _AttributesClass = util.abstract_attribute()
    _DiagnosticClass = util.abstract_attribute()
    _PreprocessorClass = preprocessor.DefaultPreprocessor
    _DataKeyClass = util.abstract_attribute()

    _deactivation_log_level = logging.ERROR # default log level for failure

    def __init__(self, case_dict, parent):
        # _id = util.MDTF_ID()        # attrs inherited from core.MDTFObjectBase
        # name: str
        # _parent: object
        # log = util.MDTFObjectLogger
        # status: ObjectStatus
        core.MDTFObjectBase.__init__(
            self, name=case_dict['CASENAME'], _parent=parent
        )
        # configure paths
        config = core.ConfigManager()
        paths = core.PathManager()
        self.overwrite = config.overwrite
        d = paths.model_paths(case_dict, overwrite=self.overwrite)
        self.code_root = paths.CODE_ROOT
        self.MODEL_DATA_DIR = d.MODEL_DATA_DIR
        self.MODEL_WK_DIR = d.MODEL_WK_DIR
        self.MODEL_OUT_DIR = d.MODEL_OUT_DIR
        util.check_dir(self, 'MODEL_WK_DIR', create=True)
        util.check_dir(self, 'MODEL_DATA_DIR', create=True)

        # set up log (CaseLoggerMixin)
        self.init_log(log_dir = self.MODEL_WK_DIR)

        self.strict = config.get('strict', False)
        self.attrs = util.coerce_to_dataclass(
            case_dict, self._AttributesClass, log=self.log, init=True
        )
        self.pods = dict.fromkeys(case_dict.get('pod_list', []))

        # set variable name convention
        translate = core.VariableTranslator()
        if hasattr(self, '_convention'):
            self.convention = self._convention
            if hasattr(self.attrs, 'convention') \
                and self.attrs.convention != self.convention:
                self.log.warning(f"{self.__class__.__name__} requires convention"
                    f"'{self.convention}'; ignoring argument "
                    f"'{self.attrs.convention}'.")
        elif hasattr(self.attrs, 'convention') and self.attrs.convention:
            self.convention = self.attrs.convention
        else:
            raise util.GenericDataSourceEvent((f"'convention' not configured "
                f"for {self.__class__.__name__}."))
        self.convention = translate.get_convention_name(self.convention)

        # configure case-specific env vars
        self.env_vars = util.WormDict.from_struct(
            config.global_env_vars.copy()
        )
        self.env_vars.update({
            k: case_dict[k] for k in ("CASENAME", "FIRSTYR", "LASTYR")
        })
        # add naming-convention-specific env vars
        convention_obj = translate.get_convention(self.convention)
        self.env_vars.update(getattr(convention_obj, 'env_vars', dict()))

    @property
    def full_name(self):
        return f"<#{self._id}:{self.name}>"

    @property
    def _children(self):
        """Iterable of child objects (:class:`~diagnostic.Diagnostic`\s)
        associated with this object.
        """
        return self.pods.values()

    def iter_vars(self, active=None, pod_active=None):
        """Iterator over all :class:`~diagnostic.VarlistEntry`\s (grandchildren)
        associated with this case. Returns :class:`PodVarTuple`\s (namedtuples)
        of the :class:`~diagnostic.Diagnostic` and :class:`~diagnostic.VarlistEntry`
        objects corresponding to the POD and its variable, respectively.

        Args:
            active: bool or None, default None. Selects subset of
                :class:`~diagnostic.VarlistEntry`\s which are returned in the
                namedtuples:

                - active = True: only iterate over currently active VarlistEntries.
                - active = False: only iterate over inactive VarlistEntries
                    (VarlistEntries which have either failed or are currently
                    unused alternate variables).
                - active = None: iterate over both active and inactive
                    VarlistEntries.

            pod_active: bool or None, default None. Same as *active*, but
                filtering the PODs that are selected.
        """
        def _get_kwargs(active_):
            if active_ is None:
                return {'status': None}
            if active_:
                return {'status': core.ObjectStatus.ACTIVE}
            else:
                return {'status_neq': core.ObjectStatus.ACTIVE}

        pod_kwargs = _get_kwargs(pod_active)
        var_kwargs = _get_kwargs(active)
        for p in self.iter_children(**pod_kwargs):
            for v in p.iter_children(**var_kwargs):
                yield PodVarTuple(pod=p, var=v)

    def iter_vars_only(self, active=None):
        """Convenience wrapper for :meth:`iter_vars` that returns only the
        :class:`~diagnostic.VarlistEntry` objects (grandchildren) from all PODs
        in this DataSource.
        """
        yield from (pv.var for pv in self.iter_vars(active=active, pod_active=None))

    # -------------------------------------

    def setup(self):
        for pod_name in self.pods:
            self.pods[pod_name] = \
                self._DiagnosticClass.from_config(pod_name, parent=self)
        for pod in self.iter_children():
            try:
                self.setup_pod(pod)
            except Exception as exc:
                chained_exc = util.chain_exc(exc, "setting up DataSource",
                    util.PodConfigError)
                pod.deactivate(chained_exc)
                continue

        if self.status == core.ObjectStatus.NOTSET and \
            any(p.status == core.ObjectStatus.ACTIVE for p in self.iter_children()):
            self.status = core.ObjectStatus.ACTIVE

        _log.debug('#' * 70)
        _log.debug('Pre-query varlists for %s:', self.full_name)
        for v in self.iter_vars_only(active=None):
            _log.debug("%s", v.debug_str())
        _log.debug('#' * 70)

    def setup_pod(self, pod):
        """Update POD with information that only becomes available after
        DataManager and Diagnostic have been configured (ie, only known at
        runtime, not from settings.jsonc.)

        Could arguably be moved into Diagnostic's init, at the cost of
        dependency inversion.
        """
        pod.setup(self)
        for v in pod.iter_children():
            try:
                self.setup_var(pod, v)
            except Exception as exc:
                chained_exc = util.chain_exc(exc, f"configuring {v.full_name}.",
                    util.PodConfigError)
                v.deactivate(chained_exc)
                continue
        # preprocessor will edit varlist alternates, depending on enabled functions
        pod.preprocessor = self._PreprocessorClass(self, pod)
        pod.preprocessor.edit_request(self, pod)

        for v in pod.iter_children():
            # deactivate failed variables, now that alternates are fully
            # specified
            if v.last_exception is not None and not v.failed:
                v.deactivate(v.last_exception, level=logging.WARNING)
        if pod.status == core.ObjectStatus.NOTSET and \
            any(v.status == core.ObjectStatus.ACTIVE for v in pod.iter_children()):
            pod.status = core.ObjectStatus.ACTIVE

    def setup_var(self, pod, v):
        """Update VarlistEntry fields with information that only becomes
        available after DataManager and Diagnostic have been configured (ie,
        only known at runtime, not from settings.jsonc.)

        Could arguably be moved into VarlistEntry's init, at the cost of
        dependency inversion.
        """
        translate = core.VariableTranslator().get_convention(self.convention)
        if v.T is not None:
            v.change_coord(
                'T',
                new_class = {
                    'self': diagnostic.VarlistTimeCoordinate,
                    'range': util.DateRange,
                    'frequency': util.DateFrequency
                },
                range=self.attrs.date_range,
                calendar=util.NOTSET,
                units=util.NOTSET
            )
        v.dest_path = self.variable_dest_path(pod, v)
        try:
            trans_v = translate.translate(v)
            v.translation = trans_v
            # copy preferred gfdl post-processing component during translation
            if hasattr(trans_v, "component"):
                v.component = trans_v.component
        except KeyError as exc:
            # can happen in normal operation (eg. precip flux vs. rate)
            chained_exc = util.PodConfigEvent((f"Deactivating {v.full_name} due to "
                f"variable name translation: {str(exc)}."))
            # store but don't deactivate, because preprocessor.edit_request()
            # may supply alternate variables
            v.log.store_exception(chained_exc)
        except Exception as exc:
            chained_exc = util.chain_exc(exc, f"translating name of {v.full_name}.",
                util.PodConfigError)
            # store but don't deactivate, because preprocessor.edit_request()
            # may supply alternate variables
            v.log.store_exception(chained_exc)

        v.stage = diagnostic.VarlistEntryStage.INITED

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

    def data_key(self, value, expt_key=None, status=None):
        """Constructor for an instance of :class:`DataKeyBase` that's used by
        this DataSource.
        """
        if status is None:
            status = core.ObjectStatus.NOTSET
        return self._DataKeyClass(
            _parent=self, value=value,
            expt_key=expt_key, status=status
        )

    def is_fetch_necessary(self, d_key, var=None):
        if len(d_key.local_data) > 0:
            self.log.debug("Already successfully fetched %s.", d_key)
            return False
        if d_key.failed:
            self.log.debug("%s failed; not retrying.", d_key)
            return False
        return True

    def child_deactivation_handler(self, child, child_exc):
        """When a DataKey (*child*) has been deactivated during query or fetch,
        log a message on all VarlistEntries using it, and deactivate any
        VarlistEntries with no remaining viable DataKeys.
        """
        if isinstance(child, diagnostic.Diagnostic):
            # DataSource has 2 types of children: PODs and DataKeys
            # only need to handle the latter here
            return

        for v in self.iter_vars_only(active=None):
            v.deactivate_data_key(child, child_exc)

    def query_data(self):
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(MAX_DATASOURCE_ITERS):
            vars_to_query = [
                v for v in self.iter_vars_only(active=True) \
                    if v.stage < diagnostic.VarlistEntryStage.QUERIED
            ]
            if not vars_to_query:
                break # exit: queried everything or nothing active

            self.log.debug('Query batch: [%s].',
                ', '.join(v.full_name for v in vars_to_query))
            self.pre_query_hook(vars_to_query)
            for v in vars_to_query:
                try:
                    self.log.info("Querying %s.", v.translation)
                    self.query_dataset(v) # sets v.data
                    if not v.data:
                        raise util.DataQueryEvent("No data found.", v)
                    v.stage = diagnostic.VarlistEntryStage.QUERIED
                except util.DataQueryEvent as exc:
                    v.deactivate(exc)
                    continue
                except Exception as exc:
                    chained_exc = util.chain_exc(exc,
                        f"querying {v.translation} for {v.full_name}.",
                        util.DataQueryEvent)
                    v.deactivate(chained_exc)
                    continue
            self.post_query_hook(vars_to_query)
        else:
            # only hit this if we don't break
            raise util.DataRequestError(
                f"Too many iterations in query_data() for {self.full_name}."
            )

    def select_data(self):
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(MAX_DATASOURCE_ITERS):
            if update:
                # query alternates for any vars that failed since last time
                self.query_data()
                update = False
            # this loop differs from the others in that logic isn't/can't be
            # done on a per-variable basis, so we just try to execute
            # set_experiment() successfully
            try:
                self.set_experiment()
                break # successful exit
            except util.DataExperimentEvent:
                # couldn't set consistent experiment attributes. Try again b/c
                # we've deactivated problematic pods/vars.
                update = True
            except Exception as exc:
                self.log.exception("%s while setting experiment: %r",
                    util.exc_descriptor(exc), exc)
                raise exc
        else:
            # only hit this if we don't break
            raise util.DataQueryEvent(
                f"Too many iterations in select_data() for {self.full_name}."
            )

    def fetch_data(self):
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(MAX_DATASOURCE_ITERS):
            if update:
                self.select_data()
                update = False
            vars_to_fetch = [
                v for v in self.iter_vars_only(active=True) \
                    if v.stage < diagnostic.VarlistEntryStage.FETCHED
            ]
            if not vars_to_fetch:
                break # exit: fetched everything or nothing active

            self.log.debug('Fetch batch: [%s].',
                ', '.join(v.full_name for v in vars_to_fetch))
            self.pre_fetch_hook(vars_to_fetch)
            for v in vars_to_fetch:
                try:
                    v.log.info("Fetching %s.", v)
                    # fetch on a per-DataKey basis
                    for d_key in v.iter_data_keys(status=core.ObjectStatus.ACTIVE):
                        try:
                            if not self.is_fetch_necessary(d_key):
                                continue
                            v.log.debug("Fetching %s.", d_key)
                            self.fetch_dataset(v, d_key)
                        except Exception as exc:
                            update = True
                            d_key.deactivate(exc)
                            break # no point continuing

                    # check if var received everything
                    for d_key in v.iter_data_keys(status=core.ObjectStatus.ACTIVE):
                        if not d_key.local_data:
                            raise util.DataFetchEvent("Fetch failed.", d_key)
                    v.stage = diagnostic.VarlistEntryStage.FETCHED
                except Exception as exc:
                    update = True
                    chained_exc = util.chain_exc(exc,
                        f"fetching data for {v.full_name}.",
                        util.DataFetchEvent)
                    v.deactivate(chained_exc)
                    continue
            self.post_fetch_hook(vars_to_fetch)
        else:
            # only hit this if we don't break
            raise util.DataRequestError(
                f"Too many iterations in fetch_data() for {self.full_name}."
            )

    def preprocess_data(self):
        """Hook to run the preprocessing function on all variables.
        """
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(MAX_DATASOURCE_ITERS):
            if update:
                # fetch alternates for any vars that failed since last time
                self.fetch_data()
                update = False
            vars_to_process = [
                pv for pv in self.iter_vars(active=True) \
                    if pv.var.stage < diagnostic.VarlistEntryStage.PREPROCESSED
            ]
            if not vars_to_process:
                break # exit: processed everything or nothing active

            for pod in self.iter_children(status=core.ObjectStatus.ACTIVE):
                pod.preprocessor.setup(self, pod)
            for pv in vars_to_process:
                try:
                    pv.var.log.info("Preprocessing %s.", pv.var)
                    pv.pod.preprocessor.process(pv.var)
                    pv.var.stage = diagnostic.VarlistEntryStage.PREPROCESSED
                except Exception as exc:
                    update = True
                    self.log.exception("%s while preprocessing %s: %r",
                        util.exc_descriptor(exc), pv.var.full_name, exc)
                    for d_key in pv.var.iter_data_keys(status=core.ObjectStatus.ACTIVE):
                        pv.var.deactivate_data_key(d_key, exc)
                    continue
        else:
            # only hit this if we don't break
            raise util.DataRequestError(
                f"Too many iterations in preprocess_data() for {self.full_name}."
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
            self.log.exception("%s at DataSource level: %r.",
                util.exc_descriptor(exc), exc)
        # clean up regardless of success/fail
        self.post_query_and_fetch_hook()
        for p in self.iter_children():
            for v in p.iter_children():
                if v.status == core.ObjectStatus.ACTIVE:
                    v.log.debug('Data request for %s completed succesfully.',
                        v.full_name)
                    v.status = core.ObjectStatus.SUCCEEDED
                elif v.failed:
                    v.log.debug('Data request for %s failed.', v.full_name)
                else:
                    v.log.debug('Data request for %s not used.', v.full_name)
            if p.failed:
                p.log.debug('Data request for %s failed.', p.full_name)
            else:
                p.log.debug('Data request for %s completed succesfully.',
                    p.full_name)

    def query_and_fetch_cleanup(self, signum=None, frame=None):
        """Called if framework is terminated abnormally. Not called during
        normal exit.
        """
        util.signal_logger(self.__class__.__name__, signum, frame, log=self.log)
        self.post_query_and_fetch_hook()
        util.exit_handler(code=1)

# --------------------------------------------------------------------------

class DataFrameDataKey(DataKeyBase):
    """:class:`DataKeyBase` for use with :class:`DataframeQueryDataSourceBase`
    and child classes. The *value*\s stored in the DataKey are row indices on the
    catalog DataFrame in the DataSource, and the *remote_data* method returns
    values from those rows from the column in the catalog containing the paths
    to remote data.

    .. note::
       Due to implementation, the catalog used by the DataSource must be static.
       This code could readily be adapted to a dynamic catalog if its schema
       provided a unique ID number for each row, to take the place of the row
       index used here.
    """
    def __post_init__(self):
        """*value* as passed to :class:`DataframeQueryDataSourceBase` will be the
        entire DataFrame corresponding to this group of catalog entries. Here
        we convert that to a tuple of row indices and store that instead.
        """
        self.value = tuple(self.value.index.tolist())
        super(DataFrameDataKey, self).__post_init__()

    def remote_data(self):
        """Returns paths, urls, etc. to be used as input to a *fetch_data* method
        to specify how this dataset is fetched.
        """
        # pd.DataFrame loc requires list, not just iterable
        idxs = list(self.value)
        return self._parent.df[self._parent.remote_data_col].loc[idxs]

class DataFrameQueryColumnGroup():
    """Class wrapping a set of catalog (DataFrame) column names used by
    :class:`DataframeQueryDataSourceBase` in selecting experiment attributes of
    a given scope (case-wide, pod-wide or var-wide).

    One component of :class:`DataframeQueryColumnSpec`.
    """
    def __init__(self, key_cols=None, derived_cols=None):
        if key_cols is None:
            self.key_cols = tuple()
        else:
            self.key_cols = tuple(util.to_iter(key_cols, coll_type=set))
        if derived_cols is None:
            self.cols = self.key_cols
        else:
            self.cols = tuple(set(
                self.key_cols + util.to_iter(derived_cols, coll_type=tuple)
            ))

    # hard-coded column name for DataSource-specific experiment identifier
    _expt_key_col = 'expt_key'

    def expt_key(self, df, idx=None):
        """Returns string-valued key for use in grouping the rows of *df* by
        experiment.

        .. note::
           We can't just do a .groupby on column names, because pandas attempts
           to coerce DateFrequency to a timedelta64, which overflows for static
           DateFrequency. There doesn't seem to be a way to disable this type
           coercion.
        """
        if idx is not None:   # index used in groupby
            df = df.loc[idx]
        return '|'.join(str(df[col]) for col in self.key_cols)

    def expt_key_func(self, df):
        """Function that constructs the appropriate experiment_key column
        when apply()'ed to the query results DataFrame.
        """
        return pd.Series(
            {self._expt_key_col: self.expt_key(df, idx=None)},
            dtype='object'
        )

@util.mdtf_dataclass
class DataframeQueryColumnSpec(metaclass=util.MDTFABCMeta):
    """
    - *expt_cols*: Catalog columns whose values must be the same for all
      variables being fetched. This is the most common sense in which we
      "specify an experiment."
    - *pod_expt_cols*: Catalog columns whose values must be the same for each
      POD, but may differ between PODs. An example could be spatial grid
      resolution. Defaults to the empty set.
    - *var_expt_cols*: Catalog columns whose values must "be the same for each
      variable", i.e. are irrelevant differences for our purposes but must be
      constrained to a unique value in order to uniquely specify an experiment.
      An example is the CMIP6 MIP table: the same variable can appear in
      multiple MIP tables, but the choice of table isn't relvant for PODs.
      Defaults to the empty set.

    In addition, there are specially designated column names:

    - *remote_data_col*: Name of the column in the catalog containing the
      location of the data for that row (e.g., path to a netCDF file).
    - *daterange_col*: Name of the column in the catalog containing
      :class:`util.DateRange` objects specifying the date range covered by
      the data for that row. If set to None, we assume this information isn't
      available from the catalog and date range selection logic is skipped.
    """
    expt_cols: DataFrameQueryColumnGroup = util.MANDATORY
    pod_expt_cols: DataFrameQueryColumnGroup = \
        dc.field(default_factory=DataFrameQueryColumnGroup)
    var_expt_cols: DataFrameQueryColumnGroup = \
        dc.field(default_factory=DataFrameQueryColumnGroup)
    remote_data_col: str = None
    # TODO: generate DateRange from start/end date columns
    daterange_col: str = None

    def __post__init__(self):
        pass

    @property
    def has_date_info(self):
        return (self.daterange_col is not None)

    @property
    def all_expt_cols(self):
        """Columns of the DataFrame specifying the experiment. We assume that
        specifying a valid value for each of the columns in this set uniquely
        identifies an experiment.
        """
        return tuple(set(
            self.expt_cols.cols + self.pod_expt_cols.cols \
            + self.var_expt_cols.cols
        ))

    def expt_key(self, df, idx=None):
        """Returns tuple of string-valued keys for grouping files by experiment:
        (<values of expt_key_cols>, <values of pod_expt_key_cols>,
        <values of var_expt_key_cols>).
        """
        return tuple(x.expt_key(df, idx=idx) for x in \
            (self.expt_cols, self.pod_expt_cols, self.var_expt_cols))

class DataframeQueryDataSourceBase(DataSourceBase, metaclass=util.MDTFABCMeta):
    """DataSource which queries a data catalog made available as a pandas
    DataFrame, and includes logic for selecting experiment based on column values.

    .. note::
       This implementation assumes the catalog is static and locally loaded into
       memory. (I think) the only source of this limitation is the fact that it
       uses values of the DataFrame's Index as its DataKeys, instead of storing
       the complete row contents, so this limitation could be lifted if needed.

       TODO: integrate better with general Intake API.
    """
    _DataKeyClass = DataFrameDataKey
    col_spec = util.abstract_attribute() # instance of DataframeQueryColumnSpec

    def __init__(self, case_dict, parent):
        super(DataframeQueryDataSourceBase, self).__init__(case_dict, parent)
        self.expt_keys = dict()  # Object _id -> expt_key tuple

    @property
    @abc.abstractmethod
    def df(self):
        """Synonym for the DataFrame containing the catalog."""
        pass

    @property
    def all_columns(self):
        return tuple(self.df.columns)

    @property
    def remote_data_col(self):
        col_name = self.col_spec.remote_data_col
        if col_name is None:
            raise ValueError
        return col_name

    def _query_clause(self, col_name, query_attr_name, query_attr_val):
        """Translate a single field value into a logical clause in the dataframe
        catalog query. All queryable field values are assumed to be attribute
        values on a local variable named _dict_var_name.
        """
        _attrs = 'd' # local var name used in _query_catalog

        if query_attr_name in ('min_frequency', 'max_frequency'):
            col_name = 'frequency'  # need to avoid hardcoding this

        if col_name not in self.all_columns:
            return ""
        if query_attr_val is util.NOTSET \
            or (isinstance(query_attr_val, str) and not query_attr_val):
            return ""
        elif query_attr_val is None:
            # In pandas filtering, ==, != fail on None; should convert Nones to np.nans
            return f"(`{col_name}`.isnull())"

        if isinstance(query_attr_val, util.DateRange):
            # skip, since filtering on DateRange is done separately in
            # _query_catalog, since pandas doesn't allow use of 'in' for
            # non-list membership
            return ""
        elif query_attr_name == 'min_frequency':
            return f"(`{col_name}` >= @{_attrs}.{query_attr_name})"
        elif query_attr_name == 'max_frequency':
            return f"(`{col_name}` <= @{_attrs}.{query_attr_name})"
        else:
            return f"(`{col_name}` == @{_attrs}.{query_attr_name})"

    def _query_catalog(self, var):
        """Construct and execute the query to determine whether data matching
        var is present in the catalog.

        Split off logic done here to perform the query against the catalog
        (returning a dataframe with results) from the processing of those
        results, in order to simplify overriding by child classes.
        """
        # contruct query string for non-DateRange attributes
        query_d = util.WormDict()
        query_d.update(dc.asdict(self.attrs))
        field_synonyms = getattr(self, '_query_attrs_synonyms', dict())
        query_d.update(var.query_attrs(field_synonyms))
        clauses = [self._query_clause(k, k, v) for k,v in query_d.items()]
        query_str = '&'.join(c for c in clauses if c)

        # filtering on DateRange is done here, separately, due to limitations on
        # pd.query()/pd.eval() -- arbitrary method calls not supported, at least
        # not efficiently. TODO: better implementation with <=/>= separate
        # start/end date columns.
        catalog_df = self.df
        for col_name, v in query_d.items():
            if isinstance(v, util.DateRange):
                if col_name not in catalog_df:
                    # e.g., for sample model data where date_range not in catalog
                    continue
                # select files whose date range overlaps analysis date range
                # (in case we're dealing with chunked/multi-file data)
                row_sel = catalog_df.apply(
                    (lambda r: r[col_name].overlaps(v)),
                    axis=1
                )
                catalog_df = catalog_df[row_sel]

        return catalog_df.query(
            query_str,
            local_dict={'d': util.NameSpace.fromDict(query_d)}
        )

    def check_group_daterange(self, group_df, expt_key=None, log=_log):
        """Sort the files found for each experiment by date, verify that
        the date ranges contained in the files are contiguous in time and that
        the date range of the files spans the query date range.
        """
        date_col = self.col_spec.daterange_col # abbreviate
        if not self.col_spec.has_date_info or date_col not in group_df:
            return group_df

        d_key = self.data_key(group_df, expt_key=expt_key)
        try:
            sorted_df = group_df.sort_values(by=date_col)
            # method throws ValueError if ranges aren't contiguous
            files_date_range = util.DateRange.from_contiguous_span(
                *(sorted_df[date_col].to_list())
            )
            # throws AssertionError if we don't span the query range
            assert files_date_range.contains(self.attrs.date_range)
            return sorted_df
        except ValueError:
            self._query_error_handler(
                "Noncontiguous or malformed date range in files:", d_key, log=log
            )
        except AssertionError:
            log.debug(("Eliminating expt_key since date range of files (%s) doesn't "
                "span query range (%s)."), files_date_range, self.attrs.date_range)
        except Exception as exc:
            self._query_error_handler(f"Caught exception {repr(exc)}:", d_key,
                log=log)
        # hit an exception; return empty DataFrame to signify failure
        return pd.DataFrame(columns=group_df.columns)

    def _query_group_hook(self, group_df):
        """Additional filtering to do on query results for a single experiment,
        for use by child classes.
        """
        return group_df

    def query_dataset(self, var):
        """Find all rows of the catalog matching relevant attributes of the
        DataSource and of the variable (:class:`~diagnostic.VarlistEntry`).
        Group these by experiments, and for each experiment make the corresponding
        :class:`DataFrameDataKey` and store it in var's *data* attribute.
        Specifically, the *data* attribute is a dict mapping experiments
        (labeled by experiment_keys) to data found for that variable
        by this query (labeled by the DataKeys).
        """
        query_df = self._query_catalog(var)
        # assign set of sets of catalog row indices to var's data attr
        # filter out empty entries = queries that failed.
        expt_groups = query_df.groupby(
            by=(lambda idx: self.col_spec.expt_key(query_df, idx))
        )
        var.data = util.ConsistentDict()
        for expt_key, group in expt_groups:
            group = self.check_group_daterange(group, expt_key=expt_key, log=var.log)
            if group.empty:
                var.log.debug('Expt_key %s eliminated by _check_group_daterange',
                    expt_key)
                continue
            group = self._query_group_hook(group)
            if group.empty:
                var.log.debug('Expt_key %s eliminated by _query_group_hook', expt_key)
                continue
            d_key = self.data_key(group, expt_key=expt_key)
            var.log.debug('Query found <expt_key=%s, %s> for %s',
                expt_key, d_key, var.full_name)
            var.data[expt_key] = d_key

    def _query_error_handler(self, msg, d_key, log=_log):
        """Log debugging message or raise an exception, depending on if we're
        in strict mode.
        """
        err_str = msg + '\n' + textwrap.indent(str(d_key.remote_data()), 4*' ')
        if self.strict:
            raise util.DataQueryEvent(err_str, d_key)
        else:
            log.warning(err_str)

    # --------------------------------------------------------------

    def _expt_df(self, obj, var_iterator, col_group, parent_id=None, obj_name=None):
        """Return a DataFrame of partial experiment attributes (as determined by
        *cols*) that are shared by the query results of all variables covered by
        var_iterator.
        """
        key_col = col_group._expt_key_col # name of the column for the expt_key
        cols = list(col_group.cols) # DataFrame requires list
        if not cols:
            # short-circuit construction for trivial case (no columns in expt_key)
            return pd.DataFrame({key_col: [""]}, dtype='object')

        expt_df = None
        if parent_id is None:
            parent_key = tuple()
        else:
            parent_key = self.expt_keys[parent_id]
        if obj_name is None:
            obj_name = obj.name

        for v in var_iterator:
            if v.stage < diagnostic.VarlistEntryStage.QUERIED:
                continue
            rows = set([])
            for d_key in v.iter_data_keys():
                # filter vars on the basis of previously selected expt attributes
                if d_key.expt_key[:len(parent_key)] == parent_key:
                    rows.update(util.to_iter(d_key.value))
            v_expt_df = self.df[cols].loc[list(rows)].drop_duplicates().copy()
            v_expt_df[key_col] = v_expt_df.apply(col_group.expt_key_func, axis=1)
            if v_expt_df.empty:
                # should never get here
                raise util.DataExperimentEvent(("No choices of expt attrs "
                    f"for {v.full_name} in {obj_name}."), v)
            v.log.debug('%s expt attr choices for %s from %s',
                len(v_expt_df), obj_name, v.full_name)

            # take intersection with possible values of expt attrs from other vars
            if expt_df is None:
                expt_df = v_expt_df.copy()
            else:
                expt_df = pd.merge(
                    expt_df, v_expt_df,
                    how='inner', on=key_col, sort=False, validate='1:1'
                )
            if expt_df.empty:
                raise util.DataExperimentEvent(("Eliminated all choices of experiment "
                    f"attributes for {obj_name} when adding {v.full_name}."), v)

        if expt_df.empty:
            # shouldn't get here
            raise util.DataExperimentEvent(f"No active variables for {obj_name}.", None)
        obj.log.debug('%s expt attr choices for %s', len(expt_df), obj_name)
        return expt_df

    def get_expt_key(self, scope, obj, parent_id=None):
        """Set experiment attributes with case, pod or variable *scope*. Given
        *obj*, construct a DataFrame of epxeriment attributes that are found in
        the queried data for all variables in *obj*.

        If more than one choice of experiment is possible, call
        DataSource-specific heuristics in resolve_func to choose between them.
        """
        # set columns and tiebreaker function based on the scope of the
        # selection process we're at (case-wide, pod-wide or var-wide):
        if scope == 'case':
            col_group = self.col_spec.expt_cols
            resolve_func = self.resolve_expt
            obj_name = obj.name
            var_iterator = obj.iter_vars_only(active=True)
        elif scope == 'pod':
            col_group = self.col_spec.pod_expt_cols
            resolve_func = self.resolve_pod_expt
            if isinstance(obj, diagnostic.Diagnostic):
                obj_name = obj.name
                var_iterator = obj.iter_children(status=core.ObjectStatus.ACTIVE)
            else:
                obj_name = 'all PODs'
                var_iterator = obj.iter_vars_only(active=True)
        elif scope == 'var':
            col_group = self.col_spec.var_expt_cols
            resolve_func = self.resolve_var_expt
            if isinstance(obj, diagnostic.VarlistEntry):
                obj_name = obj.name
                var_iterator = [obj]
            else:
                obj_name = "all POD's variables"
                var_iterator = obj.iter_children(status=core.ObjectStatus.ACTIVE)
        else:
            raise TypeError()
        key_col = col_group._expt_key_col # name of the column for the expt_key

        # get DataFrame of allowable (consistent) choices
        expt_df = self._expt_df(obj, var_iterator, col_group, parent_id, obj_name)

        if len(expt_df) > 1:
            if self.strict:
                raise util.DataExperimentEvent((f"Experiment attributes for {obj_name} "
                    f"not uniquely specified by user input in strict mode."))
            else:
                expt_df = resolve_func(expt_df, obj)
        if expt_df.empty:
            raise util.DataExperimentEvent(("Eliminated all consistent "
                f"choices of experiment attributes for {obj_name}."))
        elif len(expt_df) > 1:
            raise util.DataExperimentEvent((f"Experiment attributes for "
                f"{obj_name} not uniquely specified by user input: "
                f"{expt_df[key_col].to_list()}"))

        # successful exit case: we've narrowed down the attrs to a single choice
        expt_key = (expt_df[key_col].iloc[0], )
        if parent_id is not None:
            expt_key = self.expt_keys[parent_id] + expt_key
        return expt_key

    def set_expt_key(self, obj, expt_key):
        # Take last entry because each level of scope in get_expt_key adds
        # an entry to the overall expt_key tuple
        key_str = str(expt_key[-1])
        if key_str:
            obj.log.debug("Setting experiment_key for '%s' to '%s'",
                obj.name, key_str)
        self.expt_keys[obj._id] = expt_key

    def set_experiment(self):
        """Ensure that all data we're about to fetch comes from the same experiment.
        If data from multiple experiments was returned by the query that just
        finished, either employ data source-specific heuristics to select one
        or return an error.
        """
        # set attributes that must be the same for all variables
        if self.failed:
            raise util.DataExperimentEvent((f"Aborting experiment selection "
                f"for '{self.name}' due to failure."))
        key = self.get_expt_key('case', self)
        self.set_expt_key(self, key)

        # set attributes that must be the same for all variables in each POD
        try:
            # attempt to choose same values for all PODs
            key = self.get_expt_key('pod', self, self._id)
            for p in self.iter_children(status=core.ObjectStatus.ACTIVE):
                self.set_expt_key(p, key)
        except Exception: # util.DataExperimentEvent:
            # couldn't do that, so allow different choices for each POD
            for p in self.iter_children(status=core.ObjectStatus.ACTIVE):
                try:
                    key = self.get_expt_key('pod', p, self._id)
                    self.set_expt_key(p, key)
                except Exception as exc:
                    exc = util.DataExperimentEvent("set_experiment() on POD-level "
                        f"experiment attributes for '{p.name}' failed ({repr(exc)}).")
                    p.deactivate(exc)
                    continue

        # Resolve irrelevant attrs. Try to choose as many values to be the same
        # as possible, to minimize the number of files we need to fetch
        try:
            # attempt to choose same values for each POD:
            for pv in self.iter_vars(active=True):
                key = self.get_expt_key('var', pv.pod, pv.pod._id)
                self.set_expt_key(pv.var, key)
        except Exception: # util.DataExperimentEvent:
            # couldn't do that, so allow different choices for each variable
            for pv in self.iter_vars(active=True):
                try:
                    key = self.get_expt_key('var', pv.var, pv.pod._id)
                    self.set_expt_key(pv.var, key)
                except Exception as exc:
                    exc = util.DataExperimentEvent("set_experiment() on variable-level "
                        f"experiment attributes for '{pv.var.name}' failed ({repr(exc)})."),
                    pv.var.deactivate(exc)
                    continue

        # finally designate selected experiment by setting its DataKeys to ACTIVE
        for v in self.iter_vars_only(active=True):
            expt_key = self.expt_keys[v._id]
            assert expt_key in v.data
            d_key = v.data[expt_key]
            assert d_key.expt_key == expt_key
            d_key.log.debug("%s selected as part of experiment_key '%s'.",
                d_key, expt_key)
            d_key.status = core.ObjectStatus.ACTIVE

    def resolve_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be
        specified by child classes.
        """
        if self.col_spec.expt_cols.key_cols:
            raise NotImplementedError
        return expt_df

    def resolve_pod_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be
        specified by child classes.
        """
        if self.col_spec.pod_expt_cols.key_cols:
            raise NotImplementedError
        return expt_df

    def resolve_var_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be
        specified by child classes.
        """
        if self.col_spec.var_expt_cols.key_cols:
            raise NotImplementedError
        return expt_df


class OnTheFlyFilesystemQueryMixin(metaclass=util.MDTFABCMeta):
    """Mixin that creates an intake_esm.esm_datastore catalog by using a regex
    (\_FileRegexClass) to query the existence of data files on a remote
    filesystem.

    For the purposes of this class, all data attributes are inferred only from
    filea nd directory naming conventions: the contents of the files are not
    examined (i.e., the data files are not read from) until they are fetched to
    a local filesystem.

    .. note::
       At time of writing, the `filename parsing
       <https://www.anaconda.com/blog/intake-parsing-data-from-filenames-and-paths>`__
       functionality included in `intake
       <https://intake.readthedocs.io/en/latest/index.html>`__ is too limited to
       correctly parse our use cases, which is why we use the
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

    @abc.abstractmethod
    def generate_catalog(self):
        """Method (to be implemented by child classes) which returns the data
        catalog as a Pandas DataFrame. One of the columns of the DataFrame must
        have the name returned by :meth:`remote_data_col` and contain paths to
        the files.
        """
        pass

    def setup_query(self):
        """Generate an intake_esm catalog of files found in CATALOG_DIR.
        Attributes of files listed in the catalog (columns of the DataFrame) are
        taken from the match groups (fields) of the class's \_FileRegexClass.
        """
        self.log.info('Starting data file search at %s:', self.CATALOG_DIR)
        self.catalog = intake_esm.core.esm_datastore.from_df(
            self.generate_catalog(),
            esmcol_data = self._dummy_esmcol_spec(),
            progressbar=False, sep='|'
        )

class OnTheFlyDirectoryHierarchyQueryMixin(
    OnTheFlyFilesystemQueryMixin, metaclass=util.MDTFABCMeta
):
    """Mixin that creates an intake_esm.esm_datastore catalog on-the-fly by
    crawling a directory hierarchy and populating catalog entry attributes
    by running a regex (\_FileRegexClass) against the paths of files in the
    directory hierarchy.
    """
    # optional regex to speed up directory crawl to skip non-matching directories
    # without examining all files; default below is to not skip any directories
    _DirectoryRegex = util.RegexPattern(".*")

    def iter_files(self):
        """Generator that yields instances of \_FileRegexClass generated from
        relative paths of files in CATALOG_DIR. Only paths that match the regex
        in \_FileRegexClass are returned.
        """
        # in case CATALOG_DIR is subset of CASE_ROOT_DIR
        path_offset = len(os.path.join(self.attrs.CASE_ROOT_DIR, ""))
        for root, _, files in os.walk(self.CATALOG_DIR):
            try:
                self._DirectoryRegex.match(root[path_offset:])
            except util.RegexParseError:
                continue
            if not self._DirectoryRegex.is_matched:
                continue
            for f in files:
                if f.startswith('.'):
                    continue
                try:
                    path = os.path.join(root, f)
                    yield self._FileRegexClass.from_string(path, path_offset)
                except util.RegexSuppressedError:
                    # decided to silently ignore this file
                    continue
                except Exception:
                    self.log.info("  Couldn't parse path '%s'.", path[path_offset:])
                    continue

    def generate_catalog(self):
        """Crawl the directory hierarchy via :meth:`iter_files` and return the
        set of found files as rows in a Pandas DataFrame.
        """
        # DataFrame constructor must be passed list, not just an iterable
        df = pd.DataFrame(list(self.iter_files()), dtype='object')
        if len(df) == 0:
            self.log.critical('Directory crawl did not find any files.')
            raise AssertionError('Directory crawl did not find any files.')
        else:
            self.log.info("Directory crawl found %d files.", len(df))
        return df

FileGlobTuple = collections.namedtuple(
    'FileGlobTuple', 'name glob attrs'
)
FileGlobTuple.__doc__ = """
    Class representing one file glob pattern. *attrs* is a dict containing the
    data catalog values that will be associated with all files found using *glob*.
    *name* is used for logging only.
"""

class OnTheFlyGlobQueryMixin(
    OnTheFlyFilesystemQueryMixin, metaclass=util.MDTFABCMeta
):
    """Mixin that creates an intake_esm.esm_datastore catalog on-the-fly by
    searching for files with (python's implementation of) the shell
    :py:mod:`glob` syntax.

    We still invoke \_FileRegexClass to parse the paths, but the expected use
    case is that this will be the trivial regex (matching everything, with no
    labeled match groups), since the file selection logic is being handled by
    the globs. If you know your data is stored according to some relevant
    structure, you should use :class:`OnTheFlyDirectoryHierarchyQueryMixin`
    instead.
    """
    @abc.abstractmethod
    def iter_globs(self):
        """Iterator returning :class:`FileGlobTuple` instances. The generated
        catalog contains the union of the files found by each of the globs.
        """
        pass

    def iter_files(self, path_glob):
        """Generator that yields instances of \_FileRegexClass generated from
        relative paths of files in CATALOG_DIR. Only paths that match the regex
        in \_FileRegexClass are returned.
        """
        path_offset = len(os.path.join(self.attrs.CASE_ROOT_DIR, ""))
        if not os.path.isabs(path_glob):
            path_glob = os.path.join(self.CATALOG_DIR, path_glob)
        for path in glob.iglob(path_glob, recursive=True):
            yield self._FileRegexClass.from_string(path, path_offset)

    def generate_catalog(self):
        """Build the catalog from the files returned from the set of globs
        provided by :meth:`rel_path_globs`.
        """
        catalog_df = pd.DataFrame(dtype='object')
        for glob_tuple in self.iter_globs():
            # DataFrame constructor must be passed list, not just an iterable
            df = pd.DataFrame(
                list(self.iter_files(glob_tuple.glob)),
                dtype='object'
            )
            if len(df) == 0:
                self.log.critical("No files found for '%s' with pattern '%s'.",
                    glob_tuple.name, glob_tuple.glob)
                raise AssertionError((f"No files found for '{glob_tuple.name}' "
                    f"with pattern '{glob_tuple.glob}'."))
            else:
                self.log.info("%d files found for '%s'.", len(df), glob_tuple.name)

            # add catalog attributes specific to this set of files
            for k,v in glob_tuple.attrs.items():
                df[k] = v
            catalog_df = catalog_df.append(df)
        # need to fix repeated indices from .append()ing
        return catalog_df.reset_index(drop=True)

class LocalFetchMixin(AbstractFetchMixin):
    """Mixin implementing data fetch for files on a locally mounted filesystem.
    No data is transferred; we assume that xarray can open the paths directly.
    Paths are unaltered and set as variable's *local_data*.
    """
    def fetch_dataset(self, var, d_key):
        paths = d_key.remote_data()
        if isinstance(paths, pd.Series):
            paths = paths.to_list()
        if not util.is_iterable(paths):
            paths = (paths, )
        for path in paths:
            if not os.path.exists(path):
                raise util.DataFetchEvent((f"Fetch {d_key} ({var.full_name}): "
                    f"File not found at {path}."), var)
            else:
                self.log.debug("Fetch %s: found %s.", d_key, path)
        d_key.local_data = paths


class LocalFileDataSource(
    OnTheFlyDirectoryHierarchyQueryMixin, LocalFetchMixin,
    DataframeQueryDataSourceBase
):
    """DataSource for dealing data in a regular directory hierarchy on a
    locally mounted filesystem. Assumes data for each variable may be split into
    several files according to date, with the dates present in their filenames.
    """
    def __init__(self, case_dict, parent):
        self.catalog = None
        super(LocalFileDataSource, self).__init__(case_dict, parent)


class SingleLocalFileDataSource(LocalFileDataSource):
    """DataSource for dealing data in a regular directory hierarchy on a
    locally mounted filesystem. Assumes all data for each variable (in each
    experiment) is contained in a single file.
    """
    def query_dataset(self, var):
        """Verify that only a single file was found from each experiment.
        """
        super(SingleLocalFileDataSource, self).query_dataset(var)
        for d_key in var.data.values():
            if len(d_key.value) != 1:
                self._query_error_handler(
                    "Query found multiple files when one was expected:",
                    d_key, log=var.log
                )
