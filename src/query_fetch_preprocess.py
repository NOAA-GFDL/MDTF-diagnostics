import abc
import collections
import glob
from abc import ABC
import intake_esm
import os
import pandas as pd
import signal
from src import core, diagnostic, util


FileGlobTuple = collections.namedtuple(
    'FileGlobTuple', 'name glob attrs'
)
FileGlobTuple.__doc__ = """
    Class representing one file glob pattern. *attrs* is a dict containing the
    data catalog values that will be associated with all files found using *glob*.
    *name* is used for logging only.
"""


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
        # df: DataFrame, catalog content that would otherwise be in a csv file
        # esmcol_data: Optional[Dict[str, Any]] = None, ESM collection spec information
        # progressbar: bool = True, if True, prints progress bar to standard error when loading info into xarray dataset
        # sep: str = '.', delimiter to use when constructing key for a query
        # **kwargs: Any

        self.catalog = intake_esm.core.esm_datastore.from_df(
            self.generate_catalog(),
            esmcol_data=self._dummy_esmcol_spec(),
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
            for k, v in glob_tuple.attrs.items():
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


PodVarTuple = collections.namedtuple('PodVarTuple', ['pod', 'var'])
MAX_DATASOURCE_ITERS = 5


class DataSourceQFPMixin(core.MDTFObjectBase, util.CaseLoggerMixin,
                         AbstractDataSource, ABC, metaclass=util.MDTFABCMeta):
    """Mixin implementing data query, fetch, and preprocessing-related attributes and
       methods
    """
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
                break  # exit: queried everything or nothing active

            self.log.debug('Query batch: [%s].',
                           ', '.join(v.full_name for v in vars_to_query))
            self.pre_query_hook(vars_to_query)
            for v in vars_to_query:
                try:
                    self.log.info("Querying %s.", v.translation)
                    self.query_dataset(v)  # sets v.data
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
                break  # successful exit
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
                break  # exit: fetched everything or nothing active

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
                            break  # no point continuing

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
                break  # exit: processed everything or nothing active

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


class MultirunDataSourceQFPMixin(DataSourceQFPMixin, ABC):
    """Mixin implementing data query, fetch, and preprocessing-related attributes and
       methods
    """

    @property
    def _children(self):
        """Iterable of child objects (:class:`~diagnostic.MultirunDiagnostic`\s)
        associated with this object.
        No-op because ~MDTFFramework._children provides pod data via the parent parameter
        """
        pass

    def iter_vars(self, parent, active=None, pod_active=None):
        """Iterator over all :class:`~diagnostic.VarlistEntry`\s (grandchildren)
        associated with this case. Returns :class:`PodVarTuple`\s (namedtuples)
        of the :class:`~diagnostic.Diagnostic` and :class:`~diagnostic.VarlistEntry`
        objects corresponding to the POD and its variable, respectively.

        Args:
            parent: the MultirunDiagnostic parent class instance that contains
            the pod attributes
            active: bool or None, default None. Selects subset of
                :class:`~diagnostic.VarlistEntry`\s returned in the
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
       # for p in parent.iter_children(**pod_kwargs):  # _children returns pod values for multirun mode.
            # Defined in core.MDTFFramework
        p = parent
        for v in self.iter_children(**var_kwargs):  # _children returns varlist values. Defined in data.sources
            yield PodVarTuple(pod=p, var=v)

    def iter_vars_only(self, parent, active=None):
        """Convenience wrapper for :meth:`iter_vars` that returns only the
        :class:`~MultirunDiagnostic.VarlistEntry` objects (grandchildren) from all PODs
        in this DataSource.
        """
        yield from (pv.var for pv in self.iter_vars(parent, active=active, pod_active=None))

    def query_data(self, parent):
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(MAX_DATASOURCE_ITERS):
            vars_to_query = [
                v for v in self.iter_vars_only(parent, active=True) \
                if v.stage < diagnostic.VarlistEntryStage.QUERIED
            ]
            if not vars_to_query:
                break  # exit: queried everything or nothing active

            self.log.debug('Query batch: [%s].',
                           ', '.join(v.full_name for v in vars_to_query))
            self.pre_query_hook(vars_to_query)
            for v in vars_to_query:
                try:
                    self.log.info("Querying %s.", v.translation)
                    self.query_dataset(v)  # sets v.data
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

    def select_data(self, parent):
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(MAX_DATASOURCE_ITERS):
            if update:
                # query alternates for any vars that failed since last time
                self.query_data(parent)
                update = False
            # this loop differs from the others in that logic isn't/can't be
            # done on a per-variable basis, so we just try to execute
            # set_experiment() successfully
            try:
                self.set_experiment(parent)
                break  # successful exit
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

    def fetch_data(self, parent):
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(MAX_DATASOURCE_ITERS):
            if update:
                self.select_data(parent)
                update = False
            vars_to_fetch = [
                v for v in self.iter_vars_only(parent, active=True) \
                if v.stage < diagnostic.VarlistEntryStage.FETCHED
            ]
            if not vars_to_fetch:
                break  # exit: fetched everything or nothing active

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
                            break  # no point continuing

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

    def preprocess_data(self, parent):
        """Hook to run the preprocessing function on all variables.
        """
        update = True
        # really a while-loop, but limit # of iterations to be safe
        for _ in range(MAX_DATASOURCE_ITERS):
            if update:
                # fetch alternates for any vars that failed since last time
                self.fetch_data(parent)
                update = False
            vars_to_process = [
                pv for pv in self.iter_vars(parent, active=True) \
                if pv.var.stage < diagnostic.VarlistEntryStage.PREPROCESSED
            ]
            if not vars_to_process:
                break  # exit: processed everything or nothing active

            for pod in parent.iter_children(status=core.ObjectStatus.ACTIVE):
                parent.preprocessor.setup(self, pod)
            for pv in vars_to_process:
                try:
                    pv.var.log.info("Preprocessing %s.", pv.var)
                    parent.preprocessor.process(pv.var, self.name)
 #                   pv.pod.preprocessor.process(pv.var, self.name)
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

    def request_data(self, parent):
        """Top-level method to iteratively query, fetch and preprocess all data
        requested by PODs, switching to alternate requested data as needed.
        """
        # Call cleanup method if we're killed
        signal.signal(signal.SIGTERM, self.query_and_fetch_cleanup)
        signal.signal(signal.SIGINT, self.query_and_fetch_cleanup)
        self.pre_query_and_fetch_hook()
        try:
            self.preprocess_data(parent)
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
                p.log.debug('Data request for %s completed successfully.',
                            p.full_name)

