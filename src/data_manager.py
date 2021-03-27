"""Base classes implementing logic for querying, fetching and preprocessing 
model data requested by the PODs.
"""
import os
import abc
import collections
import dataclasses
import glob
import itertools
import re
import signal
from src import util, core, diagnostic, preprocessor
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
        """Returns list of identifiers for fetched data (paths to locally 
        downloaded copies of data) or raises an exception."""
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
        """Returns list of identifiers for fetched data (paths to locally 
        downloaded copies of data) or raises an exception."""
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
    date_range: util.DateRange = dataclasses.field(init=False)
    CASE_ROOT_DIR: str = ""
    convention: str = util.MANDATORY

    def _set_case_root_dir(self):
        config = core.ConfigManager()
        if not self.CASE_ROOT_DIR and config.CASE_ROOT_DIR:
            _log.debug("Using global CASE_ROOT_DIR = '%s'.", config.CASE_ROOT_DIR)
            self.CASE_ROOT_DIR = config.CASE_ROOT_DIR
        # verify case root dir exists
        if not os.path.isdir(self.CASE_ROOT_DIR):
            _log.critical("Data directory CASE_ROOT_DIR = '%s' not found.",
                self.CASE_ROOT_DIR)
            exit(1)

    def __post_init__(self):
        self._set_case_root_dir()
        self.date_range = util.DateRange(self.FIRSTYR, self.LASTYR)

        # validate convention name
        translate = core.VariableTranslator()
        if not self.convention:
            raise util.GenericDataSourceError((f"'convention' not configured "
                f"for {self.__class__.__name__}."))
        self.convention = translate.get_convention_name(self.convention)


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
        translate = core.VariableTranslator()
        self._id = 0
        self.id_number = itertools.count(start=1) # IDs for PODs, vars
        self.strict = config.get('strict', False)
        self.attrs = util.coerce_to_dataclass(
            case_dict, self._AttributesClass, init=True
        )
        self.pods = case_dict.get('pod_list', [])
        # data_key -> local path of successfully fetched data
        self.local_data = dict()
        # VarlistEntry _id -> list of data_keys for which preprocessing failed
        self.failed_data = collections.defaultdict(list)
        self.exceptions = util.ExceptionQueue()

        # configure case-specific env vars
        self.env_vars = util.WormDict.from_struct(
            config.global_env_vars.copy()
        )
        self.env_vars.update({
            k: case_dict[k] for k in ("CASENAME", "FIRSTYR", "LASTYR")
        })
        # add naming-convention-specific env vars 
        convention_obj = translate.get_convention(self.attrs.convention)
        self.env_vars.update(getattr(convention_obj, 'env_vars', dict()))

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

    def update_active_pods(self):
        # logic differs from VarlistEntry->POD propagation
        # because POD is active if & only if it hasn't failed
        _log.debug("Updating active PODs for CASENAME '%s'", self.name)
        if self.failed:
            self.deactivate_if_failed()
            return
        for pod in self.iter_pods(active=True):
            pod.update_active_vars()
        self.deactivate_if_failed()

    def deactivate_if_failed(self):
        """Deactivate this DataSource if all requested PODs have failed, and
        deactivate all PODs for this DataSource if the DataSource has failed 
        through a non-POD-specific mechanism.
        """
        # logic differs from VarlistEntry->POD propagation
        # because POD is active if & only if it hasn't failed
        if not any(self.iter_pods(active=True)):
            try:
                raise util.GenericDataSourceError((f"No active PODs remaining "
                    f"for CASENAME {self.name}."))
            except Exception as exc:
                self.exceptions.log(exc)

        if self.failed:
            # Originating exception will have been logged at a higher priority?
            _log.debug("Execution for CASENAME '%s' couldn't be completed successfully.", 
                self.name)
            for p in self.iter_pods(active=True):
                try:
                    raise util.GenericDataSourceError((f"Deactivating POD '{p.name}' "
                        f"due to unrecoverable error processing CASENAME {self.name}."))
                except Exception as exc:
                    p.exceptions.log(exc)
                p.deactivate_if_failed()

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
                _log.exception(exc)
                try:
                    raise util.PodConfigError((f"Caught {repr(exc)} in DataManager "
                        f"setup. Deactivating {pod.name}."), pod) from exc
                except Exception as chained_exc:
                    _log.error(chained_exc)
                    pod.exceptions.log(chained_exc)    
                continue

        self.deactivate_if_failed()
        _log.debug('#' * 70)
        _log.debug('Pre-query varlists for %s:', self.name)
        for v in self.iter_vars(active=None, active_pods=None):
            _log.debug("%s", v.debug_str())
        _log.debug('#' * 70)

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
                _log.exception(exc)
                try:
                    raise util.PodConfigError((f"Caught {repr(exc)} when configuring "
                        f"{v.full_name}; deactivating."), pod) from exc
                except Exception as chained_exc:
                    _log.error(chained_exc)
                v.deactivate(exc)  
                # pod.update_active_vars() "catches" this and sets v.active=False
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
        translate = core.VariableTranslator().get_convention(self.attrs.convention)
        v.change_coord(
            'T',
            new_class = {
                'self': diagnostic.VarlistTimeCoordinate,
                'range': util.DateRange,
                'frequency': util.DateFrequency
            },
            range=self.attrs.date_range
        )
        v._id = next(self.id_number)
        v.dest_path = self.variable_dest_path(pod, v)
        try:
            trans_v = translate.translate(v)
            v.translation = trans_v
        except KeyError as exc:
            _log.warning("Deactivating %s due to translation failure (%s).", 
                v.full_name, exc)
            v.deactivate(exc) 
        v.status = diagnostic.VarlistEntryStatus.INITED

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

    def is_fetch_necessary(self, d_key, var=None):
        if d_key in self.local_data:
            _log.debug("Already successfully downloaded data_key=%s.", d_key)
            return False
        if d_key in self.failed_data[self._id]:
            _log.debug("Already failed to fetch data_key=%s; not retrying.", 
                d_key)
            return False
        if var is not None and (d_key in self.failed_data[var._id]):
            # preprocessing failed on this d_key for this var (redundant condition)
            _log.debug("Preprocessing failed for data_key=%s; not retrying fetch.", 
                d_key)
            return False
        return True

    def iter_valid_remote_data(self, v):
        """Yield expt_key:data_key tuples from v's remote_data dict, filtering 
        out those data_keys that have been eliminated via previous failures in
        fetching or preprocessing.
        """
        failed_dkeys = set(self.failed_data[self._id])
        failed_dkeys.update(self.failed_data[v._id])
        yield from filter(
            (lambda kv: kv[1] not in failed_dkeys), 
            v.remote_data.items()
        )

    def eliminate_data_key(self, d_key, var=None):
        """Mark a query result (represented by a data_key) as invalid due to 
        failures in fetch or preprocessing. If all query results for a 
        VarlidstEntry are invalidated, deactivate it.
        """
        def _check_variable(v):
            if v.status < diagnostic.VarlistEntryStatus.QUERIED:
                return
            if not any(self.iter_valid_remote_data(v)):
                # all data_keys obtained for this var during query have
                # been eliminated, so need to deactivate var
                dk_list = list(v.remote_data.values())
                _log.debug("Deactivating %s since all data_keys eliminated (%s).",
                    v.full_name, dk_list)
                try:
                    raise util.GenericDataSourceError((f"Deactivating {v.full_name} "
                        f"since all data_keys eliminated ({dk_list})."), v)
                except Exception as exc:
                    v.deactivate(exc)

        if var is None:
            # eliminate data_key for all vars (failed during fetch)
            _log.debug("Eliminating data_key=%s for all vars.", d_key)
            self.failed_data[self._id].append(d_key)
            for v in self.iter_vars(active=True):
                _check_variable(v)
        else:
            # eliminate data_key for this var only (failed during preprocess)
            _log.debug("Eliminating data_key=%s for %s.", d_key, var.full_name)
            self.failed_data[var._id].append(d_key)
            _check_variable(var)

    def query_data(self):
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(5): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time.
            if update:
                self.update_active_pods()
                update = False
            vars_to_query = [
                v for v in self.iter_vars(active=True) \
                    if v.status < diagnostic.VarlistEntryStatus.QUERIED
            ]
            if not vars_to_query:
                break # exit: queried everything or nothing active
            
            _log.debug('Query batch: [%s]', 
                ', '.join(v.full_name for v in vars_to_query))
            self.pre_query_hook(vars_to_query)
            for v in vars_to_query:
                try:
                    _log.info("Querying %s", v.translation)
                    self.query_dataset(v) # sets v.remote_data
                    if not v.remote_data:
                        raise util.DataQueryError("No data found.", v)
                    v.status = diagnostic.VarlistEntryStatus.QUERIED
                except util.DataQueryError as exc:
                    update = True
                    _log.info("No data found for %s.", v.translation)
                    v.deactivate(exc)
                    continue
                except Exception as exc:
                    update = True
                    _log.exception("Caught exception querying %s: %r", 
                        v.translation, exc)
                    try:
                        raise util.DataQueryError(("Caught exception while querying "
                            f"{v.translation} for {v.full_name}."), v) from exc
                    except Exception as chained_exc:
                        v.deactivate(chained_exc)
                    continue
            self.post_query_hook(vars_to_query)
        else:
            # only hit this if we don't break
            raise util.DataQueryError(
                f"Too many iterations in {self.__class__.__name__}.query_data()."
            )

    def select_data(self):
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(5): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time.
            if update:
                self.query_data()
                self.update_active_pods()
                update = False
            # this loop differs from the others in that logic isn't/can't be 
            # done on a per-variable basis, so we just try to execute
            # set_experiment() successfully
            try:
                self.set_experiment()
            except util.DataExperimentError:
                # couldn't set consistent experiment attributes, so deactivate
                # problematic pods/vars and try again
                update = True
                self.update_active_pods()
            except Exception as exc:
                _log.exception("Caught exception setting experiment: %r", exc)
                raise exc
            break # successful exit
        else:
            # only hit this if we don't break
            raise util.DataQueryError(
                f"Too many iterations in {self.__class__.__name__}.select_data()."
            )

    def fetch_data(self):
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(5): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time and query them.
            if update:
                self.select_data()
                self.update_active_pods()
                update = False
            vars_to_fetch = [
                v for v in self.iter_vars(active=True) \
                    if v.status < diagnostic.VarlistEntryStatus.FETCHED
            ]
            if not vars_to_fetch:
                break # exit: fetched everything or nothing active

            _log.debug('Fetch batch: [%s]', 
                ', '.join(v.full_name for v in vars_to_fetch))
            self.pre_fetch_hook(vars_to_fetch)
            for v in vars_to_fetch:
                try:
                    _log.info("Fetching %s", v)

                    # fetch on a per-data_key basis
                    for data_key in self.iter_data_keys(v):
                        try:
                            if not self.is_fetch_necessary(data_key):
                                continue
                            _log.debug("Fetching data_key=%s", data_key)
                            self.local_data[data_key] = \
                                self.fetch_dataset(v, self.remote_data(data_key))
                        except Exception as exc:
                            update = True
                            self.eliminate_data_key(data_key)
                            break # no point continuing

                    # check if var received everything
                    for data_key in self.iter_data_keys(v):
                        if not self.local_data.get(data_key, None):
                            raise util.DataFetchError("Fetch failed.", data_key)
                        else:
                            paths = util.to_iter(self.local_data[data_key])
                            v.local_data.extend(paths)
                    v.status = diagnostic.VarlistEntryStatus.FETCHED
                except util.DataFetchError as exc:
                    update = True
                    _log.info("Fetch failed for %s.", v)
                    v.deactivate(exc)
                    continue
                except Exception as exc:
                    update = True
                    _log.exception("Caught exception fetching %s: %r", v, exc)
                    try:
                        raise util.DataFetchError(("Caught exception while "
                            f"fetching data for {v.full_name}."), v) from exc
                    except Exception as chained_exc:
                        v.deactivate(chained_exc)
                    continue
            self.post_fetch_hook(vars_to_fetch)
        else:
            # only hit this if we don't break
            raise util.DataFetchError(
                f"Too many iterations in {self.__class__.__name__}.fetch_data()."
            )

    def preprocess_data(self):
        """Hook to run the preprocessing function on all variables.
        """
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(5): 
            # refresh list of active variables/PODs; find alternate vars for any
            # vars that failed since last time and fetch them.
            if update:
                self.fetch_data()
                self.update_active_pods()
                update = False
            vars_to_process = [
                pv for pv in self.iter_pod_vars(active=True) \
                    if pv.var.status < diagnostic.VarlistEntryStatus.PREPROCESSED
            ]
            if not vars_to_process:
                break # exit: processed everything or nothing active

            for pod, v in vars_to_process:
                try:
                    _log.info("Processing %s", v)
                    pod.preprocessor.process(v)
                    v.status = diagnostic.VarlistEntryStatus.PREPROCESSED
                except Exception as exc:
                    update = True
                    _log.exception("Caught exception processing %s with data_key=%s: %r", 
                        v, ', '.join(str(k) for k in self.iter_data_keys(v)), exc)
                    for k in self.iter_data_keys(v):
                        self.eliminate_data_key(k, v)
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
        self.deactivate_if_failed()
        try:
            self.preprocess_data()
        except Exception as exc:
            _log.exception(f"Caught DataSource-level exception: {repr(exc)}.")
            self.exceptions.log(exc)
        # clean up regardless of success/fail
        self.deactivate_if_failed()
        self.post_query_and_fetch_hook()

    def query_and_fetch_cleanup(self, signum=None, frame=None):
        """Called if framework is terminated abnormally. Not called during
        normal exit.
        """
        util.signal_logger(self.__class__.__name__, signum, frame)
        self.post_query_and_fetch_hook()
        exit(1)

# --------------------------------------------------------------------------

class DataframeQueryDataSourceBase(DataSourceBase, metaclass=util.MDTFABCMeta):
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
        super(DataframeQueryDataSourceBase, self).__init__(case_dict)
        self.expt_keys = dict() # _id -> expt_key tuple

    @property
    @abc.abstractmethod
    def df(self):
        """Synonym for the DataFrame containing the catalog."""
        pass

    # Name of the column in the catalog containing the location (eg, the path)
    # of the data for that row.
    remote_data_col = util.abstract_attribute()

    # column of the DataFrame containing util.DateRange objects 
    # If 'None', date range selection logic is skipped.
    # TODO: generate DateRange from start/end date columns
    daterange_col = None

    @property
    def has_date_info(self):
        return (self.daterange_col is not None)

    # Catalog columns whose values must be the same for all variables being
    # fetched. This is the most common sense in which we "specify an experiment."
    expt_key_cols = util.abstract_attribute()
    expt_cols = util.abstract_attribute()

    # Catalog columns whose values must be the same for each POD, but may differ
    # between PODs. An example could be spatial grid resolution.
    pod_expt_key_cols = tuple()
    pod_expt_cols = tuple()

    # Catalog columns whose values must "be the same for each variable", ie are 
    # irrelevant differences for our purposes but must be constrained to a 
    # unique value. An example is the CMIP6 MIP table: the same variable can 
    # appear in multiple MIP tables, but the choice of table isn't relvant for PODs.
    var_expt_key_cols = tuple()
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
        if query_attr_val == util.NOTSET \
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
        query_d.update(dataclasses.asdict(self.attrs))
        field_synonyms = getattr(self, '_query_attrs_synonyms', dict())
        query_d.update(var.query_attrs(field_synonyms))
        clauses = [self._query_clause(k, k, v) for k,v in query_d.items()]
        query_str = '&'.join(c for c in clauses if c)

        # need to do filtering on DateRange separately due to limitations on
        # pd.query()/pd.eval() -- arbitrary methods not supported, at least not
        # efficiently. TODO: better implementation with <=/>= separate start/end
        # date columns.
        catalog_df = self.df
        for col_name, v in query_d.items():
            if isinstance(v, util.DateRange):
                if col_name not in catalog_df:
                    # e.g., for sample model data where date_range not in catalog
                    continue
                row_sel = catalog_df.apply((lambda r: v in r[col_name]), axis=1)
                catalog_df = catalog_df[row_sel]

        return catalog_df.query(
            query_str, 
            local_dict={'d': util.NameSpace.fromDict(query_d)}
        )

    def _experiment_key(self, df=None, idx=None, cols=None):
        """Returns tuple of string-valued keys for grouping files by experiment:
        (<values of expt_key_cols>, <values of pod_expt_key_cols>, 
        <values of var_expt_key_cols>), or individual entries in that tuple if
        *cols* is specified.

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
            # return full key
            return tuple(
                _key_str(x) for x in \
                (self.expt_key_cols, self.pod_expt_key_cols, self.var_expt_key_cols)
            )
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
        if not self.has_date_info or self.daterange_col not in group_df:
            return group_df

        data_key = self._data_key(group_df)
        try:
            sorted_df = group_df.sort_values(by=self.daterange_col)
            # method throws ValueError if ranges aren't contiguous
            files_date_range = util.DateRange.from_contiguous_span(
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
            _log.debug(("Eliminating expt_key since date range of files (%s) doesn't "
                "span query range (%s)."), files_date_range, self.attrs.date_range)
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
            group = self._check_group_daterange(group)
            if group.empty:
                _log.debug('Expt_key %s eliminated by _check_group_daterange', expt_key)
                continue
            group = self._query_group_hook(group)
            if group.empty:
                _log.debug('Expt_key %s eliminated by _query_group_hook', expt_key)
                continue
            data_key = self._data_key(group)
            _log.debug('Query found <expt_key=%s, data_key=%s> for %s',
                expt_key, data_key, var.full_name)
            var.remote_data[expt_key] = data_key

    def _query_error_logger(self, msg, data_key):
        """Log debugging message or raise an exception, depending on if we're
        in strict mode.
        """
        data_key = util.to_iter(data_key, list)
        err_str = '\n'.join(
            '\t'+str(self.df[self.remote_data_col].loc[idx]) for idx in data_key
        )
        err_str = msg + '\n' + err_str
        if self.strict:
            raise util.DataQueryError(err_str, data_key)
        else:
            _log.warning(err_str)

    # --------------------------------------------------------------

    _expt_key_col = 'expt_key' # column name for DataSource-specific experiment identifier

    def _expt_df(self, obj, cols, key_cols, parent_id=None, obj_name=None):
        """Return a DataFrame of partial experiment attributes (as determined by
        cols) that are shared by the query results of all variables covered by
        var_iterator.
        """
        cols = list(cols) # DataFrame requires list
        if not cols:
            # short-circuit construction for trivial case (empty key)
            return pd.DataFrame({self._expt_key_col: [""]}, dtype='object')

        def _key_col_func(df):
            """Function that constructs the appropriate experiment_key column 
            when apply()'ed to the query results DataFrame.
            """
            return pd.Series({
                self._expt_key_col: self._experiment_key(df, idx=None, cols=key_cols)
            }, dtype='object')

        expt_df = None
        if parent_id is None:
            parent_key = tuple()
        else:
            parent_key = self.expt_keys[parent_id]
        if obj_name is None:
            obj_name = obj.name
        if hasattr(obj, 'iter_vars'):
            var_iterator = obj.iter_vars(active=True)
        else:
            assert isinstance(obj, diagnostic.VarlistEntry)
            var_iterator = [obj]

        for v in var_iterator:
            if v.status < diagnostic.VarlistEntryStatus.QUERIED:
                continue
            rows = set([])
            for expt_key, data_key in self.iter_valid_remote_data(v):
                # filter variables on the basis of previously selected expt 
                # attributes
                if expt_key[:len(parent_key)] == parent_key:
                    rows.update(data_key)
            v_expt_df = self.df[cols].loc[list(rows)].drop_duplicates().copy()
            v_expt_df[self._expt_key_col] = v_expt_df.apply(_key_col_func, axis=1)
            if v_expt_df.empty:
                # should never get here
                raise util.DataExperimentError(("No choices of expt attrs "
                    f"for {v.full_name} in {obj_name}."), v)
            _log.debug('%s expt attr choices for %s from %s', 
                len(v_expt_df), obj_name, v.full_name)

            # take intersection with possible values of expt attrs from other vars
            if expt_df is None:
                expt_df = v_expt_df.copy()
            else:
                expt_df = pd.merge(
                    expt_df, v_expt_df, 
                    how='inner', on=self._expt_key_col, sort=False, validate='1:1'
                )
            if expt_df.empty:
                raise util.DataExperimentError(("Eliminated all choices of experiment "
                    f"attributes for {obj_name} when adding {v.full_name}."), v)

        _log.debug('%s expt attr choices for %s', len(expt_df), obj_name)
        return expt_df

    def _get_expt_key(self, stage, obj, parent_id=None):
        """Set experiment attributes at the case, pod or variable level. Given obj,
        construct a DataFrame of epxeriment attributes that are found in the 
        queried data for all variables in obj. If more than one choice of 
        experiment is possible, call DataSource-specific heuristics in resolve_func
        to choose between them. 
        """
        # set columns and tiebreaker function based on the level of the 
        # selection process we're at (case-wide, pod-wide or var-wide):
        if stage == 'case':
            df_cols = self.expt_cols
            df_key_cols = self.expt_key_cols
            resolve_func = self.resolve_expt
            obj_name = obj.name
        elif stage == 'pod':
            df_cols = self.pod_expt_cols
            df_key_cols = self.pod_expt_key_cols
            resolve_func = self.resolve_pod_expt
            if isinstance(obj, diagnostic.Diagnostic):
                obj_name = obj.name
            else:
                obj_name = 'all PODs'
        elif stage == 'var':
            df_cols = self.var_expt_cols
            df_key_cols = self.var_expt_key_cols
            resolve_func = self.resolve_var_expt
            if isinstance(obj, diagnostic.VarlistEntry):
                obj_name = obj.name
            else:
                obj_name = "all POD's variables"
        else:
            raise TypeError()

        # get DataFrame of allowable (consistent) choices
        expt_df = self._expt_df(obj, df_cols, df_key_cols, parent_id, obj_name)
        
        if len(expt_df) > 1:
            if self.strict:
                raise util.DataExperimentError((f"Experiment attributes for {obj_name} "
                    f"not uniquely specified by user input in strict mode."))
            else:
                expt_df = resolve_func(expt_df, obj)
        if expt_df.empty:
            raise util.DataExperimentError(("Eliminated all consistent "
                f"choices of experiment attributes for {obj_name}."))
        elif len(expt_df) > 1:  
            raise util.DataExperimentError((f"Experiment attributes for "
                f"{obj_name} not uniquely specified by user input: "
                f"{expt_df[self._expt_key_col].to_list()}"))

        # successful exit case: we've narrowed down the attrs to a single choice        
        expt_key = (expt_df[self._expt_key_col].iloc[0], )
        if parent_id is not None:
            expt_key = self.expt_keys[parent_id] + expt_key
        return expt_key

    def set_experiment(self):
        """Ensure that all data we're about to fetch comes from the same experiment.
        If data from multiple experiments was returned by the query that just
        finished, either employ data source-specific heuristics to select one
        or return an error. 
        """
        def _set_expt_key(obj_, key_):
            key_str = str(key_[-1])
            if key_str:
                _log.debug("Setting experiment_key for %s to '%s'", obj_.name, key_str)
            self.expt_keys[obj_._id] = key_

        # set attributes that must be the same for all variables
        if self.failed:
            raise util.DataExperimentError((f"Aborting experiment selection "
                f"for CASENAME '{self.name}' due to failure."))
        key = self._get_expt_key('case', self)
        _set_expt_key(self, key)

        # set attributes that must be the same for all variables in each POD
        try:
            # attempt to choose same values for all PODs
            key = self._get_expt_key('pod', self, self._id)
            for p in self.iter_pods(active=True):
                _set_expt_key(p, key)
        except Exception: # util.DataExperimentError:
            # couldn't do that, so allow different choices for each POD
            for p in self.iter_pods(active=True):
                try:
                    key = self._get_expt_key('pod', p, self._id)
                    _set_expt_key(p, key)
                except Exception as exc:
                    _log.warning(('set_experiment on pod-level experiment attributes: '
                        '%s caught %r; deactivating.'), p.name, exc)
                    p.exceptions.log(exc)
                    continue

        # resolve irrelevant attributes -- still try to choose as many values to
        # be the same as possible, to minimize the number of unique data files we
        # need to fetch
        try:
            # attempt to choose same values for each POD:
            for p in self.iter_pods(active=True):
                key = self._get_expt_key('var', p, p._id)
                for v in p.iter_vars(active=True):
                    _set_expt_key(v, key)
        except Exception: # util.DataExperimentError:
            # couldn't do that, so allow different choices for each variable
            for p, v in self.iter_pod_vars(active=True):
                try:
                    key = self._get_expt_key('var', v, p._id)
                    _set_expt_key(v, key)
                except Exception as exc:
                    v.exception = exc
                    continue
        
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
        """Generator iterating over data_keys belonging to the experiment 
        attributes selected for the variable var.
        """
        expt_key = self.expt_keys[var._id]
        yield var.remote_data[expt_key]
  
    def remote_data(self, data_key):
        """Given one or more row indices in the catalog's dataframe (data_keys, 
        as found by query_dataset()), return the corresponding remote_paths.
        """
        if util.is_iterable(data_key):
            # loc requires list, not just iterable
            data_key = util.to_iter(data_key, list) 
        return self.df[self.remote_data_col].loc[data_key]


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
        _log.info('Starting data file search at %s', self.CATALOG_DIR)
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
                    _log.info("Couldn't parse path %s", path[path_offset:])
                    continue

    def generate_catalog(self):
        """Crawl the directory hierarchy via :meth:`iter_files` and return the
        set of found files as rows in a Pandas DataFrame.
        """
        # DataFrame constructor must be passed list, not just an iterable
        df = pd.DataFrame(list(self.iter_files()), dtype='object')
        if len(df) == 0:
            _log.critical('Directory crawl did not find any files.')
            raise AssertionError('Directory crawl did not find any files.')
        else:
            _log.info("Directory crawl found %d files.", len(df))
        return df

FileGlobTuple = collections.namedtuple(
    'FileGlobTuple', 'name glob attrs'
)
FileGlobTuple.__doc__ = """
    Class representing one file glob pattern. 'attrs' is a dict containing the
    data catalog values that will be associated with all files found using 'glob'.
    'name' is used for logging only.
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

    def iter_files(self, rel_path_glob):
        """Generator that yields instances of \_FileRegexClass generated from 
        relative paths of files in CATALOG_DIR. Only paths that match the regex
        in \_FileRegexClass are returned.
        """
        path_offset = len(os.path.join(self.attrs.CASE_ROOT_DIR, ""))
        for path in glob.iglob(os.path.join(self.CATALOG_DIR, rel_path_glob),
            recursive=True):
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
                _log.critical("No files found for '%s' with pattern '%s'.",
                    glob_tuple.name, glob_tuple.glob)
                raise AssertionError((f"No files found for '{glob_tuple.name}' "
                    f"with pattern '{glob_tuple.glob}'."))
            else:
                _log.info("%d files found for '%s'.", len(df), glob_tuple.name)
            
            # add catalog attributes specific to this set of files
            for k,v in glob_tuple.attrs.items():
                df[k] = v
            catalog_df = catalog_df.append(df)
        return catalog_df

class LocalFetchMixin(AbstractFetchMixin):
    """Mixin implementing data fetch for files on a locally mounted filesystem. 
    No data is transferred; we assume that xarray can open the paths directly.
    Paths are returned unaltered, to be set as variable's local_data.
    """
    def fetch_dataset(self, var, paths):
        if isinstance(paths, pd.Series):
            paths = paths.to_list()
        if not util.is_iterable(paths):
            paths = (paths, )
        for path in paths:
            if not os.path.exists(path):
                raise util.DataFetchError((f"Fetch {var.full_name}: File not "
                    f"found at {path}."), var)
            else:
                _log.debug("Fetch %s: found %s.", var.full_name, path)
        return paths


class LocalFileDataSource(
    OnTheFlyDirectoryHierarchyQueryMixin, LocalFetchMixin, 
    DataframeQueryDataSourceBase
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
